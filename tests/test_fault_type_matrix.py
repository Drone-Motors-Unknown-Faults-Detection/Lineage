import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from loguru import logger
from experiments import fault_type_matrix as matrix
from tests.test_fault_type_manifest import _campaign_fixture
from tests.test_fault_type_runner import FixtureStore


def registry_fixture():
    records, catalog, role, _ = _campaign_fixture()
    role["n_known_faults"] = 1
    registry = {"dataset_fingerprint": catalog["dataset_fingerprint"], "protocol_a": [role],
        "protocol_b_n5": [], "sample_split_seeds": [42, 123, 2026]}
    registry["registry_checksum"] = matrix._digest(registry)
    return records, catalog, registry


class FaultTypeMatrixTests(unittest.TestCase):
    def setUp(self):
        logger.disable("experiments.fault_type_matrix")

    def tearDown(self):
        logger.enable("experiments.fault_type_matrix")

    def test_checkpoint_failure_preserves_previous_valid_state(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            matrix._write_json(path, {"completed": 1})
            with patch.object(matrix.os, "fsync", side_effect=OSError("simulated interruption")):
                with self.assertRaises(OSError):
                    matrix._write_json(path, {"completed": 2})
            self.assertEqual(json.loads(path.read_text()), {"completed": 1})
            matrix._write_json(path, {"completed": 2})
            self.assertEqual(json.loads(path.read_text()), {"completed": 2})
            self.assertFalse(path.with_name("state.json.tmp").exists())

    def test_plan_is_predeclared_deterministic_and_tamper_rejected(self):
        _, _, registry = registry_fixture()
        kwargs = dict(n_values=[1], protocol="A", git_commit="fixed", methods=["mahalanobis", "knn"])
        self.assertEqual(matrix.make_plan(registry, **kwargs), matrix.make_plan(registry, **kwargs))
        registry["protocol_a"][0]["unknown_test_labels"] = []
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            matrix.make_plan(registry, **kwargs)

    def test_smoke_caps_preserve_sources_and_declared_exclusions(self):
        records, _, _, fold = _campaign_fixture()
        capped = matrix.cap_fold(fold, records, 2)
        selected = set().union(*(set(v) for v in capped["sample_ids"].values()))
        excluded = {e["sample_id"] for e in capped["excluded"]}
        self.assertFalse(selected & excluded)
        self.assertEqual(len(selected | excluded), len(records))
        self.assertEqual(len(capped["sample_ids"]["test"]), 18)

    def test_resume_verifies_artifacts_and_never_refits_completed_runs(self):
        records, catalog, registry = registry_fixture()
        plan = matrix.make_plan(registry, n_values=[1], protocol="A", git_commit="unit", methods=["mahalanobis", "knn"], pilot=True)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(matrix, "load_formal_catalog", return_value=(records, catalog)), patch.object(matrix, "FeatureStore", return_value=FixtureStore()):
                first = matrix.run_matrix(data_root=root, plan=plan, root=root / "matrix", log=logger)
                self.assertEqual(first["completed"], 2)
                old = json.loads(Path(first["strata"][0]["path"]).read_text())
                matrix.annotate_pooled_task_count(root / "matrix", logger)
                updated = json.loads(Path(first["strata"][0]["path"]).read_text())
                self.assertEqual(old["pooled_sample"]["metrics"]["known_classification"], updated["pooled_sample"]["metrics"]["known_classification"])
                self.assertEqual(updated["pooled_sample"]["metrics"]["known_fault_count"], 1)
                with patch.object(matrix, "run", side_effect=AssertionError("must not refit")):
                    second = matrix.run_matrix(data_root=root, plan=plan, root=root / "matrix", log=logger)
                self.assertEqual(second["completed"], 2)
                status = json.loads((root / "matrix" / "run_status.json").read_text())
                summary_path = next(iter(status["runs"].values()))["summary_path"]
                summary = json.loads(Path(summary_path).read_text())
                summary["metrics"]["known_classification"]["accuracy"] = -1
                manifest = matrix.read_split_manifest(next(iter(status["runs"].values()))["manifest_path"])
                with self.assertRaisesRegex(ValueError, "metrics do not match"):
                    matrix.verify_saved(summary, manifest)
                summary = json.loads(Path(summary_path).read_text())
                artifact = Path(summary["prediction_artifact"]["path"])
                artifact.write_bytes(b"corrupt")
                with self.assertRaisesRegex(ValueError, "resume checksum mismatch"):
                    matrix.run_matrix(data_root=root, plan=plan, root=root / "matrix", log=logger)

    def test_failed_runs_are_not_silently_removed(self):
        records, catalog, registry = registry_fixture()
        plan = matrix.make_plan(registry, n_values=[1], protocol="A", git_commit="unit", methods=["mahalanobis"], pilot=True)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(matrix, "load_formal_catalog", return_value=(records, catalog)), patch.object(matrix, "FeatureStore", return_value=FixtureStore()), patch.object(matrix, "run", side_effect=RuntimeError("intentional fixture failure")):
                result = matrix.run_matrix(data_root=root, plan=plan, root=root / "matrix", log=logger)
            self.assertEqual(result["completed"], 0)
            self.assertEqual(result["not_completed"], 1)
            self.assertIn("intentional fixture failure", result["failed_or_pending"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
