"""Immutable versioned sample manifests, including their validation evidence."""

from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

from core.fault_type_validator import compute_manifest_checksum, validate_split_manifest


def build_split_manifest(records: list[dict], catalog: dict, role: dict, fold: dict, *,
                         sample_split_seed: int, git_commit: str,
                         created_at: str = "2026-09-30T00:00:00Z") -> dict:
    """Build from predeclared roles and campaign assignments; never inspect scores.

    ``created_at`` is the frozen protocol declaration time, supplied once by
    the run plan. It is not refreshed on resume, so all content is hashable.
    """
    selected = set().union(*(set(v) for v in fold["sample_ids"].values()))
    by_id = {r["sample_id"]: r for r in records}
    known = {role["healthy_label"], *role["known_fault_labels"]}
    expected = {}
    for split in ("train", "validation", "calibration", "test"):
        labels = known | (set(role["unknown_test_labels"]) if split == "test" else
                          set(role["unknown_validation_labels"]) if split == "validation" else set())
        counts = Counter()
        for source in catalog["files"]:
            if source["stage"] == fold["campaigns"][split] and source["label"] in labels:
                counts[source["label"]] += source["rows"]
        expected[split] = dict(sorted(counts.items()))
    identity = {"dataset": catalog["dataset_fingerprint"], "class_roles": role["checksum"],
                "fold": fold["fold_id"], "sample_seed": sample_split_seed, "git_commit": git_commit}
    split_id = "sample-v1-" + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:20]
    manifest = {
        "schema_version": 1, "split_id": split_id, "created_at": created_at,
        "dataset_version": "formal-clean-105d-v1", "dataset_fingerprint": catalog["dataset_fingerprint"],
        "dataset_sample_count": catalog["sample_count"], "git_commit": git_commit,
        "class_split_id": role["split_id"], "class_combination_id": role["class_combination_id"],
        "class_combination_seed": role["class_combination_seed"], "sample_split_seed": sample_split_seed,
        "protocol": role["protocol"], "healthy_label": role["healthy_label"],
        "known_fault_labels": role["known_fault_labels"],
        "unknown_validation_labels": role["unknown_validation_labels"], "unknown_test_labels": role["unknown_test_labels"],
        "sample_ids": fold["sample_ids"], "campaigns": fold["campaigns"], "fold_id": fold["fold_id"],
        "records": [by_id[sid] for sid in sorted(selected)],
        "excluded": [{"sample_id": item["sample_id"], "reason": item["reason"]} for item in fold["excluded"]],
        "source_files": catalog["files"], "shared_validation_calibration": fold["shared_validation_calibration"],
        "group_key": "acquisition_stage_campaign", "claimed_label_semantics": "configuration",
        "requested_event_metrics": False, "expected_rpms": ["6000rpm", "8000rpm", "11000rpm"],
        "expected_counts": expected,
        "actual_counts": {s: dict(sorted(Counter(by_id[i]["label"] for i in ids).items())) for s, ids in fold["sample_ids"].items()},
        "group_counts": {s: {label: {"campaigns": len({by_id[i]["stage"] for i in ids if by_id[i]["label"] == label}),
                                     "source_files": len({by_id[i]["source_file"] for i in ids if by_id[i]["label"] == label})}
                                for label in expected[s]} for s, ids in fold["sample_ids"].items()},
        "fit_sample_ids": fold["sample_ids"]["train"], "reference_sample_ids": fold["sample_ids"]["train"],
        "calibration_sample_ids": fold["sample_ids"]["calibration"],
        "selection_sample_ids": [], "limitations": fold["limitations"],
        "minimum_test_samples_per_class": 30, "minimum_test_campaigns_per_class": 2,
    }
    # Bind the identity to all protocol content, not just the seed and role.
    manifest["split_id"] = "sample-v1-" + compute_manifest_checksum(manifest)[:20]
    manifest["validator"] = validate_split_manifest(manifest, verify_checksum=False)
    manifest["manifest_checksum"] = compute_manifest_checksum(manifest)
    return manifest


def write_split_manifest(manifest: dict, output_root: Path | str) -> Path:
    if compute_manifest_checksum(manifest) != manifest.get("manifest_checksum"):
        raise ValueError("manifest checksum mismatch")
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{manifest['split_id']}_{manifest['manifest_checksum'][:16]}.json.gz"
    content = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    packed = gzip.compress(content, compresslevel=3, mtime=0)
    if path.exists():
        if path.read_bytes() != packed:
            raise ValueError(f"immutable manifest differs: {path}")
    else:
        path.write_bytes(packed)
    return path


def read_split_manifest(path: Path | str) -> dict:
    manifest = json.loads(gzip.decompress(Path(path).read_bytes()))
    if manifest.get("manifest_checksum") != compute_manifest_checksum(manifest):
        raise ValueError("manifest checksum mismatch")
    return manifest


def main() -> None:
    import argparse
    from core.logger import setup_run
    from core.fault_type_sample_split import load_formal_catalog, generate_campaign_folds

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--created-at", default="2026-09-30T00:00:00Z")
    args = parser.parse_args()
    log, paths = setup_run("fault_type_manifest")
    records, catalog = load_formal_catalog(args.data_root)
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    if registry["dataset_fingerprint"] != catalog["dataset_fingerprint"]:
        raise ValueError("registry and actual data fingerprints differ")
    role = next(r for r in registry["protocol_a"] if len(r["known_fault_labels"]) == 5)
    folds = generate_campaign_folds(records, healthy_label=role["healthy_label"],
        known_fault_labels=role["known_fault_labels"], unknown_test_labels=role["unknown_test_labels"],
        unknown_validation_labels=role["unknown_validation_labels"])
    index = {"dataset_fingerprint": catalog["dataset_fingerprint"], "git_commit": args.git_commit, "manifests": []}
    for fold, seed in zip(folds, registry["sample_split_seeds"], strict=True):
        manifest = build_split_manifest(records, catalog, role, fold, sample_split_seed=seed,
                                       git_commit=args.git_commit, created_at=args.created_at)
        path = write_split_manifest(manifest, paths.output_dir / "manifests")
        assert read_split_manifest(path) == manifest
        index["manifests"].append({"path": str(path.resolve()), "split_id": manifest["split_id"],
            "checksum": manifest["manifest_checksum"], "seed": seed, "counts": manifest["actual_counts"],
            "validator": manifest["validator"]})
        log.info("fold={} seed={} status={}", fold["fold_id"], seed, manifest["validator"]["status"])
    (paths.output_dir / "validation_index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
