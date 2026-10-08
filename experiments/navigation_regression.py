"""相同來源／seed的原展示與新導覽有界配對回歸。"""
from __future__ import annotations

import argparse
import json

from core.data import discover_datasets
from core.logger import setup_run
from experiments.navigation_data_contract import run as contract
from web.guide import GuideHub
from web.live import LiveDemo


class Collector:
    def __init__(self):
        self.sample = None

    def write_message(self, raw):
        msg = json.loads(raw)
        if msg["type"] == "sample":
            self.sample = msg


def run(dataset, seed=42):
    source = contract(dataset, seed)
    results = []
    keys = ("t", "score", "verdict", "pca", "ewma", "cusum", "quarantine", "attempts", "phase")
    for method in ("mahalanobis", "knn"):
        options = {"openset_method": method, "mahalanobis_method": "ledoit_wolf",
                   "confidence": .95, "knn_neighbors": 5}
        hub = GuideHub([dataset], seed=seed, detector_options=options)
        hub.build(dataset["motor"], dataset["rpm"])
        original = LiveDemo(dataset, seed=seed, **options)
        collector = Collector()
        hub.clients.add(collector)
        paired = 0
        def tick():
            nonlocal paired
            expected = next(m for m in original.tick() if m["type"] == "sample")
            hub.running = True
            hub.tick()
            assert all(expected[k] == collector.sample[k] for k in keys)
            assert original.session.monitor.summary() == hub.demo.session.monitor.summary()
            paired += 1
        try:
            for _ in range(40):
                tick()
            original.set_source("5screws")
            hub.demo.set_source("5screws")
            arrival = 0
            while arrival < 600 and hub.demo.session.candidate is None:
                tick()
                arrival += 1
            found = hub.demo.session.candidate is not None
            confirmed = None
            if found:
                assert original.session.candidate["size"] == hub.demo.session.candidate["size"]
                confirmed = original.confirm()
                assert confirmed == hub.demo.confirm()
                for _ in range(60):
                    tick()
            trends = {}
            for name, total in (("A", 260), ("B", 160)):
                original._build()
                hub.demo._build()
                original.start_scenario(name)
                hub.demo.start_scenario(name)
                hub.scenario_end = total
                for _ in range(total):
                    tick()
                assert not hub.running
                assert original.alarms == hub.demo.alarms
                trends[name] = hub.demo.alarms
            results.append({"method": method, "candidate_found": found,
                            "fault_arrival_count": arrival, "confirm": confirmed,
                            "paired_samples": paired, "mismatches": 0, "trend_alarms": trends})
        finally:
            original.close()
            hub.demo.close()
            hub.executor.shutdown()
    assert source == contract(dataset, seed)
    return {"schema": "navigation_regression_v1", "data": source, "seed": seed,
            "paired_methods": results, "source_unchanged": True,
            "claim": "工程計算一致性，非模型可靠性或fresh盲測"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default="data")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    log, paths = setup_run("navigation_regression")
    dataset = next(d for d in discover_datasets(args.data_root)
                   if d["motor"] == "T1" and d["rpm"] == "8000rpm")
    result = run(dataset, args.seed)
    (paths.output_dir / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("兩方法逐筆配對完成；來源未變")


if __name__ == "__main__":
    main()
