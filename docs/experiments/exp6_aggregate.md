# 實驗六彙總：exp6 矩陣彙總

程式：`experiments/aggregate_exp6.py`。它不打分、不重新切資料。它讀已經完成的 `matrix_manifest.json`，把每一格的 `summary.json` 收成平均、標準差與成對差。

問題：54 格都在不同檔案裡時，怎樣加總才不會在缺格的時候仍印出一個看起來完整的平均。

## 實驗方法

1. `--manifest` 預設 `output/exp6_formal_matrix/matrix_manifest.json`。`--output-root` 省略時，寫到 manifest 旁邊的 `aggregate/`。
2. `load_matrix()` 要求 manifest 的 `status` 是 `completed`，`runs` 的長度等於 `expected_runs`，而且每一格的 `status` 都是 `completed`。每一格要有相對路徑欄位 `summary`，指向的 `summary.json` 必須存在，方法、seed 與資料指紋也必須和 manifest 一致。
3. 從每格 summary 取出唯一的一列。列裡的 `method`、`seed`、`motor`、`rpm` 必須和 manifest 一致，否則丟錯。
4. 對 `METRICS` 裡每個欄位算平均與樣本標準差（`ddof=1`）。欄位是 `known_accuracy`、`open_set_accuracy`、`auroc`、`aupr_unknown_positive`、`fpr_at_tpr95`、`unknown_precision`、`unknown_recall`、`unknown_f1`。非有限值直接失敗。
5. 若方法集合正好是 Mahalanobis 與 k-NN，再依 `(motor, rpm, seed)` 內連接，計算 k-NN 減 Mahalanobis。對不上就丟「not paired」，不補列。

```bash
venv/bin/python -m experiments.aggregate_exp6
venv/bin/python -m experiments.aggregate_exp6 --manifest output/exp6_formal_matrix/matrix_manifest.json
```

## 理論

平均與標準差描述的是這 9 個工況、這 3 個 seed 上的重複，不是新的檢測模型。成對差把同一格的兩種方法相減，避免拿不同工況的邊際平均來比。缺一格仍做平均，會把沒跑的工況悄悄排除；這支程式選擇失敗，讓缺漏留在 manifest 的 `incomplete`。

## 參考論文

沒有另加統計論文。樣本標準差用 pandas `std(ddof=1)` 是本專案操作約定。指標定義沿用 [exp6_formal_benchmark.md](exp6_formal_benchmark.md)。

## 預期成果

54 格都完成時，應寫出四個檔，`macro_summary` 每種方法一列，`paired_differences` 每個指標一列，`n_pairs` 為 27（9 工況 × 3 seed）。manifest 仍是 `running` 或 `incomplete` 時，程式應停，不產生一份部分平均。

## 已記錄的實測

現有檔在 `output/exp6_formal_matrix/aggregate/`。`aggregate.md` 的表已抄到 [exp6_formal_benchmark.md](exp6_formal_benchmark.md)。成對差的正號表示 k-NN 較高。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/aggregate_exp6.py` | `aggregate`、`write_aggregate`、`main` |
| `experiments/exp6_matrix.py` | 產出被讀的 `matrix_manifest.json` 與 `runs/*/summary.json` |
| `output/exp6_formal_matrix/aggregate/aggregate.json` | 完整彙總 |
| `output/exp6_formal_matrix/aggregate/aggregate.md` | 人讀的表 |
| `output/exp6_formal_matrix/aggregate/macro_summary.csv` | 方法平均 |
| `output/exp6_formal_matrix/aggregate/condition_summary.csv` | 逐工況 |
| `output/exp6_formal_matrix/aggregate/paired_differences.csv` | k-NN 減 Mahalanobis |

沒有 `logs/aggregate_exp6/`。錯誤用例外訊息退出。

### 散在其他位置的相關檔案

- 測試：`tests/test_aggregate_exp6.py`。
- 已提交紀錄：`output/exp6_formal_matrix/aggregate/`。
- 進度紀錄：`reports/exp6_ancestor_openset_progress.md` P10。
