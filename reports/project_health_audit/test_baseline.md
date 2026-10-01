# 測試與可執行基線

## 執行環境

- OS：Windows NT 10.0.26200.0。
- Python：`3.12.14`，執行檔位於 `albert/.venv/Scripts/python.exe`。
- GPU：`NVIDIA GeForce RTX 4070 Laptop GPU`，driver `566.07`，顯存約 8188 MiB；`nvidia-smi` 可用。
- CPU／RAM：WMI 查詢被目前權限拒絕，因此沒有臆測硬體資料。
- 主要套件：numpy 2.5.3、pandas 3.0.6、scipy 1.18.1、scikit-learn 1.9.1、hdbscan 0.8.44、loguru 0.7.3、tornado 6.5.10。
- `pytest`、`coverage`：環境中未安裝；repo 也沒有對應設定。

## 可重現命令

| Command | Exit Code | Duration | Pass | Fail | Skip | Notes |
|---|---:|---:|---:|---:|---:|---|
| `python -m unittest discover -s tests -v` | 0 | 2.056 s（測試本身 0.437 s） | 28 | 0 | 0 | 其中一個 CLI invalid-input 測試會刻意輸出 argparse error，測試仍通過 |
| `python -m compileall -q core experiments web` | 0 | 0.079 s | 1 | 0 | 0 | 語法／import compile smoke |
| `python -m pip check` | 0 | <1 s | 1 | 0 | 0 | `No broken requirements found` |
| `python -m core.formal_data --help` | 0 | 1.155 s | 1 | 0 | 0 | CLI help smoke |
| `python -m experiments.exp1_cold_start --help` | 0 | 1.476 s | 1 | 0 | 0 | CLI help smoke |
| `python -m experiments.exp2_scale_growth --help` | 0 | 1.514 s | 1 | 0 | 0 | CLI help smoke |
| `python -m experiments.exp3_trend --help` | 0 | 1.473 s | 1 | 0 | 0 | CLI help smoke |
| `python -m experiments.compare_openset --help` | 0 | 1.483 s | 1 | 0 | 0 | CLI help smoke |
| `python -m experiments.exp6_osr_benchmark --help` | 0 | 1.449 s | 1 | 0 | 0 | CLI help smoke |
| `python -m experiments.exp6_matrix --help` | 0 | 1.464 s | 1 | 0 | 0 | CLI help smoke |
| `python -m experiments.aggregate_exp6 --help` | 0 | 0.459 s | 1 | 0 | 0 | CLI help smoke |

本次未重新產生正式 54-run 結果，因為稽核邊界禁止重新產生全部正式實驗；既有 `output/exp6_formal_matrix/` 與 aggregate 只作 schema／追溯性檢查。

## 功能與測試對照（現況）

| Feature | Unit | Integration | E2E | Regression | Coverage Gap |
|---|---|---|---|---|---|
| Formal materialization／105 維 contract | 有（`test_formal_data.py`） | 部分 | 無 | 有欄位 contract | 真實 archive、9 工況完整性未在測試中重建 |
| Data discovery／pool loading | 無直接測試 | 間接（exp6 fixture） | 無 | 無 | 缺檔、缺 class、欄序／非數值欄位漂移 |
| Mahalanobis | 有 | 有（factory／fixture） | 無 | 有 singular covariance regression | 缺少正式資料跨 seed regression |
| k-NN | 有 | 有（monitor／comparison） | 無 | 有 k 大於 reference bank | 缺少大型 reference bank benchmark |
| Open Set factory | 有 | 有 | 無 | 有 default／alias regression | 介面可再加 runtime contract test |
| PolarMap | 有（兩項） | 有（method switch） | 無 | 有 health-only invariant | 缺少 Web 端到端展示測試 |
| exp1／exp2／exp3 | 無直接模組測試 | 無 | 無 | 依 README 舊輸出 | metadata、錯誤路徑、seed regression 缺口 |
| exp6 single run | 有 | 有 | 未執行正式資料 | 有 schema／metric tests | 大型資料與失敗復原邊界 |
| exp6 matrix／resume／aggregate | 有部分 | 有部分 | 未重跑 | 有 completed schema | results.csv、run.log、manifest 一致性仍可加強 |
| Web server／protocol | 無 | 無 | 無 | 無 | origin、命令驗證、錯誤回傳均未自動測試 |
| CLI | help smoke | invalid choice 一項 | 無 | 無 | Windows path／資料缺漏錯誤訊息 |

## 基線判讀

現有測試對近期正式資料與 Open Set 改動有良好保護，但測試數量集中在 `core.formal_data`、`core.openset`、PolarMap 與 exp6。沒有 CI、coverage、lint 或 type-check 設定，表示本機 28/28 通過不能推論 Web、歷史 exp1–3、資料載入器與跨平台行為已被保護。這些是測試／工程缺口，不是目前已證明的模型錯誤。

## 可重現性盤點

| 項目 | exp6 現況 | exp1–3 現況 | 稽核判讀 |
|---|---|---|---|
| seed／split | summary 有 seed；正式 contract 明確 60/20/20 | seed／split 部分存在 | 已完成的 exp6 contract 不需重做；歷史實驗需統一 schema |
| dataset fingerprint | 有 manifest 時使用 archive/file hash；54-run aggregate 指紋一致 | 沒有保存 | REPRO-001、DATA-003 |
| commit SHA | 有 | 沒有 | REPRO-001 |
| Python／package versions | 只有 Python，沒有 package lock／版本表 | 沒有 | ENV-001、REPRO-002 |
| hardware／CUDA | 沒有 | 沒有 | REPRO-002；目前硬體僅記錄於本稽核環境 |
| resolved config | 分散在 config 欄位與 top-level 欄位 | 分散且不完整 | ARCH-001、REPRO-001 |
| checkpoint | formal path 不使用 checkpoint，summary 明確為 `None` | 同樣沒有 | 不是 bug；應明確保存 `not_used` |
| run identity／resume | matrix run_id、status、summary reference 存在 | timestamp 目錄，無跨實驗 schema | EXP-002、ARCH-001 |

## 重要的「已確認」與「需驗證」界線

- 已確認：沒有 CI／coverage/lint/type-check；高風險模組沒有直接測試；exp1–3 與 exp6 的 metadata 不一致；aggregate 只信 JSON evidence。
- 需驗證：正式資料是否在所有來源副本都維持相同 bytes、跨 OS 的浮點差異大小、GPU 是否實際參與目前 pipeline。這些不在本輪宣稱為 bug。

## 效能 baseline

不重新產生正式矩陣；直接讀取既有 54-run summaries 的 27 個 Mahalanobis 與 27 個 k-NN `inference_seconds` 欄位：

| Method | n | Min (s) | Mean (s) | Max (s) | 判讀 |
|---|---:|---:|---:|---:|---|
| Mahalanobis | 27 | 0.003835 | 0.006262 | 0.008675 | 目前 formal workload 很快 |
| k-NN | 27 | 0.011378 | 0.013440 | 0.016254 | 約為 Mahalanobis 2.15 倍，但仍非整體瓶頸證據 |

資料讀取、Web reset/dataset reload 的 wall time 與記憶體目前沒有 instrumentation，因此 PERF-001/002 只列 profile 任務，不宣稱主要瓶頸。任何快取或 k-NN 向量化必須先有 baseline，並用 byte-equivalence／score regression 保證不改數值。
