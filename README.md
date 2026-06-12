# Ancestor — 馬達故障診斷與持續學習系統

本專案實作了一套完整的旋轉機械（馬達）**故障診斷與預後健康管理（PHM）** 流程，核心亮點在於結合深度學習分類與無監督異常偵測，實現對**未知故障的自動發現與持續學習**能力（開放集故障診斷 / Open-Set Fault Diagnosis）。

---

## 目錄

1. [系統架構](#系統架構)
2. [目錄結構](#目錄結構)
3. [環境設定](#環境設定)
4. [資料說明](#資料說明)
5. [Step 1：資料預處理](#step-1資料預處理)
6. [Step 2：特徵萃取](#step-2特徵萃取)
7. [Step 3：CNN 模型訓練](#step-3cnn-模型訓練)
8. [Step 4：未知故障偵測](#step-4未知故障偵測)
9. [Step 5：隨機取樣偵測驗證](#step-5隨機取樣偵測驗證)
10. [Step 6：模型重訓練](#step-6模型重訓練)
11. [附加功能：健康度退化建模](#附加功能健康度退化建模)
12. [基礎設施模組](#基礎設施模組)
13. [模型編號系統](#模型編號系統)
14. [執行流程](#執行流程)
15. [注意事項與限制](#注意事項與限制)

---

## 系統架構

```
原始訊號（3 軸振動 + 電流 + 溫度差）
  └─ Step 1：資料預處理（IQR 離群值移除 → 切割成 1 秒段）
       └─ Step 2：特徵萃取（統計特徵 + FFT → 105 維固定特徵向量）
            └─ Step 3：CNN 模型訓練（1D CNN，5 類已知故障）
                 ├─ Step 4：未知故障偵測（HDBSCAN 叢集 + 馬氏距離閾值）
                 ├─ Step 5：隨機取樣偵測驗證（多批次強健性測試）
                 └─ Step 6：模型重訓練（5 類 → 10 類增量學習）
                       └─ 回到 Step 4（持續迭代）

附加功能：T1_T2_T3.ipynb — 馬達生命週期健康度退化曲線
```

---

## 目錄結構

```
/home/albert/Ancestor/
│
├── 核心腳本
│   ├── Step1_Data_Preprocessing_figure_*.py  # 原始訊號視覺化（×6）
│   ├── Step1_Data_Preprocessing_save_*.py    # 資料預處理與儲存（×9）
│   └── Step2_Feature_Extraction_*.py         # 105 維特徵萃取（×9）
│
├── Jupyter Notebooks
│   ├── Step3_Model_{1..9}.ipynb                         # CNN 訓練，基礎版本（×9）
│   ├── Step3_Model_{10..27}_OneStage.ipynb              # CNN 訓練，OneStage 遷移學習（×18）
│   ├── Step3_Model_{10..27}_TwoStage.ipynb              # CNN 訓練，TwoStage 遷移學習（×18）
│   ├── Step4_Model_{1..27}_Detecting.ipynb              # 未知故障偵測（×27）
│   ├── Step5_Model_{1..27}_Random_Detecting.ipynb       # 隨機取樣驗證（×27）
│   ├── Step6_Model_{1..27}_Retrain.ipynb                # 模型重訓練（×27）
│   ├── T1_T2_T3.ipynb                                   # 健康度退化建模
│   └── GPU-Test.ipynb                                   # GPU / CUDA 環境驗證
│
├── 基礎設施
│   ├── logger.py                             # 自訂日誌框架
│   ├── gpu_utils.py                          # GPU/CPU 自動選擇模組
│   └── requirements.txt                      # Python 套件清單
│
├── docs/                                     # 各步驟詳細說明文件
│   ├── Step1_Data_Preprocessing.md
│   ├── Step2_Feature_Extraction.md
│   ├── Step3_Model_Training.md
│   ├── Step4_Unknown_Detection.md
│   ├── Step5_Random_Sampling_Detection.md
│   ├── Step6_Model_Retraining.md
│   └── Tensorflow.md                         # TensorFlow & GPU 安裝指南
│
└── data/                                     # 所有資料（讀寫基準）
    ├── Step-1/
    │   ├── csv/        # Step 1 輸出：切割後的原始訊號
    │   ├── myfeature/  # Step 2 輸出：105 維特徵向量
    │   └── model/      # Step 3/6 輸出：訓練完成的 .keras 模型
    ├── Step-2/
    │   ├── csv/ / myfeature/ / model/
    └── Step-3/
        ├── csv/ / myfeature/ / model/
```

> 所有腳本與 Notebook 皆以**專案根目錄**為執行基準（即 `.../Ancestor/`），資料統一存放於 `data/` 目錄。

---

## 環境設定

### 需求套件

```
numpy
pandas
matplotlib
scipy
scikit-learn
tensorflow[and-cuda]    # GPU 版 TensorFlow（含 CUDA 支援）
seaborn
hdbscan                 # 階層式 DBSCAN 叢集演算法
natsort                 # 自然排序（用於檔案排序）
jupyter
loguru                  # 日誌框架（可選，logger.py 內部使用）
```

安裝：

```bash
pip install -r requirements.txt
```

或手動安裝：

```bash
pip install tensorflow[and-cuda] hdbscan scikit-learn scipy pandas numpy matplotlib seaborn jupyter natsort loguru
```

### GPU 環境（目前實驗機）

| 項目 | 版本 |
|------|------|
| Python | 3.12 |
| TensorFlow | 2.21.0 |
| CUDA | 13.1 |
| cuDNN | 9.21.1 |
| GPU | NVIDIA L40S（46 GB VRAM）|
| 驅動程式 | 590.48.01 |

### 驗證 GPU 可用性

執行 `GPU-Test.ipynb` 或：

```python
import tensorflow as tf
print(tf.config.list_physical_devices('GPU'))  # 應回傳 [PhysicalDevice(name='/physical_device:GPU:0', ...)]
```

詳細安裝步驟見 [docs/Tensorflow.md](docs/Tensorflow.md)。

---

## 資料說明

### 感測器與訊號

每組實驗擷取以下 5 種訊號：

| 訊號 | 欄位名稱 | 說明 |
|------|----------|------|
| 三軸振動加速度 | `Acceleration_X/Y/Z` | 馬達殼體振動量測 |
| 馬達電流 | `Current` | 電機驅動電流 |
| 溫度差 | `Delta_T` | 馬達溫度 − 環境溫度 |

- **取樣率（Fs）：10,000 Hz**（固定，所有腳本共用，**不可修改**）
- **每段訊號長度：10,000 點 = 1 秒**

### 實驗配置

實驗以三個維度交叉組合：

| 維度 | 選項 |
|------|------|
| **資料集階段** | Step-1 / Step-2 / Step-3（馬達生命週期三個時期）|
| **轉速（RPM）** | 6000 / 8000 / 11000 |
| **螺絲配置** | 8screws / 1-7screws / 3_14screws / 4_146screws |

### 故障模擬方式

透過**移除馬達固定螺絲**來模擬不同程度的機械鬆動故障：

| 螺絲數量 | 標籤 | 語意 | 類別屬性 |
|----------|------|------|----------|
| 8 screws | 0 | Healthy（健康）| 已知 |
| 1 screw | 1 | Faulty 1（故障 1）| 已知 |
| 2 screws | 2 | Faulty 2（故障 2）| 已知 |
| 3 screws | 3 | Faulty 3（故障 3）| 已知 |
| 4 screws | 4 | Faulty 4（故障 4）| 已知 |
| 5 screws | 5 | New Faulty 1 | **未知**（Step 4 偵測目標）|
| 6 screws | 6 | New Faulty 2 | **未知** |
| 7 screws | 7 | New Faulty 3 | **未知** |
| 3_14 screws | 8 | New Faulty 4（複合鬆動）| **未知** |
| 4_146 screws | 9 | New Faulty 5（複合鬆動）| **未知** |

> 螺絲數量越少，機械鬆動越嚴重，振動訊號特徵越明顯。複合配置（`3_14`、`4_146`）代表非均勻鬆動模式。

### `data/` 目錄完整結構

```
data/
├── Step-{1|2|3}/
│   ├── csv/
│   │   └── {Motor}/               # 馬達代碼（T1、T2、T3 等）
│   │       └── {RPM}/             # 6000rpm / 8000rpm / 11000rpm
│   │           └── {Screws}/      # 8screws / 1screws / ... / 4_146screws
│   │               ├── {Motor}_Current_data.csv
│   │               ├── {Motor}_X_data.csv          # 或 Acceleration_X_data.csv
│   │               ├── {Motor}_Y_data.csv
│   │               ├── {Motor}_Z_data.csv
│   │               └── {Motor}_Delta_T_data.csv
│   ├── myfeature/
│   │   └── {Motor}/
│   │       └── {RPM}/
│   │           └── {Screws}/
│   │               ├── {Motor}_Group_feature_data.csv        # 原始萃取特徵
│   │               ├── {Motor}_Group_feature_data_raw.csv    # 中間結果
│   │               └── {Motor}_Group_feature_data_clean.csv  # 去除離群值後的乾淨特徵
│   └── model/
│       └── CNN_*.keras             # 訓練完成的模型（Step 3 / Step 6 輸出）
```

---

## Step 1：資料預處理

**檔案：** `Step1_Data_Preprocessing_save_*.py`（×9）、`Step1_Data_Preprocessing_figure_*.py`（×6，僅視覺化）

**輸入：** 原始量測 CSV 檔（Tab 分隔，標頭位於第 22 行）
**輸出：** `data/Step-{1|2|3}/csv/{Motor}/{RPM}/{Screws}/{Motor}_{Signal}_data.csv`

### 處理流程

```
1. 讀取原始 CSV（以 tab 分隔，略過前 21 行說明文字）
2. 提取 5 種訊號欄位（Acceleration X/Y/Z、Current、Delta_T）
3. IQR 離群值移除（scale=3.0）
4. 切割成 10,000 點的連續片段（= 1 秒 @ 10 kHz）
5. 橫向拼接所有片段（每欄 = 1 個片段）
6. 儲存為 CSV（欄數 = 片段數，列數 = 10,000）
```

### 離群值移除（IQR 方法）

```python
def iqr(data, scale=3.0):
    Q1 = data.quantile(0.25)
    Q3 = data.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - scale * IQR
    upper = Q3 + scale * IQR
    return data[(data >= lower) & (data <= upper)]
```

`scale=3.0` 意指移除超出 3 倍四分位距範圍的資料點，保留極端但合理的訊號。

### 輸出格式

每個輸出 CSV 的結構：

- **列（rows）：** 10,000 列，對應每段 1 秒訊號的取樣點
- **欄（columns）：** 每欄為一個時間片段（第 0 段、第 1 段…）
- 欄數因每組實驗的可用資料量而異

### 腳本命名規則

```
Step1_Data_Preprocessing_save_{RPM}_{variant}.py
```

- `{RPM}` = `6000` / `8000` / `11000`
- `{variant}` = `1` / `2` / `3`（對應不同馬達/配置批次）

---

## Step 2：特徵萃取

**檔案：** `Step2_Feature_Extraction_{RPM}_{variant}.py`（×9）

**輸入：** `data/Step-{1|2|3}/csv/`（Step 1 輸出）
**輸出：** `data/Step-{1|2|3}/myfeature/`（105 維特徵向量 CSV）

### 特徵向量結構（105 維）

每個 1 秒訊號片段萃取出 105 維的固定特徵向量：

```
維度 1  ~  15 ：Current（電流）— 15 種統計特徵
維度 16 ~  40 ：Vibration X  — 15 種統計特徵 + 10 種 FFT 頻域特徵
維度 41 ~  65 ：Vibration Y  — 15 種統計特徵 + 10 種 FFT 頻域特徵
維度 66 ~  90 ：Vibration Z  — 15 種統計特徵 + 10 種 FFT 頻域特徵
維度 91 ~ 105 ：Delta_T（溫差）— 15 種統計特徵
```

### 15 種統計特徵定義

| 特徵 | 公式 | 說明 |
|------|------|------|
| RMS | $\sqrt{\frac{1}{N}\sum x_i^2}$ | 均方根值 |
| Mean | $\bar{x}$ | 平均值 |
| Kurtosis | $\frac{\mu_4}{\sigma^4}$ | 峰態係數 |
| Std | $\sigma$ | 標準差 |
| Skewness | $\frac{\mu_3}{\sigma^3}$ | 偏態係數 |
| Peak-to-Peak | $x_{max} - x_{min}$ | 峰峰值 |
| Crest Indicator | $\frac{x_{max}}{RMS}$ | 波峰指標 |
| Clearance Indicator | $\frac{x_{max}}{(\frac{1}{N}\sum\sqrt{\|x_i\|})^2}$ | 間隙指標 |
| Shape Indicator | $\frac{RMS}{\frac{1}{N}\sum\|x_i\|}$ | 形狀指標 |
| Impulse Indicator | $\frac{x_{max}}{\frac{1}{N}\sum\|x_i\|}$ | 衝擊指標 |
| Max | $x_{max}$ | 最大值 |
| Min | $x_{min}$ | 最小值 |
| MSA | $\frac{1}{N}\sum x_i^2$ | 均方振幅（Mean Square Amplitude）|
| Variance | $\sigma^2$ | 變異數 |
| Mean Amplitude | $\frac{1}{N}\sum\|x_i\|$ | 平均振幅 |

### 10 種 FFT 頻域特徵（僅振動軸）

對每個振動軸執行 FFT，並在基頻及其諧波附近萃取能量特徵：

| 轉速 | 基頻（Base Frequency） |
|------|----------------------|
| 6000 RPM | 100 Hz |
| 8000 RPM | 133 Hz |
| 11000 RPM | 183 Hz |

從基頻的 1 倍至 10 倍諧波各萃取 1 個能量值（共 10 個），捕捉機械鬆動時的諧波放大現象。

### 標準化

在萃取特徵前，先對原始訊號套用 `RobustScaler`（對離群值具強健性的標準化），避免極端振幅污染統計特徵。

### 輸出格式

```
{Motor}_Group_feature_data.csv       ← 所有螺絲配置的特徵向量合併
{Motor}_Group_feature_data_raw.csv   ← 未去除離群值的原始版本
{Motor}_Group_feature_data_clean.csv ← IQR 去除特徵離群值後的版本
```

每列 = 1 個 1 秒片段的 105 維特徵向量，最後一欄為螺絲配置標籤。

---

## Step 3：CNN 模型訓練

**檔案：** `Step3_Model_{1..9}.ipynb`（×9 基礎版）、`Step3_Model_{10..27}_OneStage.ipynb`（×18）、`Step3_Model_{10..27}_TwoStage.ipynb`（×18），共 45 個

**輸入：** `data/Step-{1|2|3}/myfeature/` 的 105 維特徵 CSV
**輸出：** `data/Step-{1|2|3}/model/CNN_*.keras`

### 問題定義

以**5 類已知故障**進行監督式分類：

| 類別 | 螺絲配置 | 物理意義 |
|------|----------|----------|
| 0 | 8 screws | Healthy（健康，基準狀態）|
| 1 | 1 screw | Faulty 1（最嚴重鬆動）|
| 2 | 2 screws | Faulty 2 |
| 3 | 3 screws | Faulty 3 |
| 4 | 4 screws | Faulty 4（輕度鬆動）|

### CNN 模型架構

```
Input: (105, 1)  ← 105 維特徵向量 reshape 為 1D 序列
│
├── Conv1D(filters=16, kernel=3, padding='same', activation='relu')
├── Conv1D(filters=16, kernel=3, activation='relu')  + MaxPooling1D(pool_size=2)
├── Conv1D(filters=16, kernel=3, activation='relu')  + MaxPooling1D(pool_size=2)
├── Conv1D(filters=16, kernel=3, activation='relu')  + MaxPooling1D(pool_size=2)
│
├── Flatten()  →  176 維中間特徵（供 Step 4/5 使用）
├── Dense(16, activation='relu')
├── Dropout(rate=0.3)
└── Dense(5, activation='softmax')   # Step 6 重訓練時改為 10
```

> `Flatten` 層的 176 維輸出作為**無監督特徵空間**，供 Step 4/5 的異常偵測使用。

### 訓練設定

| 超參數 | 值 |
|--------|-----|
| 最佳化器 | Adam（lr=1e-4）|
| 損失函數 | Sparse Categorical Crossentropy |
| 最大訓練輪數 | 100 |
| 早停（EarlyStopping） | patience=10（監控驗證集損失）|
| Batch Size | 32 |
| 資料分割 | 訓練集 80% / 測試集 20%（分層抽樣）|

### 訓練流程（Notebook 結構）

```
1. [Bootstrap]  初始化 logger + tee 輸出
2. [設定]      匯入套件 + GPU 設定（gpu_utils）
3. [載入資料]  從 myfeature/ 載入乾淨特徵 CSV
4. [標籤編碼]  螺絲字串 → 整數標籤（8screws→0, 1screw→1, ...）
5. [分割資料]  train_test_split（stratify=True）
6. [標準化]    RobustScaler fit on train → transform train + test
7. [建模]      建立 CNN 模型（上述架構）
8. [訓練]      model.fit + EarlyStopping callback
9. [評估]      混淆矩陣 + 準確率 + 損失曲線
10.[儲存]      model.save('data/Step-*/model/CNN_*.keras')
```

### 模型變體說明

27 個模型對應不同的資料組合與訓練策略，詳見[模型編號系統](#模型編號系統)。

---

## Step 4：未知故障偵測

**檔案：** `Step4_Model_{1..27}_Detecting.ipynb`（×27）

**輸入：** Step 3 訓練的 `.keras` 模型 + 未知螺絲配置（5-7 screws、3_14、4_146）
**輸出：** 叢集距離分布圖、異常判定結果

### 核心問題

已知故障類別（0-4）訓練的 CNN 無法直接識別未知故障（5-9）。Step 4 利用 CNN 的**中間層特徵**，透過無監督學習判斷：

> **「這筆資料是否屬於模型已知的故障模式？」**

### 偵測流程

```
階段 A：訓練資料的特徵空間建立
─────────────────────────────────
1. 載入 Step 3 訓練完的 CNN 模型
2. 建立特徵萃取模型：Input → Flatten 層輸出（176 維）
3. 對 5 類訓練資料萃取 Flatten 特徵
4. 執行 HDBSCAN 叢集（將訓練特徵分成有意義的叢集）
5. 計算每個訓練樣本到其叢集中心的馬氏距離（Mahalanobis Distance）
6. 設定閾值 = 訓練距離的 第 95 百分位數

階段 B：對未知資料進行偵測
─────────────────────────────────
1. 對每批未知資料（5-7 screws 等）萃取 Flatten 特徵
2. 以 HDBSCAN 叢集
3. 計算叢集中心到最近已知叢集中心的馬氏距離
4. 比較距離與閾值：
   - 距離 > 閾值 → 判定為「Unknown」（未知故障）
   - 距離 ≤ 閾值 → 歸入最近的已知故障類別
```

### HDBSCAN 參數

| 參數 | 值 | 說明 |
|------|----|------|
| `min_cluster_size` | 25 | 叢集最少需包含 25 個樣本 |
| `min_samples` | 3 | 核心點判定所需的鄰近樣本數 |
| `cluster_selection_method` | `'leaf'` 或 `'eom'` | 叢集選取策略 |

### 馬氏距離閾值

```python
threshold = np.percentile(train_distances, 95)
# 95% 的訓練樣本距離 ≤ 閾值 → 超過此值視為異常
```

調整百分位數的影響：

| 百分位數 | 影響 |
|----------|------|
| 提高（e.g. 99%）| 降低誤報，但可能遺漏真實未知故障 |
| 降低（e.g. 90%）| 更敏感地偵測未知，但誤報增加 |

### 取樣限制

| 參數 | 值 |
|------|----|
| 每類螺絲配置取樣上限 | 60 筆 |
| 批次最大樣本數 | 450 筆（= 7.5 × 60）|

### 輸出視覺化

- 長條圖：各未知螺絲配置的叢集中心距離 vs. 閾值
- 顏色標示：超過閾值（紅色）= Unknown，未超過（藍色）= 歸入已知類別

---

## Step 5：隨機取樣偵測驗證

**檔案：** `Step5_Model_{1..27}_Random_Detecting.ipynb`（×27）

**目的：** 驗證 Step 4 偵測結果的**強健性與穩定性**

### 與 Step 4 的差異

Step 4 使用固定批次資料進行偵測；Step 5 則對相同資料集進行**多次隨機取樣**，測試不同批次組合下的偵測一致性：

```
重複 N 次：
  1. 隨機取樣 K 筆未知資料（每次取不同子集）
  2. 執行 HDBSCAN + 馬氏距離偵測
  3. 記錄各批次的偵測結果（Unknown/Known 比例）

統計分析：
  - 計算各配置被判定為 Unknown 的比例（平均值 ± 標準差）
  - 若比例穩定 → 偵測結果具強健性
  - 若比例波動大 → 需重新檢視 Step 3 模型或閾值設定
```

---

## Step 6：模型重訓練

**檔案：** `Step6_Model_{1..27}_Retrain.ipynb`（×27）

**輸入：** 5 類已知故障資料 + Step 4/5 確認的未知故障資料
**輸出：** 重訓練的 10 類 `.keras` 模型

### 目的

當 Step 4/5 確認某個螺絲配置確實是新型故障後，將其**納入訓練集**，擴充模型的已知類別：

```
原始已知（5 類）  +  新確認故障（5 類）  →  重訓練 10 類 CNN
```

### 新增的 10 類別定義

| 類別 | 螺絲配置 | 語意 |
|------|----------|------|
| 0 | 8 screws | Healthy |
| 1 | 1 screw | Faulty 1 |
| 2 | 2 screws | Faulty 2 |
| 3 | 3 screws | Faulty 3 |
| 4 | 4 screws | Faulty 4 |
| 5 | 5 screws | New Faulty 1 |
| 6 | 6 screws | New Faulty 2 |
| 7 | 7 screws | New Faulty 3 |
| 8 | 3_14 screws | New Faulty 4 |
| 9 | 4_146 screws | New Faulty 5 |

### 重訓練策略

目前採用**從頭重訓練**（from scratch），不使用 Fine-tuning：

```
架構修改：最後一層 Dense(5, softmax) → Dense(10, softmax)
訓練配置：與 Step 3 相同（Adam + EarlyStopping + Batch=32）
資料合併：合併原始已知類別資料 + 新確認的未知類別資料
```

> 重訓練完成後，新模型可回到 Step 4 使用，對下一批未知資料進行偵測（持續學習迴圈）。

---

## 附加功能：健康度退化建模

**檔案：** `T1_T2_T3.ipynb`

**目的：** 模擬並預測馬達從健康到失效的**漸進式退化過程**，用於預防性維護排程。

### 生命週期三階段定義

| 階段 | 健康指標（HI）範圍 | 顏色 | 物理意義 |
|------|-------------------|------|----------|
| T1 | 1.0 → 0.7 | 綠色 | 健康期（新機器）|
| T2 | 0.7 → 0.3 | 灰色 | 老化期（性能下降）|
| T3 | 0.3 → 0.0 | 紅色 | 即將失效期 |

### 建模方法

```python
# 特徵：105 維特徵向量（使用健康狀態資料）
# 目標：健康指標（HI），從 1.0 線性衰減至 0.0

model = MLPRegressor(
    hidden_layer_sizes=(32, 32),
    activation='relu',
    solver='adam',
    max_iter=500
)
model.fit(X_train_health, y_HI_train)
```

### 視覺化輸出

- X 軸：量測序號（時間順序）
- Y 軸：健康指標（0.0 ~ 1.0）
- 實線：原始預測 HI
- 虛線：60 點移動平均（平滑曲線）
- 顏色分段：綠（T1）→ 灰（T2）→ 紅（T3）

---

## 基礎設施模組

### `logger.py` — 日誌框架

所有腳本與 Notebook 共用此模組，提供統一的日誌管理。

#### 主要類別與函式

**`RunPaths`（dataclass）**

每次執行時自動建立隔離的目錄：

```python
RunPaths(
    program_name = "Step3_Model_1",
    timestamp    = "2026-05-07-13-51-09",
    logs_dir     = Path("logs/Step3_Model_1_2026-05-07-13-51-09/"),
    output_dir   = Path("output/Step3_Model_1_2026-05-07-13-51-09/"),
    log_file     = Path("logs/Step3_Model_1_2026-05-07-13-51-09/program.log"),
)
```

**`SimpleFileLogger`**

輕量級文件日誌，不依賴 loguru 背景執行緒（避免 Jupyter 環境的遞迴問題）：

```python
log, paths = setup_logger("Step3_Model_1.ipynb")
log.info("開始訓練，epoch={}", epochs)
log.warning("資料量不足：{}", count)
log.error("模型載入失敗：{}", e)
```

日誌格式：

```
2026-05-07 13:51:09 | INFO  | Logger initialized
2026-05-07 13:51:09 | INFO  | log_file=logs/program_2026-05-07-13-51-09/program.log
2026-05-07 13:51:09 | ERROR | 某個錯誤訊息
```

**`_TeeToFileStream`**（Notebook 專用）

同時寫入終端機與日誌檔，並過濾 Keras 進度條噪音：

```python
# Notebook 頂部 bootstrap cell：
with tee_std_to_file(log_file):
    # 以下所有 print / stdout / stderr 輸出同步寫入 program.log
    model.fit(...)
```

過濾規則：
- 保留：`Epoch x/y` 標頭
- 保留：每 Epoch 最後一個 step 的 loss/accuracy 摘要
- 丟棄：中間進度條行（含 `━━━━━━━━` 等符號）
- 丟棄：ANSI 控制碼（顏色字元）

**`save_plot()`**

自動儲存 matplotlib 圖表，使用遞增編號：

```python
save_plot(plt, log, run_paths)
# → output/program_2026-05-07-13-51-09/plot_000.png
# → output/program_2026-05-07-13-51-09/plot_001.png
```

#### Notebook Bootstrap Cell

每個 Notebook 早期 cell（自動維護）：

```python
# --- logging bootstrap (auto-added) ---
import importlib
import logger as _logger_mod
_logger_mod = importlib.reload(_logger_mod)
save_plot = _logger_mod.save_plot
setup_logger = _logger_mod.setup_logger
tee_std_to_file = _logger_mod.tee_std_to_file

LOG, RUN_PATHS = setup_logger('notebook', console=False)
_tee_ctx = tee_std_to_file(RUN_PATHS.log_file)
_tee_ctx.__enter__()
import atexit
atexit.register(_tee_ctx.__exit__, None, None, None)
# ... (自動儲存圖表與 GPU 資源釋放邏輯略)
# --- end logging bootstrap ---
```

---

### `gpu_utils.py` — GPU/CPU 自動管理

```python
from gpu_utils import device_scope, DEVICE, gpu_count, is_gpu

print(f"使用裝置：{DEVICE}")   # → /GPU:0 或 /CPU:0
print(f"GPU 數量：{gpu_count()}")

with device_scope():
    model = build_cnn_model()
    model.fit(X_train, y_train, ...)
```

#### 內部機制

```python
def _configure():
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)  # 動態記憶體分配
        return "/GPU:0", gpus
    return "/CPU:0", []

DEVICE, _gpus = _configure()
```

- **動態記憶體分配（`set_memory_growth=True`）**：避免 TensorFlow 一次佔用全部 GPU 記憶體，允許多個程序共用 GPU。
- **自動回退**：無 GPU 時自動使用 CPU，程式碼不需修改。

---

## 模型編號系統

45 個 Step3 Notebook（Model 1 ~ 27，含 OneStage / TwoStage 變體）涵蓋不同的資料組合與診斷策略：

| 編號範圍 | 類型 | 說明 |
|----------|------|------|
| 1 ~ 9 | 基礎版本 | 不同轉速 / 馬達組合的標準訓練 |
| 10 ~ 27（OneStage）| OneStage 變體 | 一階段遷移學習（凍結前半層，以不同馬達資料 Fine-tune）|
| 10 ~ 27（TwoStage）| TwoStage 變體 | 兩階段遷移學習（OneStage 後再以第三組馬達資料 Fine-tune）|

> 模型 10~27 各自同時存在 OneStage 與 TwoStage 兩個訓練版本，Step 4/5/6 的編號 10~27 可對應其中任一版本。

**重要：** 各步驟的 Notebook 編號必須對應，**不可混用**：

```
Step3_Model_5.ipynb  →  Step4_Model_5_Detecting.ipynb
                     →  Step5_Model_5_Random_Detecting.ipynb
                     →  Step6_Model_5_Retrain.ipynb
```

---

## 執行流程

### 完整執行步驟

```bash
# === Step 1：資料預處理（按轉速 × 批次執行）===
python Step1_Data_Preprocessing_save_6000_1.py
python Step1_Data_Preprocessing_save_6000_2.py
python Step1_Data_Preprocessing_save_6000_3.py
python Step1_Data_Preprocessing_save_8000_1.py
python Step1_Data_Preprocessing_save_8000_2.py
python Step1_Data_Preprocessing_save_8000_3.py
python Step1_Data_Preprocessing_save_11000_1.py
python Step1_Data_Preprocessing_save_11000_2.py
python Step1_Data_Preprocessing_save_11000_3.py

# 視覺化確認（可選）
python Step1_Data_Preprocessing_figure_6000_1.py  # 查看 6000 RPM 原始訊號

# === Step 2：特徵萃取 ===
python Step2_Feature_Extraction_6000_1.py
python Step2_Feature_Extraction_6000_2.py
python Step2_Feature_Extraction_6000_3.py
python Step2_Feature_Extraction_8000_1.py
python Step2_Feature_Extraction_8000_2.py
python Step2_Feature_Extraction_8000_3.py
python Step2_Feature_Extraction_11000_1.py
python Step2_Feature_Extraction_11000_2.py
python Step2_Feature_Extraction_11000_3.py

# === Step 3 ~ 6：依序開啟並執行對應 Jupyter Notebook ===
# 以 Model 1 為例：
#   1. 執行 Step3_Model_1.ipynb              → 訓練 CNN，儲存模型
#   2. 執行 Step4_Model_1_Detecting.ipynb    → 偵測未知故障
#   3. 執行 Step5_Model_1_Random_Detecting.ipynb   → 隨機取樣驗證
#   4. 執行 Step6_Model_1_Retrain.ipynb      → 重訓練 10 類模型
# 以 Model 10 為例（含遷移學習版本）：
#   1a. 執行 Step3_Model_10_OneStage.ipynb   → 一階段遷移學習
#   1b. 執行 Step3_Model_10_TwoStage.ipynb   → 兩階段遷移學習

# === 附加：健康度退化建模（獨立執行）===
# 執行 T1_T2_T3.ipynb
```

### 資料流摘要

```
原始 CSV（tab 分隔）
    ↓  Step 1（IQR 過濾 + 切割）
data/Step-*/csv/.../*_data.csv
    ↓  Step 2（統計 + FFT 特徵萃取）
data/Step-*/myfeature/.../*_feature_data_clean.csv  （105 維）
    ↓  Step 3（1D CNN 訓練）
data/Step-*/model/CNN_*.keras  （5 類模型）
    ↓  Step 4（HDBSCAN + 馬氏距離）
偵測結果：Unknown / Known 判定
    ↓  Step 6（從頭重訓練）
data/Step-*/model/CNN_*_retrained.keras  （10 類模型）
    ↓  回到 Step 4 繼續下一輪
```

### 日誌與輸出

每次執行自動生成：

```
logs/
└── {program_name}_{YYYY-MM-DD-HH-MM-SS}/
    └── program.log       ← 完整執行日誌

output/
└── {program_name}_{YYYY-MM-DD-HH-MM-SS}/
    ├── plot_000.png      ← 混淆矩陣
    ├── plot_001.png      ← 損失曲線
    ├── plot_002.png      ← 準確率曲線
    └── ...
```

---

## 注意事項與限制

### 固定約束（不可更動）

| 約束 | 值 | 原因 |
|------|-----|------|
| 取樣率 Fs | **10,000 Hz** | 所有腳本硬編碼，修改會導致 FFT 基頻錯誤 |
| 特徵維度 | **105 維** | 已訓練模型的輸入層固定，修改需重訓練所有模型 |
| 模型輸入形狀 | **(105, 1)** | CNN 結構固定，不可更改 |
| Notebook 編號對應 | Step3 N ↔ Step4 N | 不同編號使用不同資料組合，混用會導致錯誤 |

### 已知限制

1. **HDBSCAN 隨機性**：叢集結果在不同執行間可能略有差異，建議固定 `random_state`。

2. **馬氏距離奇異矩陣**：若訓練特徵高度共線（接近零行列式），馬氏距離計算會失敗。解決方式：先以 PCA 降維後再計算。

3. **Step 6 從頭重訓練**：未使用 Fine-tuning，當資料量大時訓練時間較長（可考慮遷移學習優化）。

4. **路徑相對性**：所有腳本使用相對路徑，**必須在專案根目錄（`.../Ancestor/`）下執行**。

5. **資料量平衡**：各螺絲配置的資料量不一致時，訓練集可能不均衡，建議使用分層抽樣（已實作）或加入 class_weight。

### 新增實驗配置指引

#### 新增轉速

1. 在 Step 1 新增 `Step1_Data_Preprocessing_save_{NewRPM}_*.py`，調整 IQR 參數與目錄路徑
2. 在 Step 2 新增 `Step2_Feature_Extraction_{NewRPM}_*.py`，設定對應的 `base_freq`（Hz = RPM/60）
3. 以新資料執行 Step 3 建立新模型編號

#### 新增故障類型

- **未知故障**（不知是否為新型）：將原始訊號放入對應目錄 → 執行 Step 1/2 → 執行 Step 4/5 偵測 → 若確認為新故障 → 執行 Step 6 重訓練
- **已知故障**（明確定義）：修改 Step 3 中輸出層類別數 → 加入新類別資料 → 重新訓練

#### 調整偵測靈敏度

```python
# Step 4 Notebook 中調整此行：
threshold = np.percentile(train_distances, 95)  # 95 可調整為 90~99
```

---

## 文件索引

| 文件 | 說明 |
|------|------|
| [Step 1 詳細說明](docs/Step1_Data_Preprocessing.md) | IQR 過濾、切割演算法、CSV 格式 |
| [Step 2 詳細說明](docs/Step2_Feature_Extraction.md) | 105 維特徵完整定義與公式 |
| [Step 3 詳細說明](docs/Step3_Model_Training.md) | CNN 架構、訓練設定、模型評估 |
| [Step 4 詳細說明](docs/Step4_Unknown_Detection.md) | HDBSCAN 原理、馬氏距離計算、閾值選擇 |
| [Step 5 詳細說明](docs/Step5_Random_Sampling_Detection.md) | 隨機批次驗證方法與解讀 |
| [Step 6 詳細說明](docs/Step6_Model_Retraining.md) | 增量學習流程、資料合併策略 |
| [TensorFlow & GPU 指南](docs/Tensorflow.md) | CUDA 安裝、記憶體管理、疑難排解 |
| [Agent 指引](AGENT.md) | AI 自動化工具的操作慣例與約束 |
