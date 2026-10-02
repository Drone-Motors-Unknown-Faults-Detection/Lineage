"""iter_run()（Web 邊跑邊畫）與 run()（批次）必須算出相同結果。

需要本機 data/（git 忽略）；沒有資料時整組略過。
"""

import json
import unittest

from core.data import discover_datasets, load_pools
from web.experiments import ExperimentRunner, jsonable

DATASETS = discover_datasets("data")
T1_8000 = next((d for d in DATASETS if d["motor"] == "T1" and d["rpm"] == "8000rpm"), None)


def _last_result(events):
    events = list(events)
    assert events[-1]["event"] == "result"
    return events, events[-1]["result"]


@unittest.skipUnless(T1_8000, "需要本機 data/ 的 T1/8000rpm")
class IterRunMatchesRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pools = load_pools(T1_8000["path"])

    def same(self, a, b):
        self.assertEqual(json.dumps(jsonable(a), sort_keys=True), json.dumps(jsonable(b), sort_keys=True))

    def test_exp1(self):
        from experiments.exp1_cold_start import iter_run, run

        for method in ("mahalanobis", "knn"):
            events, result = _last_result(iter_run(self.pools, seed=7, openset_method=method))
            self.same(result, run(self.pools, seed=7, openset_method=method))
            self.assertEqual(events[0]["event"], "fitted")
            n_scores = sum(len(e["scores"]) for e in events if e["event"] == "scores")
            self.assertEqual(n_scores, sum(r["n"] for r in result["rows"]))

    def test_exp3(self):
        from experiments.exp3_trend import iter_run, run

        events, result = _last_result(iter_run(self.pools, n_trials=3, seed=5))
        self.same(result, run(self.pools, n_trials=3, seed=5))
        self.assertEqual(sum(e["event"] == "trial" for e in events), len(result["trials"]))

    def test_exp4(self):
        from experiments.exp4_polar_map import iter_run, run

        events, result = _last_result(iter_run(self.pools, parts="ac"))
        self.same(result, run(self.pools, parts="ac"))
        self.assertEqual([e["name"] for e in events if e["event"] == "part"], ["geometry", "severity"])

    def test_health_monitor(self):
        from experiments.health_monitor import iter_run, run

        kwargs = dict(seed=3, motor_id="m", session_id="s", max_windows=30)
        windows = [e["window"] for e in iter_run("data", "T1", "8000rpm", "8screws", **kwargs)
                   if e["event"] == "window"]
        self.same(windows, run("data", "T1", "8000rpm", "8screws", **kwargs))


@unittest.skipUnless(T1_8000, "需要本機 data/ 的 T1/8000rpm")
class StreamFrames(unittest.TestCase):
    def test_stream_ends_with_done_matching_batch_run(self):
        runner = ExperimentRunner(DATASETS, "data")
        frames = list(runner.stream("exp1", {"dataset": "T1/8000rpm", "seed": 11}))
        self.assertEqual(frames[0][0]["event"], "start")
        done = frames[-1][0]
        self.assertEqual(done["event"], "done")
        batch = runner.run("exp1", {"dataset": "T1/8000rpm", "seed": 11})
        self.assertEqual(done["payload"]["result"], batch["result"])
        units = sum(u for _, u in frames)
        self.assertEqual(units, sum(r["n"] for r in batch["result"]["rows"]))
        for frame, _ in frames:
            json.dumps(frame, allow_nan=False)

    def test_batch_only_experiment_is_rejected(self):
        runner = ExperimentRunner(DATASETS, "data")
        with self.assertRaises(ValueError):
            list(runner.stream("exp5", {}))


if __name__ == "__main__":
    unittest.main()
