import copy
import gzip
import hashlib
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import numpy as np
from sklearn.preprocessing import RobustScaler

from core.fault_type_validator import SplitValidationError
from core.openset import create_openset_detector
from experiments import fault_type_openset as runner
from tests.test_fault_type_validator import _make_complete_manifest, _seal


def fixture():
    manifest = _make_complete_manifest()
    for split in ("train", "validation", "calibration"):
        for sid in list(manifest["sample_ids"][split]):
            original = next(r for r in manifest["records"] if r["sample_id"] == sid)
            for i in range(1, 30):
                row = {**original, "sample_id": sid + f"-extra-{i}"}
                manifest["records"].append(row)
                manifest["sample_ids"][split].append(row["sample_id"])
    counts = Counter(r["source_file"] for r in manifest["records"])
    for source in manifest["source_files"]:
        source["rows"] = counts[source["source_file"]]
    manifest.update(dataset_sample_count=len(manifest["records"]), protocol="A", sample_split_seed=42,
        class_split_id="roles-test", class_combination_id="combination-test", git_commit="unit-test")
    manifest["fit_sample_ids"] = manifest["sample_ids"]["train"]
    manifest["reference_sample_ids"] = manifest["sample_ids"]["train"]
    return _seal(manifest)


class FixtureStore:
    def __init__(self):
        self.calls = []

    def load(self, records):
        self.calls.append([r["sample_id"] for r in records])
        output = []
        for row in records:
            seed = int(hashlib.sha256(row["sample_id"].encode()).hexdigest()[:8], 16)
            rng = np.random.default_rng(seed)
            center = {"8screws": 0., "5screws": 4., "7screws": 20.}[row["label"]]
            output.append(rng.normal(center, .2, 105))
        return np.asarray(output).reshape(len(records), 105)


class FaultTypeRunnerTests(unittest.TestCase):
    def test_train_only_scaler_and_factory_calibration_inputs(self):
        manifest, store = fixture(), FixtureStore()
        captures = {}

        class SpyScaler(RobustScaler):
            def fit(self, X, y=None):
                captures["scaler_X"] = X.copy()
                return super().fit(X, y)

        def factory(method, **kwargs):
            captures["method"] = method
            real = create_openset_detector(method, **kwargs)
            fit = real.fit

            def spy_fit(X, y, C, z):
                captures["reference_X"], captures["cal_X"] = X.copy(), C.copy()
                return fit(X, y, C, z)
            real.fit = spy_fit
            return real

        with patch.object(runner, "RobustScaler", SpyScaler), patch.object(runner, "create_openset_detector", factory):
            result = runner.run(store, manifest=manifest)
        records = {r["sample_id"]: r for r in manifest["records"]}
        train_X = FixtureStore().load([records[s] for s in manifest["sample_ids"]["train"]])
        cal_X = FixtureStore().load([records[s] for s in manifest["sample_ids"]["calibration"]])
        np.testing.assert_array_equal(captures["scaler_X"], train_X)
        expected_scaler = RobustScaler().fit(train_X)
        np.testing.assert_array_equal(captures["reference_X"], expected_scaler.transform(train_X))
        np.testing.assert_array_equal(captures["cal_X"], expected_scaler.transform(cal_X))
        self.assertEqual(captures["method"], "mahalanobis")
        self.assertEqual(result["fit_audit"]["threshold_calibration_ids"], manifest["sample_ids"]["calibration"])
        self.assertFalse(set(result["fit_audit"]["scaler_fit_ids"]) & set(manifest["sample_ids"]["test"]))

    def test_pairing_determinism_and_actual_probability_output(self):
        manifest = fixture()
        results = [runner.run(FixtureStore(), manifest=manifest, openset_method=m) for m in ("mahalanobis", "knn")]
        repeated = runner.run(FixtureStore(), manifest=manifest)
        self.assertEqual(results[0]["predictions"], repeated["predictions"])
        self.assertEqual([r["sample_id"] for r in results[0]["predictions"]], [r["sample_id"] for r in results[1]["predictions"]])
        self.assertEqual(results[0]["manifest_checksum"], results[1]["manifest_checksum"])
        for result in results:
            for row in result["predictions"]:
                self.assertAlmostEqual(sum(row["classifier_probabilities"].values()), 1.)
                self.assertEqual(row["is_unknown"], row["openset_score"] > row["threshold"])
                self.assertIn(row["nearest_known_class"], result["known_labels"])
            with tempfile.TemporaryDirectory() as temp:
                summary = runner.save_result(result, temp)
                blob = Path(summary["prediction_artifact"]["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(blob).hexdigest(), summary["prediction_artifact"]["sha256"])
                rows = [json.loads(line) for line in gzip.decompress(blob).splitlines()]
                self.assertEqual(rows, result["predictions"])

    def test_invalid_fails_before_loading_and_does_not_save(self):
        manifest, store = fixture(), FixtureStore()
        manifest["selection_sample_ids"] = manifest["sample_ids"]["test"][:1]
        _seal(manifest)
        with self.assertRaises(SplitValidationError):
            runner.run(store, manifest=manifest)
        self.assertEqual(store.calls, [])

    def test_protocol_b_unknown_validation_is_diagnostic_not_calibration(self):
        manifest = fixture()
        manifest["protocol"] = "B"
        manifest["unknown_validation_labels"] = ["7screws"]
        manifest["unknown_test_labels"] = ["new-unknown"]
        # Move the original unknown into validation; introduce a separate test label.
        for r in manifest["records"]:
            if r["label"] == "7screws":
                r["label"] = "new-unknown"
        source = "validation/7screws/group.csv"
        r = {"sample_id": "unknown-val", "label": "7screws", "group_id": source, "source_file": source, "rpm": "6000rpm", "source_interval": None}
        manifest["records"].append(r)
        manifest["sample_ids"]["validation"].append(r["sample_id"])
        manifest["source_files"].append({"source_file": source, "rows": 1, "source_sha256": "a" * 64})
        manifest["dataset_sample_count"] += 1
        _seal(manifest)

        class BStore(FixtureStore):
            def load(self, records):
                return super().load([{**r, "label": "7screws" if r["label"] == "new-unknown" else r["label"]} for r in records])
        result = runner.run(BStore(), manifest=manifest)
        self.assertFalse(result["unknown_validation_diagnostic"]["used_for_fitting_or_selection"])
        self.assertNotIn("unknown-val", result["fit_audit"]["threshold_calibration_ids"])


if __name__ == "__main__":
    unittest.main()
