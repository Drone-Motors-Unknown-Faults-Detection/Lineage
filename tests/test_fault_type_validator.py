"""Semantic tests for the fault-configuration split validator."""

from __future__ import annotations

import copy
import hashlib
import unittest
from collections import Counter

from core.fault_type_validator import (
    ERROR_CODES,
    SplitValidationError,
    assert_valid_for_formal,
    compute_manifest_checksum,
    validate_split_manifest,
)


def _seal(manifest: dict) -> dict:
    manifest.pop("manifest_checksum", None)
    manifest["manifest_checksum"] = compute_manifest_checksum(manifest)
    return manifest


def _make_complete_manifest() -> dict:
    """Return a small but genuinely PASS-capable independent split."""

    labels = ("8screws", "5screws")
    records: list[dict] = []
    sample_ids: dict[str, list[str]] = {
        "train": [], "validation": [], "calibration": [], "test": [],
    }

    def add(split: str, label: str, index: int, *, test: bool = False) -> None:
        sample_id = f"{split}-{label}-{index:02d}"
        group_number = index % 2 if test else 0
        source_file = f"{split}/{label}/group-{group_number}.csv"
        sample_ids[split].append(sample_id)
        records.append({
            "sample_id": sample_id,
            "label": label,
            "group_id": f"{split}-{label}-group-{group_number}",
            "source_file": source_file,
            "rpm": ("6000rpm", "8000rpm", "11000rpm")[index % 3],
            "stage": split,
            "source_interval": None,
        })

    for split in ("train", "validation", "calibration"):
        for label in labels:
            add(split, label, 0)
    for label in (*labels, "7screws"):
        for index in range(30):
            add("test", label, index, test=True)

    source_counts = Counter(record["source_file"] for record in records)
    source_files = [
        {
            "source_file": source,
            "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "rows": count,
        }
        for source, count in sorted(source_counts.items())
    ]
    manifest = {
        "schema_version": 1,
        "split_id": "unit-independent-split",
        "dataset_fingerprint": "d" * 64,
        "dataset_sample_count": len(records),
        "healthy_label": "8screws",
        "known_fault_labels": ["5screws"],
        "unknown_validation_labels": [],
        "unknown_test_labels": ["7screws"],
        "sample_ids": sample_ids,
        "records": records,
        "excluded": [],
        "source_files": source_files,
        "fit_sample_ids": list(sample_ids["train"]),
        "reference_sample_ids": list(sample_ids["train"]),
        "selection_sample_ids": list(sample_ids["validation"]),
        "shared_validation_calibration": False,
        "group_key": "verified_session",
        "independent_acquisition_verified": True,
        "expected_rpms": ["6000rpm", "8000rpm", "11000rpm"],
        "claimed_label_semantics": "configuration",
        "requested_event_metrics": False,
    }
    return _seal(manifest)


def _record(manifest: dict, sample_id: str) -> dict:
    return next(item for item in manifest["records"] if item["sample_id"] == sample_id)


class FaultTypeValidatorTests(unittest.TestCase):
    def test_complete_independent_manifest_passes(self) -> None:
        report = validate_split_manifest(_make_complete_manifest())
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["error_codes"], [])

    def test_every_declared_error_code_has_a_semantic_trigger(self) -> None:
        cases = {}

        manifest = _make_complete_manifest()
        test_id = manifest["sample_ids"]["test"][0]
        train_id = manifest["sample_ids"]["train"][0]
        _record(manifest, test_id)["group_id"] = _record(manifest, train_id)["group_id"]
        cases["TEST_GROUP_LEAKAGE"] = (_seal(manifest), {})

        manifest = _make_complete_manifest()
        train_id = manifest["sample_ids"]["train"][0]
        test_id = manifest["sample_ids"]["test"][0]
        _record(manifest, train_id).update(raw_source_id="raw-a", source_interval=[0, 10])
        _record(manifest, test_id).update(raw_source_id="raw-a", source_interval=[5, 15])
        cases["TEST_WINDOW_OVERLAP_LEAKAGE"] = (_seal(manifest), {})

        manifest = _make_complete_manifest()
        _record(manifest, manifest["sample_ids"]["train"][0])["label"] = "7screws"
        cases["UNKNOWN_LABEL_LEAKAGE"] = (_seal(manifest), {})

        manifest = _make_complete_manifest()
        paired = manifest["sample_ids"]["test"][:-1]
        cases["TEST_MANIFEST_MISMATCH"] = (manifest, {"paired_test_ids": paired})

        manifest = _make_complete_manifest()
        manifest["selection_sample_ids"] = [manifest["sample_ids"]["test"][0]]
        cases["TEST_USED_FOR_SELECTION"] = (_seal(manifest), {})

        manifest = _make_complete_manifest()
        manifest["excluded"] = [{
            "sample_id": manifest["sample_ids"]["test"][0],
            "reason": "incorrectly_selected_and_excluded",
        }]
        cases["TEST_EXCLUSION_UNDECLARED"] = (_seal(manifest), {})

        manifest = _make_complete_manifest()
        manifest["records"][0]["rpm"] = "tampered"
        cases["TEST_NOT_REPRODUCIBLE"] = (manifest, {})

        manifest = _make_complete_manifest()
        for item in manifest["records"]:
            if item["sample_id"] in manifest["sample_ids"]["test"] and item["label"] == "8screws":
                item["label"] = "5screws"
        cases["TEST_MISSING_HEALTHY"] = (_seal(manifest), {})

        manifest = _make_complete_manifest()
        for item in manifest["records"]:
            if item["sample_id"] in manifest["sample_ids"]["test"] and item["label"] == "5screws":
                item["label"] = "8screws"
        cases["TEST_MISSING_KNOWN_CLASS"] = (_seal(manifest), {})

        manifest = _make_complete_manifest()
        for item in manifest["records"]:
            if item["sample_id"] in manifest["sample_ids"]["test"] and item["label"] == "7screws":
                item["label"] = "5screws"
        cases["TEST_MISSING_UNKNOWN_CLASS"] = (_seal(manifest), {})

        manifest = _make_complete_manifest()
        removed_id = next(
            sample_id for sample_id in manifest["sample_ids"]["test"]
            if _record(manifest, sample_id)["label"] == "7screws"
        )
        manifest["sample_ids"]["test"].remove(removed_id)
        manifest["records"] = [item for item in manifest["records"] if item["sample_id"] != removed_id]
        manifest["excluded"] = [{"sample_id": removed_id, "reason": "predeclared_test_cap"}]
        cases["TEST_INSUFFICIENT_SAMPLES"] = (_seal(manifest), {})

        manifest = _make_complete_manifest()
        for item in manifest["records"]:
            if item["sample_id"] in manifest["sample_ids"]["test"] and item["label"] == "7screws":
                item["group_id"] = "one-unknown-test-group"
        cases["TEST_INSUFFICIENT_GROUPS"] = (_seal(manifest), {})

        manifest = _make_complete_manifest()
        for item in manifest["records"]:
            if item["sample_id"] in manifest["sample_ids"]["test"] and item["label"] == "7screws":
                item["rpm"] = "6000rpm"
        cases["TEST_CONDITION_COVERAGE_INCOMPLETE"] = (_seal(manifest), {})

        manifest = _make_complete_manifest()
        manifest["claimed_label_semantics"] = "verified_physical_fault_type"
        cases["LABEL_SEMANTICS_MISMATCH"] = (_seal(manifest), {})

        manifest = _make_complete_manifest()
        manifest["requested_event_metrics"] = True
        cases["EVENT_BOUNDARY_INCOMPLETE"] = (_seal(manifest), {})

        self.assertEqual(set(cases), set(ERROR_CODES))
        for expected_code, (manifest, kwargs) in cases.items():
            with self.subTest(error_code=expected_code):
                report = validate_split_manifest(manifest, **kwargs)
                self.assertIn(expected_code, report["error_codes"])
                expected_status = "INVALID" if expected_code.startswith("TEST_") and expected_code in {
                    "TEST_GROUP_LEAKAGE", "TEST_WINDOW_OVERLAP_LEAKAGE", "TEST_MANIFEST_MISMATCH",
                    "TEST_USED_FOR_SELECTION", "TEST_EXCLUSION_UNDECLARED", "TEST_NOT_REPRODUCIBLE",
                } or expected_code == "UNKNOWN_LABEL_LEAKAGE" else "INCOMPLETE"
                self.assertEqual(report["status"], expected_status)

    def test_invalid_fails_fast_and_incomplete_requires_opt_in(self) -> None:
        invalid = _make_complete_manifest()
        invalid["selection_sample_ids"] = [invalid["sample_ids"]["test"][0]]
        _seal(invalid)
        with self.assertRaises(SplitValidationError) as caught:
            assert_valid_for_formal(invalid)
        self.assertIn("TEST_USED_FOR_SELECTION", caught.exception.report["error_codes"])

        incomplete = _make_complete_manifest()
        incomplete["claimed_label_semantics"] = "unverified"
        _seal(incomplete)
        with self.assertRaisesRegex(ValueError, "explicit exploratory mode"):
            assert_valid_for_formal(incomplete)
        report = assert_valid_for_formal(incomplete, allow_incomplete=True)
        self.assertEqual(report["status"], "INCOMPLETE")

    def test_detector_pairing_requires_identical_test_ids_and_checksum(self) -> None:
        manifest = _make_complete_manifest()
        report = validate_split_manifest(
            manifest,
            paired_test_ids=manifest["sample_ids"]["test"][:-1],
            paired_checksum="0" * 64,
        )
        self.assertEqual(report["status"], "INVALID")
        self.assertIn("TEST_MANIFEST_MISMATCH", report["error_codes"])
        self.assertEqual(len(report["details"]["TEST_MANIFEST_MISMATCH"]), 2)

    def test_checksum_binds_nested_content(self) -> None:
        manifest = _make_complete_manifest()
        original = manifest["manifest_checksum"]
        manifest["records"][0]["rpm"] = "tampered-after-freeze"
        self.assertNotEqual(compute_manifest_checksum(manifest), original)
        report = validate_split_manifest(manifest)
        self.assertEqual(report["status"], "INVALID")
        self.assertIn("TEST_NOT_REPRODUCIBLE", report["error_codes"])

    def test_threshold_inputs_must_be_calibration_only(self) -> None:
        manifest = _make_complete_manifest()
        manifest["calibration_sample_ids"] = manifest["sample_ids"]["test"][:1]
        self.assertIn("UNKNOWN_LABEL_LEAKAGE", validate_split_manifest(_seal(manifest))["error_codes"])

    def test_nonfinite_interval_is_invalid(self) -> None:
        manifest = _make_complete_manifest()
        manifest["records"][0]["source_interval"] = [0, float("inf")]
        self.assertIn("TEST_NOT_REPRODUCIBLE", validate_split_manifest(manifest)["error_codes"])


if __name__ == "__main__":
    unittest.main()
