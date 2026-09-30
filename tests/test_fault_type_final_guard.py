import copy
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from core.fault_type_final_guard import (FinalTestBlocked, guard_final_test, ingest,
    seal, numeric_row_digest, record_final_exposure)
from core.formal_data import _sha256_file


def fixture():
    ledger = seal({"files": {"old.csv": "old-sha"}, "numeric_row_digests": ["old-row"],
        "motor_ids": ["T1"], "sessions": ["session-old"], "runs": [], "raw_recording_sha256": []}, "ledger_checksum")
    locked = seal({"status": "locked", "selection_input_ids": ["train"], "training_artifact_sha256": "fitted",
        "feature_version": "v1", "exposure_ledger_checksum": ledger["ledger_checksum"],
        "known_labels": ["8screws"], "unknown_labels": ["1screws"], "training_records": [],
        "minimum_test_samples_per_class": 1, "minimum_test_groups_per_class": 1,
        "expected_rpms": ["8000rpm"]}, "locked_checksum")
    rows = [{"sample_id": str(i), "source_sha256": "fresh-sha", "raw_source_sha256": "raw-new",
        "source_interval": [i*10000, (i+1)*10000], "numeric_row_digest": f"fresh-row{i}",
        "motor_id": "T4", "session_id": "session-new", "run_id": "run-new", "label": label, "rpm": "8000rpm"}
        for i, label in enumerate(["8screws", "1screws"])]
    bundle = seal({"feature_version": "v1", "records": rows}, "data_version_checksum")
    return bundle, ledger, locked


class GuardTests(unittest.TestCase):
    def test_new_test_exposure_cannot_be_rebranded_fresh(self):
        b, l, c = fixture()
        updated = record_final_exposure(l, b, evaluation_id="actual-test")
        c["exposure_ledger_checksum"] = updated["ledger_checksum"]
        with self.assertRaises(FinalTestBlocked): self.evaluate(b, updated, c)
        self.assertTrue(updated["evaluations"][0]["registered_before_prediction"])

    def test_exposure_receipt_requires_id_and_sealed_inputs(self):
        b, l, _ = fixture()
        with self.assertRaises(FinalTestBlocked): record_final_exposure(l, b, evaluation_id="")
        b["feature_version"] = "changed"
        with self.assertRaises(FinalTestBlocked): record_final_exposure(l, b, evaluation_id="retry")

    def evaluate(self, bundle, ledger, locked, **kwargs):
        return guard_final_test(seal(bundle, "data_version_checksum"), ledger, seal(locked, "locked_checksum"), claim=kwargs.pop("claim", "new_motor"), **kwargs)

    def test_new_motor_and_new_session_different_claims(self):
        b, l, c = fixture()
        self.assertEqual(self.evaluate(b, l, c)["status"], "ELIGIBLE_WITH_ATTESTED_PROVENANCE")
        for row in b["records"]: row["motor_id"] = "T1"
        with self.assertRaises(FinalTestBlocked):
            self.evaluate(b, l, c)
        self.assertEqual(self.evaluate(b, l, c, claim="new_session")["claim"], "new_session")

    def test_same_recording_cannot_supply_fake_new_session(self):
        b, l, c = fixture(); b["records"][1]["session_id"] = "fake-second-session"
        with self.assertRaises(FinalTestBlocked): self.evaluate(b, l, c)

    def test_same_run_cannot_cross_motor(self):
        b, l, c = fixture(); b["records"][1]["motor_id"] = "T5"; b["records"][1]["raw_source_sha256"] = "different-raw"
        with self.assertRaises(FinalTestBlocked): self.evaluate(b, l, c)

    def test_exposed_recording(self):
        b, l, c = fixture()
        b["records"][0]["raw_source_sha256"] = "old-sha"
        with self.assertRaises(FinalTestBlocked): self.evaluate(b, l, c)

    def test_copy_feature_bytes(self):
        b, l, c = fixture()
        b["records"][0]["source_sha256"] = "old-sha"
        with self.assertRaises(FinalTestBlocked): self.evaluate(b, l, c)

    def test_reserialized_numeric_copy(self):
        self.assertEqual(numeric_row_digest([1., 2.]), numeric_row_digest([1, 2]))
        b, l, c = fixture()
        b["records"][0]["numeric_row_digest"] = "old-row"
        with self.assertRaises(FinalTestBlocked): self.evaluate(b, l, c)

    def test_overlapping_windows(self):
        b, l, c = fixture()
        b["records"][1]["source_interval"] = [9000, 19000]
        with self.assertRaises(FinalTestBlocked): self.evaluate(b, l, c)

    def test_train_window_overlap(self):
        b, l, c = fixture()
        with self.assertRaises(FinalTestBlocked):
            self.evaluate(b, l, c, training_records=[{"raw_source_sha256": "raw-new", "source_interval": [9000, 11000]}])

    def test_same_recording_nonoverlap_still_exposed(self):
        b, l, c = fixture()
        with self.assertRaises(FinalTestBlocked):
            self.evaluate(b, l, c, training_records=[{"raw_source_sha256": "raw-new", "source_interval": [30000, 40000]}])

    def test_not_locked(self):
        b, l, c = fixture(); c["status"] = "selected_not_locked"
        with self.assertRaises(FinalTestBlocked): self.evaluate(b, l, c)

    def test_fingerprint_tampering(self):
        b, l, c = fixture(); b["records"][0]["motor_id"] = "changed"
        with self.assertRaises(FinalTestBlocked): guard_final_test(b, l, c, claim="new_motor")

    def test_same_session_and_inadequate_coverage(self):
        b, l, c = fixture(); b["records"][0]["session_id"] = "session-old"
        with self.assertRaises(FinalTestBlocked): self.evaluate(b, l, c)
        b, l, c = fixture(); c["minimum_test_groups_per_class"] = 2
        with self.assertRaises(FinalTestBlocked): self.evaluate(b, l, c)

    def test_feature_version_mismatch(self):
        b, l, c = fixture(); c["feature_version"] = "v2"
        with self.assertRaises(FinalTestBlocked): self.evaluate(b, l, c)

    def test_ingest_real_files_and_reject_false_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            # Synthetic fixture only, not claimed actual DAQ.
            feature = root / "features.csv"
            pd.DataFrame([[float(i) for i in range(105)]]).to_csv(feature, index=False)
            raw = root / "raw.csv"
            pd.DataFrame({"x": [0., 1.]}).to_csv(raw, index=False)
            window = {"row_index": 0, "motor_id": "T4", "session_id": "S4", "run_id": "R4", "label": "8screws",
                "rpm": "8000rpm", "acquisition_timestamp": "2026-10-01T02:00:00+08:00", "attestation": "synthetic test",
                "raw_source_file": "raw.csv", "raw_source_sha256": _sha256_file(raw), "source_interval": [0, 2],
                "raw_sample_count": 2, "sample_rate_hz": 10000, "physical_time_alignment_verified": True}
            manifest = {"feature_version": "v1", "extractor_sha256": "code", "acquisition_evidence": "test-only",
                "physical_contract": {k: "test-only" for k in ["sensor_units", "orientation", "calibration", "mounting", "load"]},
                "feature_files": [{"path": "features.csv", "sha256": _sha256_file(feature), "windows": [window]}]}
            result = ingest(root, seal(manifest, "manifest_checksum"))
            self.assertEqual(len(result["records"]), 1)
            window["physical_time_alignment_verified"] = False
            with self.assertRaises(FinalTestBlocked): ingest(root, seal(manifest, "manifest_checksum"))
