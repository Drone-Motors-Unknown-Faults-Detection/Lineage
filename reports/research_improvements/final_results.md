# Lineage 下一輪研究改進：目前可驗證結果

## 結論先講

本輪已完成 P0–P9 的可執行程式、測試與報告骨架，並在分支 `research-improvements-20260920` 逐階段推送。正式資料只讀取、不修改；P1 建立 immutable test 與 leakage contract，後續 P2–P6 都沿用同一份 split fingerprint `dff5656eeba26fdeea1c050b6b0b45162536d3f9049bae36615db8556801162d`。

在目前 formal replay 的 detector comparison 中，Mahalanobis–Ledoit–Wolf 是健康 FPR 與 unknown recall 平衡最實用的已完成方法：healthy FPR `0.0023`、unknown recall `0.5910`、AUROC `0.7859`、AUPR `0.9680`。Isolation Forest 的 AUROC/AUPR 較高，但 threshold alarm 幾乎不觸發（unknown recall `0.0572`），所以不能只用 ranking metric 選它。這些是離線 formal replay，不是現場保證。

## 各階段狀態

| 階段 | 已完成內容 | 驗證結果 | 邊界／限制 |
|---|---|---|---|
| P0 | 基線、README、progress 與研究範圍 | baseline 62 tests passed | formal data metadata 不含可靠 motor/session/time |
| P1 | source-file conservative split、immutable test、sample fingerprints | 30 source files；immutable test 7,422 samples；無 file-group overlap | 沒有 trusted session/timestamp，只能做保守分組 |
| P2 | independent percentile、conformal、condition fallback、event policy、ablation | 45 rows；LW independent q=.95 unknown recall `0.617260`、FPR `0.002257` | event 指標是 replay；沒有真實事件邊界 |
| P3 | health deviation、unknown、direction familiarity 分離 | health deviation 前後 max abs change `0.0`；unknown score 下降 | 新類別更新是 simulated arrival |
| P4 | arrival-only continual learning、4 nested budgets、4 orders、5 strategies | 240 rows；budget 10/25/50/100；test 不進 replay/reference | 沒有真實到達時間與人工確認時間 |
| P5 | mixed unknown、HDBSCAN、condition shift、contamination、sensor anomaly、transient/persistent | 6 scenarios completed | cluster ground truth 與現場 sensor stream 尚未有 |
| P6 | 公平 detector comparison | 30 rows；18 completed、12 blocked/not-applicable | Deep SVDD 缺 neural runtime/policy；MSP/Energy/OpenMax 缺 logits |
| P7 | 現場資料 metadata validator、duplicate gate、candidate manifest | 2 unit tests；不把 candidate 混進 formal | 尚未取得真實硬體資料 |
| P8 | per-motor longitudinal schema、T1/T2/T3 不拼接、RUL endpoint gate | 2 unit tests；無 failure endpoint 時拒絕 estimated RUL | 沒有 run-to-failure trajectory |
| P9 | FaultEvent、HumanAnnotation、ModelVersion、RollbackGuard、ExperimentReport、stream adapter | 4 unit tests；全套 92 tests passed | UI、設備 socket、registry 與 latency/throughput 尚未接線 |

## 主要正式數字

- Calibration：legacy self-threshold 會造成 healthy FPR `1.0`，不能作正式部署 threshold；獨立 calibration 後才有可解釋的 FPR。LW 相對 legacy 在同一 independent q=.95 設定下 AUROC 約 `+0.0826`、unknown recall 約 `+0.338`，但 healthy FPR 由 `0` 變為約 `0.00226`。
- Continual learning：full historical replay binary accuracy `0.6069`、immutable unknown recall `0.5541`；new-class-only 的 unknown recall `0.5910`，但這是 forgetting trade-off，不是推薦直接部署的策略。budget 10→25→50→100 的 new-class recall 平均為 `0.1605/0.2228/0.2466/0.2720`。
- Field scenarios：mixed unknown（3 screws + 4 screws）在選定 200 筆 replay 上 HDBSCAN purity/ARI/NMI 都為 `1.0`；這只代表該 replay，不代表未知故障普遍可完美分群。single spike 使用 consecutive=2 可把 false event 從 `1` 降到 `0`，persistent event recall 為 `1.0`。

## 尚不能宣稱的內容

目前不能宣稱真實現場 false alarms/hour、early-warning lead time、longitudinal degradation rate、故障嚴重度或 RUL；原因是 formal data 沒有可靠時間軸、同一馬達的長期 run-to-failure、確認故障 endpoint 與人工 severity label。P7 protocol 已指定安全停機、固定防護測試台、checksum、operator、maintenance 與 sensor quality 欄位，待新資料取得後再開新的 protocol fingerprint。

## 可重現入口

- 全測試：`venv\\Scripts\\python.exe -m unittest discover -s tests -v` → **92 passed, 0 failed**。
- 編譯檢查：`venv\\Scripts\\python.exe -m compileall -q core experiments health web`。
- 狀態來源：`progress.json`；結果檔分別位於 `calibration_ablation/`、`score_separation/`、`continual_learning/`、`field_scenarios/`、`detector_comparison/`。
- 正式推送分支：`research-improvements-20260920`。
