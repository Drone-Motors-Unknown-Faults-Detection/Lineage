# `experiments/health/` 與 `reports/` 內容說明

對應 issue [#21](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/21)。2026-10-03 依 main `80bdf54` 核對。

兩個目錄都是 05zhi 在 2026-09-19～20 於 `feat/knn-openset-comparison` 分支做的，2026-10-01 由 `0aa3e97` 併入 main。之後 main 沒有再改過裡面的檔案。

- `experiments/health/` 是實驗八（exp8）的 Python 套件，2026-10-03 由根目錄的 `health/` 搬進來，引入路徑改為 `experiments.health`。它把 `core.openset` 的開集分數換成 0～1 的相對健康指數，再加上嚴重度分級、`fault_type` 規則和逐 session 的趨勢告警。
- `reports/` 是同一批工作的紀錄：資料來源稽核、正式資料接入進度、專案程式碼稽核、資料能力判定，以及一組 health index 正式結果。裡面只有 `reports/exp8_health_index_results/` 是程式寫出來的，其餘都是手寫 Markdown、清單 CSV/JSON 與 PowerShell 稽核腳本。

容易搞混的兩點：

1. `reports/project_health_audit/` 的「health」指專案程式碼的健康度（測試、CI、安全），跟 `experiments/health/` 套件和馬達健康指數無關。
2. 專案裡有兩套趨勢告警。`core/trend.py` 的 `TrendMonitor` 給 exp3 和 Web 用，做「漸進 vs 突發」判別；`experiments/health/trajectory.py` 的 `SessionTrajectoryMonitor` 只給 `experiments/health_monitor.py` 用，追蹤健康指數的平滑值與斜率。兩者參數和輸入都不同，見下面第 1.3 節。

---

## 1. `experiments/health/` 套件

### 1.1 模組

`experiments/health/` 只服務實驗八。實驗八三支入口與全部相關檔案見 [experiments/README.md](experiments/README.md#各實驗的檔案位置)。

| 檔案 | 內容 | 呼叫端 |
|---|---|---|
| `experiments/health/index.py` | `CalibratedHealthIndex`：fit 時用已知類別的 train 擬合 `RobustScaler` 與 `core.openset.create_openset_detector`，再用 calibration 分數擬合 `HealthIndexCalibrator`；`predict()` 每個視窗回傳一筆 `HealthMonitoringResult` | `experiments/health_index_benchmark.py`、`experiments/health_monitor.py`、`experiments/health/trajectory.py` |
| `experiments/health/calibration.py` | `HealthIndexCalibrator`：calibration 分數第 10 百分位 → 健康 1.0，第 95 百分位（= `confidence`）→ 0.0，中間線性、兩端截斷 | `experiments/health/index.py` |
| `experiments/health/severity.py` | `RelativeSeverityPolicy`：health `>=0.8` healthy、`>=0.5` early_warning、`>=0.2` degraded，其餘 critical；`basis="relative_calibrated"` | `experiments/health/index.py` |
| `experiments/health/diagnosis.py` | `DiagnosisResolver`：開集拒絕一律 `fault_type="unknown"`；已知類別沒有版本化 taxonomy 時輸出 `"uncertain"` | `experiments/health/index.py` |
| `experiments/health/schema.py` | `HealthMonitoringResult`：輸出欄位與合法值；`to_dict(mode)` 支援 binary / health / full | 全套件 |
| `experiments/health/trajectory.py` | `SessionTrajectoryMonitor` + `TrajectoryConfig`：以 `(motor_id, session_id)` 分開保存歷史 | `experiments/health_monitor.py` |
| `experiments/health/evaluation.py` | `evaluate_open_set`（accuracy、AUROC、AUPR、unknown recall/F1）、`evaluate_trajectory`、`evaluate_event_metrics`、`assert_group_disjoint`、`assert_temporal_order` | `evaluate_open_set` 由 `health_index_benchmark` 使用；其餘只有 `tests/test_health_evaluation.py` |
| `experiments/health/config.py` | `HealthMonitorConfig` 設定 dataclass | 只有 `tests/test_health_schema.py` |
| `experiments/health/interfaces.py` | `WindowHealthPredictor`、`SessionHealthMonitor` 兩個 Protocol | 沒有呼叫端 |

`web/` 不使用 `experiments/health/`。網頁上的健康地圖與趨勢卡來自 `core/geometry.py`、`core/trend.py`。

### 1.2 資料流

```
8screws train ──► RobustScaler ──► core.openset 偵測器（Mahalanobis+LW 或 k-NN）
8screws cal   ──► 校準分數 ──► HealthIndexCalibrator（p10→1.0，p95→0.0）
新視窗 ──► openset_score ──┬─► score > 1 → is_unknown_fault / fault_type="unknown"
                           └─► health_index ──► severity_stage（相對分級）
                                    │
                                    └─► SessionTrajectoryMonitor（選用）
                                          → smoothed_health_index、trend、alarm_state、change_point_state
```

開集判定線仍是 `score > 1`，跟 `core.openset` 相同。`prediction_confidence` 是 `|score−1| / (1+|score−1|)`，表示離判定線多遠，不是校準過的機率（`experiments/health/index.py:48`）。`estimated_rul` 固定為 `None`、`rul_available=False`。

### 1.3 兩套趨勢邏輯的差別

| | `core/trend.py` `TrendMonitor` | `experiments/health/trajectory.py` `SessionTrajectoryMonitor` |
|---|---|---|
| 輸入 | 逐筆「開集分數 > 1」旗標 | 逐筆 `health_index` |
| 平滑 | EWMA `alpha=0.08` | 最近 3 筆中位數後再 EWMA `alpha=0.2` |
| 告警 | 異常比例 ≥ 0.5；中間帶 [0.2, 0.5) | smoothed < 0.5 warning、< 0.2 critical；進入與解除各需連續 3 筆，解除線 0.6 / 0.3 |
| 額外判定 | 中間帶停留 ≤ 12 筆為突發，否則漸進 | 線性斜率判 stable / worsening / recovering；單筆下降 ≥ 0.15 連 2 筆為 change point confirmed |
| 身分 | 不分馬達 | 缺 `motor_id` 或 `session_id` 時回 `data_quality="insufficient"` |
| 使用者 | `experiments/exp3_trend.py`、`web/live.py` | `experiments/health_monitor.py` |

AGENT.md「關鍵參數」表列的趨勢參數是 `TrendMonitor` 的；`SessionTrajectoryMonitor` 的預設值在 `experiments/health/trajectory.py:16` 的 `TrajectoryConfig`。

### 1.4 測試與文件

- 測試：`tests/test_health_*.py` 共 9 檔，2026-10-03 在 Python 3.10.19 跑 `venv/bin/python -m unittest discover -s tests -t .`，全部 62 個測試通過。
- 方法、正式結果、CLI：[exp8_health_monitoring_workflow.md](exp8_health_monitoring_workflow.md)。
- 各 CLI 的技術報告：[exp8_health_index_benchmark](experiments/exp8_health_index_benchmark.md)、[exp8_health_index_matrix](experiments/exp8_health_index_matrix.md)、[exp8_health_monitor](experiments/exp8_health_monitor.md)。

### 1.5 與 AGENT.md 慣例不一致的地方

這些是現況紀錄，本次沒有改程式：

- 三支 health CLI 都沒有呼叫 `core.logger.setup_run()`（鐵則 4）。`health_index_benchmark` 與 `health_monitor` 把 JSON 印到 stdout；`health_index_matrix` 預設寫到 `reports/exp8_health_index_results/`（`experiments/health_index_matrix.py:49`），不是 `output/`。
- `reports/exp8_health_index_results/aggregate_summary.json` 與 `aggregate_by_condition.csv` 沒有對應的產生程式，`experiments/aggregate_exp6.py` 只處理 exp6。
- [exp8_health_monitoring_workflow.md](exp8_health_monitoring_workflow.md) 的指令是 Windows PowerShell 寫法（`.\venv\Scripts\python.exe`）且帶 `--data-root data/formal_local`；本 repo 其他文件用 `venv/bin/python`。
- `experiments/health/config.py` 與 `experiments/health/interfaces.py` 目前只有測試或沒有使用者，是預留給未來串流 API 的介面。

---

## 2. `reports/` 目錄

### 2.1 總表

| 路徑 | 類型 | 日期 | 內容 | 現況 |
|---|---|---|---|---|
| `github_data_audit/` | 稽核紀錄（16 檔） | 2026-09-19 | 掃 Ancestor、Lineage、GPU-Learning-PyTorch、GPU-Learning-Tensorflow 四個 repo、7 個分支，找可直接給 Lineage 用的 105 維 clean features | 結案。結論是 GitHub 上找不到正式資料集 |
| `raw_data_audit/` | 稽核紀錄（19 檔） | 2026-09-19 | 盤點本機 raw 資料（`階段1/2/3.zip`，4.6 GiB）：450 個 raw CSV、T1/T3 各 30 個 clean CSV、T2 缺 `myfeature.zip`；含 `formal_source_manifest.json` 與 PowerShell 腳本 | 結案。結論落實為 `core/formal_data.py`（T2 由 raw 重建 105 維） |
| `exp6_ancestor_openset_progress.md` | 進度紀錄 | 2026-09-19～20 | P1–P10 逐階段紀錄：git 基線、資料來源、物化、可信度修正、exp6 factory、PolarMap 固定在 Mahalanobis、54-run 矩陣與跨 seed 彙整 | 結案。2026-10-03 由 `ancester_openset_exp6_progress.md` 改名，順便修正 `Ancestor` 拼字；`project_health_audit/` 等歷史稽核檔仍寫舊檔名 |
| `project_health_audit/` | 程式碼稽核（7 檔） | 2026-09-20 | 以 `44d98da` 為基準的工程稽核：`findings.csv` 21 項、`roadmap.md` R1–R10、各面向評分 | 報告結案，發現大多未處理，見 2.3 |
| `exp8_health_monitoring_data_capability.md` | 資料能力判定 | 2026-09-20 | 判定現有資料最高只到 Level A：相對健康指數、unknown 拒絕、session 內相對趨勢；不支援物理損傷比例、故障原因、RUL | 現行依據。`experiments/health/` 的輸出限制都出自這份 |
| `exp8_fault_type_data_requirements.md` | 資料規格 | 2026-09-20 | 為何螺絲配置名稱不能改名成物理故障類型；未來監督式故障分類需要的欄位（`motor_id`、`session_id`、`timestamp`、`fault_type`、`severity_stage`、`failure_endpoint`） | 現行依據 |
| `exp8_health_index_results/` | 實驗結果（16 檔） | 2026-09-20 | `health_index_matrix` 的 9 工況 × 3 seed（42/123/2026）× 2 方法 = 54 列；資料指紋 `81c91924…8228` | 現行結果，數字見 2.2 |

前三項是「把正式資料接進 Lineage」這件事的過程紀錄。資料已經由 `core/formal_data.py` 物化到 git 忽略的 `data/formal_local/`，這三份現在只用來追溯來源，不需要重跑。它們引用的 `<RAW_DATA_ROOT>`、`<LOCAL_CHECKOUT>` 是去識別化後的本機路徑，`*.ps1` 腳本要在 Windows PowerShell 下、對著原始 ZIP 目錄執行。

### 2.2 `exp8_health_index_results/` 的數字

來源 `reports/exp8_health_index_results/README.md`，每列是 9 工況 × 3 seed 的平均 ± 標準差：

| method | health gap（known − unknown） | Open Set accuracy | AUROC | unknown recall |
|---|---:|---:|---:|---:|
| Mahalanobis + Ledoit–Wolf | 0.583144 ± 0.073301 | 0.998849 ± 0.000887 | 1.000000 | 1.000000 |
| k-NN | 0.601657 ± 0.071637 | 0.998842 ± 0.000937 | 1.000000 | 1.000000 |

所有 held-out unknown 的健康指數都是 0.0。這組結果說明 unknown 與健康分得開，不說明健康指數能排出物理劣化程度。

檔案：

- `seed_{42,123,2026}/{mahalanobis,knn}.json`：每工況一列，含 provenance 與資料指紋。
- 同名 `.csv`：同一批列的精簡表。
- `matrix_manifest.json`：六格的 `run_id` 與 `status=completed`。
- `aggregate_summary.json`、`aggregate_by_condition.csv`：跨 seed 平均（產生方式見 1.5）。

### 2.3 `project_health_audit/` 的發現在 main 上的狀態

稽核基準是 `44d98da`。到 `80bdf54` 為止，git 歷史裡沒有針對這些發現的修正 commit。下面幾項在 main 上抽查過，仍然成立：

| ID | 稽核內容 | main 現況 |
|---|---|---|
| ENV-001 | `pyproject.toml` 鎖死 Python 3.10.19、依賴未鎖版 | `requires-python = "==3.10.19"`，未變 |
| TEST-001 | 沒有 CI | repo 沒有 `.github/`；測試從 28 個增加到 62 個 |
| SEC-001 | Web 對所有 origin 開放 | `web/server.py:118` `check_origin` 放行、`web/server.py:261` 監聽 `0.0.0.0` |
| ARCH-003 | `OpenSetMonitor` 未擬合就呼叫推論時沒有明確錯誤 | `core/monitor.py` 仍沒有 `_require_fitted` |

其餘 17 項沒有逐一重驗。要處理的話，從 `reports/project_health_audit/roadmap.md` 的 R1–R10 挑，先確認該項在 main 上仍成立再開 issue。

### 2.4 研究分支上的 `reports/`

`research-improvements-20260920` 分支另外有 `reports/continuous_research/`、`reports/data_independence/`、`reports/fault_type_openset/` 等 10 個子目錄，屬於 [#22](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/22) 的研究，尚未併入 main，本文件不涵蓋。

---

## 3. 之後放東西的規則

- 新的馬達健康監測邏輯放 `experiments/health/`，實驗入口放 `experiments/health_*.py`，並照 AGENT.md「實驗手冊」在 `docs/experiments/` 寫技術報告。
- 一般實驗輸出照鐵則 4 寫到 `logs/` 與 `output/`。`reports/` 只放稽核紀錄、資料規格這類人工撰寫的報告；`reports/exp8_health_index_results/` 是既有的例外。
- 新增 `reports/` 子目錄時，在 [reports/README.md](../reports/README.md) 的表加一列。
