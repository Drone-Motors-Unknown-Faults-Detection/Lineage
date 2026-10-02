# 實驗六矩陣：9 工況 × seed × 方法

程式：`experiments/exp6_matrix.py`。每一格呼叫 [exp6_formal_benchmark.md](exp6_formal_benchmark.md) 的 `run()`，再把該工況的一列寫進自己的目錄。它不重新定義偵測器。

問題：正式比較要能中斷後續跑，而且 54 格的指紋、commit、種子與方法要對得上，不能靠人手改檔名。

## 實驗方法

預設格子是 9 工況 × seed `(42, 123, 2026)` × `FORMAL_METHODS`（`mahalanobis`、`knn`），共 54。`run_id` 形如 `T1_8000rpm_seed42_mahalanobis`。

1. `expected_run_matrix` 先確認掃到的工況數正好是 9。方法必須落在 `FORMAL_METHODS`。
2. 寫 `matrix_manifest.json`。`data_root` 只存目錄名。JSON 用暫存檔再 `os.replace`，避免寫到一半壞掉。
3. `resume=True` 時，若該格 `summary.json` 已完成、且指紋與這次資料根一致，標 `resumed` 並跳過。
4. 否則呼叫 `experiments.exp6_formal_benchmark.run`，它仍會對九個工況都打分。矩陣只留下 `motor` 與 `rpm` 對上這一格的那一列，並把 `formal_condition_count` 改成 1。列數不是 1 就丟錯。
5. 失敗的格寫 `status=failed` 與錯誤訊息，迴圈繼續。結束時若完成數等於 54，manifest `status=completed`，否則 `incomplete`。

```bash
venv/bin/python -m experiments.exp6_matrix
venv/bin/python -m experiments.exp6_matrix --data-root data/formal_local --output-root output/exp6_formal_matrix
```

`--no-resume` 會重算已完成的格。彙總另跑 [exp6_aggregate.md](exp6_aggregate.md)，本檔不計算平均。

## 理論

每一格的統計模型和單次正式 benchmark 相同：健康 60/20/20、未知只在打分後當正類、分數 `> 1` 拒絕。矩陣多做的是實驗設計上的重複：三個 seed 讓切分不要只靠 42；兩種方法在同一批工況上成對出現，後面才能逐格相減。

`exp6_formal_benchmark.run` 每次仍走完整個資料根。某一格失敗時，其他工況的分數不會被這支矩陣存下來。續跑靠 manifest 與指紋，不靠部分列。

## 參考論文

偵測器與開集拒絕的出處同 [exp6_formal_benchmark.md](exp6_formal_benchmark.md)。種子清單、54 格、原子寫入與 resume 規則是本專案操作約定，寫在 `DEFAULT_SEEDS`、`expected_run_matrix`、`_is_complete`。

## 預期成果

資料根正好 9 個工況、且每格都能打完時，manifest 的 `expected_runs` 與 `completed_runs` 都是 54，`failed_runs` 是 0。中斷後再跑，已完成格的 `resumed` 應為真，摘要檔不被覆寫。工況數不是 9 時應在開跑前失敗，而不是寫出一份缺格的正式表。

若兩種方法的成對差距只在小數點後很多位，讀法與單次 benchmark 相同：這份特徵把健康和未知分開了，方法排名還不構成更換預設偵測器的理由。

## 已記錄的實測

`output/exp6_formal_matrix/aggregate/aggregate.md` 寫 `expected runs: 54`、`completed runs: 54`。數字表見 [exp6_formal_benchmark.md](exp6_formal_benchmark.md) 的實測節。那份 aggregate 是事後彙總，不是本程式的預期。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/exp6_matrix.py` | `expected_run_matrix`、`run_matrix`、`main` |
| `experiments/exp6_formal_benchmark.py` | 每一格的 `run`、`dataset_fingerprint`、`FORMAL_METHODS` |
| `experiments/aggregate_exp6.py` | 讀完成後的 manifest |
| `core/data.py` | `discover_datasets` |

預設輸出根 `output/exp6_formal_matrix/`：

- `matrix_manifest.json`
- `runs/{run_id}/summary.json`
- `runs/{run_id}/results.csv`
- `runs/{run_id}/run.log`

本程式不呼叫 `setup_run`，所以不會另開 `logs/exp6_matrix/`。

### 散在其他位置的相關檔案

- 測試：`tests/test_exp6_matrix.py`。
- 已提交紀錄：`output/exp6_formal_matrix/`（`matrix_manifest.json`、`runs/`、`aggregate/`）。
- 進度紀錄：[實驗六進度紀錄（已刪除，見 commit 80bdf54）](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/80bdf54fdf43d466ea19549fb7c0b4e391394799/reports/ancester_openset_exp6_progress.md) P9。
