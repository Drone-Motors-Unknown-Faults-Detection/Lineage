# 實驗七：單工況 Open Set 對照

程式：`experiments/compare_openset.py`。在一個工況、同一組健康切分上，把 `core.openset` 允許的方法各跑一次。

它和 [exp6_formal_benchmark.md](exp6_formal_benchmark.md) 用同一套工廠與同一條 `score > 1` 規則。差別是這裡只跑 CLI 指定的那一個資料集，輸出走 `setup_run("openset_comparison")`，不寫 54 格矩陣，也不算健康指數。

## 實驗方法

1. `resolve_dataset` 載入 `--motor` / `--rpm` 的 `pools`。
2. `--openset-methods` 預設是 `SUPPORTED_OPENSET_METHODS`，也就是 `mahalanobis` 與 `knn` 都跑。可以只留一個。
3. 每個方法各自建一個 `OpenSetMonitor` 並 `fit_initial()`。預設 `--confidence 0.95`、`--method ledoit_wolf`、`--knn-neighbors 5`、`--seed 42`。`--method` 還可以選 `legacy`、`oas`、`mcd`，只影響 Mahalanobis 的共變異數估計。
4. 健康分數只用 holdout。未知配置逐一打分，再拼成正類。未知不進擬合。
5. `evaluate_method` 計算 AUROC、未知為正類的 AUPR、ROC 上的 FPR@TPR95、open-set accuracy、未知 precision / recall / F1，以及健康誤報率。`details` 另給每個未知配置的 recall 與分數中位數。

```bash
venv/bin/python -m experiments.compare_openset --motor T1 --rpm 8000rpm
venv/bin/python -m experiments.compare_openset --motor T1 --rpm 8000rpm --openset-methods mahalanobis knn
```

## 理論

同一工況、同一 seed 的兩次 `fit_initial` 用同一組索引，所以訓練、校準、holdout 的列號一致。方法差只來自分數怎麼算：橢球距離，或到訓練集 k 近鄰的平均距離。共變異數若改成 `oas` 或 `mcd`，比的就不再是主線預設的 Ledoit–Wolf，讀圖時要看 summary 裡的 `method` 欄。

`legacy` 在這支 CLI 沒有被擋下。正式矩陣會拒絕它。單工況對照若要和 `output/exp6_formal_matrix/` 並排，應維持 `ledoit_wolf`。

## 參考論文

- 馬氏距離、Ledoit–Wolf、k 近鄰出處同 [exp1_cold_start.md](exp1_cold_start.md)。
- Y. Chen, A. Wiesel, Y. C. Eldar, and A. O. Hero (2010), “Shrinkage Algorithms for MMSE Covariance Estimation,” *IEEE Transactions on Signal Processing*, 58(10), 5016–5029。DOI [10.1109/TSP.2010.2053029](https://doi.org/10.1109/TSP.2010.2053029)。對應 `--method oas`。
- P. J. Rousseeuw and K. Van Driessen (1999), “A Fast Algorithm for the Minimum Covariance Determinant Estimator,” *Technometrics*, 41(3), 212–223。DOI [10.1080/00401706.1999.10485670](https://doi.org/10.1080/00401706.1999.10485670)。對應 `--method mcd`。
- 三種收縮在本資料上的比較紀錄見 [Mahalanobis_Improvement.md](../Mahalanobis_Improvement.md)。預設仍是 Ledoit–Wolf。

## 預期成果

兩種方法都應給出有限的 AUROC 與 F1。在 T1/8000 rpm 這種健康與故障已分開的工況上，AUROC 會接近 1，長條圖的差距會很小。若 `legacy` 的健康誤報遠高於 `ledoit_wolf`，現象應和七偵測器比較裡的 `maha_legacy` 同一方向。這個單工況圖不能代替九工況矩陣。

## 已記錄的實測

本程式沒有一份被指定為正式結論的彙總檔。九工況的數字以 `output/exp6_formal_matrix/aggregate/aggregate.md` 為準，說明見 [exp6_formal_benchmark.md](exp6_formal_benchmark.md)。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/compare_openset.py` | `evaluate_method`、`run`、`_make_figure`、`main` |
| `core/monitor.py` | `OpenSetMonitor` |
| `core/openset.py` | `SUPPORTED_OPENSET_METHODS` |
| `core/mahalanobis.py` | `legacy` / `ledoit_wolf` / `oas` / `mcd` |
| `core/runner.py` | `add_dataset_args`、`resolve_dataset` |

輸出：

- `logs/openset_comparison/{時間戳}.log`
- `output/openset_comparison/{時間戳}/summary.csv`
- `output/openset_comparison/{時間戳}/details.csv`
- `output/openset_comparison/{時間戳}/summary.json`
- `output/openset_comparison/{時間戳}/method_comparison.png`

### 散在其他位置的相關檔案

- 測試：`tests/test_openset.py` 匯入 `experiments.compare_openset.run`。
- 已提交紀錄：沒有。`logs/openset_comparison/`、`output/openset_comparison/` 目前不在 repo；目錄名沿用 `setup_run("openset_comparison")`，沒有帶實驗編號。
- 正式版 9 工況比較在實驗六：[exp6_formal_benchmark](exp6_formal_benchmark.md)。
- 其他文件：[Experiments_Guide.md](../Experiments_Guide.md) 第 8 節。
