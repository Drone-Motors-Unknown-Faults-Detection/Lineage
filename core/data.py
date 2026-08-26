"""資料池載入、切分與串流抽樣。

本專案只讀取論文版（Ancestor）管線已產出的 105 維 clean 特徵檔：
    data/Step-*/myfeature/{Motor}/{RPM}/{Screws}/*_Group_feature_data_clean.csv
（clean = 逐列 IQR scale=1.5 過濾後的版本，與論文 Step 4/5 的輸入相同），
不依賴論文版程式碼。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

HEALTHY = "8screws"
FEATURE_DIM = 105

# 展示與報表排序：健康 → 鬆動由輕到重 → 複合配置
CONFIG_ORDER = [
    "8screws", "7screws", "6screws", "5screws", "4screws",
    "3screws", "2screws", "1screws", "1screw", "3_14screws", "4_146screws",
]

DISPLAY_NAMES = {
    "8screws": "Healthy（8 螺絲全鎖）",
    "7screws": "7 螺絲（最輕微鬆動）",
    "6screws": "6 螺絲（輕微鬆動）",
    "5screws": "5 螺絲（中度鬆動）",
    "4screws": "4 螺絲（明顯鬆動）",
    "3screws": "3 螺絲（嚴重鬆動）",
    "2screws": "2 螺絲（很嚴重鬆動）",
    "1screws": "1 螺絲（最嚴重鬆動）",
    "1screw": "1 螺絲（最嚴重鬆動）",
    "3_14screws": "3_14（複合不均勻鬆動）",
    "4_146screws": "4_146（複合不均勻鬆動）",
}


def config_sort_key(name: str) -> tuple[int, str]:
    try:
        return (CONFIG_ORDER.index(name), name)
    except ValueError:
        return (len(CONFIG_ORDER), name)


def display_name(config: str | None) -> str:
    if config is None:
        return "未知"
    return DISPLAY_NAMES.get(config, config)


def discover_datasets(data_root: Path | str) -> list[dict]:
    """列出可用的 (motor, rpm) 組合與其 myfeature 目錄。"""
    found: list[dict] = []
    for step_dir in sorted(Path(data_root).glob("Step-*")):
        myfeature = step_dir / "myfeature"
        if not myfeature.is_dir():
            continue
        for motor_dir in sorted(p for p in myfeature.iterdir() if p.is_dir()):
            for rpm_dir in sorted(p for p in motor_dir.iterdir() if p.is_dir()):
                if any(rpm_dir.glob("*/*_Group_feature_data_clean.csv")):
                    found.append({"motor": motor_dir.name, "rpm": rpm_dir.name, "path": rpm_dir})
    return found


def load_pools(dataset_path: Path | str) -> dict[str, np.ndarray]:
    """讀取一個 (motor, rpm) 目錄下所有螺絲配置的 clean 特徵矩陣。"""
    pools: dict[str, np.ndarray] = {}
    config_dirs = sorted(
        (p for p in Path(dataset_path).iterdir() if p.is_dir()),
        key=lambda p: config_sort_key(p.name),
    )
    for config_dir in config_dirs:
        files = sorted(config_dir.glob("*_Group_feature_data_clean.csv"))
        if not files:
            continue
        frames = [pd.read_csv(f) for f in files]
        X = pd.concat(frames, ignore_index=True).select_dtypes("number").to_numpy(dtype=float)
        X = X[np.isfinite(X).all(axis=1)]
        if X.shape[1] != FEATURE_DIM:
            raise ValueError(f"{config_dir}: 預期 {FEATURE_DIM} 維特徵，實際 {X.shape[1]}")
        if len(X):
            pools[config_dir.name] = X
    if HEALTHY not in pools:
        raise ValueError(f"{dataset_path} 缺少健康基準 {HEALTHY}")
    return pools


@dataclass(frozen=True)
class Split:
    """單一配置資料池的索引切分：train/cal 供擬合與校準，holdout 供串流與評估。"""

    train: np.ndarray
    cal: np.ndarray
    holdout: np.ndarray


def make_split(n: int, rng: np.random.Generator, ratios: tuple[float, float] = (0.6, 0.2)) -> Split:
    order = rng.permutation(n)
    n_train = int(n * ratios[0])
    n_cal = max(1, int(n * ratios[1]))
    return Split(order[:n_train], order[n_train:n_train + n_cal], order[n_train + n_cal:])


class CycleSampler:
    """在指定索引上循環抽樣；每輪重新洗牌，抽完自動續圈。"""

    def __init__(self, pool: np.ndarray, indices: np.ndarray, rng: np.random.Generator):
        if len(indices) == 0:
            raise ValueError("CycleSampler 需要至少一筆樣本")
        self.pool = pool
        self.indices = np.asarray(indices)
        self.rng = rng
        self._order: list[int] = []

    def draw(self) -> np.ndarray:
        if not self._order:
            self._order = list(self.rng.permutation(self.indices))
        return self.pool[self._order.pop()]
