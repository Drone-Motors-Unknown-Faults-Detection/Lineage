# 實驗八串流：健康監測逐窗輸出

程式：`experiments/health_monitor.py`。它對一個工況擬合 `CalibratedHealthIndex`，再用 `SessionTrajectoryMonitor` 把 holdout 窗口一筆一筆送進去，把每筆結果印成一行 JSON。

它不寫 `reports/exp8_health_index_results/`。那裡的 54 列是 [exp8_health_index_matrix.md](exp8_health_index_matrix.md) 的批次評估。本程式看的是同一套指數在一條序列上的平滑、斜率與告警。

## 實驗方法

1. `--data-root` 預設 `data/formal_local`。`--motor`、`--rpm` 必填。轉速可以寫 `8000` 或 `8000rpm`，程式會補上 `rpm`。`discover_datasets` 必須正好找到一組。
2. `--config` 預設 `8screws`。擬合永遠只用該工況的 `8screws` train/calibration，與 `--config` 無關。`--config` 決定送進監測器的 holdout 來自哪一個池。
3. 預設 `--openset-method mahalanobis`、`--method ledoit_wolf`、`--knn-neighbors 5`、`--seed 42`。
4. `SessionTrajectoryMonitor.update` 需要 `motor_id` 與 `session_id` 才會把歷史接在同一條序列上。沒給又沒有 `--allow-no-identity` 時，`require_identity=True`，趨勢維持資料不足，不把不同馬達串在一起。
5. `--max-windows` 只截 holdout 的前段，省略則全送。`--output-mode` 為 `binary`、`health` 或 `full`（預設）。

```bash
venv/bin/python -m experiments.health_monitor --data-root data/formal_local --motor T1 --rpm 8000rpm --config 1screws --openset-method mahalanobis --output-mode full --motor-id motor-001 --session-id session-001 --max-windows 20
venv/bin/python -m experiments.health_monitor --data-root data/formal_local --motor T1 --rpm 8000rpm --config 8screws --output-mode binary --allow-no-identity --max-windows 5
```

`full` 印 `HealthMonitoringResult.to_dict("full")` 再加 `window_index`。`health` 只留故障旗標、健康指數、劣化分數、stage、趨勢、告警與變點。`binary` 只留 `is_fault`。

## 理論

單窗健康指數的定義同 [exp8_health_index_benchmark.md](exp8_health_index_benchmark.md)。時間部分在 `experiments/health/trajectory.py`。

狀態鍵是 `(motor_id, session_id)`。平滑先取最近值的 rolling median，再做 EWMA，`α = 0.2`。歷史少於 `min_history = 5` 時，趨勢是 `insufficient_history`，斜率不做。滿 5 筆之後用線性斜率：絕對斜率小於 `stable_slope = 0.005` 視為持平，負斜率是變差，正斜率是回升。

告警進入與解除都要連續 3 筆。warning 進入線 0.5、解除線 0.6；critical 進入線 0.2、解除線 0.3。解除線高於進入線，避免在門檻上來回跳。健康值相對近期下降超過 0.15，一筆記 `change_point_state=candidate`，連續兩筆記 `confirmed`。

時間戳在這支 CLI 裡固定傳 `None`。沒有真實時間軸時，延遲與每小時誤報不要從這些行計算。`estimated_rul` 維持 null。

## 參考論文

- 健康指數的馬氏距離、Ledoit–Wolf、k 近鄰出處同 [exp1_cold_start.md](exp1_cold_start.md)。
- S. W. Roberts (1959), “Control Chart Tests Based on Geometric Moving Averages,” *Technometrics*, 1(3), 239–250。DOI [10.1080/00401706.1959.10489860](https://doi.org/10.1080/00401706.1959.10489860)。這裡的 `α` 是 0.2，和實驗三 `TrendMonitor` 的 0.08 不是同一個物件。
- rolling median、5 筆才算斜率、3 筆持續、0.15 的變點：本專案操作約定，寫在 `TrajectoryConfig`。

## 預期成果

`--config 8screws` 且給了身份時，多數窗口的 `health_index` 應高、`is_fault` 應少，趨勢在前 4 筆是歷史不足，第 5 筆之後才有斜率標籤。`--config` 換成故障配置時，健康指數應下降，`is_unknown_fault` 應為真；若校準錨點把這些分數都送到 0，連續窗口的斜率會是持平的 0，不會出現一段慢慢下降的曲線。

沒有 `motor_id` / `session_id` 又未允許缺身份時，不應把多筆合成一條惡化曲線。`binary` 模式不應冒出健康指數欄位。

## 已記錄的實測

本 CLI 沒有進版的逐窗 JSONL。批次分離度見 `reports/exp8_health_index_results/`，說明見 [exp8_health_index_benchmark.md](exp8_health_index_benchmark.md)。那份結果裡的 unknown 健康指數飽和在 0.0，所以用故障配置來播這支程式時，預期會看到貼底的指數，而不是一條分級下降的軌跡。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/health_monitor.py` | `run`、`iter_run`、`main`、三種 `output-mode`；`run` 收集 `iter_run` 的 `window` 事件（2026-10-03 起）。已知問題：故障配置用健康池的 holdout 索引取樣，樣本數較少的配置會 `IndexError`（例如 T1/8000rpm 的 5screws），見 [#35](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/35) |
| `experiments/health/index.py` | `CalibratedHealthIndex` |
| `experiments/health/trajectory.py` | `SessionTrajectoryMonitor`、`TrajectoryConfig` |
| `experiments/health/schema.py` | `HealthMonitoringResult.to_dict` |
| `experiments/health/severity.py` | stage 門檻 |
| `core/data.py` | `discover_datasets`、`load_pools`、`make_split`、`HEALTHY` |

沒有 `logs/health_monitor/` 或 `output/health_monitor/`。結果是 stdout 的 JSON 行。要留檔時由呼叫端導向。

### 散在其他位置的相關檔案

- 測試：`tests/test_health_trajectory.py`、`tests/test_health_schema.py`；CLI 本身沒有測試。
- 套件：`experiments/health/`，見 [health_and_reports.md](../health_and_reports.md) 第 1.1 節。
- 資料能力與限制：[exp8_health_monitoring_workflow.md](../exp8_health_monitoring_workflow.md)；原始稽核見 [health_and_reports.md](../health_and_reports.md) 第 2.2 節。
- 其他文件：[Experiments_Guide.md](../Experiments_Guide.md) 第 9 節。
- Web 實驗頁：頁首「實驗八」的 8-3，`web/experiments.py` 的 `CATALOG` 項目 `exp8_monitor` 呼叫本程式的 `run()`，畫面在 `web/static/experiments.js` 的 `RENDER.exp8_monitor`；結果存到 `output/web_server/{ts}/experiments/exp8_monitor_{時間}.json`。
- 邊跑邊畫：頁面上的「⏵ 邊跑邊畫」改走 `iter_run()`，經 `web/experiments.py` 的 `ExperimentRunner.stream()` 與 `web/server.py` 的 `StreamHandler`（Server-Sent Events，`GET /api/experiments/{id}/stream`）逐步推送，速度 20／80／400 筆/秒可選。`iter_run()` 只多吐出中間事件，計算與 `run()` 相同；`tests/test_iter_run.py` 比對兩者輸出。逐窗畫出健康度、平滑值與告警。
