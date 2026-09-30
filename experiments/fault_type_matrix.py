"""Predeclared, resumable campaign-fold matrix for fault configurations."""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import time
import traceback
from collections import Counter, defaultdict
from pathlib import Path

from core.fault_type_features import FeatureStore
from core.fault_type_manifest import build_split_manifest, read_split_manifest, write_split_manifest
from core.fault_type_sample_split import generate_campaign_folds, load_formal_catalog
from core.fault_type_validator import compute_manifest_checksum
from core.logger import setup_run, save_plot
from core.openset import SUPPORTED_OPENSET_METHODS
from experiments.fault_type_metrics import aggregate_fault_type_runs, evaluate_fault_type_predictions, paired_mahalanobis_knn
from experiments.fault_type_openset import CLASSIFIER_CONFIG, DETECTOR_CONFIG, run, save_result


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _write_json(path: Path, value) -> None:
    # A terminated process must leave the previous valid checkpoint intact.
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        file.write(json.dumps(value, indent=2, allow_nan=False))
        file.flush()
        os.fsync(file.fileno())
    temporary.replace(path)


def cap_fold(fold: dict, records: list[dict], cap: int) -> dict:
    """Only for predeclared smoke, keeping every source file represented."""
    result = copy.deepcopy(fold)
    by_id = {r["sample_id"]: r for r in records}
    selected_before = set().union(*(set(ids) for ids in result["sample_ids"].values()))
    for split, ids in result["sample_ids"].items():
        grouped = defaultdict(list)
        for sid in ids:
            grouped[by_id[sid]["source_file"]].append(sid)
        result["sample_ids"][split] = [sid for source in sorted(grouped)
            for sid in sorted(grouped[source], key=lambda s: by_id[s].get("row_index", s))[:cap]]
    selected_after = set().union(*(set(ids) for ids in result["sample_ids"].values()))
    result["excluded"].extend({"sample_id": sid, "reason": f"predeclared_smoke_first_{cap}_rows_per_source"} for sid in sorted(selected_before - selected_after))
    result["limitations"].append("Smoke-only source-row cap; not a formal accuracy estimate")
    return result


def make_plan(registry: dict, *, n_values: list[int], protocol: str, git_commit: str,
              methods: list[str], pilot: bool = False, cap: int | None = None) -> dict:
    if not n_values or len(n_values) != len(set(n_values)) or any(n not in range(1, 10) for n in n_values):
        raise ValueError("N values must be unique integers from 1 through 9")
    if protocol not in {"A", "B"}:
        raise ValueError("protocol must be A or B")
    if cap is not None and cap < 1:
        raise ValueError("sample cap must be positive")
    if len(methods) != len(set(methods)) or not methods or set(methods) - set(SUPPORTED_OPENSET_METHODS):
        raise ValueError("methods must be unique supported detectors")
    checksum = registry.get("registry_checksum")
    if checksum != _digest({k: v for k, v in registry.items() if k != "registry_checksum"}):
        raise ValueError("class registry checksum mismatch")
    roles = [r for r in registry["protocol_a" if protocol == "A" else "protocol_b_n5"] if r["n_known_faults"] in n_values]
    if not roles:
        raise ValueError("no matching predeclared roles")
    if pilot:
        roles = roles[:1]
    elif cap is not None:
        raise ValueError("sample cap is smoke-only and requires --pilot")
    plan = {"schema_version": 1, "git_commit": git_commit,
        "dataset_fingerprint": registry["dataset_fingerprint"], "registry_checksum": checksum,
        "created_at": "2026-09-30T00:00:00Z", "protocol": protocol, "n_values": n_values,
        "roles": roles, "sample_split_seeds": registry["sample_split_seeds"],
        "fold_indices": [0] if pilot else [0, 1, 2], "methods": methods,
        "pilot": pilot, "sample_cap_per_source": cap, "scope": "exploratory_incomplete_campaign_holdout",
        "classifier": CLASSIFIER_CONFIG, "detector": DETECTOR_CONFIG,
        "unknown_validation_used_for_selection": False, "test_used_for_selection": False}
    plan["plan_checksum"] = _digest(plan)
    return plan


def verify_saved(summary: dict, manifest: dict) -> None:
    if summary["manifest_checksum"] != manifest["manifest_checksum"]:
        raise ValueError("resume manifest mismatch")
    for key in ("prediction_artifact", "fit_audit_artifact"):
        blob = Path(summary[key]["path"]).read_bytes()
        if hashlib.sha256(blob).hexdigest() != summary[key]["sha256"]:
            raise ValueError(f"resume checksum mismatch: {key}")
    blob = gzip.decompress(Path(summary["prediction_artifact"]["path"]).read_bytes())
    rows = [json.loads(line) for line in blob.splitlines()]
    if {r["sample_id"] for r in rows} != set(manifest["sample_ids"]["test"]) or len(rows) != len(manifest["sample_ids"]["test"]):
        raise ValueError("resume test IDs mismatch")
    if any(r["manifest_checksum"] != manifest["manifest_checksum"] for r in rows):
        raise ValueError("resume prediction manifest mismatch")
    by_id = {r["sample_id"]: r for r in manifest["records"]}
    for row in rows:
        source = by_id[row["sample_id"]]
        if row["true_label"] != source["label"] or row["group_id"] != source["group_id"]:
            raise ValueError("resume true label or group mismatch")
        if row["threshold"] != 1.0 or row["is_unknown"] != (row["openset_score"] > 1.0):
            raise ValueError("resume rejection decision mismatch")
    recomputed = evaluate_fault_type_predictions(rows, healthy_label=summary["healthy_label"],
        known_labels=summary["known_labels"], unknown_labels=summary["unknown_labels"],
        known_fault_count=summary["known_fault_count"])
    if recomputed != summary["metrics"]:
        raise ValueError("resume metrics do not match actual predictions")


def _slim_predictions(path: str) -> list[dict]:
    keys = ("sample_id", "true_label", "true_role", "predicted_known_class", "openset_score", "is_unknown", "nearest_known_class")
    return [{k: row[k] for k in keys} for line in gzip.decompress(Path(path).read_bytes()).splitlines()
            for row in [json.loads(line)]]


def summarize_matrix(root: Path, state: dict, log) -> dict:
    groups = defaultdict(list)
    summaries = []
    failed = []
    for item in state["runs"].values():
        if item["status"] == "completed":
            summary = json.loads(Path(item["summary_path"]).read_text(encoding="utf-8"))
            summaries.append(summary)
            groups[(summary["protocol"], summary["known_fault_count"], summary["openset_method"])].append(summary)
        else:
            failed.append(item)
    index = {"completed": len(summaries), "not_completed": len(failed), "failed_or_pending": failed,
        "plan_checksum": state["plan_checksum"], "strata": [],
        "feature_ablation": {"status": "skipped", "reason": "no usable neural embedding pipeline/artifact in current Lineage; only formal 105D features"}}
    for (protocol, n, method), runs in sorted(groups.items()):
        log.info("aggregate protocol={} N={} method={} runs={}", protocol, n, method, len(runs))
        enriched = [{**r, "predictions": _slim_predictions(r["prediction_artifact"]["path"])} for r in runs]
        result = aggregate_fault_type_runs(enriched)
        result["result_scope"] = "exploratory_incomplete_not_main_independent_test_conclusion"
        destination = root / f"aggregate_{protocol}_n{n}_{method}.json"
        _write_json(destination, result)
        index["strata"].append({"protocol": protocol, "N": n, "method": method,
            "path": str(destination.resolve()), "runs": len(runs),
            "metrics": result["macro_over_splits"]["metrics"], "validator_statuses": dict(Counter(r["validator"]["status"] for r in runs))})
        del enriched, result
    paired = paired_mahalanobis_knn(summaries)
    _write_json(root / "paired_comparison.json", paired)
    index["paired_comparison"] = str((root / "paired_comparison.json").resolve())
    _write_json(root / "matrix_index.json", index)
    return index


def annotate_pooled_task_count(root: Path, log) -> None:
    """Migrate descriptive metadata only; numeric metrics/predictions unchanged."""
    index = json.loads((root / "matrix_index.json").read_text(encoding="utf-8"))
    changes = []
    for stratum in index["strata"]:
        path = Path(stratum["path"])
        before_blob = path.read_bytes()
        aggregate = json.loads(before_blob)
        pooled = aggregate["pooled_sample"]["metrics"]
        original_numeric = {k: v for k, v in pooled.items() if k not in {"known_fault_count", "known_fault_label_union_size", "known_fault_count_scope"}}
        union_size = len(pooled["known_classification"]["labels"]) - 1
        pooled.update(known_fault_count=stratum["N"], known_fault_label_union_size=union_size,
            known_fault_count_scope="per-run task; classification labels are the union across tasks")
        assert original_numeric == {k: v for k, v in pooled.items() if k not in {"known_fault_count", "known_fault_label_union_size", "known_fault_count_scope"}}
        _write_json(path, aggregate)
        changes.append({"path": str(path), "before_sha256": hashlib.sha256(before_blob).hexdigest(),
            "after_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "per_run_N": stratum["N"], "union_size": union_size})
    _write_json(root / "pooled_metadata_migration.json", {"changes": changes, "numerical_metrics_changed": False, "raw_predictions_or_manifests_changed": False})
    log.info("annotated {} pooled strata; no numerical metric changed", len(changes))


def run_matrix(*, data_root: Path, plan: dict, root: Path, log, retry_failed: bool = False) -> dict:
    """Plan is written before the first feature/model/test evaluation."""
    root.mkdir(parents=True, exist_ok=True)
    plan_path, state_path = root / "run_plan.json", root / "run_status.json"
    if plan_path.exists():
        if json.loads(plan_path.read_text(encoding="utf-8")) != plan:
            raise ValueError("immutable run plan differs; choose a new output run")
    else:
        _write_json(plan_path, plan)
    records, catalog = load_formal_catalog(data_root)
    if catalog["dataset_fingerprint"] != plan["dataset_fingerprint"]:
        raise ValueError("actual formal data does not match plan")
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"plan_checksum": plan["plan_checksum"], "runs": {}}
    if state["plan_checksum"] != plan["plan_checksum"]:
        raise ValueError("resume state belongs to a different plan")
    store = FeatureStore(data_root)
    elapsed = time.perf_counter()
    for role in plan["roles"]:
        folds = generate_campaign_folds(records, healthy_label=role["healthy_label"],
            known_fault_labels=role["known_fault_labels"], unknown_test_labels=role["unknown_test_labels"],
            unknown_validation_labels=role["unknown_validation_labels"])
        for fold_index in plan["fold_indices"]:
            fold = folds[fold_index]
            if plan["sample_cap_per_source"] is not None:
                fold = cap_fold(fold, records, plan["sample_cap_per_source"])
            manifest = build_split_manifest(records, catalog, role, fold,
                sample_split_seed=plan["sample_split_seeds"][fold_index], git_commit=plan["git_commit"], created_at=plan["created_at"])
            manifest_path = write_split_manifest(manifest, root / "manifests")
            if read_split_manifest(manifest_path) != manifest:
                raise ValueError("manifest round-trip mismatch")
            for method in plan["methods"]:
                run_id = manifest["split_id"] + "_" + method
                prior = state["runs"].get(run_id)
                if prior and prior["status"] == "completed":
                    verify_saved(json.loads(Path(prior["summary_path"]).read_text(encoding="utf-8")), manifest)
                    log.info("resume verified {}; no refit", run_id)
                    continue
                if prior and prior["status"] == "failed" and not retry_failed:
                    log.warning("retaining failed {}; use --retry-failed with reason recorded", run_id)
                    continue
                item = prior or {"run_id": run_id, "protocol": plan["protocol"], "N": len(role["known_fault_labels"]),
                    "method": method, "seed": manifest["sample_split_seed"], "manifest_path": str(manifest_path.resolve()), "attempts": []}
                item["status"] = "retry" if prior else "running"
                item["attempts"].append({"status": "running", "reason": "explicit_retry_failed_or_interrupted" if prior else "initial_predeclared_run"})
                state["runs"][run_id] = item
                _write_json(state_path, state)
                try:
                    result = run(store, manifest=manifest, openset_method=method, allow_incomplete=True)
                    result["metrics"] = evaluate_fault_type_predictions(result["predictions"],
                        healthy_label=result["healthy_label"], known_labels=result["known_labels"],
                        unknown_labels=result["unknown_labels"], known_fault_count=result["known_fault_count"])
                    summary = save_result(result, root / "runs")
                    verify_saved(summary, manifest)
                    item.update(status="completed", summary_path=str((root / "runs" / run_id / "summary.json").resolve()),
                        elapsed_seconds=summary["elapsed_seconds"])
                    item["attempts"][-1]["status"] = "completed"
                    log.info("completed {} N={} seed={} method={} seconds={:.2f} progress={}", run_id,
                        item["N"], item["seed"], method, summary["elapsed_seconds"], sum(r["status"] == "completed" for r in state["runs"].values()))
                    del result
                except Exception as error:
                    item.update(status="failed", reason=f"{type(error).__name__}: {error}", traceback=traceback.format_exc())
                    item["attempts"][-1].update(status="failed", reason=item["reason"])
                    log.exception("failed {}", run_id)
                _write_json(state_path, state)
    state["execution_seconds_this_invocation"] = time.perf_counter() - elapsed
    state["declared_run_count"] = len(plan["roles"]) * len(plan["fold_indices"]) * len(plan["methods"])
    _write_json(state_path, state)
    return summarize_matrix(root, state, log)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data/formal_local"))
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--n", type=int, nargs="+", default=[5])
    parser.add_argument("--protocol", choices=("A", "B"), default="A")
    parser.add_argument("--methods", choices=SUPPORTED_OPENSET_METHODS, nargs="+", default=list(SUPPORTED_OPENSET_METHODS))
    parser.add_argument("--pilot", action="store_true", help="first predeclared role and first fold only; not primary result")
    parser.add_argument("--sample-cap-per-source", type=int)
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--aggregate-only", action="store_true", help="rebuild derived summaries from completed artifacts; never refit")
    parser.add_argument("--annotate-pooled-task-count-only", action="store_true", help="metadata-only migration; no model/metric recomputation")
    args = parser.parse_args()
    log, paths = setup_run("fault_type_matrix")
    if args.resume:
        root = args.resume
        plan = json.loads((root / "run_plan.json").read_text(encoding="utf-8"))
        if plan["plan_checksum"] != _digest({k: v for k, v in plan.items() if k != "plan_checksum"}):
            raise ValueError("run plan checksum mismatch")
        if plan["classifier"] != CLASSIFIER_CONFIG or plan["detector"] != DETECTOR_CONFIG:
            raise ValueError("resume algorithm configuration changed")
    else:
        if not args.registry:
            parser.error("--registry is required for a new run")
        commit = subprocess.check_output(["git", "-c", f"safe.directory={Path.cwd().as_posix()}", "rev-parse", "HEAD"], text=True).strip()
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        plan = make_plan(registry, n_values=args.n, protocol=args.protocol, git_commit=commit,
                         methods=args.methods, pilot=args.pilot, cap=args.sample_cap_per_source)
        root = paths.output_dir
        _write_json(root / "environment.json", {"python": platform.python_version(), "platform": platform.platform(),
            "packages": {p: importlib.metadata.version(p) for p in ("numpy", "pandas", "scipy", "scikit-learn", "threadpoolctl")}})
    if args.annotate_pooled_task_count_only:
        if not args.resume or args.aggregate_only:
            parser.error("metadata annotation requires --resume, without --aggregate-only")
        annotate_pooled_task_count(root, log)
        return
    if args.aggregate_only:
        if not args.resume:
            parser.error("--aggregate-only requires --resume")
        state = json.loads((root / "run_status.json").read_text(encoding="utf-8"))
        for item in state["runs"].values():
            if item["status"] == "completed":
                summary = json.loads(Path(item["summary_path"]).read_text(encoding="utf-8"))
                verify_saved(summary, read_split_manifest(item["manifest_path"]))
        index = summarize_matrix(root, state, log)
    else:
        index = run_matrix(data_root=args.data_root, plan=plan, root=root, log=log, retry_failed=args.retry_failed)
    log.info("matrix finished: completed={} not_completed={} root={}", index["completed"], index["not_completed"], root.resolve())


if __name__ == "__main__":
    main()
