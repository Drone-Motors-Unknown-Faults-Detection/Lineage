import copy
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pandas as pd

from core.fault_type_sample_split import (
    SampleSplitError,
    _main,
    generate_campaign_folds,
    load_formal_catalog,
)


def _records():
    records = []
    for stage in (1, 2, 3):
        for label in ("8screws", "5screws", "6screws", "7screws", "unused"):
            for row in range(2):
                source = f"Step-{stage}/myfeature/T{stage}/8000rpm/{label}/T{stage}.csv"
                records.append({
                    "sample_id": f"s{stage}-{label}-{row}",
                    "label": label,
                    "stage": stage,
                    "source_file": source,
                    "group_id": source,
                })
    return records


def _folds(records=None):
    return generate_campaign_folds(
        _records() if records is None else records,
        healthy_label="8screws",
        known_fault_labels=["5screws"],
        unknown_validation_labels=["6screws"],
        unknown_test_labels=["7screws"],
    )


def _write_formal_fixture(root: Path, *, feature_dim: int = 105) -> None:
    for stage in (1, 2, 3):
        for label_index, label in enumerate(("8screws", "5screws", "7screws")):
            path = root / f"Step-{stage}" / "myfeature" / f"T{stage}" / "8000rpm" / label
            path.mkdir(parents=True, exist_ok=True)
            values = np.arange(2 * feature_dim, dtype=float).reshape(2, feature_dim) + stage * 1000 + label_index * 100
            pd.DataFrame(values, columns=[f"f{i}" for i in range(feature_dim)]).to_csv(
                path / f"T{stage}_Group_feature_data_clean.csv", index=False
            )


class CampaignSplitTests(unittest.TestCase):
    def test_three_deterministic_rotations_keep_campaigns_whole(self):
        first = _folds()
        second = _folds(list(reversed(_records())))
        self.assertEqual(first, second)
        self.assertEqual(
            [fold["campaigns"] for fold in first],
            [
                {"train": "1", "validation": "2", "calibration": "2", "test": "3"},
                {"train": "2", "validation": "3", "calibration": "3", "test": "1"},
                {"train": "3", "validation": "1", "calibration": "1", "test": "2"},
            ],
        )
        for fold in first:
            ids = fold["sample_ids"]
            self.assertTrue(fold["shared_validation_calibration"])
            self.assertEqual(fold["group_ids"]["train"], fold["source_files"]["train"])
            self.assertEqual(fold["group_ids"]["validation"], fold["source_files"]["validation"])
            self.assertFalse(set(ids["train"]) & set(ids["test"]))
            self.assertFalse(set(ids["validation"]) & set(ids["test"]))
            self.assertFalse(set(ids["calibration"]) & set(ids["test"]))
            self.assertEqual(len(ids["train"]), 4)
            self.assertEqual(len(ids["validation"]), 6)
            self.assertEqual(len(ids["calibration"]), 4)
            self.assertEqual(len(ids["test"]), 6)
            self.assertEqual(set(ids["calibration"]), {sample for sample in ids["validation"] if "6screws" not in sample})
            self.assertTrue(all("7screws" in sample or "5screws" in sample or "8screws" in sample for sample in ids["test"]))
            self.assertTrue(all("7screws" not in sample for part in ("train", "validation", "calibration") for sample in ids[part]))
            self.assertTrue(all("6screws" not in sample for part in ("train", "calibration", "test") for sample in ids[part]))
            self.assertIn("independent test campaigns", " ".join(fold["limitations"]))

    def test_exclusions_are_explicit_and_cover_every_unused_sample(self):
        fold = _folds()[0]
        reasons = {item["reason"] for item in fold["excluded"]}
        self.assertEqual(reasons, {
            "UNKNOWN_VALIDATION_OUTSIDE_VALIDATION",
            "UNKNOWN_TEST_OUTSIDE_FINAL_TEST",
            "LABEL_NOT_IN_CLASS_ROLE",
        })
        self.assertEqual(len(fold["excluded"]), 14)
        accounted = set(fold["sample_ids"]["train"] + fold["sample_ids"]["validation"] + fold["sample_ids"]["test"])
        self.assertEqual(len(accounted | {item["sample_id"] for item in fold["excluded"]}), len(_records()))

    def test_duplicate_sample_ids_and_group_owners_fail(self):
        records = _records()
        records.append(copy.deepcopy(records[0]))
        with self.assertRaisesRegex(SampleSplitError, "duplicate sample_id"):
            _folds(records)
        records = _records()
        records[2]["group_id"] = records[0]["group_id"]
        with self.assertRaisesRegex(SampleSplitError, "group_id crosses"):
            _folds(records)

    def test_source_files_cannot_change_group_or_label(self):
        records = _records()
        records[1]["group_id"] = "other-group"
        with self.assertRaisesRegex(SampleSplitError, "source_file crosses"):
            _folds(records)
        records = _records()
        records[1]["label"] = "6screws"
        with self.assertRaisesRegex(SampleSplitError, "source_file crosses"):
            _folds(records)

    def test_role_overlap_and_missing_campaign_fail(self):
        with self.assertRaisesRegex(SampleSplitError, "class roles"):
            generate_campaign_folds(
                _records(), healthy_label="8screws", known_fault_labels=["5screws"],
                unknown_test_labels=["5screws"],
            )
        with self.assertRaisesRegex(SampleSplitError, "all three campaigns"):
            _folds([item for item in _records() if item["stage"] != 3])

    def test_catalog_uses_p1_sample_ids_without_returning_feature_vectors(self):
        with tempfile.TemporaryDirectory() as temp:
            data_root = Path(temp) / "formal"
            _write_formal_fixture(data_root)
            records, summary = load_formal_catalog(data_root)
            self.assertEqual((summary["file_count"], summary["sample_count"], summary["feature_dim"]), (9, 18, 105))
            self.assertEqual(len(records), 18)
            self.assertEqual({item["stage"] for item in records}, {"1", "2", "3"})
            self.assertTrue(all(item["physical_motor_id"] is None for item in records))
            self.assertTrue(all(item["source_interval"] is None for item in records))
            self.assertTrue(all("features" not in item for item in records))
            self.assertTrue(all(item["group_id"] == item["source_file"] for item in records))
            source = data_root / "Step-1/myfeature/T1/8000rpm/8screws/T1_Group_feature_data_clean.csv"
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            first_row = pd.read_csv(source).to_numpy(dtype=float)[0]
            expected_id = hashlib.sha256(source_hash.encode("ascii") + b":0:" + first_row.tobytes()).hexdigest()
            self.assertIn(expected_id, {item["sample_id"] for item in records})
            expected_fingerprint = hashlib.sha256(
                json.dumps(sorted(item["source_sha256"] for item in summary["files"]), separators=(",", ":")).encode()
            ).hexdigest()
            self.assertEqual(summary["dataset_fingerprint"], expected_fingerprint)

    def test_catalog_rejects_wrong_feature_width(self):
        with tempfile.TemporaryDirectory() as temp:
            data_root = Path(temp) / "formal"
            _write_formal_fixture(data_root, feature_dim=104)
            with self.assertRaisesRegex(SampleSplitError, "expected exactly 105 numeric columns"):
                load_formal_catalog(data_root)

    def test_cli_summary_is_compact_and_refuses_changed_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data_root = root / "formal"
            output_root = root / "results"
            _write_formal_fixture(data_root)
            args = [
                "--data-root", str(data_root), "--output-root", str(output_root),
                "--known", "5screws", "--unknown-test", "7screws",
            ]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(_main(args), 0)
            target = output_root / "campaign_split_summary.json"
            original = target.read_bytes()
            result = json.loads(original)
            self.assertEqual(len(result["folds"]), 3)
            self.assertNotIn("sample_ids", result["folds"][0])
            self.assertEqual(result["folds"][0]["counts_by_split_label"]["test"]["7screws"], 2)
            self.assertEqual(len(result["folds"][0]["group_ids"]["test"]), 3)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(_main(args), 0)
            self.assertEqual(target.read_bytes(), original)
            changed = args[:-1] + ["6screws"]
            with self.assertRaisesRegex(SampleSplitError, "refusing to change"):
                with redirect_stdout(io.StringIO()):
                    _main(changed)
            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
