"""Web 即時展示的協調器（LiveDemo）。

把三個實驗模組串成可互動的即時串流——本模組只做編排與訊息組裝，
實驗邏輯全部住在 experiments / core：
    實驗一（冷啟動監測）  → ScaleGrowthSession 內的 OpenSetMonitor 階段 0
    實驗二（量尺擴張）    → ScaleGrowthSession（隔離、分群、確認、擴張）
    實驗三（變化點判別）  → TrendMonitor + exp3 的 SCENARIOS 劇本定義
"""

from __future__ import annotations

import numpy as np

from core.data import (
    HEALTHY,
    CycleSampler,
    config_sort_key,
    display_name,
    load_pools,
)
from core.trend import TrendMonitor
from experiments.exp2_scale_growth import ScaleGrowthSession
from experiments.exp3_trend import KIND_DISPLAY, SCENARIOS


def _event(level: str, text: str, t: int) -> dict:
    return {"type": "event", "level": level, "text": text, "t": t}


class LiveDemo:
    def __init__(self, dataset: dict, seed: int = 42):
        self.meta = {"motor": dataset["motor"], "rpm": dataset["rpm"]}
        self.pools = load_pools(dataset["path"])
        self.seed = seed
        self._build()

    def _build(self) -> None:
        self.session = ScaleGrowthSession(self.pools, seed=self.seed)
        self.trend = TrendMonitor()
        self.stream_rng = np.random.default_rng(self.seed + 1)
        self.t = 0
        self.source = HEALTHY
        self.scenario: dict | None = None
        self.switch_t = 0
        self.fault_onset_t: int | None = None
        self.metrics = {c: {"streamed": 0, "flagged": 0} for c in self.pools}
        self.alarms: list[dict] = []
        self.samplers: dict[str, CycleSampler] = {}
        self._refresh_samplers()

    def _refresh_samplers(self) -> None:
        """已知配置只從 holdout 抽（未參與擬合），未知配置從整池抽。"""
        mon = self.session.monitor
        for config, pool in self.pools.items():
            if config in mon.known:
                idx = mon.splits[config].holdout
            else:
                idx = np.arange(len(pool))
            self.samplers[config] = CycleSampler(pool, idx, self.stream_rng)

    # -- 控制 ------------------------------------------------------------------

    def set_source(self, config: str) -> list[dict]:
        if config not in self.pools:
            raise KeyError(config)
        self.scenario = None
        self.source = config
        self.switch_t = self.t
        self.fault_onset_t = self.t if config != HEALTHY else None
        self.trend.rearm()
        return [_event("info", f"注入來源切換 → {display_name(config)}", self.t)]

    def start_scenario(self, key: str) -> list[dict]:
        scen = SCENARIOS[key]
        self.scenario = {"key": key, "phases": scen["phases"], "idx": 0,
                         "left": scen["phases"][0][2]}
        self.source = HEALTHY
        self.switch_t = self.t
        self.fault_onset_t = self.t + scen["phases"][0][2]
        self.trend.rearm()
        return [_event("info", f"▶ 啟動{scen['name']}（先回到健康基線）", self.t)]

    def confirm(self) -> dict:
        """操作員確認候選 → 量尺擴張（重擬合；由伺服器丟進執行緒池跑）。"""
        result = self.session.confirm()
        self._refresh_samplers()
        self.trend.rearm()
        self.switch_t = self.t
        return result

    # -- 串流 ------------------------------------------------------------------

    def _draw_config(self) -> tuple[str, list[dict]]:
        msgs: list[dict] = []
        if self.scenario is None:
            return self.source, msgs
        sc = self.scenario
        config, ratio, _ticks = sc["phases"][sc["idx"]]
        pick = config if (config != HEALTHY and self.stream_rng.random() < ratio) else HEALTHY
        sc["left"] -= 1
        if sc["left"] <= 0:
            if sc["idx"] + 1 < len(sc["phases"]):
                sc["idx"] += 1
                nxt = sc["phases"][sc["idx"]]
                sc["left"] = nxt[2]
                msgs.append(_event(
                    "info",
                    f"劇本進入下一階段：{display_name(nxt[0])}（混入比例 {int(nxt[1]*100)}%）",
                    self.t,
                ))
            else:
                sc["left"] = 10 ** 9
                msgs.append(_event("info", "劇本播畢，維持最後狀態", self.t))
        return pick, msgs

    def tick(self) -> list[dict]:
        config, msgs = self._draw_config()
        x = self.samplers[config].draw()
        r = self.session.process(x, config)
        tr = self.trend.update(r["score"])
        self.t += 1
        self.metrics[config]["streamed"] += 1
        if r["label"] is None:
            self.metrics[config]["flagged"] += 1

        if r["label"] is None:
            verdict = "unknown"
        elif r["label"] == HEALTHY:
            verdict = "healthy"
        else:
            verdict = "known"
        xy = self.session.monitor.project(x)[0]

        out = [{
            "type": "sample",
            "t": self.t,
            "score": round(float(r["score"]), 3),
            "verdict": verdict,
            "cls": display_name(r["label"]),
            "truth": config,
            "truth_display": display_name(config),
            "pca": [round(float(xy[0]), 3), round(float(xy[1]), 3)],
            "ewma": tr["ewma"],
            "cusum": tr["cusum"],
            "health": round(min(1.0, 1.0 / max(r["score"], 1e-9)) * 100, 1),
            "quarantine": r["quarantine"],
            "phase": self.phase(),
        }] + msgs

        if tr["alarm_now"]:
            latency = None if self.fault_onset_t is None else self.t - self.fault_onset_t
            self.alarms.append({
                "t": self.t, "source": config, "kind": tr["kind"],
                "kind_display": KIND_DISPLAY.get(tr["kind"], tr["kind"]),
                "transition": tr["transition"], "latency": latency,
            })
            extra = "" if latency is None else f"，自故障注入起 {latency} 筆"
            out.append(_event(
                "warn",
                f"⚠ 變化點警報：判別為「{KIND_DISPLAY.get(tr['kind'])}」"
                f"（中間帶停留 {tr['transition']} 筆{extra}）",
                self.t,
            ))
        if r["candidate_new"]:
            c = self.session.candidate
            out.append(_event(
                "warn",
                f"◎ HDBSCAN 在隔離區發現穩定叢集（{c['size']} 筆、純度 {c['purity']*100:.0f}%）"
                f"→ 產生候選新故障，等待操作員確認",
                self.t,
            ))
            out.append(self.state_msg())
        return out

    # -- 狀態 ------------------------------------------------------------------

    def phase(self) -> str:
        if self.session.candidate is not None:
            return "pending"
        if len(self.session.quarantine_X) > 0:
            return "accumulating"
        return "monitoring"

    def state(self) -> dict:
        mon = self.session.monitor
        return {
            "meta": self.meta,
            "t": self.t,
            "phase": self.phase(),
            "source": self.source,
            "scenario": None if self.scenario is None else {
                "key": self.scenario["key"],
                "name": SCENARIOS[self.scenario["key"]]["name"],
            },
            "known": [
                {"config": c, "display": display_name(c), "label": l}
                for c, l in mon.known.items()
            ],
            "configs": [
                {"config": c, "display": display_name(c), "n": int(len(p)),
                 "known": c in mon.known}
                for c, p in sorted(self.pools.items(), key=lambda kv: config_sort_key(kv[0]))
            ],
            "quarantine": len(self.session.quarantine_X),
            "min_cluster_size": self.session.min_cluster_size,
            "candidate": None if self.session.candidate is None else {
                k: v for k, v in self.session.candidate.items() if k != "indices"
            },
            "centroids": [
                {"config": c, "display": display_name(c),
                 "x": round(xy[0], 3), "y": round(xy[1], 3)}
                for c, xy in mon.centroids.items()
            ],
        }

    def state_msg(self) -> dict:
        return {"type": "state_patch", **self.state()}

    def metrics_msg(self) -> dict:
        rows = [
            {"config": c, "display": display_name(c),
             "streamed": m["streamed"], "flagged": m["flagged"],
             "rate": round(m["flagged"] / m["streamed"] * 100, 1)}
            for c, m in sorted(self.metrics.items(), key=lambda kv: config_sort_key(kv[0]))
            if m["streamed"] > 0
        ]
        return {"type": "metrics", "rows": rows, "alarms": self.alarms[-5:]}
