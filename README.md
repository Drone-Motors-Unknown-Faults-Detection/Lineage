# Lineage — 馬達故障診斷與持續學習系統

本專案實作了一套完整的旋轉機械（馬達）**故障診斷與預後健康管理（PHM）** 流程，核心亮點在於結合深度學習分類與無監督異常偵測，實現對**未知故障的自動發現與持續學習**能力（開放集故障診斷 / Open-Set Fault Diagnosis）。

> ### 與 Ancestor 的關係
>
> 本專案自 [`Ancestor`](https://github.com/Drone-Motors-Unknown-Faults-Detection/Ancestor) 分出，**完整保留其 git 歷史**——包含論文原始碼的兩次上傳（`1ea243f`、`5b0e8d6`）以及後續所有修正。
>
> 分家的原因是程式碼已與論文原始版本有實質差異，且後續研究方向也將與原論文分歧。逐項差異對照見 [Differents.md](Differents.md)。
>
> | | |
> |---|---|
> | **Ancestor** | 論文版本的存檔。**issue 與 PR 只存在於該處**（#1~#60 記錄了每一個缺陷的成因、修正與驗證）|
> | **Lineage**（本專案） | 後續研究的主線 |
>
> git 歷史可在兩邊互相對照，但 issue 討論串無法隨 git 複製，需要查閱時請回到 Ancestor。

---

## 目錄

1. [系統架構](#系統架構)
2. [目錄結構](#目錄結構)
3. [環境設定](#環境設定)
4. [資料說明](#資料說明)
5. [Step 1：資料預處理](#step-1資料預處理)
6. [Step 2：特徵萃取](#step-2特徵萃取)
7. [Step 3：模型訓練](#step-3模型訓練)
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
            └─ Step 3：模型訓練（1D CNN / ResNet / VGG16，5 類已知故障）
                 ├─ Step 4：未知故障偵測（HDBSCAN 叢集 + 馬氏距離閾值）
                 ├─ Step 5：隨機取樣偵測驗證（多批次強健性測試）
                 └─ Step 6：模型重訓練（5 類 → 10 類增量學習）
                       └─ 回到 Step 4（持續迭代）

附加功能：T1_T2_T3.ipynb — 馬達生命週期健康度退化曲線
```

---

## 目錄結構

```
/home/albert/Lineage/
│
├── 核心腳本
│   ├── Step1_Data_Preprocessing_figure_{6000,8000,11000}.py  # 原始訊號視覺化（×3）
│   ├── Step1_Data_Preprocessing_save_*.py    # 資料預處理與儲存（×9）
│   └── Step2_Feature_Extraction_*.py         # 105 維特徵萃取（×9）
│
├── 批次執行腳本
│   ├── Step1_Data_Preprocessing.sh           # 依序跑完 Step1 的 12 支腳本
│   ├── Step2_Feature_Extraction.sh           # 依序跑完 Step2 的 9 支腳本
│   ├── Step3_Model.sh                        # 依序跑完 45 個 Step3 Notebook
│   ├── Step4_Model_Detecting.sh              # ×27
│   ├── Step5_Model_Random_Detecting.sh       # ×27
│   └── Step6_Model_Retrain.sh                # ×27
│
├── Jupyter Notebooks
│   ├── Step3_Model_{01..09}.ipynb                       # 從頭訓練，基礎版本（×9）
│   ├── Step3_Model_{10..27}_OneStage.ipynb              # OneStage 遷移學習（×18）
│   ├── Step3_Model_{10..27}_TwoStage.ipynb              # TwoStage 遷移學習（×18）
│   ├── Step4_Model_{01..27}_Detecting.ipynb             # 未知故障偵測（×27）
│   ├── Step5_Model_{01..27}_Random_Detecting.ipynb      # 隨機取樣驗證（×27）
│   ├── Step6_Model_{01..27}_Retrain.ipynb               # 模型重訓練（×27）
│   ├── T1_T2_T3.ipynb                                   # 健康度退化建模
│   └── GPU-Test.ipynb                                   # GPU / CUDA 環境驗證
│
├── scripts/                                  # 基礎設施模組（以套件形式匯入）
│   ├── logger.py                             # 自訂日誌框架
│   ├── gpu_utils.py                          # GPU/CPU 自動選擇模組
│   ├── notebook_bootstrap.py                 # Notebook 共用初始化（日誌 + 自動存圖）
│   ├── model_utils.py                        # 依架構取特徵層（Step 4/5 用）
│   ├── train_guard.py                        # 訓練前後的健全性斷言（Step 3/6 用）
│   └── render_docs.py                        # 由 .md 產生 docs 的 .html
│
├── pyproject.toml                            # 套件依賴與 Python 版本
├── build_uv.sh / build_venv.sh               # 建立 venv 的兩種方式
│
├── docs/                                     # 各步驟詳細說明文件
│   ├── Step1_Data_Preprocessing.md
│   ├── Step2_Feature_Extraction.md
│   ├── Step3_Model_Training.md
│   ├── Step4_Unknown_Detection.md
│   ├── Step5_Random_Sampling_Detection.md
│   ├── Step6_Model_Retraining.md
│   ├── OpenSet_Recognition.md                # 開放集辨識取代馬氏距離的技術評估
│   ├── Model_Choice_Analysis.md              # 換模型／調參數的實測分析
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

> 所有腳本與 Notebook 皆以**專案根目錄**為執行基準（即 `.../Lineage/`），資料統一存放於 `data/` 目錄。

---

## 環境設定

### 依賴管理

套件與 Python 版本統一定義在 `pyproject.toml`（Python 釘在 **3.10.19**），依平台分成兩組 optional dependencies：

| extra | 內容 |
|-------|------|
| `linux` | `tensorflow[and-cuda]`（GPU 版，含 CUDA） |
| `mac` | `tensorflow==2.18.0` + `tensorflow-metal==1.2.0` |

共用依賴：`numpy`、`pandas`、`matplotlib`、`scipy`、`scikit-learn`、`seaborn`、`hdbscan`（階層式 DBSCAN）、`natsort`（檔案自然排序）、`absl-py`、`jupyter`、`loguru`、`markdown`（產生文件 HTML）。

### 建立環境

```bash
./build_uv.sh        # 以 uv 建立 venv（Linux，安裝 .[linux]）
./build_uv_mac.sh    # 以 uv 建立 venv（macOS，安裝 .[mac]）
./build_venv.sh      # 以標準 venv 建立
```

三者都會在專案根目錄產生 `venv/`。所有批次執行腳本都直接使用 `venv/bin/python` 與 `venv/bin/jupyter`，不需要先 activate。

### GPU 環境（目前實驗機）

| 項目 | 版本 |
|------|------|
| Python | 3.10.19 |
| TensorFlow | 2.21.0 |
| CUDA（TF 建置） | 12.5.1 |
| cuDNN | 9 |
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
│   │               ├── {Motor}_Group_feature_data.csv        # 萃取結果（Step 3/6 訓練用）
│   │               └── {Motor}_Group_feature_data_clean.csv  # IQR 過濾後（Step 4/5 用）
│   └── model/
│       └── {CNN|ResNet|VGG16}_*.keras   # 訓練完成的模型（Step 3 / Step 6 輸出）
```

---

## Step 1：資料預處理

**檔案：** `Step1_Data_Preprocessing_save_*.py`（×9）、`Step1_Data_Preprocessing_figure_{6000,8000,11000}.py`（×3，僅視覺化）

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

每個螺絲配置的目錄下各產生兩個檔案：

```
{Motor}_Group_feature_data.csv       ← 萃取結果，Step 3 / Step 6 訓練用
{Motor}_Group_feature_data_clean.csv ← 再以 IQR 逐列過濾，Step 4 / Step 5 用
```

每列 = 1 個 1 秒片段的 105 維特徵向量。

`_clean` 版本的過濾規則：**任一維特徵落在 `[Q1 - 1.5*IQR, Q3 + 1.5*IQR]` 之外，整列捨棄**。

```python
def drop_feature_outliers(df, scale=1.5):
    Q1 = df.quantile(0.25)
    Q3 = df.quantile(0.75)
    IQR = Q3 - Q1
    return df[((df >= Q1 - scale * IQR) & (df <= Q3 + scale * IQR)).all(axis=1)]
```

> `scale=1.5` 比 Step 1 訊號層用的 `3.0` 嚴格得多，實測約會濾掉一半的列。Step 4/5 的 HDBSCAN 叢集與馬氏距離對離群值敏感，因此另外準備這份乾淨版本；Step 3/6 的訓練仍讀未過濾的版本。

---

## Step 3：模型訓練

**檔案：** `Step3_Model_{01..09}.ipynb`（×9，從頭訓練）、`Step3_Model_{10..27}_OneStage.ipynb`（×18）、`Step3_Model_{10..27}_TwoStage.ipynb`（×18），共 45 個

**輸入：** `data/Step-{1|2|3}/myfeature/` 的 105 維特徵 CSV
**輸出：** `data/Step-{1|2|3}/model/{CNN|ResNet|VGG16}_*.keras`

### 問題定義

以**5 類已知故障**進行監督式分類：

| 類別 | 螺絲配置 | 物理意義 |
|------|----------|----------|
| 0 | 8 screws | Healthy（健康，基準狀態）|
| 1 | 1 screw | Faulty 1（最嚴重鬆動）|
| 2 | 2 screws | Faulty 2 |
| 3 | 3 screws | Faulty 3 |
| 4 | 4 screws | Faulty 4（輕度鬆動）|

### 三種模型架構

每個轉速 / 馬達組合都會分別以三種架構各訓練一次（論文中稱 CNN_11 Layers、CNN_Res、CNN_VGG）：

| 架構 | 建構函式 | 特點 |
|------|----------|------|
| CNN | `build_cnn_model()` | 4 層 Conv1D 堆疊，最精簡 |
| ResNet | `build_resnet_model()` | 加入殘差連接，緩解深層退化 |
| VGG16 | `build_vgg16_model()` | VGG 風格的連續卷積區塊 |

三者的輸入（`(105, 1)`）、輸出（5 類 softmax）、訓練設定完全一致，只有中間的特徵萃取結構不同。

#### CNN 架構（基準）

```
Input: (105, 1)  ← 105 維特徵向量 reshape 為 1D 序列
│
├── Conv1D(filters=16, kernel=3, padding='same', activation='relu')
├── Conv1D(filters=16, kernel=3, activation='relu')  + MaxPooling1D(pool_size=2)
├── Conv1D(filters=16, kernel=3, activation='relu')  + MaxPooling1D(pool_size=2)
├── Conv1D(filters=16, kernel=3, activation='relu')  + MaxPooling1D(pool_size=2)
│
├── Flatten()  →  176 維中間特徵（供 Step 4/5 使用；ResNet 改用 GAP 得 128 維、VGG16 得 48 維）
├── Dense(16, activation='relu')
├── Dropout(rate=0.3)
└── Dense(5, activation='softmax')   # Step 6 重訓練時改為 10
```

> CNN 的 `Flatten` 層輸出（176 維）作為**無監督特徵空間**，供 Step 4/5 的異常偵測使用。
> ResNet 沒有 Flatten 層，改以 `global_average_pooling1d`（128 維）；VGG16 的 Flatten 為 48 維。
> Step 4/5 以 `scripts/model_utils.py` 的 `get_feature_layer()` 自動判別。

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
10.[儲存]      model.save('data/Step-*/model/{ARCH}_*.keras')
```

### 模型變體說明

45 個 Notebook 對應「馬達時期 × 轉速 × 架構」的完整交叉組合，以及 OneStage / TwoStage 兩種遷移策略，詳見[模型編號系統](#模型編號系統)。

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
2. 建立特徵萃取模型：Input → 中間層輸出（CNN 176 / ResNet 128 / VGG16 48 維）
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

> 這個機制有三個結構性弱點——單一全域共變異數、百分位數不是機率、判定粒度是叢集而非樣本。
> 替代方案（OpenMax、能量分數、證據深度學習等）的評估見
> [docs/OpenSet_Recognition.md](docs/OpenSet_Recognition.md)。

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

### `scripts/logger.py` — 日誌框架

所有腳本與 Notebook 共用此模組，提供統一的日誌管理。

#### 主要類別與函式

**`RunPaths`（dataclass）**

每次執行時自動建立隔離的目錄：

```python
RunPaths(
    program_name = "Step3_Model_01",
    timestamp    = "2026-08-05-14-30-35",
    logs_dir     = Path("logs/Step3_Model_01/"),
    output_dir   = Path("output/Step3_Model_01/2026-08-05-14-30-35/"),
    log_file     = Path("logs/Step3_Model_01/2026-08-05-14-30-35.log"),
)
```

**`SimpleFileLogger`**

輕量級文件日誌，不依賴 loguru 背景執行緒（避免 Jupyter 環境的遞迴問題）：

```python
log, paths = setup_logger("Step3_Model_01.ipynb")
log.info("開始訓練，epoch={}", epochs)
log.warning("資料量不足：{}", count)
log.error("模型載入失敗：{}", e)
```

日誌格式：

```
2026-08-05 14:30:35 | INFO  | Logger initialized
2026-08-05 14:30:35 | INFO  | log_file=logs/Step3_Model_01/2026-08-05-14-30-35.log
2026-08-05 14:30:35 | ERROR | 某個錯誤訊息
```

**`_TeeToFileStream`**（Notebook 專用）

同時寫入終端機與日誌檔，並過濾 Keras 進度條噪音：

```python
# Notebook 頂部 bootstrap cell：
with tee_std_to_file(log_file):
    # 以下所有 print / stdout / stderr 輸出同步寫入該次執行的 .log
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

全部 128 個 Notebook 的第一個 cell 都是這三行：

```python
# --- logging bootstrap (auto-added) ---
from scripts.notebook_bootstrap import bootstrap

LOG, RUN_PATHS = bootstrap()
# --- end logging bootstrap ---
```

`bootstrap()` 一次做完四件事：建立本次執行的 logger、把 stdout/stderr 導向 log、
註冊 TensorFlow 的資源釋放，以及攔截 `plt.show()` 自動存圖。

> 這段先前是 56 行、複製在每個 Notebook 裡的。要修一個 bug 就得改 128 個地方，
> 因此收斂到 `scripts/notebook_bootstrap.py` 統一維護。

---

### `scripts/gpu_utils.py` — GPU/CPU 自動管理

```python
from scripts.gpu_utils import device_scope, DEVICE, gpu_count, is_gpu

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

### `scripts/model_utils.py` — 依架構取特徵層

Step 4/5 需要模型的中間層輸出作為無監督特徵空間，但三種架構的特徵層並不同名：

```python
from scripts.model_utils import get_feature_layer

feat_model = Model(inputs=cnn.input, outputs=get_feature_layer(cnn).output)
```

| 架構 | 取到的層 | 維度 |
|------|----------|------|
| CNN | `flatten` | 176 |
| ResNet | `global_average_pooling1d` | 128 |
| VGG16 | `flatten` | 48 |

依 `FEATURE_LAYER_CANDIDATES` 的順序尋找，都找不到時退回輸出層的前一層。

---

### `scripts/train_guard.py` — 訓練健全性斷言

訓練若因輸入含 NaN 而失敗，並不會拋出例外——模型照樣存檔、Notebook 照樣「成功」結束，
唯一的線索是準確率剛好等於 `1 / 類別數`。這個模組把那種靜默失敗變成明確的例外：

```python
from scripts.train_guard import assert_finite_inputs, assert_model_learned

assert_finite_inputs(X_train=X_train, X_test=X_test)
# ... 訓練 ...
assert_model_learned(history, results, len(np.unique(y_train_screws)))
```

| 函式 | 檢查內容 |
|------|----------|
| `assert_finite_inputs` | 輸入不得含 NaN/inf，錯誤訊息會指出前幾個出問題的 `(列, 欄)` |
| `assert_model_learned` | 訓練與評估的 loss 必須有限；測試準確率不得落在 `1/類別數 + margin` 以內 |

Step 3 的 45 個與 Step 6 的 27 個 Notebook 都已插入這兩道檢查。

---

## 模型編號系統

Model 01 ~ 27 是**三個維度的完整交叉組合**：

```
編號 N  →  馬達時期 = 01-09:T1 / 10-18:T2 / 19-27:T3
           轉速     = ((N-1) // 3) % 3  →  0:8000rpm  1:6000rpm  2:11000rpm
           架構     = (N-1) % 3         →  0:CNN  1:ResNet  2:VGG16
```

論文中三種架構分別稱為 CNN_11 Layers、CNN_Res、CNN_VGG。

### 資料夾 T 碼與模型檔名字母碼是反的

這是最容易踩到的一點——**資料目錄用 `T1/T2/T3`，模型檔名卻用 `C/B/A`，順序相反**：

| 資料目錄 | 馬達時期 | 模型檔名字母 |
|----------|----------|--------------|
| `data/Step-1/` | T1（新機）| `*_C*.keras` |
| `data/Step-2/` | T2（老化）| `*_B*.keras` |
| `data/Step-3/` | T3（衰退）| `*_A*.keras` |

### 完整對照表

| Model | 資料 | 轉速 | 架構 | Step3 產出 |
|-------|------|------|------|-----------|
| 01 / 02 / 03 | T1 | 8000 | CNN / ResNet / VGG16 | `{ARCH}_C8000.keras` |
| 04 / 05 / 06 | T1 | 6000 | CNN / ResNet / VGG16 | `{ARCH}_C6000_1.keras` |
| 07 / 08 / 09 | T1 | 11000 | CNN / ResNet / VGG16 | `{ARCH}_C11000_1.keras` |
| 10 ~ 12 | T2 | 8000 | CNN / ResNet / VGG16 | `{ARCH}_B8000{_1}.keras` |
| 13 ~ 15 | T2 | 6000 | CNN / ResNet / VGG16 | `{ARCH}_B6000{_1}.keras` |
| 16 ~ 18 | T2 | 11000 | CNN / ResNet / VGG16 | `{ARCH}_B11000{_1}.keras` |
| 19 ~ 21 | T3 | 8000 | CNN / ResNet / VGG16 | `{ARCH}_A8000{_1}.keras` |
| 22 ~ 24 | T3 | 6000 | CNN / ResNet / VGG16 | `{ARCH}_A6000{_1}.keras` |
| 25 ~ 27 | T3 | 11000 | CNN / ResNet / VGG16 | `{ARCH}_A11000{_1}.keras` |

> `_1` 後綴代表 OneStage 版本；TwoStage 版本不帶後綴。

### 訓練來源鏈

**只有 Model 01 ~ 03 是從頭訓練的**，產出 `CNN_C8000` / `ResNet_C8000` / `VGG16_C8000`——這三個是全專案唯一的 baseline，後面 24 組全部由此遷移而來（凍結前 50% 層 Fine-tune）。

| 變體 | 載入的來源模型 |
|------|---------------|
| Model 04 ~ 09 | `{ARCH}_C8000.keras`（同馬達、不同轉速）|
| OneStage（10 ~ 27）| 一律 `{ARCH}_C8000.keras` |
| TwoStage（10~12、19~21，8000rpm 組）| 同樣是 `{ARCH}_C8000.keras` |
| TwoStage（13~18、22~27，6000/11000rpm 組）| 同馬達的 8000rpm 模型（`{ARCH}_B8000` / `{ARCH}_A8000`）|

> 注意：**8000rpm 的 TwoStage 其實與 OneStage 載入同一個模型**，兩者只差在存檔名。真正跑滿兩階段的只有 6000/11000rpm 那 12 組。

**Step 4/5 一律載入 OneStage 產物（帶 `_1` 的檔案）。** Step 6 不載入既有模型，直接以 10 類從頭重訓練。

### 編號必須對應

```
Step3_Model_05.ipynb  →  Step4_Model_05_Detecting.ipynb
                      →  Step5_Model_05_Random_Detecting.ipynb
                      →  Step6_Model_05_Retrain.ipynb
```

---

## 執行流程

### 批次執行（建議）

各步驟都有對應的 `.sh` 入口，會依序跑完該步驟的所有腳本 / Notebook，並直接使用 `venv/`，不需要先 activate：

```bash
./Step1_Data_Preprocessing.sh      # 12 支腳本（3 支 figure + 9 支 save）
./Step2_Feature_Extraction.sh      # 9 支腳本
./Step3_Model.sh                   # 45 個 Notebook
./Step4_Model_Detecting.sh         # 27 個 Notebook
./Step5_Model_Random_Detecting.sh  # 27 個 Notebook
./Step6_Model_Retrain.sh           # 27 個 Notebook
```

Step 1 另有按轉速拆分的版本，方便只重跑其中一組：

```bash
./Step1_Data_Preprocessing_6000.sh
./Step1_Data_Preprocessing_8000.sh
./Step1_Data_Preprocessing_11000.sh
```

### 單獨執行

```bash
venv/bin/python Step2_Feature_Extraction_8000_1.py

# Notebook 須帶上 JUPYTER_NOTEBOOK_NAME，logger 才能取到正確的程式名稱
JUPYTER_NOTEBOOK_NAME="Step3_Model_01.ipynb" venv/bin/jupyter execute Step3_Model_01.ipynb
```

單一模型的完整流程（以 Model 05 為例）：

```
Step3_Model_05.ipynb            → 訓練並儲存 ResNet_C6000_1.keras
Step4_Model_05_Detecting.ipynb  → 偵測未知故障
Step5_Model_05_Random_Detecting.ipynb → 隨機取樣驗證
Step6_Model_05_Retrain.ipynb    → 重訓練 10 類模型
```

### 資料流摘要

```
原始 CSV（tab 分隔）
    ↓  Step 1（IQR scale=3.0 過濾 + 切割成 1 秒段）
data/Step-*/csv/.../*_data.csv
    ↓  Step 2（統計 + FFT 特徵萃取，105 維）
data/Step-*/myfeature/.../*_Group_feature_data.csv        → Step 3 / Step 6 訓練用
data/Step-*/myfeature/.../*_Group_feature_data_clean.csv  → Step 4 / Step 5 用（IQR scale=1.5 逐列過濾）
    ↓  Step 3（1D CNN / ResNet / VGG16 訓練）
data/Step-*/model/{ARCH}_*.keras  （5 類模型）
    ↓  Step 4（HDBSCAN + 馬氏距離）
偵測結果：Unknown / Known 判定
    ↓  Step 6（10 類從頭重訓練）
data/Step-*/model/{ARCH}_{LETTER}{RPM}_retrained.keras  （10 類模型）
    ↓  回到 Step 4 繼續下一輪
```

### 日誌與輸出

每次執行自動生成（同一支程式的多次執行以時間戳區分）：

```
logs/
└── {program_name}/
    └── {YYYY-MM-DD-HH-MM-SS}.log    ← 完整執行日誌

output/
└── {program_name}/
    └── {YYYY-MM-DD-HH-MM-SS}/
        ├── plot_000.png              ← 依 plt.show() 的呼叫順序編號
        ├── plot_001.png
        └── ...
```

`logs/` 與 `output/` 都納入版控，執行紀錄會跟著 commit 一起保存。

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

4. **路徑相對性**：所有腳本使用相對路徑，**必須在專案根目錄（`.../Lineage/`）下執行**。

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
| [開放集辨識評估](docs/OpenSet_Recognition.md) | 現行馬氏距離閾值的三個弱點，以及 OpenMax、能量分數等五種替代方案 |
| [模型選擇分析](docs/Model_Choice_Analysis.md) | 固定馬氏距離流程下，換模型／調參數對準確率與偵測能力的實測分析 |
| [馬氏距離改善實驗](docs/Mahalanobis_Improvement.md) | Legacy、Ledoit–Wolf、OAS、MCD 的 18 模型真實資料比較與採用結論 |
| [TensorFlow & GPU 指南](docs/Tensorflow.md) | CUDA 安裝、記憶體管理、疑難排解 |
| [Agent 指引](AGENT.md) | AI 自動化工具的操作慣例與約束 |
| [與原始版本的差異](Differents.md) | 對照 `1ea243f` / `5b0e8d6` 兩個原始上傳版本，逐項說明改了什麼與為什麼 |

---

## 文件維護

`README.html` 與 `docs/*.html` 由對應的 Markdown 產生，改完 `.md` 後執行：

```bash
venv/bin/python scripts/render_docs.py           # 重新產生全部 HTML
venv/bin/python scripts/render_docs.py --check   # 只檢查是否過期（不寫檔，過期時回傳 1）
```

樣式來自 `scripts/templates/doc.css`，八份文件共用。
