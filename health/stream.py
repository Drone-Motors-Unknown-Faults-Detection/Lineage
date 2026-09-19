"""Common packet interface for CSV replay and future live adapters."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Protocol, Sequence


@dataclass(frozen=True)
class StreamPacket:
    timestamp: float
    motor_id: str
    session_id: str
    features: tuple[float, ...]
    source: str


@dataclass
class StreamStats:
    received: int = 0
    emitted: int = 0
    dropped: int = 0
    out_of_order: int = 0


class StreamAdapter(Protocol):
    stats: StreamStats

    def __iter__(self) -> Iterator[StreamPacket]: ...


class CsvReplayAdapter:
    """Replay a CSV through the same packet contract a live adapter will use."""

    def __init__(self, packets: Iterable[StreamPacket]) -> None:
        self._packets = list(packets)
        self.stats = StreamStats()

    @classmethod
    def from_csv(cls, path: Path | str, *, feature_columns: Sequence[str]) -> "CsvReplayAdapter":
        packets = []
        with Path(path).open("r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                packets.append(
                    StreamPacket(
                        timestamp=float(row["timestamp"]),
                        motor_id=str(row["motor_id"]),
                        session_id=str(row["session_id"]),
                        features=tuple(float(row[name]) for name in feature_columns),
                        source=str(path),
                    )
                )
        return cls(packets)

    def __iter__(self) -> Iterator[StreamPacket]:
        previous: float | None = None
        for packet in self._packets:
            self.stats.received += 1
            if previous is not None and packet.timestamp < previous:
                self.stats.out_of_order += 1
                self.stats.dropped += 1
                continue
            previous = packet.timestamp
            self.stats.emitted += 1
            yield packet
