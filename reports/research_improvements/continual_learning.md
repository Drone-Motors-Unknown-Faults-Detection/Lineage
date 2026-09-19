# P4 Continual Learning

# P4 Continual Learning

## Protocol

`experiments.continual_learning` 使用 P1 manifest 的 `human_confirmed_update_pool`，以 simulated source-file row order 建立 `mild→severe`、`severe→mild`、`random`、`interleaved` 四種到達順序。budgets 固定為 nested `10/25/50/100`；較大的 budget 只增加前一個 prefix，不重新挑最好樣本。immutable test 7,422 筆永不進入 update、replay 或 reference bank。

策略分成：

1. `full_historical_replay`：保留所有已到達樣本。
2. `fixed_capacity_random`：fault replay 容量 50，固定 seed 隨機保留。
3. `fixed_capacity_class_balanced`：容量 50，依 class round-robin。
4. `new_class_only`：只保留最新到達故障，作為 catastrophic-forgetting 負面 baseline。
5. `full_pool_oracle`：使用完整標記資料池，只作上限參考，不能稱為現場 continual learning。

每個 row 保存 model version、parent/rollback pointer、sample ID sidecar、replay fingerprint、calibration/reference version、update time、memory、metrics before/after 與 `future_samples_read=false`。

## Formal replay 結果

命令：

```powershell
venv\Scripts\python.exe -m experiments.continual_learning `
  --data-root data/formal_local `
  --output-root reports/research_improvements/continual_learning
```

3 seeds × 4 orders × 5 strategies × 4 budgets = 240 completed rows；結果在 `continual_learning/summary.json`，sample IDs 在 `sample_ids.json.gz`。

| strategy | binary accuracy | healthy FPR | immutable unknown recall | new-class recall | 平均 memory rows |
|---|---:|---:|---:|---:|---:|
| full historical replay | 0.6069 | 0.0031 | 0.5541 | 0.1569 | 46.2 |
| fixed-capacity random | 0.6069 | 0.0031 | 0.5541 | 0.1599 | 33.8 |
| fixed-capacity class-balanced | 0.6069 | 0.0031 | 0.5541 | 0.1451 | 33.8 |
| new-class-only | 0.6394 | 0.0034 | 0.5910 | 0.1460 | 35.0 |
| full-pool oracle | 0.3779 | 0.0000 | 0.2935 | 0.5196 | 1,872.0 |

budget 10→25→50→100 的平均 new-class recall 為 0.1605、0.2228、0.2466、0.2720；這支持「更多已確認 arrival samples 通常有幫助」，但不代表真實部署一定單調改善。oracle 使用完整資料池後新類別 recall 較高、unknown recall 反而較低，證明它是不同問題設定的上限參考，不可冒充 online learning。

## 限制與 rollback

正式 CSV 沒有真實 timestamp、operator confirmation time 或 motor/session identity，所以四種 order 都是 simulated replay。若舊類別退步超過 guardrail，本輪 runner 目前只保存 rollback pointer，尚未接 UI 自動阻擋部署；這列為 P9 工作。沒有資料支援時不計算 forgetting 的物理生命週期意義，也不產生 RUL。
