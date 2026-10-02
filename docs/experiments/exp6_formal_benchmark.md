# 實驗六正式版：Mahalanobis 對 k-NN

程式：`experiments/exp6_formal_benchmark.py`。一次呼叫跑完資料根目錄下的全部工況，但只跑一種 `--openset-method`、一個 `--seed`。九工況 × 多 seed × 兩方法的迴圈在 [exp6_matrix.md](exp6_matrix.md)。

這支在合併前曾叫 `exp6_osr_benchmark`。現在的七偵測器廣度比較留在原名，見 [exp6_osr_benchmark.md](exp6_osr_benchmark.md)。分支 `output/`、`logs/` 裡 2026-09-19 的 `exp6_osr_benchmark` 紀錄出自本模組。

## 實驗方法

1. `discover_datasets` 後依 `(motor, rpm)` 排序。`require_nine=True` 時工況數必須是 `FORMAL_CONDITION_COUNT = 9`，否則丟 `ValueError`。
2. `FORMAL_METHODS` 只有 `mahalanobis` 與 `knn`。Mahalanobis 若 `--method legacy` 直接拒絕。預設 `ledoit_wolf`、`confidence=0.95`、`knn_neighbors=5`、seed 42。
3. 每個工況：`RobustScaler` 只擬合 `8screws` 訓練集；`create_openset_detector(...).fit(...)` 的標籤全是 0，校準標籤也必須是已知類。未知配置在打分之後才疊成正類。
4. 預測規則是 `score > 1`。指標見下表。`peak_memory_mb` 固定寫 `null`。`inference_seconds` 只包兩次 `score_samples`，不含擬合。
5. `dataset_fingerprint` 對資料目錄做可攜的內容雜湊。摘要寫 `dataset_root` 的目錄名，不寫本機絕對路徑。另外記錄 `commit_sha`、Python 版、UTC 起迄時間。

| 欄位 | 演算法 |
|---|---|
| `known_accuracy` | 健康 holdout 預測為已知的比例 |
| `open_set_accuracy` | 健康 holdout 加全部未知窗口的準確率 |
| `auroc` | 未知為正類 |
| `aupr_unknown_positive` | 同上，average precision |
| `fpr_at_tpr95` | ROC 上 TPR ≥ 0.95 的最小 FPR |
| `unknown_precision` / `recall` / `f1` | 閾值 1.0 的未知類 |
| `known_score_median` / `unknown_score_median` | 分數中位數 |

```bash
venv/bin/python -m experiments.exp6_formal_benchmark --openset-method mahalanobis --seed 42
venv/bin/python -m experiments.exp6_formal_benchmark --openset-method knn --seed 42
```

## 理論

兩種偵測器共用工廠 `create_openset_detector`，共用「越大越未知、超過 1 就拒絕」。Mahalanobis 估的是類別橢球。k-NN 估的是到該類訓練集 k 個近鄰的平均歐氏距離，每類用自己的校準分位數正規化，再取最小正規化分數。健康-only 時只有一類，最小分數就是那一類的分數。

這次比較不包含 One-Class SVM、Isolation Forest、LOF、PCA 重建，也不包含 `core/detectors.py` 的 `knn_dist`。那些留在廣度比較。`polarmap_base_method` 在摘要裡固定寫 `mahalanobis`，因為幾何模組不跟著這次的拒絕器切換。

## 參考論文

- 馬氏距離、Ledoit–Wolf、Cover 與 Hart 的出處同 [exp1_cold_start.md](exp1_cold_start.md)。
- W. J. Scheirer, A. de Rezende Rocha, A. Sapkota, and T. E. Boult (2013), “Toward Open Set Recognition,” *IEEE TPAMI*, 35(7), 1757–1772。DOI [10.1109/TPAMI.2012.256](https://doi.org/10.1109/TPAMI.2012.256)。本程式實作的是校準距離拒絕，沒有實作該文的 open space risk 或 OpenMax。
- 拒絕 legacy 校準、未知不進閾值、指紋不含絕對路徑：本專案操作約定，寫在 `run()` 開頭的檢查與回傳字典。

## 預期成果

九列都應 `status=completed`，分數全為有限值。若特徵已經把螺絲配置和 `8screws` 分開，AUROC 與未知 recall 會接近 1，兩種方法的差距會落在小數點後段的準確率，而不是出現一個方法完全失敗。若某一工況的 `unknown_recall` 明顯低於其餘工況，先查該工況的目錄與 105 維是否齊全，再談偵測器。

`legacy` 被拒是預期行為。要看訓練集自校準的對照，跑 [exp6_osr_benchmark.md](exp6_osr_benchmark.md) 的 `maha_legacy`。

## 已記錄的實測

多 seed 的彙總不在本程式的單次輸出，而在 `output/exp6_formal_matrix/aggregate/aggregate.md`（54 列，seed 42、123、2026）：

| method | AUROC | open-set accuracy | unknown F1 |
|---|---:|---:|---:|
| mahalanobis | 1.000000 ± 0.000000 | 0.998849 ± 0.000887 | 0.999412 ± 0.000453 |
| knn | 1.000000 ± 0.000000 | 0.998842 ± 0.000937 | 0.999409 ± 0.000478 |

成對差（k-NN 減 Mahalanobis）裡，AUROC、AUPR、FPR@TPR95、unknown recall 的平均差是 0。open-set accuracy 的平均差是 −0.000007。這是矩陣跑完之後的數字。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/exp6_formal_benchmark.py` | `run`、`dataset_fingerprint`、`FORMAL_METHODS`、`main` |
| `core/openset.py` | `create_openset_detector`、`canonical_openset_method` |
| `core/data.py` | `discover_datasets`、`load_pools`、`make_split` |
| `experiments/health_index_benchmark.py` | 只借用 `dataset_fingerprint` |

`setup_run("exp6_formal_benchmark")` 寫入：

- `logs/exp6_formal_benchmark/{時間戳}.log`
- `output/exp6_formal_benchmark/{時間戳}/results.csv`
- `output/exp6_formal_benchmark/{時間戳}/summary.json`
- `output/exp6_formal_benchmark/{時間戳}/osr_benchmark.png`

摘要裡的 `output_dir` 另外記成相對路徑 `output/exp6_formal_benchmark/{時間戳}`。

### 散在其他位置的相關檔案

- 測試：`tests/test_exp6_benchmark.py`；偵測器工廠 `tests/test_openset.py`。
- 正式資料物化：`core/formal_data.py`（`tests/test_formal_data.py`），把 raw ZIP 轉成 `data/formal_local/`。
- 進度紀錄與資料來源稽核：[實驗六進度紀錄（已刪除，見 commit 80bdf54）](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/80bdf54fdf43d466ea19549fb7c0b4e391394799/reports/ancester_openset_exp6_progress.md)、[raw_data_audit/](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/tree/80bdf54fdf43d466ea19549fb7c0b4e391394799/reports/raw_data_audit)、[github_data_audit/](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/tree/80bdf54fdf43d466ea19549fb7c0b4e391394799/reports/github_data_audit)，均已刪除，清單見 [health_and_reports.md](../health_and_reports.md) 第 2.2 節。
- 其他文件：[Experiments_Guide.md](../Experiments_Guide.md) 第 7 節。
- Web 實驗頁：頁首「實驗六」的 6-2，`web/experiments.py` 的 `CATALOG` 項目 `exp6_formal` 以 `require_nine=False` 呼叫本程式的 `run()`，畫面在 `web/static/experiments.js` 的 `RENDER.exp6_formal`；結果存到 `output/web_server/{ts}/experiments/exp6_formal_{時間}.json`。
