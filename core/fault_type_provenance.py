"""Evidence overlays; never rewrite frozen experiment manifests or raw inputs."""
from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from core.fault_type_sample_split import load_formal_catalog

GUIDE_COMMIT = "afcfcc419dab3103a86a8f95601d3af85890eb38"
GUIDE_PATH = "docs/Experiments_Guide.md"
GUIDE_URL = f"https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/{GUIDE_COMMIT}/{GUIDE_PATH}"
BASELINE_FINGERPRINT = "c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d"


def evidence(value, level: str, sources: list, *, limitation: str = "") -> dict:
    """Levels describe evidence kind, not an invented confidence percentage."""
    if level not in {"document", "code", "artifact", "reconstructed", "unknown"}:
        raise ValueError("unsupported evidence level")
    if level == "unknown" and value is not None:
        raise ValueError("unknown evidence must have a null value")
    if level != "unknown" and not sources:
        raise ValueError("non-unknown evidence requires source pointers")
    return {"value": value, "evidence_level": level, "sources": sources, "limitation": limitation}


def documented_motor(t_code: str, stage: str, source: dict) -> dict:
    if t_code not in {"T1", "T2", "T3"} or str(stage) != t_code[-1]:
        raise ValueError("stage/T-code mapping conflict")
    return {
        "documented_motor_id": evidence(t_code, "document", [source],
            limitation="Documented physical individual, not a serial number or complete acquisition chain."),
        "age_description": evidence("new" if t_code == "T1" else "old", "document", [source],
            limitation="Hours and aging severity unknown; motor individuality and age are confounded."),
        "serial_number": evidence(None, "unknown", []),
        "operating_hours": evidence(None, "unknown", []),
    }


def pinned_guide(repo: Path) -> dict:
    command = ["git", "-c", f"safe.directory={repo.resolve().as_posix()}", "show", f"{GUIDE_COMMIT}:{GUIDE_PATH}"]
    payload = subprocess.check_output(command, cwd=repo)
    lines = payload.decode("utf-8").splitlines()
    if "新機" not in lines[217] or "三顆不同" not in lines[229] or "無法把兩者拆開" not in lines[230]:
        raise ValueError("pinned guide does not contain the expected motor evidence")
    return {"url": GUIDE_URL, "commit": GUIDE_COMMIT, "path": GUIDE_PATH,
        "sha256": hashlib.sha256(payload).hexdigest(), "line_numbers": [218, 230, 231],
        "verification": "local Git object bytes; not a live edited document",
        "interpretation": "T1 new, T2/T3 old; three distinct individuals; age and individuality inseparable"}


def motor_overlay(data_root: Path | str, repo: Path | str) -> dict:
    _, catalog = load_formal_catalog(data_root)
    guide = pinned_guide(Path(repo))
    files = []
    for item in catalog["files"]:
        record = dict(item)
        record["evidence"] = documented_motor(str(item["t_code"]), str(item["stage"]), guide)
        files.append(record)
    return {"schema_version": 1, "artifact_kind": "non_mutating_motor_evidence_overlay",
        "dataset_fingerprint": catalog["dataset_fingerprint"], "file_count": catalog["file_count"],
        "sample_count": catalog["sample_count"], "guide": guide,
        "mapping_check": {"status": "PASS", "files_by_documented_motor": dict(Counter(f["t_code"] for f in files)),
            "scope": "CSV path stage/T-code consistency, not physical acquisition certification"},
        "interpretation": "documented leave-one-motor-out under verified path mapping; provenance remains INCOMPLETE",
        "frozen_manifests": "unchanged; historical campaign/null motor fields retained as original evidence",
        "files": files}


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")
