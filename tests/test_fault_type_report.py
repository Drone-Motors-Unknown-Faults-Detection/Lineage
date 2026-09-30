import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from loguru import logger

from core.logger import RunPaths
from experiments import fault_type_matrix as matrix
from experiments import fault_type_report as report
from tests.test_fault_type_matrix import registry_fixture
from tests.test_fault_type_runner import FixtureStore


class FaultTypeReportTests(unittest.TestCase):
    def test_completed_matrix_generates_tables_pairs_and_plot(self):
        records, catalog, registry = registry_fixture()
        plan = matrix.make_plan(registry, n_values=[1], protocol="A", git_commit="fixed", methods=["mahalanobis", "knn"])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            logger.disable("experiments.fault_type_matrix")
            try:
                with patch.object(matrix, "load_formal_catalog", return_value=(records, catalog)), patch.object(matrix, "FeatureStore", return_value=FixtureStore()):
                    matrix.run_matrix(data_root=root, plan=plan, root=root / "matrix", log=logger)
            finally:
                logger.enable("experiments.fault_type_matrix")
            out = root / "report"
            out.mkdir()
            paths = RunPaths("unit", "unit", root / "unit.log", out)
            result = report.run([root / "matrix"], paths=paths)
            self.assertEqual(result["matrices"][0]["completed"], 6)
            self.assertTrue((out / "known_fault_sweep.png").is_file())
            self.assertTrue((out / "paired_by_protocol_and_N.json").is_file())
            self.assertIn("INCOMPLETE", (out / "report.md").read_text())
            with self.assertRaisesRegex(ValueError, "duplicate report stratum"):
                report.run([root / "matrix", root / "matrix"], paths=paths)


if __name__ == "__main__":
    unittest.main()
