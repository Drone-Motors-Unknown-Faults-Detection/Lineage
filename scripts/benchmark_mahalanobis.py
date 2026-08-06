"""Run a reproducible open-set benchmark on the stored Lineage models."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import hdbscan
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from tensorflow.keras.models import Model, load_model

from scripts.logger import setup_logger
from scripts.model_utils import get_feature_layer
from scripts.openset_mahalanobis import MahalanobisOpenSetDetector


KNOWN_SCREWS = ["8screws", "1screws", "2screws", "3screws", "4screws"]
UNKNOWN_SCREWS = ["5screws", "6screws", "7screws", "3_14screws", "4_146screws"]
METHODS = ["legacy", "ledoit_wolf", "oas", "mcd"]
ARCHITECTURES = ["CNN", "ResNet", "VGG16"]
RPMS = ["8000rpm", "6000rpm", "11000rpm"]


@dataclass(frozen=True)
class ModelConfig:
    model_id: int
    step: str
    t_code: str
    rpm: str
    architecture: str
    model_path: Path
    feature_dir: Path


def available_configs(repo_root: Path) -> list[ModelConfig]:
    configs: list[ModelConfig] = []
    for model_id in list(range(1, 10)) + list(range(19, 28)):
        zero_based = model_id - 1
        group_index = (zero_based % 9) // 3
        architecture = ARCHITECTURES[zero_based % 3]
        rpm = RPMS[group_index]
        if model_id <= 9:
            step, t_code, letter = "Step-1", "T1", "C"
            suffix = "" if rpm == "8000rpm" else "_1"
        else:
            step, t_code, letter, suffix = "Step-3", "T3", "A", "_1"
        rpm_number = rpm.removesuffix("rpm")
        model_path = repo_root / "data" / step / "model" / f"{architecture}_{letter}{rpm_number}{suffix}.keras"
        feature_dir = repo_root / "data" / step / "myfeature" / t_code / rpm
        if model_path.exists() and feature_dir.exists():
            configs.append(
                ModelConfig(model_id, step, t_code, rpm, architecture, model_path, feature_dir)
            )
    return configs


def load_group(config: ModelConfig, screws: list[str], max_per_class: int) -> tuple[np.ndarray, np.ndarray]:
    frames: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    for label, screw in enumerate(screws):
        path = config.feature_dir / screw / f"{config.t_code}_Group_feature_data_clean.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path).replace([np.inf, -np.inf], np.nan).dropna()
        if len(frame) > max_per_class:
            frame = frame.sample(max_per_class, random_state=42)
        frames.append(frame.to_numpy(dtype=np.float32))
        labels.append(np.full(len(frame), label, dtype=int))
    return np.vstack(frames), np.concatenate(labels)


def deep_features(feature_model: Model, X: np.ndarray) -> np.ndarray:
    return feature_model.predict(X.reshape(-1, X.shape[1], 1), batch_size=256, verbose=0)


def legacy_hdbscan_inliers(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=25,
        min_samples=3,
        cluster_selection_method="eom",
    ).fit(X)
    keep = clusterer.labels_ != -1
    return X[keep], y[keep]


def fpr_at_tpr95(y_true: np.ndarray, scores: np.ndarray) -> float:
    fpr, tpr, _ = roc_curve(y_true, scores)
    eligible = fpr[tpr >= 0.95]
    return float(np.min(eligible)) if len(eligible) else 1.0


def evaluate_method(
    method: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_cal: np.ndarray,
    y_cal: np.ndarray,
    X_known: np.ndarray,
    y_known: np.ndarray,
    X_unknown: np.ndarray,
    unknown_faults: np.ndarray,
) -> dict[str, float | int | str]:
    fit_X, fit_y = (legacy_hdbscan_inliers(X_train, y_train) if method == "legacy" else (X_train, y_train))
    detector = MahalanobisOpenSetDetector(method=method, confidence=0.95, random_state=42)
    detector.fit(fit_X, fit_y, X_cal, y_cal)

    known_scores = detector.score_samples(X_known)
    unknown_scores = detector.score_samples(X_unknown)
    scores = np.concatenate([known_scores, unknown_scores])
    truth = np.concatenate([np.zeros(len(known_scores), dtype=int), np.ones(len(unknown_scores), dtype=int)])
    prediction = (scores > 1.0).astype(int)

    result: dict[str, float | int | str] = {
        "method": method,
        "feature_dimensions": int(X_train.shape[1]),
        "fit_samples": int(len(fit_X)),
        "known_test_samples": int(len(X_known)),
        "unknown_test_samples": int(len(X_unknown)),
        "auroc": float(roc_auc_score(truth, scores)),
        "fpr_at_tpr95": fpr_at_tpr95(truth, scores),
        "open_set_accuracy": float(accuracy_score(truth, prediction)),
        "balanced_accuracy": float(balanced_accuracy_score(truth, prediction)),
        "known_acceptance": float(np.mean(known_scores <= 1.0)),
        "unknown_recall": float(np.mean(unknown_scores > 1.0)),
    }
    for fault_id, screw in enumerate(UNKNOWN_SCREWS):
        result[f"recall_{screw}"] = float(np.mean(unknown_scores[unknown_faults == fault_id] > 1.0))
    return result


def benchmark_config(config: ModelConfig, max_per_class: int, log) -> list[dict]:
    X_known_all, y_known_all = load_group(config, KNOWN_SCREWS, max_per_class)
    X_unknown_raw, unknown_faults = load_group(config, UNKNOWN_SCREWS, max_per_class)
    X_train_raw, X_holdout_raw, y_train, y_holdout = train_test_split(
        X_known_all, y_known_all, test_size=0.4, stratify=y_known_all, random_state=42
    )
    X_cal_raw, X_known_raw, y_cal, y_known = train_test_split(
        X_holdout_raw, y_holdout, test_size=0.5, stratify=y_holdout, random_state=42
    )
    scaler = RobustScaler().fit(X_train_raw)
    X_train_scaled = scaler.transform(X_train_raw)
    X_cal_scaled = scaler.transform(X_cal_raw)
    X_known_scaled = scaler.transform(X_known_raw)
    X_unknown_scaled = scaler.transform(X_unknown_raw)

    classifier = load_model(config.model_path, compile=False)
    feature_model = Model(classifier.input, get_feature_layer(classifier).output)
    X_train = deep_features(feature_model, X_train_scaled)
    X_cal = deep_features(feature_model, X_cal_scaled)
    X_known = deep_features(feature_model, X_known_scaled)
    X_unknown = deep_features(feature_model, X_unknown_scaled)
    closed_predictions = np.argmax(classifier.predict(
        X_known_scaled.reshape(-1, X_known_scaled.shape[1], 1), batch_size=256, verbose=0
    ), axis=1)
    closed_accuracy = float(np.mean(closed_predictions == y_known))

    rows = []
    for method in METHODS:
        result = evaluate_method(
            method, X_train, y_train, X_cal, y_cal, X_known, y_known, X_unknown, unknown_faults
        )
        result.update(
            {
                "model_id": config.model_id,
                "step": config.step,
                "t_code": config.t_code,
                "rpm": config.rpm,
                "architecture": config.architecture,
                "closed_set_accuracy": closed_accuracy,
            }
        )
        rows.append(result)
        log.info(
            "model={:02d} arch={} rpm={} method={} auroc={:.4f} accuracy={:.4f} known_accept={:.4f} unknown_recall={:.4f}",
            config.model_id,
            config.architecture,
            config.rpm,
            method,
            result["auroc"],
            result["open_set_accuracy"],
            result["known_acceptance"],
            result["unknown_recall"],
        )
    return rows


def save_outputs(frame: pd.DataFrame, output_dir: Path) -> None:
    frame.to_csv(output_dir / "results.csv", index=False)
    metrics = [
        "auroc",
        "fpr_at_tpr95",
        "open_set_accuracy",
        "balanced_accuracy",
        "known_acceptance",
        "unknown_recall",
    ]
    summary = frame.groupby("method")[metrics].agg(["mean", "std"])
    summary.to_csv(output_dir / "summary.csv")
    (output_dir / "summary.json").write_text(
        json.dumps(summary.to_dict(), ensure_ascii=False, indent=2, default=float), encoding="utf-8"
    )

    order = METHODS
    means = frame.groupby("method")[["auroc", "open_set_accuracy", "balanced_accuracy"]].mean().reindex(order)
    axes = means.plot.bar(figsize=(10, 5), ylim=(0, 1.05), rot=0, grid=True, title="Mahalanobis open-set benchmark")
    axes.set_ylabel("Score")
    plt.tight_layout()
    plt.savefig(output_dir / "method_comparison.png", dpi=180)
    plt.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="*", type=int, help="Model IDs; default is every available T1/T3 model")
    parser.add_argument("--max-per-class", type=int, default=300)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    log, paths = setup_logger("mahalanobis_benchmark", repo_root=repo_root)
    configs = available_configs(repo_root)
    if args.models:
        configs = [config for config in configs if config.model_id in set(args.models)]
    if not configs:
        raise RuntimeError("No matching models and feature directories were found under data/")
    log.info("benchmark_configs={}", [asdict(config) | {"model_path": str(config.model_path), "feature_dir": str(config.feature_dir)} for config in configs])

    rows: list[dict] = []
    for config in configs:
        log.info("starting model={:02d} path={}", config.model_id, config.model_path)
        rows.extend(benchmark_config(config, args.max_per_class, log))
    frame = pd.DataFrame(rows)
    save_outputs(frame, paths.output_dir)
    log.info("results_csv={}", paths.output_dir / "results.csv")
    log.info("summary_csv={}", paths.output_dir / "summary.csv")
    print(frame.groupby("method")[["auroc", "open_set_accuracy", "balanced_accuracy", "known_acceptance", "unknown_recall"]].mean())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
