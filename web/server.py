"""即時展示伺服器（Tornado + WebSocket）。

啟動：
    venv/bin/python -m web.server --motor T1 --rpm 8000rpm --port 8600
或使用專案根目錄的 ./run_web.sh。

伺服器本身不含實驗邏輯：以固定頻率呼叫 LiveDemo.tick()，把訊息廣播給
所有連線的瀏覽器；重擬合（確認納入、重置、換資料集）丟進執行緒池，
避免卡住串流迴圈。
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import tornado.ioloop
import tornado.web
import tornado.websocket
from loguru import logger

from core.data import discover_datasets
from core.logger import setup_run
from core.runner import add_openset_args
from web.live import LiveDemo

STATIC_DIR = Path(__file__).parent / "static"


class Hub:
    """連線集合 + 串流節拍器 + 重任務執行緒池。"""

    def __init__(
        self,
        demo: LiveDemo,
        datasets: list[dict],
        rate: int,
        seed: int,
        out_dir=None,
        detector_options: dict | None = None,
    ):
        self.demo = demo
        self.datasets = datasets
        self.seed = seed
        self.out_dir = out_dir
        self.detector_options = detector_options or {}
        self.clients: set[tornado.websocket.WebSocketHandler] = set()
        self.running = False
        self.busy = False
        self.rate = rate
        self.periodic: tornado.ioloop.PeriodicCallback | None = None
        self.executor = ThreadPoolExecutor(max_workers=1)

    # -- 廣播 ------------------------------------------------------------------

    def broadcast(self, msg: dict) -> None:
        data = json.dumps(msg, ensure_ascii=False)
        for client in list(self.clients):
            try:
                client.write_message(data)
            except Exception:
                self.clients.discard(client)

    def full_state(self) -> dict:
        state = self.demo.state()
        state.update({
            "type": "state",
            "running": self.running,
            "busy": self.busy,
            "rate": self.rate,
            "datasets": [{"motor": d["motor"], "rpm": d["rpm"]} for d in self.datasets],
        })
        return state

    def event(self, level: str, text: str) -> None:
        logger.log({"error": "ERROR", "warn": "WARNING"}.get(level, "INFO"), f"[t={self.demo.t}] {text}")
        self.broadcast({"type": "event", "level": level, "text": text, "t": self.demo.t})

    # -- 節拍 ------------------------------------------------------------------

    def tick(self) -> None:
        if not self.running or self.busy:
            return
        try:
            msgs = self.demo.tick()
        except Exception as exc:  # 展示現場永不讓伺服器死掉
            self.running = False
            self.event("error", f"串流錯誤，已暫停：{exc!r}")
            self.broadcast(self.full_state())
            return
        for msg in msgs:
            self.broadcast(msg)
        if self.demo.t % 15 == 0:
            self.broadcast(self.demo.metrics_msg())

    def set_rate(self, hz: float) -> None:
        self.rate = max(1, min(10, int(hz)))
        if self.periodic is not None:
            self.periodic.stop()
        self.periodic = tornado.ioloop.PeriodicCallback(self.tick, 1000 / self.rate)
        self.periodic.start()


HUB: Hub | None = None


class IndexHandler(tornado.web.RequestHandler):
    def get(self) -> None:
        self.set_header("Content-Type", "text/html; charset=utf-8")
        self.set_header("Cache-Control", "no-store")
        self.write((STATIC_DIR / "index.html").read_bytes())


class WSHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin: str) -> bool:  # 區網展示用
        return True

    def open(self) -> None:
        HUB.clients.add(self)
        self.write_message(json.dumps(HUB.full_state(), ensure_ascii=False))
        self.write_message(json.dumps(HUB.demo.metrics_msg(), ensure_ascii=False))

    def on_close(self) -> None:
        HUB.clients.discard(self)

    async def on_message(self, raw: str) -> None:
        try:
            msg = json.loads(raw)
            await self.dispatch(msg)
        except Exception as exc:
            HUB.event("error", f"指令失敗：{exc!r}")
            HUB.broadcast(HUB.full_state())

    async def dispatch(self, msg: dict) -> None:
        cmd = msg.get("cmd")
        if cmd == "start":
            HUB.running = True
            HUB.event("info", "▶ 串流開始")
        elif cmd == "pause":
            HUB.running = False
            HUB.event("info", "⏸ 串流暫停")
        elif cmd == "rate":
            HUB.set_rate(msg.get("value", 4))
        elif cmd == "set_source":
            for m in HUB.demo.set_source(msg["config"]):
                HUB.broadcast(m)
        elif cmd == "scenario":
            HUB.running = True
            for m in HUB.demo.start_scenario(msg["name"]):
                HUB.broadcast(m)
        elif cmd == "confirm":
            await self._heavy(self._do_confirm, "重訓練")
            return
        elif cmd == "reset":
            await self._heavy(self._do_reset, "重置")
            return
        elif cmd == "dataset":
            await self._heavy(
                lambda: self._do_dataset(msg["motor"], msg["rpm"]), "載入資料集"
            )
            return
        HUB.broadcast(HUB.full_state())

    async def _heavy(self, fn, label: str) -> None:
        if HUB.busy:
            HUB.event("warn", f"{label}略過：另一項工作進行中")
            return
        HUB.busy = True
        HUB.broadcast(HUB.full_state())
        loop = tornado.ioloop.IOLoop.current()
        t0 = time.time()
        try:
            done_text = await loop.run_in_executor(HUB.executor, fn)
            HUB.event("success", f"{done_text}（{time.time() - t0:.1f} 秒）")
        except Exception as exc:
            HUB.event("error", f"{label}失敗：{exc!r}")
        finally:
            HUB.busy = False
        HUB.broadcast(HUB.full_state())
        HUB.broadcast(HUB.demo.metrics_msg())

    # 下列三個在執行緒池中執行，回傳完成訊息文字
    @staticmethod
    def _do_confirm() -> str:
        res = HUB.demo.confirm()
        if res["action"] == "rejected_known":
            return (
                f"✋ 操作員辨識：候選叢集其實是已知類別「{res['display']}」的邊界樣本"
                f"（{res['size']} 筆——校準閾值天生會讓少量已知樣本被判未知，累積後自成一叢）"
                f"→ 已退回並清出隔離區，量尺不變"
            )
        return (
            f"✔ 操作員確認：叢集多數為「{res['display']}」（純度 {res['purity']*100:.0f}%）"
            f"→ 已納入為類別 {res['label']}，量尺擴張、監測器重新擬合完成"
        )

    @staticmethod
    def _do_reset() -> str:
        HUB.demo._build()
        HUB.running = False
        return f"↺ 已重置回階段 0（只認識健康）；session 紀錄換到 epoch {HUB.demo.epoch}"

    @staticmethod
    def _do_dataset(motor: str, rpm: str) -> str:
        for ds in HUB.datasets:
            if ds["motor"] == motor and ds["rpm"] == rpm:
                HUB.demo.close()
                HUB.demo = LiveDemo(
                    ds,
                    seed=HUB.seed,
                    out_dir=HUB.out_dir,
                    **HUB.detector_options,
                )
                HUB.running = False
                return f"已載入資料集 {motor}/{rpm}，回到階段 0"
        raise KeyError(f"{motor}/{rpm}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", default="data")
    parser.add_argument("--motor", default="T1")
    parser.add_argument("--rpm", default="8000rpm")
    parser.add_argument("--port", type=int, default=8600)
    parser.add_argument("--rate", type=int, default=4, help="每秒樣本數（1-10）")
    parser.add_argument("--seed", type=int, default=42)
    add_openset_args(parser)
    args = parser.parse_args()

    log, paths = setup_run("web_server")

    datasets = discover_datasets(args.data_root)
    if not datasets:
        raise SystemExit(f"在 {args.data_root} 找不到任何 clean 特徵資料集")
    rpm = args.rpm if args.rpm.endswith("rpm") else f"{args.rpm}rpm"
    chosen = next(
        (d for d in datasets if d["motor"] == args.motor and d["rpm"] == rpm),
        datasets[0],
    )

    global HUB
    detector_options = {
        "openset_method": args.openset_method,
        "mahalanobis_method": args.method,
        "confidence": args.confidence,
        "knn_neighbors": args.knn_neighbors,
    }
    log.info(f"載入資料集 {chosen['motor']}/{chosen['rpm']} 並擬合健康基準…")
    log.info(f"Open Set method={args.openset_method}（Mahalanobis estimator={args.method}）")
    log.info(f"session 紀錄（逐筆樣本 + 模型快照）→ {paths.output_dir}")
    HUB = Hub(
        LiveDemo(chosen, seed=args.seed, out_dir=paths.output_dir, **detector_options),
        datasets, args.rate, args.seed, out_dir=paths.output_dir,
        detector_options=detector_options,
    )

    app = tornado.web.Application([(r"/", IndexHandler), (r"/ws", WSHandler)])
    app.listen(args.port, address="0.0.0.0")
    HUB.set_rate(args.rate)
    log.info(f"就緒 → http://localhost:{args.port}  （Ctrl+C 結束）")
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        HUB.demo.close()
        log.info("伺服器結束")


if __name__ == "__main__":
    main()
