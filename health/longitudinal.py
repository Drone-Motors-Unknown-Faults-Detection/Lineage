"""Longitudinal observation contract without fabricated RUL."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Iterable


class LongitudinalDataError(ValueError):
    pass


@dataclass(frozen=True)
class LongitudinalObservation:
    motor_id: str
    session_id: str
    timestamp: str
    cumulative_operating_hours: float
    rpm: float
    load: float
    temperature_c: float
    voltage_v: float
    current_a: float
    health_deviation_score: float
    unknown_score: float
    direction_familiarity: float
    inspection_result: str
    maintenance_event: str
    part_replacement: str
    confirmed_failure_time: str | None = None
    estimated_rul: float | None = None

    def __post_init__(self) -> None:
        if not self.motor_id or not self.session_id:
            raise LongitudinalDataError("motor_id and session_id are required")
        try:
            datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise LongitudinalDataError("timestamp must be ISO-8601") from exc
        if float(self.cumulative_operating_hours) < 0:
            raise LongitudinalDataError("cumulative_operating_hours must be non-negative")
        for name in ("health_deviation_score", "unknown_score", "direction_familiarity"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise LongitudinalDataError(f"{name} must be in [0,1]")
        if self.estimated_rul is not None and self.confirmed_failure_time is None:
            raise LongitudinalDataError("estimated_rul requires a confirmed failure endpoint")

    def to_dict(self) -> dict:
        return asdict(self)


def validate_trajectories(observations: Iterable[LongitudinalObservation]) -> dict:
    rows = list(observations)
    grouped: dict[str, list[LongitudinalObservation]] = {}
    for row in rows:
        grouped.setdefault(row.motor_id, []).append(row)
    summaries = []
    for motor_id, motor_rows in sorted(grouped.items()):
        times = [datetime.fromisoformat(row.timestamp.replace("Z", "+00:00")) for row in motor_rows]
        if any(right < left for left, right in zip(times, times[1:])):
            raise LongitudinalDataError(f"timestamps are not ordered for motor {motor_id}")
        hours = [row.cumulative_operating_hours for row in motor_rows]
        if any(right < left for left, right in zip(hours, hours[1:])):
            raise LongitudinalDataError(f"operating hours are not monotone for motor {motor_id}")
        summaries.append(
            {
                "motor_id": motor_id,
                "sessions": sorted({row.session_id for row in motor_rows}),
                "n_observations": len(motor_rows),
                "rul_status": "available_only_if_failure_endpoint_and_validated_run_to_failure",
            }
        )
    return {
        "motor_count": len(grouped),
        "observation_count": len(rows),
        "trajectories": summaries,
        "stitched_motor_policy": "one motor_id is one trajectory; T1/T2/T3 are never concatenated",
    }
