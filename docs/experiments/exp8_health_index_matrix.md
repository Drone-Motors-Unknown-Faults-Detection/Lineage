# 實驗八矩陣：健康指數 9 工況 × seed × 方法

程式：`experiments/health_index_matrix.py`。它把 [exp8_health_index_benchmark.md](exp8_health_index_benchmark.md) 的 `run()` 跑 6 次：3 個 seed × 2 種方法。每次 `run()` 自己會走完 9 個工況，所以磁碟上是 6 個 JSON，每個 JSON 裡 9 列，合計 54 列。

## 實驗方法

預設 seed `(42, 123, 2026)`，方法 `mahalanobis` 與 `knn`。`run_id` 形如 `seed_42_mahalanobis`。

1. 開跑前檢查工況數是 9，方法必須能被 `canonical_openset_method` 認成 `SUPPORTED_OPENSET_METHODS`。
2. 輸出根預設 `reports/exp8_health_index_results`。manifest 先寫成 `running`。
3. `resume=True` 時，若 `seed_{seed}/{method}.json` 已存在、`status=completed`、列數是 9、seed 與方法相符，則跳過。
4. 否則呼叫 `health_index_benchmark.run(..., require_nine=True)`，把回傳字典寫成 JSON，並把 `rows` 寫成 CSV。
5. 完成數等於 6 則 manifest `status=completed`。有失敗格則整份 status 是 `incomplete`，行程退出碼 2。

```bash
venv/bin/python -m experiments.health_index_matrix --data-root data/formal_local --seed 42 --seed 123 --seed 2026 --method mahalanobis --method knn
```

`--no-resume` 重算已存在的 JSON。

## 理論

每一輪的健康映射與單次 benchmark 相同，錨點仍只來自該次 seed 的 `8screws` 校準分數。換 seed 會換切分，健康錨點與 critical 錨點會跟著變，所以 6 個檔的 `calibration_healthy_anchor` 不必相同。矩陣要保留的是這個變動，而不是把六次硬平均成一個錨點。

本檔不寫跨 seed 平均，也不呼叫 `aggregate_exp6`。`reports/exp8_health_index_results/aggregate_summary.json` 與 `aggregate_by_condition.csv` 是唯讀封存。新增 [exp8_health_index_aggregate](exp8_health_index_aggregate.md) 從六個 JSON 重算到新的 logs/output，逐欄比對舊檔；349 項比對中有兩個差值欄的精度順序未確證，詳見 [交付紀錄](exp8_health_index_aggregate_delivery.md)。不覆寫封存、不重跑模型。

## 參考論文

同 [exp8_health_index_benchmark.md](exp8_health_index_benchmark.md)。6 次呼叫、輸出路徑與 resume 條件是本專案操作約定，寫在 `DEFAULT_SEEDS`、`DEFAULT_METHODS` 與 `_is_complete`。

## 預期成果

`matrix_manifest.json` 的 `expected_runs` 為 6，`completed_runs` 為 6，`failed_runs` 為 0，每個 JSON 的 `rows` 長度為 9。再跑一次且不帶 `--no-resume` 時，六格都應標 `resumed: true`。工況數不是 9 時應在寫完結果之前失敗。

## 已記錄的實測

`reports/exp8_health_index_results/matrix_manifest.json` 的 `experiment` 是 `health_index_benchmark`，`status` 是 `completed`，六個 `run_id` 都在。平均表見 [exp8_health_index_benchmark.md](exp8_health_index_benchmark.md)，來源是同目錄的 `README.md`。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/health_index_matrix.py` | `expected_run_ids`、`run_matrix`、`main` |
| `experiments/health_index_benchmark.py` | 每次的 `run` 與 `FORMAL_CONDITION_COUNT` |
| `experiments/health/index.py` | 實際擬合與預測 |
| `reports/exp8_health_index_results/matrix_manifest.json` | 六格狀態 |
| `reports/exp8_health_index_results/seed_{42,123,2026}/{mahalanobis,knn}.json` | 全列與指紋 |
| `reports/exp8_health_index_results/seed_{42,123,2026}/{mahalanobis,knn}.csv` | 同一批列的表 |
| `reports/exp8_health_index_results/aggregate_summary.json` | 事後平均 |
| `reports/exp8_health_index_results/aggregate_by_condition.csv` | 逐工況平均 |
| `tests/test_health_matrix.py` | `expected_run_ids` |

沒有 `logs/health_index_matrix/`。進度印在 stdout 的一行 JSON。

### 散在其他位置的相關檔案

- 套件：`experiments/health/`，見 [health_and_reports.md](../health_and_reports.md) 第 1.1 節。
- 資料能力與限制：[exp8_health_monitoring_workflow.md](../exp8_health_monitoring_workflow.md)；原始稽核見 [health_and_reports.md](../health_and_reports.md) 第 2.2 節。
- 其他文件：[Experiments_Guide.md](../Experiments_Guide.md) 第 9 節。
- Web 實驗頁：頁首「實驗八」的 8-2 唯讀顯示本矩陣的 `reports/exp8_health_index_results/`（`web/experiments.py` 的 `_load_exp8_results`），不從網頁重跑。
