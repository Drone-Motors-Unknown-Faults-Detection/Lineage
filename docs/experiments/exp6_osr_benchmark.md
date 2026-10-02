# 實驗六：七種偵測器的廣度比較

程式：`experiments/exp6_osr_benchmark.py`。七個偵測器類別在 `core/detectors.py` 的 `ALL_DETECTORS`。

問題：健康-only、同一套 60/20/20、同一套「校準集第 95 百分位 = 1」之下，Ledoit–Wolf 馬氏距離的健康誤報與故障偵測，相對於另外六種單類方法站在哪。

這支程式不產生 `reports/exp8_health_index_results/`。正式版只比 Mahalanobis 與 k-NN、且走 `core.openset` 的那次，見 [exp6_formal_benchmark.md](exp6_formal_benchmark.md)。

## 實驗方法

1. `discover_datasets` 掃 `--data-root`（預設 `data`）。每個資料集用同一個 `default_rng(seed)` 往下切，預設 seed 42，所以九組的切分序列是接續的，不是各自從 42 重來。
2. 訓練集、校準集來自 `8screws`。故障池是其餘配置全部直向疊起來，只在打分之後使用。
3. 每個偵測器 `fit(X_train, X_cal)` 後，對健康 holdout 與故障池打分。指標是 AUROC、FPR@TPR95、健康誤報 `(h > 1)`、故障偵測 `(f > 1)`。
4. 跨資料集對四個指標取平均。AUROC 與健康誤報另外取標準差。摘要依 AUROC 平均降序、再依 FPR@TPR95 升序。

七個 `name`：

| 類別 | `name` | 原始分數 |
|---|---|---|
| `MahalanobisLW` | `maha_ledoit_wolf` | 呼叫 `MahalanobisOpenSetDetector(method="ledoit_wolf")`，門檻沿用該偵測器的校準分位數 |
| `MahalanobisLegacy` | `maha_legacy` | 同上，`method="legacy"`：訓練距離自己的分位數，校準集不決定門檻 |
| `OneClassSVMDet` | `ocsvm` | `OneClassSVM(nu=0.05, gamma="scale")`，分數取 decision function 的相反數 |
| `IsolationForestDet` | `iforest` | `IsolationForest(n_estimators=200)`，分數取 `score_samples` 的相反數 |
| `LOFDet` | `lof` | `LocalOutlierFactor(n_neighbors=20, novelty=True)`，分數取 decision function 的相反數 |
| `KNNDistanceDet` | `knn_dist` | `NearestNeighbors(n_neighbors=5)`，五個距離的平均 |
| `PCAReconDet` | `pca_recon` | `PCA(n_components=0.95)` 的重建誤差 L2 |

除了兩個 Mahalanobis 類別走自己的 `fit`，其餘類別都用 `_Base.fit`：`RobustScaler` 只擬合訓練集，原始分數除以校準集第 95 百分位。校準分位數 ≤ 0 時先平移再除。

```bash
venv/bin/python -m experiments.exp6_osr_benchmark
venv/bin/python -m experiments.exp6_osr_benchmark --data-root data --seed 42 --confidence 0.95
```

## 理論

比較要看的是偵測器，所以切分與「多大算未知」盡量鎖死。校準分位數把不同量綱的分數改成「相對這批健康校準窗口的尾部」。AUROC 看排序，不看 1.0 這條線；健康誤報與故障偵測才看這條線有沒有校準好。

`maha_legacy` 故意留著論文版做法：門檻用訓練集自己的距離。它和另外六種不共用校準集，讀表時要把它當成對照，不能和 `maha_ledoit_wolf` 說成同一套閾值政策。`core/detectors.py` 的 `knn_dist` 是單一健康雲上的平均近鄰距離；`core/openset.py` 的 `knn` 是逐類近鄰再取最小正規化分數。兩邊的 k 都是 5，程式不是同一份。

FPR@TPR95 的實作是：取故障分數的第 5 百分位當門檻（讓約 95% 的故障超過它），再算健康分數超過該門檻的比例。這和 ROC 曲線上插值得到的 FPR@TPR95 不一定相同。

## 參考論文

- 馬氏距離與 Ledoit–Wolf 出處同 [exp1_cold_start.md](exp1_cold_start.md)。legacy 路徑的對照說明見 [Mahalanobis_Improvement.md](../Mahalanobis_Improvement.md)。
- B. Schölkopf, J. C. Platt, J. Shawe-Taylor, A. J. Smola, and R. C. Williamson (2001), “Estimating the Support of a High-Dimensional Distribution,” *Neural Computation*, 13(7), 1443–1471。DOI [10.1162/089976601750264965](https://doi.org/10.1162/089976601750264965)。`nu=0.05` 是本專案選的。
- F. T. Liu, K. M. Ting, and Z.-H. Zhou (2008), “Isolation Forest,” *IEEE ICDM*, 413–422。DOI [10.1109/ICDM.2008.17](https://doi.org/10.1109/ICDM.2008.17)。`n_estimators=200` 是本專案選的。
- M. M. Breunig, H.-P. Kriegel, R. T. Ng, and J. Sander (2000), “LOF: Identifying Density-Based Local Outliers,” *SIGMOD Record*, 29(2), 93–104。DOI [10.1145/335191.335388](https://doi.org/10.1145/335191.335388)。
- S. Ramaswamy, R. Rastogi, and K. Shim (2000), “Efficient Algorithms for Mining Outliers from Large Data Sets,” *SIGMOD*, 427–438。DOI [10.1145/342009.335437](https://doi.org/10.1145/342009.335437)。本程式用的是 k 個距離的平均，論文原式常取第 k 距離。
- I. T. Jolliffe (2002), *Principal Component Analysis*, 2nd ed., Springer。DOI [10.1007/b98835](https://doi.org/10.1007/b98835)。保留 95% 變異後用重建殘差當異常分數，是本專案在 `PCAReconDet` 的操作約定。

## 預期成果

若 105 維已經把健康和故障拉開，多個方法的 AUROC 會同時接近 1，方法差異會出現在健康誤報而不是 AUROC。`maha_legacy` 的健康誤報若遠高於用校準集定閾值的方法，就支持「門檻不要用訓練集自己的距離」這條專案約定。若某個方法 AUROC 明顯掉到 0.5 附近，那個偵測器在這份特徵上不適合當冷啟動基準。

## 已記錄的實測

[Experiments_Guide.md](../Experiments_Guide.md) 記載九組資料、seed 42：七種方法 AUROC 都是 1.0000。健康誤報 kNN 6.0%、Ledoit–Wolf 馬氏 7.1%、legacy 83.1%。手冊因此把偵測器選擇放在特徵與校準之後，主線仍用 Ledoit–Wolf，因為它保留逐類共變異數，後續極座標與量尺擴張用得到。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/exp6_osr_benchmark.py` | `run`、`_fpr_at_tpr`、`_figure`、`main` |
| `core/detectors.py` | `ALL_DETECTORS` 與 `_Base.fit` |
| `core/mahalanobis.py` | `maha_ledoit_wolf`、`maha_legacy` |
| `core/data.py` | `discover_datasets`、`load_pools`、`make_split` |

輸出：

- `logs/exp6_osr_benchmark/{時間戳}.log`
- `output/exp6_osr_benchmark/{時間戳}/results.csv`
- `output/exp6_osr_benchmark/{時間戳}/summary.json`
- `output/exp6_osr_benchmark/{時間戳}/osr_benchmark.png`

### 散在其他位置的相關檔案

- 測試：沒有專屬測試；`core/detectors.py` 沒有直接測試。
- 已提交紀錄：`logs/exp6_osr_benchmark/`、`output/exp6_osr_benchmark/`（5 次執行，其中 2026-09-19 的出自改名前的 `exp6_formal_benchmark`）。
- 同屬實驗六：[exp6_formal_benchmark](exp6_formal_benchmark.md)、[exp6_matrix](exp6_matrix.md)、[exp6_aggregate](exp6_aggregate.md)。
- 其他文件：[Experiments_Guide.md](../Experiments_Guide.md) 第 7 節。
