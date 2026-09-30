import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from core.continual_protocol import _sample_id
from core.fault_type_features import FeatureIntegrityError, FeatureStore


class FeatureStoreTests(unittest.TestCase):
    def test_position_preserving_rows_and_checksums(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "Step-2" / "myfeature" / "T2" / "8000rpm" / "5screws" / "T2_Group_feature_data_clean.csv"
            path.parent.mkdir(parents=True)
            values = np.arange(210, dtype=float).reshape(2, 105)
            pd.DataFrame(values, columns=[f"stage2-name-{i}" for i in range(105)]).to_csv(path, index=False)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            record = {
                "source_file": path.relative_to(temp).as_posix(),
                "source_sha256": digest,
                "row_index": 1,
                "sample_id": _sample_id(digest, 1, values[1]),
            }
            store = FeatureStore(temp)
            self.assertTrue(np.array_equal(store.load([record])[0], values[1]))
            self.assertEqual(store.load([]).shape, (0, 105))
            changed = dict(record, sample_id="wrong")
            with self.assertRaisesRegex(FeatureIntegrityError, "fingerprint mismatch"):
                store.load([changed])
            changed = dict(record, source_sha256="0" * 64)
            with self.assertRaisesRegex(FeatureIntegrityError, "checksum changed"):
                store.load([changed])


if __name__ == "__main__":
    unittest.main()
