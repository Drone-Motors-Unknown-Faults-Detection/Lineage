# docs/ 文件索引

本目錄包含現行研究手冊、健康監測與同步 raw 規格，以及**論文版管線時期的技術文件快照**（對應本 repo git 歷史 `dda8910` 時的版本，
2026-09-17 放回）。下列歷史快照描述的 Step 1–6 程式碼、notebook 與 `scripts/` 模組現存於
[Ancestor repo](https://github.com/Drone-Motors-Unknown-Faults-Detection/Ancestor)，
**不對應**目前的 `core/ experiments/ web/` 架構；歷史快照頂部有歷史標記，現行手冊另列。
新專案（冷啟動 PHM）的說明見根目錄 [README.md](../README.md)。

## 現行文件

| 文件 | 內容 |
|---|---|
| [exp16 平滑L1原型距離](experiments/exp16_smooth_l1_prototypes.md) | 固定Q／S平滑、原型loss與anchor配對；runner待實作，尚無正式成績 |
| [exp15 判別式原型學習](experiments/exp15_discriminative_prototypes.md) | 固定GLVQ／anchor損失、static中心與模糊拒絕配對；保留失敗與曝露 |
| [exp13 封存後失敗診斷](experiments/exp13_metric_failure_diagnosis.md) | 固定分數分布、分類器輸出、歷史Q配對重現；不掃threshold |
| [exp14 局部 Fisher 與 PCA](experiments/exp14_local_fisher.md) | 固定秩、正則化、來源重建與全方法配對；不改正式預設 |
| [exp13 收斂距離與分類規則](experiments/exp13_metric_classification.md) | hard600、k-NN／中心／energy 配對與 factory detector 消融；未知資料不擬合、不改正式預設 |
| [exp13 實際模型來源重建](experiments/exp13_metric_source_verification.md) | 重建 train-only 數值陣列與已知 calibration；不修改封存方法 |
| [fault_type_solver_diagnosis](experiments/fault_type_solver_diagnosis.md) | train-only hard／smooth hinge與最佳化預算診斷：先手冊再實作，不稱新outer成績 |
| [fault_type_solver_report](experiments/fault_type_solver_report.md) | 27個train-only checkpoints損失/gradient重算、來源与原Q權重對照 |
| [health_monitoring_workflow](health_monitoring_workflow.md) | Level A 資料能力、Health Index、趨勢/告警、正式 9×3×2 結果、限制與 CLI |
| [研究分支說明](research_improvements_20260920.md) | 分支範圍、成果入口、資料／motor roles、性能與未知限制（Docs #11） |
| [同步 raw schema 用途](synchronized_raw_schema.md) | config 欄位、實際 parser、preview／fresh 差別與 CLI |
| [實驗手冊索引](experiments/README.md) | 本次 continuous Q 與同步 raw 手冊；後續先寫手冊再改程式 |
| [fault_type_continuous_study](experiments/fault_type_continuous_study.md) | 對應 experiments/fault_type_continuous_study.py：方法、來源、预期、程式範圍與 CLI |
| [synchronized_raw](experiments/synchronized_raw.md) | 對應 experiments/synchronized_raw.py：方法、來源、预期、程式範圍與 CLI |
| [synchronized_features](experiments/synchronized_features.md) | 對應 experiments/synchronized_features.py：方法、來源、预期、程式範圍與 CLI |
| [fault_type_continuous_inventory](experiments/fault_type_continuous_inventory.md) | 對應 experiments/fault_type_continuous_inventory.py：方法、來源、预期、程式範圍與 CLI |
| [fault_type_continuous_registry](experiments/fault_type_continuous_registry.md) | 對應 experiments/fault_type_continuous_registry.py：方法、來源、预期、程式範圍與 CLI |
| [fault_type_continuous_report](experiments/fault_type_continuous_report.md) | 對應 experiments/fault_type_continuous_report.py：方法、來源、预期、程式範圍與 CLI |
| [fault_type_continuous_report_v2](experiments/fault_type_continuous_report_v2.md) | 對應 experiments/fault_type_continuous_report_v2.py：方法、來源、预期、程式範圍與 CLI |
| [fault_type_continuous_smoke](experiments/fault_type_continuous_smoke.md) | 對應 experiments/fault_type_continuous_smoke.py：方法、來源、预期、程式範圍與 CLI |
| [fault_type_continuous_acceptance](experiments/fault_type_continuous_acceptance.md) | 對應 experiments/fault_type_continuous_acceptance.py：方法、來源、预期、程式範圍與 CLI |

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
