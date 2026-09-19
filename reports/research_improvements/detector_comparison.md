# P6 Detector Comparison

## 公平設定

`experiments.detector_comparison` 固定使用 P1 split、同一 raw 105 維 RobustScaler、同一 95% healthy calibration、同一 immutable test、3 seeds 與同一 sample budget。完成的 healthy-only 方法是 Mahalanobis–Ledoit–Wolf、k-NN、OC-SVM、Isolation Forest、LOF、PCA reconstruction；每列都記錄 healthy FPR、unknown recall、AUROC、AUPR、FPR@95TPR、inference latency 與 calibration time。

## Formal replay（3 seeds）

| 方法 | healthy FPR | unknown recall | AUROC | AUPR | FPR@95TPR |
|---|---:|---:|---:|---:|---:|
| Mahalanobis–Ledoit–Wolf | 0.0023 | 0.5910 | 0.7859 | 0.9680 | 0.7054 |
| PCA reconstruction | 0.0000 | 0.4088 | 0.7710 | 0.9643 | 0.6716 |
| k-NN | 0.0000 | 0.2238 | 0.7630 | 0.9630 | 0.6704 |
| LOF | 0.0926 | 0.2220 | 0.5674 | 0.9110 | 0.6907 |
| Isolation Forest | 0.0000 | 0.0572 | 0.8571 | 0.9790 | 0.7069 |
| OC-SVM | 0.0000 | 0.0000 | 0.7341 | 0.9499 | 0.6704 |

以 unknown recall 與低 healthy FPR 的平衡看，這組 fixed protocol 中 Mahalanobis 最實用，但它不是所有 metric 都第一：Isolation Forest AUROC/AUPR 較高卻幾乎不產生 threshold alarm；因此不能只用 AUROC 選模型。

## 不適用／阻塞的方法

- Deep SVDD（Ruff et al., *Deep One-Class Classification*, PMLR 80, 2018）列為 `blocked`：目前 CPU Lineage venv 沒有 PyTorch/TensorFlow，也沒有事先固定的 neural representation、collapse guard 或 hyperparameter policy；硬塞一個非神經 proxy 會不公平。
- MSP、Energy、OpenMax 列為 `not_applicable`：目前冷啟動管線沒有合適的 multiclass logits／activation layer。Energy 與 OpenMax 不能用 raw 105D distance 冒充 logits detector。
- multimodal class-distribution（multiple prototypes/local model）及 raw-vs-neural comparison 尚待有標註 known classes 與 neural embedding 後另開 scenario；本表沒有把 feature extractor 差異歸因給 detector。

結果檔：`detector_comparison/summary.json`。所有完成 rows 都是 raw_105d；blocked/not_applicable rows 不納入 aggregate。
