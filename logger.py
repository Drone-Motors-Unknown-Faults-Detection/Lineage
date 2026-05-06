from __future__ import annotations

import contextlib
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from itertools import count
from pathlib import Path
from typing import IO, Iterator, Optional
import re

from loguru import logger as _logger


@dataclass(frozen=True)
class RunPaths:
    program_name: str
    timestamp: str
    logs_dir: Path
    output_dir: Path
    log_file: Path


_PLOT_COUNTER = count(0)


def save_plot(
    plt,
    log,
    run_paths: RunPaths,
    *,
    ext: str = "png",
    dpi: int = 300,
    bbox_inches: str = "tight",
) -> str:
    """
    Save current matplotlib figure into this run's output dir with an auto-increment filename.
    Returns saved file path (string).
    """
    idx = next(_PLOT_COUNTER)
    plot_path = run_paths.output_dir / f"plot_{idx:03d}.{ext}"
    plt.savefig(str(plot_path), dpi=dpi, bbox_inches=bbox_inches)
    try:
        # loguru uses `{}` formatting
        log.info("Saved plot: {}", str(plot_path))
    except Exception:
        # logger failures should not break training
        pass
    return str(plot_path)


def _safe_program_name(raw: str) -> str:
    name = Path(raw).stem
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name)
    return cleaned or "program"


def setup_logger(
    program_path: str | os.PathLike[str] | None = None,
    *,
    console: bool = True,
    level: str = "INFO",
) -> tuple[object, RunPaths]:
    """
    Create per-run log file under:
      logs/{program_name}_{yyyy-MM-DD-HH-mm-ss}/program.log

    Also prepares output directory for images/artifacts:
      output/{program_name}_{yyyy-MM-DD-HH-mm-ss}/
    """
    if program_path is None:
        program_path = sys.argv[0] if sys.argv else "program"

    program_name = _safe_program_name(str(program_path))
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    run_name = f"{program_name}_{timestamp}"

    repo_root = Path.cwd()
    logs_dir = repo_root / "logs" / run_name
    output_dir = repo_root / "output" / run_name
    logs_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / "program.log"

    _logger.remove()

    if console:
        _logger.add(
            sys.stderr, level=level, enqueue=True, backtrace=False, diagnose=False
        )

    _logger.add(
        str(log_file),
        level=level,
        enqueue=True,
        backtrace=False,
        diagnose=False,
        encoding="utf-8",
    )

    paths = RunPaths(
        program_name=program_name,
        timestamp=timestamp,
        logs_dir=logs_dir,
        output_dir=output_dir,
        log_file=log_file,
    )

    _logger.bind(program_name=program_name, run_dir=str(logs_dir))
    _logger.info("Logger initialized")
    _logger.info("log_file={}", str(log_file))
    _logger.info("output_dir={}", str(output_dir))
    return _logger, paths


class _StreamToLogger:
    def __init__(self, log_method, prefix: str = "") -> None:
        self._log_method = log_method
        self._prefix = prefix
        self._buffer: list[str] = []

    def write(self, message: str) -> int:
        if not message:
            return 0
        self._buffer.append(message)
        if "\n" in message:
            self.flush()
        return len(message)

    def flush(self) -> None:
        if not self._buffer:
            return
        text = "".join(self._buffer)
        self._buffer.clear()
        for line in text.splitlines():
            line = line.rstrip()
            if line:
                cleaned = _sanitize_console_line(line)
                if cleaned is None:
                    continue
                self._log_method(f"{self._prefix}{cleaned}")

    def isatty(self) -> bool:
        return False


@contextlib.contextmanager
def redirect_std_to_logger(
    log, *, stdout_level: str = "INFO", stderr_level: str = "ERROR"
) -> Iterator[None]:
    """
    Redirect print()/stdout/stderr into the provided loguru logger.
    """
    stdout_logger = _StreamToLogger(getattr(log, stdout_level.lower()), prefix="")
    stderr_logger = _StreamToLogger(getattr(log, stderr_level.lower()), prefix="")
    old_out: Optional[IO[str]] = sys.stdout
    old_err: Optional[IO[str]] = sys.stderr
    try:
        sys.stdout = stdout_logger  # type: ignore[assignment]
        sys.stderr = stderr_logger  # type: ignore[assignment]
        yield
    finally:
        try:
            stdout_logger.flush()
            stderr_logger.flush()
        finally:
            sys.stdout = old_out  # type: ignore[assignment]
            sys.stderr = old_err  # type: ignore[assignment]


@contextlib.contextmanager
def log_run_context(
    program_path: str | os.PathLike[str] | None = None,
    *,
    console: bool = True,
    level: str = "INFO",
) -> Iterator[tuple[object, RunPaths]]:
    """
    Convenience context manager:
      - initializes logger + run dirs
      - redirects stdout/stderr to log
    """
    log, paths = setup_logger(program_path, console=console, level=level)
    with redirect_std_to_logger(log):
        yield log, paths


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_BAR_CHARS_RE = re.compile(r"[━─│┏┓┗┛┡┢┤┬┴┼]+|[━]{2,}|[─]{2,}")
_STEP_RE = re.compile(r"^\s*(\d+/\d+)\s+")
_EPOCH_RE = re.compile(r"^\s*Epoch\s+\d+/\d+\s*$", re.IGNORECASE)
_METRIC_RE = re.compile(r"([A-Za-z_]+):\s*([0-9.+-eE]+)")
_MS_PER_STEP_RE = re.compile(r"(\d+(?:\.\d+)?)\s*ms/step")
_S_PER_STEP_RE = re.compile(r"(\d+(?::\d+)?(?:\.\d+)?)\s*s/step")


def _sanitize_console_line(line: str) -> str | None:
    """
    Turn noisy Keras progress output into stable log lines.

    - remove ANSI control sequences and backspaces
    - drop pure progress-bar glyph lines
    - keep accuracy/loss metrics by extracting them into compact text
    """
    if "\b" in line:
        line = line.replace("\b", "")
    if "\x1b[" in line:
        line = _ANSI_RE.sub("", line)

    stripped = line.strip()
    if not stripped:
        return None

    if _EPOCH_RE.match(stripped):
        return stripped

    step_match = _STEP_RE.match(stripped)
    has_metrics = any(k in stripped for k in ("accuracy:", "loss:", "val_accuracy:", "val_loss:"))
    if step_match and has_metrics:
        step = step_match.group(1)
        step_time = None
        ms_m = _MS_PER_STEP_RE.search(stripped)
        if ms_m:
            step_time = f"{ms_m.group(1)}ms/step"
        else:
            s_m = _S_PER_STEP_RE.search(stripped)
            if s_m:
                step_time = f"{s_m.group(1)}s/step"

        metrics = _METRIC_RE.findall(stripped)
        metric_text = " ".join([f"{k}={v}" for k, v in metrics])
        if step_time is not None:
            return f"{step} {step_time} {metric_text}".strip()
        return f"{step} {metric_text}".strip()

    # Drop bar-only lines.
    if "━━━━━━━━" in stripped and not has_metrics:
        return None

    stripped = stripped.replace("━━━━━━━━", " ")
    stripped = _BAR_CHARS_RE.sub(" ", stripped)
    stripped = re.sub(r"\s+", " ", stripped).strip()

    if re.fullmatch(r"\d+/\d+", stripped):
        return None

    return stripped or None