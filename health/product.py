"""Portable product/audit records for events, annotations and model versions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence


class ProductSchemaError(ValueError):
    pass


def _nonempty(value: str, name: str) -> str:
    if not str(value).strip():
        raise ProductSchemaError(f"{name} must be non-empty")
    return str(value)


@dataclass(frozen=True)
class FaultEvent:
    event_id: str
    start_time: str
    end_time: str
    motor_id: str
    condition: str
    rpm: float
    load: float
    max_health_deviation: float
    min_conformal_p: float | None
    unknown_score: float
    representative_sample_ids: tuple[str, ...]
    sensor_quality: str
    human_disposition: str | None
    model_version: str

    def __post_init__(self) -> None:
        for value, name in ((self.event_id, "event_id"), (self.start_time, "start_time"), (self.end_time, "end_time"), (self.motor_id, "motor_id"), (self.model_version, "model_version")):
            _nonempty(value, name)
        if self.rpm < 0 or self.load < 0:
            raise ProductSchemaError("rpm and load must be non-negative")
        if not 0.0 <= self.max_health_deviation <= 1.0 or not 0.0 <= self.unknown_score <= 1.0:
            raise ProductSchemaError("event scores must be in [0,1]")
        if self.min_conformal_p is not None and not 0.0 <= self.min_conformal_p <= 1.0:
            raise ProductSchemaError("min_conformal_p must be in [0,1]")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class HumanAnnotation:
    event_id: str
    action: str
    annotator: str
    timestamp: str
    fault_cause: str | None = None
    notes: str = ""
    source_cluster_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.action not in {"confirm", "reject", "merge", "split", "comment"}:
            raise ProductSchemaError("unsupported annotation action")
        _nonempty(self.event_id, "event_id")
        _nonempty(self.annotator, "annotator")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ModelVersion:
    version: str
    parent_version: str | None
    training_sample_ids: tuple[str, ...]
    replay_memory_fingerprint: str
    calibration_version: str
    health_reference_version: str
    metrics_before: Mapping[str, float | None]
    metrics_after: Mapping[str, float | None]
    artifact_checksum: str
    rollback_pointer: str | None

    def __post_init__(self) -> None:
        _nonempty(self.version, "version")
        _nonempty(self.replay_memory_fingerprint, "replay_memory_fingerprint")
        _nonempty(self.calibration_version, "calibration_version")
        _nonempty(self.health_reference_version, "health_reference_version")
        if len(self.artifact_checksum) != 64:
            raise ProductSchemaError("artifact_checksum must be SHA-256")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RollbackDecision:
    allowed: bool
    reason: str
    rollback_pointer: str | None


class RollbackGuard:
    def __init__(self, *, max_forgetting: float = 0.05, max_fpr_increase: float = 0.02) -> None:
        if max_forgetting < 0 or max_fpr_increase < 0:
            raise ProductSchemaError("rollback guardrails must be non-negative")
        self.max_forgetting = float(max_forgetting)
        self.max_fpr_increase = float(max_fpr_increase)

    def evaluate(self, before: Mapping[str, float], after: Mapping[str, float], *, rollback_pointer: str | None) -> RollbackDecision:
        forgetting = float(before.get("old_class_macro_f1", 0.0) - after.get("old_class_macro_f1", 0.0))
        fpr_increase = float(after.get("healthy_false_positive_rate", 0.0) - before.get("healthy_false_positive_rate", 0.0))
        if forgetting > self.max_forgetting:
            return RollbackDecision(False, "old-class forgetting exceeds guardrail", rollback_pointer)
        if fpr_increase > self.max_fpr_increase:
            return RollbackDecision(False, "healthy FPR increase exceeds guardrail", rollback_pointer)
        return RollbackDecision(True, "candidate passes deployment guardrails", rollback_pointer)


@dataclass(frozen=True)
class ExperimentReport:
    run_id: str
    split_fingerprint: str
    seed: int
    commit_sha: str
    parameters: Mapping[str, object]
    metrics: Mapping[str, object]
    status: str
    feature_type: str
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"completed", "failed", "blocked"}:
            raise ProductSchemaError("invalid experiment status")
        if self.status == "failed" and not self.error:
            raise ProductSchemaError("failed experiment needs error")

    def to_dict(self) -> dict:
        return asdict(self)
