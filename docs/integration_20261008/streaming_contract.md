# 串流部分抽取：評估前契約

來源為 JW-Albert 的 `544d4ed8c6516622e2f46c095351f9483a61635c`、PR #36，保留 Claude Opus 5.5 原 co-author。只抽取 exp1／exp3／exp4 iter_run、SSE 編排、實驗頁背景小窗與畫面；不改 health_monitor，不註冊 exp8_monitor 串流，不關閉 #35／#36。

run 的數學計算、train/cal/holdout 與參數沿用 main 與現有實驗手冊。本輪新增的迭代與 frame 切塊為 UI 操作約定，沒有新模型。原文獻見 exp1、exp3、exp4 手冊；手冊先補寫串流範圍再適配程式。

驗收事前固定：

- fixture 比較 source MAIN_BEFORE 的原 run、抽取後 run 及 iter_run 最終結果；真實 T1/8000rpm、seed42、Maha-LW／k-NN 做配對。不能只比較兩個新入口而略過原主線。
- 健康 train/cal 仍唯一擬合來源。原 PolarMap 三子實驗與 factory 原參數不變。
- SSE start、done、error 可解析，done 保存結果；不支援的實驗拒絕。batch/SSE 互斥，完成／中斷／例外後釋放鎖。
- 健康監測原 API 與已知 bug 保留，不宣稱修復。串流控制列表不得含 exp8_monitor。
- 真實瀏覽器點擊實驗頁背景小窗、串流與停止；JS 語法檢查不是 UI 驗收。
- 相同來源輸出若不同、SSE 不能釋放鎖或舊頁失效，該部分不合 main；不調方法讓結果對齊。

影響路徑：既有 `experiments/exp1_cold_start.py`、`exp3_trend.py`、`exp4_polar_map.py`；`web/experiments.py`、`server.py`、`static/index.html`、`static/experiments.js`；三份現有手冊；新增 `tests/test_stream_integration.py`。結果納入 `output/branch_integration` 與整合報告，CLI/main/logger 不變。
