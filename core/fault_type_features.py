"""Position-preserving, checksum-checked 105-D feature access for split records.

Each record identifies an exact clean-feature CSV row.  Header text is not used
as a feature key because Stage 2 has historical naming differences; the
validated column *order* and 105-D contract are the common representation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from core.continual_protocol import _sample_id, _sha256_file
from core.formal_data import FEATURE_DIM


class FeatureIntegrityError(ValueError):
    """A manifest row does not match its immutable formal source file."""


class FeatureStore:
    def __init__(self, data_root: Path | str) -> None:
        self.root = Path(data_root).resolve()
        if not self.root.is_dir():
            raise FeatureIntegrityError(f"data root does not exist: {self.root}")
        self._cached: dict[str, tuple[str, np.ndarray]] = {}

    def _file(self, record: Mapping[str, object]) -> tuple[str, np.ndarray]:
        source = str(record["source_file"]).replace("\\", "/")
        if source in self._cached:
            return self._cached[source]
        path = (self.root / source).resolve()
        if path == self.root or self.root not in path.parents or not path.is_file():
            raise FeatureIntegrityError(f"source file is outside data root or missing: {source}")
        digest = _sha256_file(path)
        frame = pd.read_csv(path)
        numeric = frame.select_dtypes(include="number")
        if list(frame.columns) != list(numeric.columns) or numeric.shape[1] != FEATURE_DIM:
            raise FeatureIntegrityError(f"{source}: expected exactly {FEATURE_DIM} numeric columns")
        values = numeric.to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise FeatureIntegrityError(f"{source}: non-finite features")
        self._cached[source] = (digest, values)
        return digest, values

    def load(self, records: Iterable[Mapping[str, object]]) -> np.ndarray:
        rows: list[np.ndarray] = []
        for record in records:
            digest, values = self._file(record)
            expected_sha = str(record["source_sha256"])
            if digest != expected_sha:
                raise FeatureIntegrityError(f"source checksum changed: {record['source_file']}")
            index = int(record["row_index"])
            if index < 0 or index >= len(values):
                raise FeatureIntegrityError(f"row index outside source: {record['source_file']}:{index}")
            row = values[index]
            if _sample_id(digest, index, row) != str(record["sample_id"]):
                raise FeatureIntegrityError(f"sample fingerprint mismatch: {record['sample_id']}")
            rows.append(row)
        return np.vstack(rows) if rows else np.empty((0, FEATURE_DIM), dtype=float)
