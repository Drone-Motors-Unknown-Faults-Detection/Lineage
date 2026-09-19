# Lineage 下一輪研究改進

本目錄記錄「獨立測試集、現場化持續學習、校準、Open Set 壓力測試與產品化」的可重現進度。

## 目前基線

- repository：`Drone-Motors-Unknown-Faults-Detection/Lineage`
- 起始 commit：`f21ad6ac94e66cad9c78e14bb07f7dad20d54470`
- 工作分支：`research-improvements-20260920`
- 既有正式 Open Set benchmark：9 個 motor×RPM 工況、3 seeds、Mahalanobis（Ledoit–Wolf）與 k-NN。
- 既有 baseline 測試：62/62 通過；正式 aggregate 位於 `reports/health_index_results/`。

## 研究界線

本輪不修改 raw data，不把 T1/T2/T3 串成同一顆馬達生命週期，也不把模擬 stream 宣稱為真實現場時間序列。沒有真實 run-to-failure 與人工嚴重度標註時，RUL 維持 `null`。

每個階段都必須留下測試命令、資料 fingerprint、commit SHA、push 狀態及失敗／阻塞原因。`progress.json` 是可恢復狀態的來源；`final_results.md` 只彙整已完成且可驗證的結果。

## 文件索引

- `progress.json`：階段狀態與 resume 資訊。
- `baseline.md`：開始前的程式、資料、測試與已知差異。
- `calibration.md`：threshold／事件警報比較。
- `continual_learning.md`：arrival-only、budget、replay 與 rollback。
- `score_separation.md`：三種分數的獨立性與 regression。
- `field_scenarios.md`：混合未知、工況轉移、污染、感測器異常。
- `detector_comparison.md`：依研究情境分組的公平比較。
- `product_features.md`：事件、標註、版本、品質與 stream adapter。
- `final_results.md`：只有已實際跑完的項目才能寫入結論。
