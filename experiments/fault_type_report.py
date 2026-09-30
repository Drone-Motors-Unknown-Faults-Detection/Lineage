"""Evidence-only tables/plots from completed, predeclared experiment matrices."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from core.logger import setup_run, save_plot
from experiments.fault_type_metrics import _mean_ci95, paired_mahalanobis_knn


TABLE_METRICS = {
    "known_accuracy": "known_classification.accuracy",
    "known_balanced_accuracy": "known_classification.balanced_accuracy",
    "known_macro_f1": "known_classification.macro_f1",
    "unknown_auroc": "unknown_rejection.auroc_unknown_positive",
    "unknown_aupr": "unknown_rejection.aupr_unknown_positive",
    "unknown_recall": "unknown_rejection.unknown_recall",
    "unknown_f1": "unknown_rejection.unknown_f1",
    "fpr95": "unknown_rejection.fpr_at_95_tpr",
    "healthy_fpr": "healthy_safety.false_positive_rate",
    "known_acceptance": "known_acceptance_rate",
    "open_set_classification_rate": "open_set_classification_rate",
}


def _write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def _write_csv(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(pools, *, paths) -> dict:
    """``pools`` contains exact completed matrix directories, never model inputs."""
    root = paths.output_dir
    rows, all_summaries, matrices, unknown_rows, known_rows = [], [], [], [], []
    source_index = []
    strata_seen = set()
    for matrix_root in map(Path, pools):
        index = json.loads((matrix_root / "matrix_index.json").read_text(encoding="utf-8"))
        plan = json.loads((matrix_root / "run_plan.json").read_text(encoding="utf-8"))
        status = json.loads((matrix_root / "run_status.json").read_text(encoding="utf-8"))
        if plan["pilot"]:
            raise ValueError("pilot matrices cannot be mixed into research reports")
        matrices.append({"path": str(matrix_root.resolve()), "plan_checksum": plan["plan_checksum"],
            "model_git_commit": plan["git_commit"], "dataset_fingerprint": plan["dataset_fingerprint"],
            "declared": status["declared_run_count"], "completed": index["completed"],
            "failed_or_pending": index["failed_or_pending"]})
        summaries = [json.loads(Path(r["summary_path"]).read_text(encoding="utf-8"))
            for r in status["runs"].values() if r["status"] == "completed"]
        all_summaries.extend(summaries)
        for stratum in index["strata"]:
            key = (stratum["protocol"], stratum["N"], stratum["method"])
            if key in strata_seen:
                raise ValueError(f"duplicate report stratum {key}; do not double-count resumed runs")
            strata_seen.add(key)
            aggregate = json.loads(Path(stratum["path"]).read_text(encoding="utf-8"))
            row = {"protocol": key[0], "N": key[1], "method": key[2], "runs": stratum["runs"], "scope": "INCOMPLETE_exploratory"}
            for name, metric in TABLE_METRICS.items():
                stats = stratum["metrics"][metric]
                for part in ("mean", "standard_deviation", "ci95_lower", "ci95_upper"):
                    row[name + "_" + part] = stats[part]
                row[name + "_pooled"] = _nested(aggregate["pooled_sample"]["metrics"], metric)
            rows.append(row)
            unknown_rows.extend({"protocol": key[0], "N": key[1], "method": key[2], **r}
                for r in aggregate["macro_over_splits"]["per_unknown_label"])
            recalls, attractions = defaultdict(list), defaultdict(Counter)
            for summary in summaries:
                if (summary["protocol"], summary["known_fault_count"], summary["openset_method"]) != key:
                    continue
                for r in summary["metrics"]["known_classification"]["per_class"]:
                    if r["label"] != summary["healthy_label"]:
                        recalls[r["label"]].append(r["recall"])
                for r in summary["metrics"]["per_unknown_label"]:
                    attractions[r["unknown_label"]].update({c["known_class"]: c["count"] for c in r["attraction_counts"]})
            known_rows.extend({"protocol": key[0], "N": key[1], "method": key[2], "label": label,
                "recall": _mean_ci95(values)} for label, values in sorted(recalls.items()))
            source_index.append({"protocol": key[0], "N": key[1], "method": key[2],
                "unknown_attraction_counts": {label: dict(counts) for label, counts in attractions.items()}})
    rows.sort(key=lambda r: (r["protocol"], r["N"], r["method"]))
    _write_csv(root / "results_table.csv", rows)
    _write_json(root / "per_unknown_configuration.json", unknown_rows)
    _write_json(root / "per_known_configuration.json", known_rows)
    _write_json(root / "unknown_attraction_counts.json", source_index)
    pairs = []
    for protocol, n in sorted({(r["protocol"], r["known_fault_count"]) for r in all_summaries}):
        summaries = [r for r in all_summaries if r["protocol"] == protocol and r["known_fault_count"] == n]
        pairs.append({"protocol": protocol, "N": n, **paired_mahalanobis_knn(summaries)})
    _write_json(root / "paired_by_protocol_and_N.json", pairs)
    hardest = {}
    for method in ("mahalanobis", "knn"):
        known = [r for r in known_rows if r["protocol"] == "A" and r["N"] == 5 and r["method"] == method]
        unknown = [r for r in unknown_rows if r["protocol"] == "A" and r["N"] == 5 and r["method"] == method]
        hardest[method] = {"known": min(known, key=lambda r: r["recall"]["mean"]) if known else None,
            "unknown": min(unknown, key=lambda r: r["recall"]["mean"]) if unknown else None}
    _write_json(root / "hardest_configurations.json", hardest)
    _write_csv(root / "primary_condition_analysis.csv", _condition_analysis(all_summaries))
    _plot_sweep(rows, paths)
    text = ["# Fault-configuration open-set results (exploratory)", "",
        "All current matrices are INCOMPLETE: only one held-out campaign per class and shared validation/calibration. These are not complete independent physical-motor results.", "",
        "Known classifier is fixed train-only balanced logistic regression. Detector thresholds use known calibration only. A and B are separate. Intervals are descriptive across correlated combinations/campaign folds, not motor-population confidence.", "",
        "Rates below are percentages; AUROC is unitless. Healthy FPR is lower-is-better.", "",
        "| Protocol | N | Detector | Runs | Known acc % | Unknown AUROC | Unknown recall % | Healthy FPR % |", "|---|---:|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        text.append(f"| {r['protocol']} | {r['N']} | {r['method']} | {r['runs']} | {_fmt(r['known_accuracy_mean'], 100)} | {_fmt(r['unknown_auroc_mean'])} | {_fmt(r['unknown_recall_mean'], 100)} | {_fmt(r['healthy_fpr_mean'], 100)} |")
    text.extend(["", "See results_table.csv for mean, SD, nominal 95% intervals and pooled rates; per-class/paired JSON files contain detailed evidence. N=9 unknown metrics are unavailable, not zero.", "", "## Artifact source directories", ""])
    text.extend(f"- `{m['path']}`: {m['completed']}/{m['declared']} completed; model commit `{m['model_git_commit']}`." for m in matrices)
    (root / "report.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    final = {"matrices": matrices, "result_scope": "INCOMPLETE_exploratory_not_main_independent_test_conclusion", "hardest": hardest,
        "report_path": str((root / "report.md").resolve()), "table_path": str((root / "results_table.csv").resolve())}
    _write_json(root / "report_index.json", final)
    return final


def _condition_analysis(summaries):
    """Pooled primary counts by configuration/RPM/campaign; repeated predictions."""
    counts = defaultdict(Counter)
    for summary in summaries:
        if summary["protocol"] != "A" or summary["known_fault_count"] != 5:
            continue
        artifact = summary["prediction_artifact"]
        blob = Path(artifact["path"]).read_bytes()
        import hashlib
        if hashlib.sha256(blob).hexdigest() != artifact["sha256"]:
            raise ValueError("report prediction artifact checksum mismatch")
        for line in gzip.decompress(blob).splitlines():
            row = json.loads(line)
            key = (summary["openset_method"], row["true_label"], row["true_role"], row["rpm"], row["stage"])
            counts[key].update(n=1, rejected=int(row["is_unknown"]), correctly_classified=int(row["predicted_known_class"] == row["true_label"]))
    return [{"method": method, "label": label, "role": role, "rpm": rpm, "campaign": campaign,
        "prediction_count": c["n"], "rejection_rate": c["rejected"] / c["n"],
        "known_classification_accuracy": c["correctly_classified"] / c["n"] if role != "unknown_test" else None,
        "weighting": "pooled repeated predictions across predeclared combinations; not independent motors"}
        for (method, label, role, rpm, campaign), c in sorted(counts.items())]


def _nested(value, path):
    for key in path.split("."):
        value = value.get(key) if isinstance(value, dict) else None
    return value


def _fmt(value, scale=1):
    return "unavailable" if value is None else f"{value * scale:.3f}"


def _plot_sweep(rows, paths):
    selected = [r for r in rows if r["protocol"] == "A"]
    if not selected:
        return
    fig, axes = plt.subplots(1, 3, figsize=(13, 4))
    for ax, metric, title in zip(axes, ("known_accuracy", "unknown_auroc", "healthy_fpr"),
                                ("Known-class accuracy", "Unknown-positive AUROC", "Healthy false-positive rate"), strict=True):
        for method in ("mahalanobis", "knn"):
            points = sorted((r for r in selected if r["method"] == method and r[metric + "_mean"] is not None), key=lambda r: r["N"])
            x, y = [r["N"] for r in points], [r[metric + "_mean"] for r in points]
            lower = [max(0, r[metric + "_ci95_lower"] if r[metric + "_ci95_lower"] is not None else r[metric + "_mean"]) for r in points]
            upper = [min(1, r[metric + "_ci95_upper"] if r[metric + "_ci95_upper"] is not None else r[metric + "_mean"]) for r in points]
            ax.plot(x, y, marker="o", label=method)
            ax.fill_between(x, lower, upper, alpha=.15)
        ax.set(title=title, xlabel="Number of known fault configurations N", ylim=(0, 1))
        ax.grid(alpha=.2)
    axes[0].legend()
    fig.suptitle("Exploratory campaign holdout; descriptive nominal 95% intervals (not independent motors)", fontsize=10)
    fig.tight_layout()
    save_plot(fig, paths, "known_fault_sweep.png")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, action="append", required=True)
    args = parser.parse_args()
    log, paths = setup_run("fault_type_report")
    result = run(args.matrix, paths=paths)
    log.info("report created: {}", result["report_path"])


if __name__ == "__main__":
    main()
