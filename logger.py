from __future__ import annotations

import contextlib
import os
import sys
import re
from dataclasses import dataclass
from datetime import datetime
from itertools import count
from pathlib import Path
from typing import IO, Iterator, Optional


@dataclass(frozen=True)
class RunPaths:
    program_name: str
    timestamp: str
    logs_dir: Path
    output_dir: Path
    log_file: Path


_PLOT_COUNTER = count(0)


def _safe_program_name(raw: str) -> str:
    name = Path(raw).stem
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name)
    return cleaned or "program"


def _detect_program_name() -> str:
    """Auto-detect the running script or notebook filename."""
    # 1. Shell script sets this before running jupyter execute
    env_name = os.environ.get("JUPYTER_NOTEBOOK_NAME", "")
    if env_name:
        return _safe_program_name(env_name)

    # 2. VS Code Jupyter sets __vsc_ipynb_file__ in the kernel namespace
    try:
        from IPython import get_ipython
        ip = get_ipython()
        if ip is not None:
            nb_file = ip.user_ns.get("__vsc_ipynb_file__")
            if nb_file:
                return _safe_program_name(str(nb_file))
    except Exception:
        pass

    # 3. Standard Python script (skip kernel launcher)
    argv0 = sys.argv[0] if sys.argv else ""
    if argv0 and "ipykernel" not in argv0:
        return _safe_program_name(argv0)

    return "program"


def _format_braces(msg: str, *args: object) -> str:
    try:
        return msg.format(*args)
    except Exception:
        if args:
            return f"{msg} {args}"
        return msg


class SimpleFileLogger:
    def __init__(self, log_file: Path) -> None:
        self.log_file = log_file

    def _write(self, level: str, msg: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts} | {level:<5} | {msg}\n"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(line)

    def info(self, msg: str, *args: object) -> None:
        self._write("INFO", _format_braces(msg, *args))

    def warning(self, msg: str, *args: object) -> None:
        self._write("WARN", _format_braces(msg, *args))

    def error(self, msg: str, *args: object) -> None:
        self._write("ERROR", _format_braces(msg, *args))


def setup_logger(
    program_path: str | os.PathLike[str] | None = None,
    *,
    console: bool = True,
    level: str = "INFO",
) -> tuple[SimpleFileLogger, RunPaths]:
    """
    Create per-run log file under:
      logs/{program_name}/{yyyy-MM-DD-HH-mm-ss}.log

    Also prepares output directory for images/artifacts:
      output/{program_name}/{yyyy-MM-DD-HH-mm-ss}/

    This logger never redirects stdout/stderr.
    """
    if program_path is None or str(program_path) == "notebook":
        program_name = _detect_program_name()
    else:
        program_name = _safe_program_name(str(program_path))
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    repo_root = Path.cwd()
    logs_dir = repo_root / "logs" / program_name
    output_dir = repo_root / "output" / program_name / timestamp
    logs_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / f"{timestamp}.log"

    global _PLOT_COUNTER
    _PLOT_COUNTER = count(0)

    paths = RunPaths(
        program_name=program_name,
        timestamp=timestamp,
        logs_dir=logs_dir,
        output_dir=output_dir,
        log_file=log_file,
    )

    log = SimpleFileLogger(log_file)
    log.info("Logger initialized")
    log.info("log_file={}", str(log_file))
    log.info("output_dir={}", str(output_dir))

    if console:
        try:
            sys.stderr.write(f"[logger] log_file={log_file}\n")
            sys.stderr.flush()
        except Exception:
            pass

    return log, paths


def save_plot(
    plt,
    log: SimpleFileLogger,
    run_paths: RunPaths,
    *,
    ext: str = "png",
    dpi: int = 300,
    bbox_inches: str = "tight",
) -> str:
    idx = next(_PLOT_COUNTER)
    plot_path = run_paths.output_dir / f"plot_{idx:03d}.{ext}"
    plt.savefig(str(plot_path), dpi=dpi, bbox_inches=bbox_inches)
    log.info("Saved plot: {}", str(plot_path))
    return str(plot_path)


class _TeeToFileStream:
    """
    Stream wrapper that writes through to the original stream (so Jupyter shows output)
    and also appends the same text to a log file.
    """

    def __init__(self, original: IO[str], log_file: Path) -> None:
        self._original = original
        self._log_file = log_file
        self._buf: str = ""

    def __getattr__(self, item: str):
        return getattr(self._original, item)

    _ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
    _STEP_RE = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s+")
    _EPOCH_RE = re.compile(r"^\s*Epoch\s+\d+/\d+\s*$", re.IGNORECASE)
    _METRIC_RE = re.compile(r"([A-Za-z_]+):\s*([0-9.+-eE]+)")
    _MS_PER_STEP_RE = re.compile(r"(\d+(?:\.\d+)?)\s*ms/step")
    _S_PER_STEP_RE = re.compile(r"(\d+(?::\d+)?(?:\.\d+)?)\s*s/step")

    @classmethod
    def _sanitize(cls, s: str) -> str:
        if "\b" in s:
            s = s.replace("\b", "")
        if "\x1b[" in s:
            s = cls._ANSI_RE.sub("", s)
        return s

    @classmethod
    def _filter_for_log(cls, line: str) -> Optional[str]:
        """
        Filter keras/tf progress output for program.log.
        Keep:
        - 'Epoch x/y'
        - final step line (e.g. '75/75 ... loss: ... val_loss: ...') summarized
        Drop:
        - intermediate step progress lines and bar glyph noise.
        """
        line = cls._sanitize(line).strip()
        if not line:
            return None

        if cls._EPOCH_RE.match(line):
            return line

        # If it's a step progress line, only keep the FINAL step, and only if it has metrics.
        m = cls._STEP_RE.match(line)
        if m:
            cur = int(m.group(1))
            total = int(m.group(2))
            if cur != total:
                return None

            has_metrics = any(k in line for k in ("accuracy:", "loss:", "val_accuracy:", "val_loss:"))
            if not has_metrics:
                return None

            step_time = None
            ms_m = cls._MS_PER_STEP_RE.search(line)
            if ms_m:
                step_time = f"{ms_m.group(1)}ms/step"
            else:
                s_m = cls._S_PER_STEP_RE.search(line)
                if s_m:
                    step_time = f"{s_m.group(1)}s/step"

            metrics = cls._METRIC_RE.findall(line)
            metric_text = " ".join([f"{k}={v}" for k, v in metrics])
            if step_time is not None:
                return f"{cur}/{total} {step_time} {metric_text}".strip()
            return f"{cur}/{total} {metric_text}".strip()

        # Drop bar-only lines (common in keras)
        if "━━━━" in line and not any(k in line for k in ("accuracy:", "loss:", "val_accuracy:", "val_loss:")):
            return None

        return line

    def _flush_to_logfile(self) -> None:
        if not self._buf:
            return
        parts = re.split(r"[\r\n]+", self._buf)
        # Keep last partial chunk in buffer (no line break yet)
        if self._buf and self._buf[-1] not in ("\n", "\r"):
            self._buf = parts[-1]
            parts = parts[:-1]
        else:
            self._buf = ""

        if not parts:
            return
        try:
            with self._log_file.open("a", encoding="utf-8") as f:
                for p in parts:
                    out = self._filter_for_log(p)
                    if out is None:
                        continue
                    f.write(out + "\n")
        except Exception:
            pass

    def write(self, s: str) -> int:
        n = self._original.write(s)
        # Always accumulate raw stream; we'll filter before writing to log.
        self._buf += s
        # Flush to file on any newline or carriage-return (progress bars use \r).
        if "\n" in s or "\r" in s:
            self._flush_to_logfile()
        try:
            self._original.flush()
        except Exception:
            pass
        return n

    def flush(self) -> None:
        try:
            self._original.flush()
        except Exception:
            pass
        self._flush_to_logfile()


@contextlib.contextmanager
def tee_std_to_file(log_file: Path) -> Iterator[None]:
    """
    Tee both stdout/stderr to `log_file` while keeping normal output behavior.
    """
    old_out: Optional[IO[str]] = sys.stdout
    old_err: Optional[IO[str]] = sys.stderr
    sys.stdout = _TeeToFileStream(old_out, log_file)  # type: ignore[assignment]
    sys.stderr = _TeeToFileStream(old_err, log_file)  # type: ignore[assignment]
    try:
        yield
    finally:
        sys.stdout = old_out  # type: ignore[assignment]
        sys.stderr = old_err  # type: ignore[assignment]


@contextlib.contextmanager
def redirect_std_to_logger(*args, **kwargs) -> Iterator[None]:
    log_file: Optional[Path] = None
    if args and isinstance(args[0], SimpleFileLogger):
        log_file = args[0].log_file
    if log_file is not None:
        with tee_std_to_file(log_file):
            yield
    else:
        yield