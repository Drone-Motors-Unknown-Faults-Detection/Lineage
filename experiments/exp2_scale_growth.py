"""實驗二：量尺擴張（Scale Growth）— 未知偵測 → 隔離累積 → HDBSCAN 分群 → 操作員確認 → 擴張重訓。

ScaleGrowthSession 是核心狀態機（Web 即時展示直接驅動它）：
    1. 每筆樣本以 OpenSetMonitor 打分；判為未知者進隔離區
    2. 隔離區累積達 min_cluster_size 後以 HDBSCAN 找穩定叢集 → 產生「候選新故障」
    3. confirm() 模擬操作員確認：以叢集多數真實配置為標註（此時才揭示 ground truth），
       納入已知類別並重新擬合 → 量尺擴張
    偵測與分群過程從未使用標籤；標籤只在確認步驟扮演「操作員」。

批次執行（產出論文數據：逐配置的發現延遲、叢集純度、擴張後準確率）：
    venv/bin/python -m experiments.exp2_scale_growth --motor T1 --rpm 8000rpm
"""

from __future__ import annotations

import argparse

import hdbscan
import numpy as np

from core.data import CONFIG_ORDER, HEALTHY, CycleSampler, config_sort_key, display_name
from core.logger import setup_run
from core.monitor import OpenSetMonitor
from core.runner import add_dataset_args, resolve_dataset, save_json


class ScaleGrowthSession:
    """從健康基準起步、隨確認逐步擴張的開放集監測 session。"""

    def __init__(
        self,
        pools: dict[str, np.ndarray],
        seed: int = 42,
        confidence: float = 0.95,
        method: str = "ledoit_wolf",
        min_cluster_size: int = 25,
        min_samples: int = 3,
        recluster_every: int = 10,
    ) -> None:
        self.pools = pools
        self.monitor = OpenSetMonitor(pools, seed=seed, confidence=confidence, method=method)
        self.monitor.fit_initial()
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.recluster_every = recluster_every
        self.quarantine_X: list[np.ndarray] = []
        self.quarantine_truth: list[str] = []
        self.candidate: dict | None = None
        self._since_cluster = 0

    # -- 串流 ------------------------------------------------------------------

    def process(self, x_raw: np.ndarray, truth: str) -> dict:
        """處理一筆樣本。truth 僅存入隔離區供之後的「操作員確認」揭示。"""
        score = float(self.monitor.score(x_raw)[0])
        label = self.monitor.classify(x_raw)[0]
        candidate_new = False
        if label is None:
            self.quarantine_X.append(np.asarray(x_raw, dtype=float).ravel())
            self.quarantine_truth.append(truth)
            self._since_cluster += 1
            if (
                self.candidate is None
                and len(self.quarantine_X) >= self.min_cluster_size
                and self._since_cluster >= self.recluster_every
            ):
                candidate_new = self._try_cluster()
        return {
            "score": score,
            "label": label,
            "quarantine": len(self.quarantine_X),
            "candidate_new": candidate_new,
        }

    def _try_cluster(self) -> bool:
        X = self.monitor.scaler.transform(np.vstack(self.quarantine_X))
        labels = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size, min_samples=self.min_samples
        ).fit_predict(X)
        self._since_cluster = 0
        best, best_size = None, 0
        for cl in set(labels) - {-1}:
            size = int((labels == cl).sum())
            if size > best_size:
                best, best_size = cl, size
        if best is None or best_size < self.min_cluster_size:
            return False
        idx = np.flatnonzero(labels == best)
        truths = [self.quarantine_truth[i] for i in idx]
        majority = max(set(truths), key=truths.count)
        self.candidate = {
            "indices": idx.tolist(),
            "size": best_size,
            "majority": majority,
            "majority_display": display_name(majority),
            "purity": round(truths.count(majority) / len(truths), 4),
        }
        return True

    # -- 擴張 ------------------------------------------------------------------

    def confirm(self) -> dict:
        """操作員確認候選叢集 → 納入已知並重新擬合（量尺擴張）。"""
        if self.candidate is None:
            raise RuntimeError("目前沒有待確認的候選叢集")
        config = self.candidate["majority"]
        result = {
            "config": config,
            "display": display_name(config),
            "size": self.candidate["size"],
            "purity": self.candidate["purity"],
        }
        result["label"] = self.monitor.add_class(config)
        keep = [i for i, t in enumerate(self.quarantine_truth) if t != config]
        self.quarantine_X = [self.quarantine_X[i] for i in keep]
        self.quarantine_truth = [self.quarantine_truth[i] for i in keep]
        self.candidate = None
        # 殘餘的未知樣本（可能屬於另一種故障）在下一筆未知樣本進來時即可再分群
        self._since_cluster = self.recluster_every
        return result

    def state(self) -> dict:
        return {
            "known": [
                {"config": c, "display": display_name(c), "label": l}
                for c, l in self.monitor.known.items()
            ],
            "quarantine": len(self.quarantine_X),
            "candidate": self.candidate
            and {k: v for k, v in self.candidate.items() if k != "indices"},
        }


# -- 批次重播（論文數據） -----------------------------------------------------


def run(
    pools: dict[str, np.ndarray],
    sequence: list[str] | None = None,
    seed: int = 42,
    confidence: float = 0.95,
    method: str = "ledoit_wolf",
    max_ticks_per_stage: int = 600,
) -> dict:
    """依序注入各未知配置：量測發現延遲 → 自動確認 → 驗證擴張後的分類能力。"""
    if sequence is None:
        sequence = sorted((c for c in pools if c != HEALTHY), key=config_sort_key)
    session = ScaleGrowthSession(pools, seed=seed, confidence=confidence, method=method)
    rng = np.random.default_rng(seed + 1)

    stages = []
    for config in sequence:
        sampler = CycleSampler(pools[config], np.arange(len(pools[config])), rng)
        found_at = None
        for tick in range(1, max_ticks_per_stage + 1):
            session.process(sampler.draw(), config)
            if session.candidate is not None:
                found_at = tick
                break
        row = {"config": config, "display": display_name(config), "discovered": found_at is not None}
        if found_at is None:
            stages.append(row)
            continue
        res = session.confirm()
        own = session.monitor.classify(session.monitor.holdout(res["config"]))
        healthy = session.monitor.classify(session.monitor.holdout(HEALTHY))
        row.update(
            {
                "learned": res["config"],
                "samples_to_candidate": found_at,
                "cluster_size": res["size"],
                "cluster_purity": res["purity"],
                "own_holdout_acc": float(np.mean([l == res["config"] for l in own])),
                "healthy_holdout_acc": float(np.mean([l == HEALTHY for l in healthy])),
                "known_after": len(session.monitor.known),
            }
        )
        stages.append(row)

    return {
        "stages": stages,
        "final_known": list(session.monitor.known),
        "seed": seed,
        "confidence": confidence,
        "method": method,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_dataset_args(parser)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--method", default="ledoit_wolf")
    parser.add_argument(
        "--sequence", nargs="*", default=None,
        help="注入順序（預設：所有未知配置由輕到重）",
    )
    args = parser.parse_args()

    ds, pools = resolve_dataset(args)
    log, paths = setup_run("exp2_scale_growth")
    log.info(f"實驗二：量尺擴張重播 — {ds['motor']}/{ds['rpm']}"
             f"（method={args.method}, confidence={args.confidence}, seed={args.seed}）")

    result = run(
        pools, sequence=args.sequence, seed=args.seed,
        confidence=args.confidence, method=args.method,
    )
    result["dataset"] = {"motor": ds["motor"], "rpm": ds["rpm"]}

    import pandas as pd

    pd.DataFrame(result["stages"]).to_csv(paths.output_dir / "stages.csv", index=False)
    save_json(paths.output_dir / "summary.json", result)

    log.info(f"{'注入配置':<14}{'發現(筆)':>9}{'叢集':>6}{'純度':>8}{'自類準確':>10}{'健康保持':>10}{'已知數':>8}")
    for s in result["stages"]:
        if not s["discovered"]:
            log.info(f"{s['config']:<14}{'未發現':>9}")
            continue
        log.info(
            f"{s['config']:<14}{s['samples_to_candidate']:>9}{s['cluster_size']:>6}"
            f"{s['cluster_purity']*100:>7.1f}%{s['own_holdout_acc']*100:>9.1f}%"
            f"{s['healthy_holdout_acc']*100:>9.1f}%{s['known_after']:>8}"
        )
    log.info(f"最終已知類別：{' → '.join(result['final_known'])}")
    log.info(f"輸出：{paths.output_dir}")


if __name__ == "__main__":
    main()
