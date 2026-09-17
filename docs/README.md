# docs/ 文件索引

本目錄是**論文版管線時期的技術文件快照**（對應本 repo git 歷史 `dda8910` 時的版本，
2026-09-17 放回）。文中描述的 Step 1–6 程式碼、notebook 與 `scripts/` 模組現存於
[Ancestor repo](https://github.com/Drone-Motors-Unknown-Faults-Detection/Ancestor)，
**不對應**目前的 `core/ experiments/ web/` 架構；每份文件頂部都有歷史標記。
新專案（冷啟動 PHM）的說明見根目錄 [README.md](../README.md)。

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
