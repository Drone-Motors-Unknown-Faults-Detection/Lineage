# 實驗13執行紀錄

所有新增敘述採繁體中文。日期2026-10-03，Asia/Taipei。

| 階段 | 實際指令與結果 | 提交／推送 |
|---|---|---|
| P0 | 讀最新 main AGENT.md、本機規範、歷史來源帳冊與最新 Q／solver；282個無關 tracked deletions保留；exp13未使用 | `a83e4f8f62f6d45b505931a270b0b2447c6b215d`；remote核對一致 |
| P1 | 新公式14項測試；第一次空矩陣測試失敗，修正後14通過。synthetic smoke僅工程測試 | `1d1fd9cba6eacfab4046e51122dcbfc0f9865d1d`；remote核對一致 |
| 環境 | `.venv310/Scripts/python.exe -m experiments.fault_type_continuous_acceptance`；Python3.10.19，410通過，pip check與既有37 CLI通過。`venv/Scripts/python.exe`同指令：Python3.14.6亦410通過；兩個新增CLI各於兩環境 --help通過 | 環境證據位於下列output；加入7項來源測試後仍需最後完整回歸 |
| lock | `python -m experiments.fault_type_metric_classification lock --solver-protocol output/fault_type_solver_lock/2026-10-02-23-46-28/protocol.json --diagnosis output/fault_type_solver_fit/2026-10-02-23-51-52/diagnosis.json` | protocol先推送才 fit |
| fit | 同模組 `fit --protocol output/fault_type_metric_classification_lock/2026-10-03-09-42-02/protocol.json --data-root data/formal_local`；九份模型封存 | fit lock待本階段提交；未執行 outer |
| 來源核對 | 新 verifier 的7項人工污染測試，兩環境各7通過；正式九模型正在重建；不變更方法或參數 | 狀態依後續行更新 |

協定 SHA：`9ca9be082013349680b642e509be761d84ca150a947429251bd1c50f86ed1a8b`。fit 路徑 `output/fault_type_metric_classification_fit/2026-10-03-09-43-55/locked_study.json`。環境 output 路徑 `output/fault_type_continuous_acceptance_py3_10_19/2026-10-03-09-41-18`、`output/fault_type_continuous_acceptance_py3_14_6/2026-10-03-09-41-36`。新 verifier 路徑 `output/fault_type_metric_source_verification/2026-10-03-09-48-46`。

已確認基線不改，尚未取得本批正式 accuracy；不把收斂或測試通過算成可靠提升。raw來源 UNKNOWN、fresh unavailable，但不阻擋現有資料比較。

## 09:54接續檢查點

九份模型從原 manifest 的 known train／calibration 數值重建，全部精確相符；四種分類器陣列、三種原型、四個 factory detector 與 energy reference 均逐份核對。來源校驗 SHA：`5611f1e6ab41451a7c9c38090a597a01efe76c242ca53e00dc8566f5a0eaf673`。此 verifier 未讀取 test 特徵，不能因此宣稱採集獨立性或 fresh test 已成立。

新增7項來源污染測試後，Python3.10.19完整測試417項通過（169.047秒），Python3.14.6亦417項通過（171.419秒）。最終CLI環境摘要仍在產生；先前已完成的410項環境摘要保留。新摘要路徑為 `output/fault_type_continuous_acceptance_py3_10_19/2026-10-03-09-50-03` 與 `output/fault_type_continuous_acceptance_py3_14_6/2026-10-03-09-50-16`。

本階段封存 fit lock、來源核對程式／測試／手冊及來源摘要後，才執行：

```powershell
.venv310/Scripts/python.exe -m experiments.fault_type_metric_classification evaluate --protocol output/fault_type_metric_classification_lock/2026-10-03-09-42-02/protocol.json --lock output/fault_type_metric_classification_fit/2026-10-03-09-43-55/locked_study.json --data-root data/formal_local
```

待辦：108格正式配對、逐樣本重算、固定門檻判定、完整分母的 final fault F1、D槽備份、後續 LFDA 文獻與有界協定。九份 joblib 與大型 audit 不加入Git；以後續 archive 索引交付。既有282個無關刪除不納入提交。
