# reports/

2026-09-19～20 在 `feat/knn-openset-comparison` 分支產生的稽核紀錄、資料規格與 health index 正式結果，2026-10-01 由 `0aa3e97` 併入 main。各項的來龍去脈與現況見 [docs/health_and_reports.md](../docs/health_and_reports.md)。

`project_health_audit/` 稽核的是專案程式碼，跟 `health/` 套件無關。

| 路徑 | 內容 | 現況 |
|---|---|---|
| [github_data_audit/](github_data_audit/README.md) | 四個 GitHub repo 的正式資料搜尋 | 結案：找不到正式資料 |
| [raw_data_audit/](raw_data_audit/README.md) | 本機 raw ZIP 盤點、驗證與資料契約對照 | 結案：已由 `core/formal_data.py` 物化 |
| [exp6_ancestor_openset_progress.md](exp6_ancestor_openset_progress.md) | 正式資料接入與 exp6 矩陣 P1–P10 進度 | 結案 |
| [project_health_audit/](project_health_audit/README.md) | 程式碼工程稽核（基準 `44d98da`）：21 項發現、R1–R10 roadmap | 報告結案，發現大多未處理 |
| [exp8_health_monitoring_data_capability.md](exp8_health_monitoring_data_capability.md) | 現有資料只支援 Level A 的判定 | 現行依據 |
| [exp8_fault_type_data_requirements.md](exp8_fault_type_data_requirements.md) | 物理故障類型分類所需的資料欄位 | 現行依據 |
| [exp8_health_index_results/](exp8_health_index_results/README.md) | `experiments/health_index_matrix.py` 的 9 工況 × 3 seed × 2 方法結果 | 現行結果 |

一般實驗輸出寫到 `logs/` 與 `output/`（AGENT.md 鐵則 4），不放這裡。新增子目錄時在上表加一列。
