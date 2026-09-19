import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from core.continual_protocol import ProtocolError, build_protocol, validate_leakage


def _write_csv(root: Path, stage: int, config: str, motor: str = "T1", rpm: str = "8000rpm") -> None:
    path = root / f"Step-{stage}" / "myfeature" / motor / rpm / config
    path.mkdir(parents=True, exist_ok=True)
    columns = [f"f{i}" for i in range(105)]
    offset = stage * 0.1 + sum(ord(char) for char in config) * 1e-3
    rows = np.arange(3 * 105, dtype=float).reshape(3, 105) + offset
    pd.DataFrame(rows, columns=columns).to_csv(path / f"{motor}_Group_feature_data_clean.csv", index=False)


class ContinualProtocolTests(unittest.TestCase):
    def test_manifest_is_deterministic_and_test_is_immutable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for stage, config in ((1, "8screws"), (2, "8screws"), (2, "7screws"), (2, "6screws"), (2, "5screws"), (3, "6screws"), (3, "5screws"), (3, "8screws"), (3, "7screws"), (3, "4screws"), (3, "3screws"), (3, "2screws"), (3, "1screws"), (3, "3_14screws"), (3, "4_146screws")):
                _write_csv(root / "data", stage, config)
            first = build_protocol(root / "data", root / "out1", seed=42)
            second = build_protocol(root / "data", root / "out2", seed=999)
            self.assertEqual(first["protocol_fingerprint"], second["protocol_fingerprint"])
            self.assertEqual(
                sorted(item["sample_id"] for item in first["records"] if item["split"] == "immutable_test"),
                sorted(item["sample_id"] for item in second["records"] if item["split"] == "immutable_test"),
            )
            self.assertEqual(validate_leakage(first)["status"], "passed")
            self.assertEqual(len(first["summary"]["files_by_split"]), 6)

    def test_test_samples_cannot_enter_replay_or_reference(self):
        manifest = {
            "records": [
                {"sample_id": "test", "source_file": "test.csv", "group_id": "test.csv", "split": "immutable_test"},
                {"sample_id": "cal", "source_file": "cal.csv", "group_id": "cal.csv", "split": "healthy_calibration"},
            ]
        }
        with self.assertRaises(ProtocolError):
            validate_leakage(manifest, replay_sample_ids=["test"])
        with self.assertRaises(ProtocolError):
            validate_leakage(manifest, reference_sample_ids=["test"])

    def test_manifest_is_saved_with_fingerprints(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for stage, config in ((1, "8screws"), (2, "8screws"), (3, "8screws")):
                _write_csv(root / "data", stage, config)
            manifest = build_protocol(root / "data", root / "protocol")
            self.assertTrue((root / "protocol" / "split_manifest.json").is_file())
            payload = json.loads((root / "protocol" / "split_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["protocol_fingerprint"], manifest["protocol_fingerprint"])


if __name__ == "__main__":
    unittest.main()
