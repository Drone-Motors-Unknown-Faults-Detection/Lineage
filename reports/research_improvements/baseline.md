# P0 基線與差異

## repository 狀態

本輪從遠端 `origin/feat/knn-openset-comparison` 的 `f21ad6a` 開始，另建 `research-improvements-20260920` 分支。原始工作樹沒有未提交修改；raw data 位於 git-ignore 的 `data/formal_local`，本輪只讀取。

## 目前已有

1. `core.openset`：Mahalanobis（預設 Ledoit–Wolf）與逐類 k-NN 共用 factory。
2. `health.index`：只用已知 training/calibration 的相對健康量尺，RUL 明確不可用。
3. `health.trajectory`：以 `(motor_id, session_id)` 分離歷史、EWMA、hysteresis、change point。
4. `health.evaluation`：Open Set 與事件指標骨架；沒有 event labels 時會明確回報 unavailable。
5. 正式 9 工況×3 seeds×2 methods aggregate；Mahalanobis 的 Open Set accuracy/F1 略高，k-NN 的 health gap 略高。

## 與本任務要求的主要差異

- 尚無 immutable test manifest 與完整 leakage contract。
- threshold 目前以獨立 calibration split 的 percentile 為主，尚無 conformal、condition fallback 與事件警報比較。
- 三個分數尚未在同一個結果 schema 中完整輸出 `health_deviation_score`、`unknown_score`、`direction_familiarity`。
- 尚無 arrival-only continual-learning protocol；既有 `add_class` 是 full-pool/oracle 型流程。
- 尚無 mixed-unknown、工況 shift、污染健康初始化與 sensor anomaly 的固定 scenario manifest。
- 現有 detector benchmark 主要是 Mahalanobis/k-NN；Deep SVDD、Energy/MSP/OpenMax 需要相符的 feature/logit 與額外資料，不能以不公平設定硬湊表格。
- 新硬體微鬆動、同數量不同位置、長期退化與 run-to-failure 資料尚未取得。

## 基線測試

`venv\\Scripts\\python.exe -m unittest discover -s tests -v`：62 passed、0 failed。

## 正式 baseline（已存在）

結果見 `reports/health_index_results/aggregate_summary.json`。該檔顯示 Mahalanobis 的 Open Set accuracy `0.998849 ± 0.000887`、unknown F1 `0.999412 ± 0.000453`；k-NN 的 accuracy `0.998842 ± 0.000937`、F1 `0.999409 ± 0.000478`。兩者 AUROC 與 unknown recall 都是 1.0。這些數字不是本輪新跑出的結果，後續結果會使用新的 protocol 另行保存。
