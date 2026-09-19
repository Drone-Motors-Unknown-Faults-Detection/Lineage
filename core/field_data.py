"""Validation and manifest helpers for new field data.

The formal dataset is read-only.  New hardware samples must pass this
metadata contract and checksum/duplicate checks before they can be copied to a
future training or validation pool.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping


REQUIRED_FIELDS = (
    "motor_id",
    "session_id",
    "timestamp",
    "screw_position",
    "measured_torque_nm",
    "rpm",
    "load",
    "temperature_c",
    "voltage_v",
    "current_a",
    "sensor_quality",
    "operator",
    "maintenance_action",
    "source_file",
)


class FieldDataError(ValueError):
    pass


@dataclass(frozen=True)
class FieldSampleMetadata:
    motor_id: str
    session_id: str
    timestamp: str
    screw_position: str
    measured_torque_nm: float
    rpm: float
    load: float
    temperature_c: float
    voltage_v: float
    current_a: float
    sensor_quality: str
    operator: str
    maintenance_action: str
    source_file: str
    checksum_sha256: str | None = None

    def __post_init__(self) -> None:
        for name in REQUIRED_FIELDS:
            if not str(getattr(self, name)).strip():
                raise FieldDataError(f"{name} must be non-empty")
        try:
            datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise FieldDataError("timestamp must be ISO-8601") from exc
        for name in ("measured_torque_nm", "rpm", "load", "temperature_c", "voltage_v", "current_a"):
            value = float(getattr(self, name))
            if value != value or value in {float("inf"), float("-inf")}:
                raise FieldDataError(f"{name} must be finite")
        if float(self.measured_torque_nm) < 0 or float(self.rpm) < 0 or float(self.load) < 0:
            raise FieldDataError("torque, rpm and load must be non-negative")
        if self.checksum_sha256 is not None and len(self.checksum_sha256) != 64:
            raise FieldDataError("checksum_sha256 must be a SHA-256 hex digest")

    def to_dict(self) -> dict:
        return asdict(self)


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_field_records(records: Iterable[Mapping[str, object]]) -> list[FieldSampleMetadata]:
    validated: list[FieldSampleMetadata] = []
    seen: set[tuple[str, str, str, str]] = set()
    for raw in records:
        missing = [name for name in REQUIRED_FIELDS if name not in raw]
        if missing:
            raise FieldDataError(f"missing required metadata: {missing}")
        item = FieldSampleMetadata(**{name: raw[name] for name in (*REQUIRED_FIELDS, "checksum_sha256") if name in raw})  # type: ignore[arg-type]
        identity = (item.motor_id, item.session_id, item.timestamp, item.source_file)
        if identity in seen:
            raise FieldDataError(f"duplicate field sample identity: {identity}")
        seen.add(identity)
        validated.append(item)
    return validated


def write_field_manifest(records: Iterable[Mapping[str, object]], output: Path | str, *, source_label: str = "new_field_candidate") -> dict:
    validated = validate_field_records(records)
    manifest = {
        "schema_version": 1,
        "source_label": source_label,
        "split_policy": "candidate stays outside formal dataset until schema/checksum/duplicate review",
        "records": [item.to_dict() for item in validated],
        "status": "validated_metadata_only",
    }
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
