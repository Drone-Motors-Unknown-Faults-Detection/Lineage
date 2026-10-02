# docs/ 文件索引

> 實驗的白話說明在 [實驗說明手冊](Experiments_Guide.md)。
> 對程式的技術報告在 [experiments/](experiments/README.md)。
> 下面的 Step 1–6、Tensorflow 與三份 Lineage 研究筆記是論文版管線的歷史快照。

歷史快照對應本 repo git 歷史 `dda8910`（2026-09-17 放回）。那些文件裡的 Step 1–6
程式、notebook 與 `scripts/` 現存於
[Ancestor repo](https://github.com/Drone-Motors-Unknown-Faults-Detection/Ancestor)，
**不對應**目前的 `core/ experiments/ web/`；每份快照頂部都有歷史標記。
新專案的說明見根目錄 [README.md](../README.md)。

## 現行實驗技術報告

`experiments/` 的每一支程式各有一份，目錄與各實驗散在 `core/`、`health/`、`web/`、`tests/`、`reports/` 的檔案位置在 [experiments/README.md](experiments/README.md)。白話版仍是 [Experiments_Guide.md](Experiments_Guide.md)。

| 編號 | 文件 | 程式 |
|---|---|---|
| 實驗一 | [exp1_cold_start](experiments/exp1_cold_start.md) | `experiments/exp1_cold_start.py` |
| 實驗二 | [exp2_scale_growth](experiments/exp2_scale_growth.md) | `experiments/exp2_scale_growth.py` |
| 實驗三 | [exp3_trend](experiments/exp3_trend.md) | `experiments/exp3_trend.py` |
| 實驗四 | [exp4_polar_map](experiments/exp4_polar_map.md) | `experiments/exp4_polar_map.py` |
| 實驗五 | [exp5_cross_condition](experiments/exp5_cross_condition.md) | `experiments/exp5_cross_condition.py` |
| 實驗六 | [exp6_osr_benchmark](experiments/exp6_osr_benchmark.md) | `experiments/exp6_osr_benchmark.py` |
| 實驗六 | [exp6_formal_benchmark](experiments/exp6_formal_benchmark.md) | `experiments/exp6_formal_benchmark.py` |
| 實驗六 | [exp6_matrix](experiments/exp6_matrix.md) | `experiments/exp6_matrix.py` |
| 實驗六 | [exp6_aggregate](experiments/exp6_aggregate.md) | `experiments/aggregate_exp6.py` |
| 實驗七 | [exp7_compare_openset](experiments/exp7_compare_openset.md) | `experiments/compare_openset.py` |
| 實驗八 | [exp8_health_index_benchmark](experiments/exp8_health_index_benchmark.md) | `experiments/health_index_benchmark.py` |
| 實驗八 | [exp8_health_index_matrix](experiments/exp8_health_index_matrix.md) | `experiments/health_index_matrix.py` |
| 實驗八 | [exp8_health_monitor](experiments/exp8_health_monitor.md) | `experiments/health_monitor.py` |

## 現行健康監測工作流程

| 文件 | 內容 |
|---|---|
| [exp8_health_monitoring_workflow](exp8_health_monitoring_workflow.md) | 實驗八總覽：Level A 資料能力、Health Index、趨勢/告警、正式 9×3×2 結果、限制與 CLI |
| [health_and_reports](health_and_reports.md) | `health/` 各模組與呼叫端、兩套趨勢邏輯的差別、`reports/` 各子目錄的來源與現況 |

## 論文版管線文件（程式碼在 Ancestor）

| 文件 | 內容 | 與新專案的關係 |
|---|---|---|
| [Step1_Data_Preprocessing](Step1_Data_Preprocessing.md) | 原始訊號清洗、IQR、切段 | 新專案不重跑，只讀其下游產物 |
| [Step2_Feature_Extraction](Step2_Feature_Extraction.md) | **105 維特徵定義**（15 統計量 × 5 通道 + FFT 諧波）| **直接沿用**——新專案的輸入格式即此，`*_clean.csv` 的由來 |
| [Step3_Model_Training](Step3_Model_Training.md) | CNN/ResNet/VGG16 訓練與遷移學習 | 新專案捨深度模型（見 Model_Choice 結論）|
| [Step4_Unknown_Detection](Step4_Unknown_Detection.md) | HDBSCAN + 馬氏距離 95 百分位未知偵測 | 判定機制的前身；新專案改逐類 Ledoit–Wolf、逐樣本判定 |
| [Step5_Random_Sampling_Detection](Step5_Random_Sampling_Detection.md) | 隨機組合驗證 | 概念由 exp2 隨機注入取代 |
| [Step6_Model_Retraining](Step6_Model_Retraining.md) | 5 類 → 10 類重訓練 | 概念由 exp2 量尺擴張（全資料重擬合）取代 |
| [Tensorflow](Tensorflow.md) | 論文版環境的 TF/GPU 指南 | 新專案不需 TF/GPU |

## Lineage 時期研究文件（結論已進入新專案）

| 文件 | 內容 | 對新專案的貢獻 |
|---|---|---|
| [Mahalanobis_Improvement](Mahalanobis_Improvement.md) | Ledoit–Wolf / OAS / MCD 三法實測比較 | **`core/mahalanobis.py` 預設 `ledoit_wolf` 的實驗依據**（開集準確率 0.951 → 0.986）|
| [Model_Choice_Analysis](Model_Choice_Analysis.md) | 45 模型實測：閉集準確率飽和、開集分離度才是關鍵 | 「換模型／調參無益，該動特徵與判定機制」——新專案改用 105 維手工特徵冷啟動的背景 |
| [OpenSet_Recognition](OpenSet_Recognition.md) | OpenMax、能量分數等五種 OSR 替代方案評估 | 新專案的未來方向清單（README「限制與未來工作」）|

> 注意：文內的相對連結（如 `logs/claude/Result.md`、`scripts/*.py`、`../README.md` 的舊錨點）
> 指向撰寫當時的 repo 佈局，於現行佈局中可能失效——以 Ancestor repo 與 git 歷史為準。
