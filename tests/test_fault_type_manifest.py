"""Round-trip and campaign-holdout checks for immutable split manifests."""

from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from core.fault_type_manifest import build_split_manifest, read_split_manifest, write_split_manifest
from core.fault_type_sample_split import generate_campaign_folds
from core.fault_type_validator import compute_manifest_checksum, validate_split_manifest
from tests.test_fault_type_validator import _make_complete_manifest


def _campaign_fixture() -> tuple[list[dict], dict, dict, dict]:
    records: list[dict] = []
    for stage in ("1", "2", "3"):
        for label in ("8screws", "5screws", "7screws"):
            for rpm in ("6000rpm", "8000rpm", "11000rpm"):
                source = f"Step-{stage}/myfeature/T{stage}/{rpm}/{label}/clean.csv"
                for row in range(10):
                    records.append({
                        "sample_id": f"{stage}-{label}-{rpm}-{row}",
                        "label": label,
                        "stage": stage,
                        "rpm": rpm,
                        "source_file": source,
                        "group_id": source,
                        "source_interval": None,
                    })
    source_counts = Counter(item["source_file"] for item in records)
    source_meta = {item["source_file"]: item for item in records}
    files = [
        {
            "source_file": source,
            "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "rows": count,
            "stage": source_meta[source]["stage"],
            "rpm": source_meta[source]["rpm"],
            "label": source_meta[source]["label"],
        }
        for source, count in sorted(source_counts.items())
    ]
    catalog = {
        "dataset_fingerprint": "c" * 64,
        "sample_count": len(records),
        "files": files,
    }
    role = {
        "checksum": "r" * 64,
        "split_id": "role-a",
        "class_combination_id": "known-5screws",
        "class_combination_seed": 42,
        "protocol": "A",
        "healthy_label": "8screws",
        "known_fault_labels": ["5screws"],
        "unknown_validation_labels": [],
        "unknown_test_labels": ["7screws"],
    }
    fold = generate_campaign_folds(
        records,
        healthy_label=role["healthy_label"],
        known_fault_labels=role["known_fault_labels"],
        unknown_validation_labels=role["unknown_validation_labels"],
        unknown_test_labels=role["unknown_test_labels"],
    )[0]
    return records, catalog, role, fold


class FaultTypeManifestTests(unittest.TestCase):
    def test_gzip_round_trip_is_deterministic_and_checksum_checked(self) -> None:
        manifest = _make_complete_manifest()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = write_split_manifest(manifest, root)
            frozen_bytes = path.read_bytes()
            self.assertEqual(read_split_manifest(path), manifest)
            self.assertEqual(write_split_manifest(copy.deepcopy(manifest), root), path)
            self.assertEqual(path.read_bytes(), frozen_bytes)

            tampered = copy.deepcopy(manifest)
            tampered["records"][0]["rpm"] = "changed-after-checksum"
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                write_split_manifest(tampered, root)

            path.write_bytes(frozen_bytes[:-1] + bytes([frozen_bytes[-1] ^ 1]))
            with self.assertRaises((OSError, ValueError)):
                read_split_manifest(path)

    def test_built_campaign_holdout_is_honestly_incomplete(self) -> None:
        records, catalog, role, fold = _campaign_fixture()
        manifest = build_split_manifest(
            records,
            catalog,
            role,
            fold,
            sample_split_seed=42,
            git_commit="abc123",
        )
        self.assertEqual(manifest["manifest_checksum"], compute_manifest_checksum(manifest))
        self.assertEqual(manifest["validator"]["status"], "INCOMPLETE")
        self.assertIn("TEST_INSUFFICIENT_GROUPS", manifest["validator"]["error_codes"])
        self.assertIn("validation and calibration", " ".join(manifest["validator"]["details"]["TEST_INSUFFICIENT_GROUPS"]))
        self.assertIn("1 test groups", " ".join(manifest["validator"]["details"]["TEST_INSUFFICIENT_GROUPS"]))
        self.assertTrue(manifest["shared_validation_calibration"])
        self.assertEqual(manifest["campaigns"]["test"], "3")
        self.assertIn("documented distinct motor IDs", " ".join(manifest["limitations"]))
        self.assertIn("raw acquisition provenance is unverified", " ".join(manifest["limitations"]))
        self.assertEqual(validate_split_manifest(manifest)["status"], "INCOMPLETE")

    def test_embedded_validation_evidence_is_checksum_bound(self) -> None:
        records, catalog, role, fold = _campaign_fixture()
        manifest = build_split_manifest(
            records, catalog, role, fold,
            sample_split_seed=42, git_commit="abc123",
        )
        manifest["validator"]["status"] = "PASS"
        self.assertNotEqual(manifest["manifest_checksum"], compute_manifest_checksum(manifest))
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                write_split_manifest(manifest, temp)


if __name__ == "__main__":
    unittest.main()
