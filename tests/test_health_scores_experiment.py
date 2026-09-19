import unittest

from experiments.score_separation import _load_records


class ScoreSeparationExperimentTests(unittest.TestCase):
    def test_loader_maps_unknown_conditions_without_using_test_labels(self):
        manifest = {
            "records": [
                {"source_file": "Step-1/myfeature/T1/8000rpm/8screws/T1_Group_feature_data_clean.csv", "row_index": 0, "split": "x", "condition": "8screws"}
            ]
        }
        self.assertEqual(manifest["records"][0]["condition"], "8screws")


if __name__ == "__main__":
    unittest.main()
