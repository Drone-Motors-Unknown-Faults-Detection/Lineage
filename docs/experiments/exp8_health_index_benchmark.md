# 實驗八：健康指數 benchmark

程式：`experiments/health_index_benchmark.py`。它在正式版 Open Set 的分數上再套一層 `CalibratedHealthIndex`，多報相對健康指數與 known−unknown 的健康差距。

單次 `run()` 只跑一種方法、一個 seed，涵蓋資料根裡的九個工況。六次呼叫的寫檔在 [exp8_health_index_matrix.md](exp8_health_index_matrix.md)。逐窗串流在 [exp8_health_monitor.md](exp8_health_monitor.md)。

## 實驗方法

1. 工況必須是 9，除非 `--allow-partial`。排序鍵是 `(motor, rpm)`。
2. 每個工況只用 `8screws` 的 train 與 calibration。標籤傳進 `CalibratedHealthIndex.fit` 時全是 0。`legacy` 共變異數直接拒絕。
3. 擬合順序寫在 `experiments/health/index.py`：訓練集擬合 `RobustScaler` 與 `create_openset_detector`；校準集分數交給 `HealthIndexCalibrator`。健康錨點是校準分數的第 10 百分位，critical 錨點是第 95 百分位（`confidence=0.95`）。分數越高，健康指數越低。`degradation_score = 1 - health_index`。
4. 已知測驗是健康 holdout，未知測驗是其餘配置直向疊起。兩者都只在 `predict` 之後進入 `evaluate_open_set`。
5. 每一列同時有健康分布（平均、標準差、中位數、`≥ 0.8` 的比例、`< 0.2` 的比例）、`health_gap_known_minus_unknown`、Cohen 式效果量，以及 open-set accuracy、AUROC、AUPR、unknown recall、unknown F1。`rul_available` 固定 false。

```bash
venv/bin/python -m experiments.health_index_benchmark --data-root data/formal_local --seed 42 --openset-method mahalanobis
venv/bin/python -m experiments.health_index_benchmark --data-root data/formal_local --seed 42 --openset-method knn
```

`main()` 只把 status、列數、方法與 seed 印到 stdout。檔案要由矩陣程式寫，見下一節的輸出路徑。

## 理論

Open Set 分數已經能拒絕未知。健康指數是把這份分數壓進 `[0, 1]` 的單調函數，錨點只從已知校準集來。低於健康錨點的分數映成 1，高於 critical 錨點的分數映成 0，中間線性下降。它描述的是「相對這批健康校準窗口有多偏」，不是損壞百分比，也不是剩餘壽命。

嚴重度門檻是展示政策：`≥ 0.8` healthy、`≥ 0.5` early_warning、`≥ 0.2` degraded，其餘 critical。本 benchmark 的列裡沒有逐窗 stage，那些出現在 `health_monitor` 的 JSON。資料裡沒有ordinal 嚴重度標籤，所以這些門檻不能當成真實損壞等級。

`dataset_fingerprint` 直接呼叫 `experiments.exp6_formal_benchmark.dataset_fingerprint`，讓健康指數結果和正式 Open Set 矩陣能對上同一份資料。

## 參考論文

- 馬氏距離、Ledoit–Wolf、k 近鄰出處同 [exp1_cold_start.md](exp1_cold_start.md)。
- 分數到 `[0, 1]` 的分位數錨點、第 10 與第 95 百分位、`degradation_score = 1 - health_index`：本專案操作約定，寫在 `experiments/health/calibration.py` 的 `HealthIndexCalibrator`。
- 不能把指數說成物理損傷或 RUL：資料能力寫在 [exp8_health_monitoring_workflow.md](../exp8_health_monitoring_workflow.md) 與 [health_monitoring_data_capability.md（已刪除，見 commit 80bdf54）](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/80bdf54fdf43d466ea19549fb7c0b4e391394799/reports/health_monitoring_data_capability.md)。

## 預期成果

九列都完成，`unknown_calibration_leakage` 為 false，健康指數落在 `[0, 1]`。已知類的健康平均應高於未知類，`health_gap_known_minus_unknown` 為正。若未知窗口的健康指數全部貼在 0，表示它們的 Open Set 分數已經超過 critical 錨點，分離是有的，未知配置之間的高低仍然排不出來。

兩種方法的健康差距若只差約 0.02，而 open-set accuracy 的差距在 0.00001 這一量級，就不足以把預設偵測器從 Mahalanobis 換成 k-NN。

## 已記錄的實測

`reports/exp8_health_index_results/README.md` 對 9 工況 × 3 seed 的平均：

| method | health gap known−unknown | open-set accuracy | AUROC | unknown recall |
|---|---:|---:|---:|---:|
| Mahalanobis + Ledoit–Wolf | 0.583144 ± 0.073301 | 0.998849 ± 0.000887 | 1.000000 | 1.000000 |
| k-NN | 0.601657 ± 0.071637 | 0.998842 ± 0.000937 | 1.000000 | 1.000000 |

k-NN 的健康差距高 0.018513。Mahalanobis 的 accuracy 高 0.000007。同一份 README 寫明：held-out unknown 的健康指數在這組錨點下都飽和到 0.0。資料指紋 `81c9192476ecd1e23a17b3ed5a343dcd50cdc2e5b7e0cc5466e9162941898228`。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/health_index_benchmark.py` | `run`、`_health_distribution`、`_effect_size`、`main` |
| `experiments/health/index.py` | `CalibratedHealthIndex.fit` / `predict` |
| `experiments/health/calibration.py` | `HealthIndexCalibrator` |
| `experiments/health/evaluation.py` | `evaluate_open_set` |
| `experiments/health/severity.py` | 相對 stage 門檻 |
| `experiments/exp6_formal_benchmark.py` | `dataset_fingerprint` |
| `core/openset.py` | 偵測器工廠 |
| `core/data.py` | 載入與 `make_split` |

單次 CLI 不寫 `output/`。矩陣寫到 `reports/exp8_health_index_results/seed_{seed}/{method}.json` 與同名 CSV。

### 散在其他位置的相關檔案

- 套件：`experiments/health/` 全部模組，對照表見 [health_and_reports.md](../health_and_reports.md) 第 1.1 節。
- 測試：`tests/test_health_benchmark.py`，以及 `tests/test_health_{calibration,diagnosis,evaluation,index,schema,severity}.py`。
- 結果：`reports/exp8_health_index_results/`。
- 資料能力與限制：[exp8_health_monitoring_workflow.md](../exp8_health_monitoring_workflow.md)；原始稽核見 [health_and_reports.md](../health_and_reports.md) 第 2.2 節。
- 其他文件：[Experiments_Guide.md](../Experiments_Guide.md) 第 9 節。
