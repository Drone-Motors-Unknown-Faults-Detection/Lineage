"""experiments.health_monitor：故障配置的窗口取樣（#35）與 8screws 輸出不變。"""
from functools import lru_cache
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import numpy as np

from experiments.health_monitor import run

BASE = "64cb71d84663e1745ec54db74abad68def67e8e6"  # #35 修正前的 main
CONFIGS = ["8screws", "7screws", "6screws", "5screws", "4screws", "3screws",
           "2screws", "1screws", "3_14screws", "4_146screws"]
SIZES = {"8screws": 300, "5screws": 40}  # 5screws 比健康 holdout 最大索引還少


@lru_cache(None)
def baseline_run():
    source = subprocess.check_output(["git", "show", f"{BASE}:experiments/health_monitor.py"])
    namespace = {"__name__": "experiments._baseline_health_monitor"}
    exec(compile(source, f"{BASE}/health_monitor", "exec"), namespace)
    return namespace["run"]


def write_dataset(root: Path) -> None:
    rng = np.random.default_rng(3)
    base = root / "Step-5" / "myfeature" / "T1" / "8000rpm"
    columns = ",".join(f"f{i}" for i in range(105))
    for i, config in enumerate(CONFIGS):
        folder = base / config
        folder.mkdir(parents=True)
        rows = rng.normal(size=(SIZES.get(config, 120), 105)) + i
        np.savetxt(folder / f"{config}_Group_feature_data_clean.csv", rows,
                   delimiter=",", header=columns, comments="")


class HealthMonitorWindows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        write_dataset(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def call(self, fn, config, **kwargs):
        return fn(self.root, "T1", "8000", config, seed=42, motor_id="m", session_id="s", **kwargs)

    def test_small_fault_pool_streams_whole_pool_in_order(self):
        rows = self.call(run, "5screws")
        self.assertEqual(len(rows), SIZES["5screws"])
        self.assertEqual([r["window_index"] for r in rows], list(range(SIZES["5screws"])))
        with self.assertRaises(IndexError):
            self.call(baseline_run(), "5screws")

    def test_max_windows_truncates_fault_pool(self):
        self.assertEqual(len(self.call(run, "5screws", max_windows=7)), 7)
        self.assertEqual(len(self.call(run, "7screws", max_windows=500)), 120)

    def test_healthy_output_unchanged(self):
        for kwargs in ({}, {"max_windows": 9}):
            old = self.call(baseline_run(), "8screws", **kwargs)
            new = self.call(run, "8screws", **kwargs)
            self.assertEqual(json.dumps(old, sort_keys=True), json.dumps(new, sort_keys=True))
            self.assertEqual(len(new), kwargs.get("max_windows", 60))


if __name__ == "__main__":
    unittest.main()
