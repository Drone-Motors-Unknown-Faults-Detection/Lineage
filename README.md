# Ancestor — 馬達故障診斷與持續學習系統

本專案實作了一套完整的旋轉機械（馬達）**故障診斷與預後健康管理（PHM）** 流程，核心亮點在於結合深度學習分類與無監督異常偵測，實現對**未知故障的自動發現與持續學習**能力。

---

## 系統架構

```
原始訊號
  └─ Step 1：資料預處理
       └─ Step 2：特徵萃取（105 維）
            └─ Step 3：CNN 模型訓練（5 類已知故障）
                 ├─ Step 4：未知故障偵測（HDBSCAN + 馬氏距離）
                 ├─ Step 5：隨機取樣偵測驗證
                 └─ Step 6：模型重訓練（10 類擴充）
                       └─ 回到 Step 4（持續迭代）
```

---

## 六步驟快速說明

| 步驟 | 主題 | 技術 | 檔案類型 |
|------|------|------|----------|
| [Step 1](docs/Step1_Data_Preprocessing.md) | 資料預處理 | IQR 離群值移除、訊號切割 | Python (.py) × 15 |
| [Step 2](docs/Step2_Feature_Extraction.md) | 特徵萃取 | 統計特徵 + FFT 頻域特徵（105 維）| Python (.py) × 9 |
| [Step 3](docs/Step3_Model_Training.md) | CNN 模型訓練 | 1D CNN + Keras | Jupyter (.ipynb) × 27 |
| [Step 4](docs/Step4_Unknown_Detection.md) | 未知故障偵測 | HDBSCAN + 馬氏距離 | Jupyter (.ipynb) × 27 |
| [Step 5](docs/Step5_Random_Sampling_Detection.md) | 隨機取樣偵測 | 隨機批次驗證 | Jupyter (.ipynb) × 27 |
| [Step 6](docs/Step6_Model_Retraining.md) | 模型重訓練 | 增量學習（5 類 → 10 類）| Jupyter (.ipynb) × 27 |

---

## 資料說明

### 訊號來源

- **感測器：** 三軸振動加速度、馬達電流、馬達溫度、環境溫度
- **轉速：** 6000 / 8000 / 11000 RPM
- **馬達：** Motor A、B、C（及 T1 時序馬達）

### 故障類型模擬

透過移除馬達固定螺絲來模擬不同程度的故障：

| 螺絲數量 | 狀態 | 階段 |
|----------|------|------|
| 8 screws | 健康（Healthy）| 已知 |
| 1 ~ 4 screws | 故障 1-4（Faulty 1-4）| 已知 |
| 5 ~ 7 screws | 未知故障 1-3 | 未知（待偵測）|
| 3_14、4_146 | 複合故障 4-5 | 未知（待偵測）|

---

## 核心技術

```
訊號處理：pandas、numpy、scipy（FFT、統計）
深度學習：TensorFlow / Keras（1D CNN）
叢集分析：HDBSCAN
異常偵測：Mahalanobis Distance
退化建模：MLPRegressor（健康度指標回歸）
視覺化：matplotlib、seaborn
```

---

## 執行順序

```bash
# 1. 資料預處理（依轉速執行）
python Step1_Data_Preprocessing_save_6000_1.py
python Step1_Data_Preprocessing_save_8000_1.py
python Step1_Data_Preprocessing_save_11000_1.py
# 其他馬達/配置可改跑對應的 *_2.py / *_3.py

# 2. 特徵萃取
python Step2_Feature_Extraction_6000_1.py
python Step2_Feature_Extraction_8000_1.py
python Step2_Feature_Extraction_11000_1.py
# 其他馬達/配置可改跑對應的 *_2.py / *_3.py

# 3 ~ 6. 依序開啟對應 Jupyter Notebook 執行
# Step3_Model N.ipynb → Step4_Model N__Detecting.ipynb
# → Step5_Model N__Random_Detecting.ipynb → Step6_Model N__Retrain.ipynb
```

---

## `data/` 目錄建議結構（讀寫路徑基準）

本專案所有腳本/Notebooks 皆以**專案根目錄**為基準，並統一從 `data/` 目錄讀寫資料：

```
data/
├── Step-1/
│   ├── csv/
│   │   └── {Motor}/
│   │       └── {RPM}/
│   │           └── {Screws}/
│   │               ├── {Motor}_Current_data.csv
│   │               ├── {Motor}_Acceleration_X_data.csv   # 或 {Motor}_X_data.csv（依馬達型別/腳本而定）
│   │               ├── {Motor}_Acceleration_Y_data.csv   # 或 {Motor}_Y_data.csv
│   │               ├── {Motor}_Acceleration_Z_data.csv   # 或 {Motor}_Z_data.csv
│   │               └── {Motor}_Delta_T_data.csv
│   ├── myfeature/
│   │   └── {T_CODE}/
│   │       └── {RPM}/
│   │           └── {Screws}/
│   │               ├── {T_CODE}_Group_feature_data.csv
│   │               ├── {T_CODE}_Group_feature_data_raw.csv
│   │               └── {T_CODE}_Group_feature_data_clean.csv
│   └── model/
│       └── *.keras
├── Step-2/
│   ├── csv/ ...
│   ├── myfeature/ ...
│   └── model/ ...
└── Step-3/
    ├── csv/ ...
    ├── myfeature/ ...
    └── model/ ...
```

- **Step-1 / Step-2 / Step-3**：對應原本的「階段1/2/3」資料集（目前已統一改為 `Step-N` 命名）。
- **`csv/`**：Step 1 輸出（Step 2 的輸入）。
- **`myfeature/`**：Step 2 輸出（Step 3/4/5/6 的輸入）。
- **`model/`**：Step 3 / Step 6 訓練後的模型輸出（`.keras`）。

---

## 附加功能

**[T1_T2_T3.ipynb]** — 馬達健康度退化曲線建模

- 將馬達生命週期分為三個時期（T1 / T2 / T3）
- 健康指標（HI）從 1.0 線性衰減至 0.0
- 使用 MLPRegressor 從 105 維特徵預測健康指標
- 適用於預防性維護時程規劃

---

## 文件索引

- [Step 1 說明文件](docs/Step1_Data_Preprocessing.md)
- [Step 2 說明文件](docs/Step2_Feature_Extraction.md)
- [Step 3 說明文件](docs/Step3_Model_Training.md)
- [Step 4 說明文件](docs/Step4_Unknown_Detection.md)
- [Step 5 說明文件](docs/Step5_Random_Sampling_Detection.md)
- [Step 6 說明文件](docs/Step6_Model_Retraining.md)
- [TensorFlow 與 GPU 使用指南](docs/Tensorflow.md)
- [Agent 指引](AGENT.md)
