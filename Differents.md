# 與原始版本的差異

本文比對目前程式碼與兩個原始上傳版本，逐項說明改了什麼、為什麼改、影響範圍。

## 比對基準

| Commit | 日期 | 檔案數 | 內容 |
|--------|------|--------|------|
| `1ea243f` | 2025-12-28 16:03 | 101 | Step 1 ~ Step 5 |
| `5b0e8d6` | 2025-12-28 16:05 | 152 | 追加 Step 6（27 個）、`T1_T2_T3.ipynb` 等 51 個檔案 |

兩者相隔 76 秒，是同一批上傳的前後兩次；`5b0e8d6` 完全包含 `1ea243f`，因此以 **`5b0e8d6` 為比對基準**。

目前版本（排除 `logs/`、`output/`、`data/`）共 193 個檔案。

---

## 一、檔案層面的變化

### 更名：146 個檔案

Notebook 原本使用空格與雙底線、編號不補零：

```
Step3_Model 1.ipynb                →  Step3_Model_01.ipynb
Step3_Model 10__OneStage.ipynb     →  Step3_Model_10_OneStage.ipynb
Step4_Model 1__Detecting.ipynb     →  Step4_Model_01_Detecting.ipynb
Step5_Model 1__Random_Detecting.ipynb → Step5_Model_01_Random_Detecting.ipynb
Step6_Model 1__Retrain.ipynb       →  Step6_Model_01_Retrain.ipynb
```

**為什麼改：** 檔名含空格在 shell 中需要額外引號，批次執行腳本容易出錯；編號不補零會讓 `Model 10` 排在 `Model 2` 前面。補零後 `ls` 與 glob 的順序即為執行順序。

### 合併：Step 1 視覺化腳本 6 支 → 3 支

```
Step1_Data_Preprocessing_figure_{6000,8000,11000}_{1,2}.py   （6 支）
                    ↓
Step1_Data_Preprocessing_figure_{6000,8000,11000}.py         （3 支）
```

`_1` 與 `_2` 兩支內容重複，只保留一支並去掉後綴。

### 新增：47 個檔案

| 類別 | 檔案 | 用途 |
|------|------|------|
| 批次執行 | `Step{1..6}*.sh`（9 支） | 依序跑完各步驟，取代手動逐一開啟 Notebook |
| 環境建置 | `pyproject.toml`、`build_uv.sh`、`build_uv_mac.sh`、`build_venv.sh` | 釘住 Python 3.10.19 與依賴版本 |
| 基礎設施 | `scripts/logger.py`、`gpu_utils.py`、`notebook_bootstrap.py`、`model_utils.py`、`train_guard.py`、`render_docs.py` | 見第二節第 11 項 |
| 文件 | `AGENT.md`、`docs/*.md`（8 份）、對應的 `.html` | 原本只有一份 README |
| 其他 | `.gitignore`、`GPU-Test.ipynb`、`GPU.sh`、`論文全文.md` | — |

---

## 二、功能變更

以下依「改動的性質」分類。**所有數字都是實測比對的結果**，比對方式見文末附錄。

### 1. 資料路徑：`階段N` → `data/Step-N`（144 處）

```python
# 原始
FEATURE_DIR = os.path.join(ROOT_DIR, "階段1", "myfeature")
cnn_model.save(f'{rootDir}\\階段1\\model\\CNN_C8000.keras')

# 現行
FEATURE_DIR = os.path.join(ROOT_DIR, 'data', 'Step-1', "myfeature")
cnn_model.save(os.path.join(modelDirectory, 'CNN_C8000.keras'))
```

**改了兩件事：**

- **中文目錄名改為 ASCII。** 中文路徑在跨平台與跨編碼環境容易出問題。
- **字串拼接的 Windows 反斜線改為 `os.path.join`。** `f'{rootDir}\\階段1\\model\\...'` 在 Linux 上會產生檔名含反斜線的單一檔案，而不是巢狀目錄。

同時把所有資料收攏到 `data/` 底下，與程式碼分離。

### 2. Step 1：螺絲配置從 7 種補齊為 10 種

```python
# 原始
screws_config = [8, 7, 6, 5, 4, 3, 2]

# 現行
screws_config = [8, 7, 6, 5, 4, 3, 2, 1, '3_14', '4_146']
```

原始版本漏掉 `1screws` 與兩種複合鬆動配置（`3_14`、`4_146`），而這三種正是 Step 4/5 要偵測的未知故障當中的三類。

### 3. Step 1：切割時濾掉不足 10000 點的尾段

```python
# 原始
for i in range(0, len(raw_data), 10000):

# 現行
for i in range(0, len(raw_data) - 10000 + 1, 10000):
```

原始版本的最後一次迭代會取到不足 10000 點的殘段，`pd.concat(axis=1)` 會把短的那欄補上 `NaN`。這些 NaN 一路流到 Step 2 的特徵計算，是後續 NaN 汙染的源頭之一。

### 4. Step 2：新增 `_clean.csv` 輸出（9 支腳本）

```python
def drop_feature_outliers(df, scale=1.5):
    """任一維特徵落在 [Q1 - scale*IQR, Q3 + scale*IQR] 之外，整列捨棄。"""
    Q1, Q3 = df.quantile(0.25), df.quantile(0.75)
    IQR = Q3 - Q1
    return df[((df >= Q1 - scale*IQR) & (df <= Q3 + scale*IQR)).all(axis=1)]
```

原始版本只輸出 `_Group_feature_data.csv`，但 Step 4/5 讀的是 `_clean.csv`——**這個檔案沒有任何程式會產生**。T2 因此完全沒有 clean 檔，Step 4/5 的 Model 10–18 只會印一串「缺少檔案」再拿空 DataFrame 往下跑。

過濾規則不是自行選定，而是從既有的 `_clean.csv` 反推：以 T1/8000rpm（唯一來源與 clean 檔仍一致的資料）比對，`scale=1.5` 且「任一維超界即捨棄整列」能 10/10 完全重現既有檔案的形狀與數值。

實測 90 個配置合計 53588 列 → 28891 列（保留 54%）。

> 相關 issue #34、#36

### 5. Step 3 / Step 6：移除 LabelEncoder 的二次編碼（72 個 Notebook）

```python
# 原始 —— 先用 label_mapping 映射成整數，再用 LabelEncoder 編一次
label_mapping = {screw: idx for idx, screw in enumerate(desired_order)}
combined_data['screws'] = combined_data['screws'].map(label_mapping)
le_screws = LabelEncoder()
combined_data['screws'] = le_screws.fit_transform(combined_data['screws'])

# 現行 —— 只保留 label_mapping
label_mapping = {screw: idx for idx, screw in enumerate(desired_order)}
combined_data['screws'] = combined_data['screws'].map(label_mapping)
```

`desired_order` 已經明確定義了 `8screws→0, 1screws→1, ...` 的順序，`LabelEncoder` 會**再依字典序重排一次**，把手動指定的語意順序打亂。

移除後 `plot_confusion_matrix` 的呼叫端仍傳 `le_screws`，造成 `NameError`（issue #32），已一併改為直接傳類別清單。

### 6. Step 3 / Step 6：分割時加入分層抽樣（72 個 Notebook）

```python
# 原始
train_test_split(X, y_screws, test_size=0.2, random_state=42)

# 現行
train_test_split(X, y_screws, test_size=0.2, random_state=42, stratify=y_screws)
```

各螺絲配置的樣本數不一致（實測 580 ~ 600 列不等），未分層時測試集的類別比例會偏移。

### 7. Step 4 / Step 5：特徵層取法（54 個 Notebook）

```python
# 原始 —— 對 max_pooling 輸出「另外接一個新的 Flatten」
feat_model = Model(inputs=cnn.input,
                   outputs=Flatten()(cnn.get_layer("max_pooling1d").output))

# 現行 —— 取模型自身的特徵層
feat_model = Model(inputs=cnn.input, outputs=get_feature_layer(cnn).output)
```

**改了兩件事：**

- **原始版本取的是 `max_pooling1d`（第一個池化層）的輸出**，而非模型末端的 Flatten。這在 CNN 上會得到一個維度完全不同的中間表徵，與文件描述的「Flatten 層 176 維」不符。
- **硬編層名對 ResNet 無效。** ResNet 使用 Global Average Pooling，沒有 Flatten 層，也沒有名為 `max_pooling1d` 的層可供接續。18 個 ResNet Notebook 因此 100% 拋 `ValueError`。

`scripts/model_utils.get_feature_layer()` 依序嘗試候選層名，實測三種架構取到：

| 架構 | 特徵層 | 維度 |
|------|--------|------|
| CNN | `flatten` | 176 |
| ResNet | `global_average_pooling1d` | 128 |
| VGG16 | `flatten` | 48 |

> 相關 issue #52

### 8. Step 5：固定隨機種子（27 個 Notebook）

```python
random.seed(42)
```

Step 5 的核心是隨機取樣多批次驗證。原始版本未固定種子，每次執行的批次組合都不同，結果無法重現。

### 9. Step 6：補上模型存檔（27 個 Notebook）

原始版本的 27 個 Retrain Notebook **全部沒有 `model.save()`**——重訓練出來的 10 類模型只存在於記憶體，Notebook 一結束就消失，README 描述的「回到 Step 4 持續迭代」迴圈是斷的。

現行命名規則 `{ARCH}_{LETTER}{RPM}_retrained.keras`，與 Step 3 既有的字母碼一致（`Step-1`→C、`Step-2`→B、`Step-3`→A）。

> 相關 issue #33

### 10. Step 3 / Step 6：新增訓練健全性斷言（72 個 Notebook）

```python
assert_finite_inputs(X_train=X_train, X_test=X_test)
# ... 訓練 ...
assert_model_learned(history, results, len(np.unique(y_train_screws)))
```

訓練若因輸入含 NaN 而失敗，**不會拋出任何例外**——模型照樣存檔、Notebook 照樣「成功」結束、`set -e` 也不會觸發，唯一的線索是準確率剛好等於 `1 / 類別數`：

```
Step3_Model_01   Loss: nan, Accuracy: 0.2017     # 0.2017 = 1/5
```

2972 × 105 個值裡只有**一個** NaN 就足以造成這個結果。這道斷言把靜默失敗變成明確的例外。

> 相關 issue #50

### 11. 全部 Notebook 與腳本：統一日誌與 GPU 管理

| 新增 | 作用 |
|------|------|
| `scripts/notebook_bootstrap.py` | 每個 Notebook 第一個 cell 三行呼叫 `bootstrap()`，建立 logger、導向 stdout/stderr、自動存圖 |
| `scripts/logger.py` | 每次執行寫入 `logs/{程式名}/{時間戳}.log`，圖存到 `output/{程式名}/{時間戳}/` |
| `scripts/gpu_utils.py` | `device_scope()` 自動選 GPU/CPU，設定 `set_memory_growth` |

原始版本沒有任何日誌機制，訓練輸出只在 Notebook 的 cell output 裡；也沒有統一的裝置管理（72 個 Notebook 新增 `device_scope`）。

### 12. 清理未使用的匯入（72 個 Notebook）

原始版本每個 Step 3/6 Notebook 都匯入了大量未使用的模組：

```python
import logging
import absl.logging
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.preprocessing import StandardScaler, label_binarize, LabelEncoder, RobustScaler
from sklearn.metrics import confusion_matrix, classification_report, roc_curve, auc, precision_recall_curve
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
```

實際只用到 `train_test_split`、`RobustScaler`、`confusion_matrix`。已縮減為實際使用的部分。

> 註：15 個 Notebook 仍出現 `KFold` 字樣，位於被整段註解掉的交叉驗證區塊內，屬於保留供參考的內容。

---

## 三、特徵計算與數值正確性的修正

上一節談的是結構與流程。這一節是**計算本身出錯**的部分——這類修正只改一兩行，卻直接影響特徵值與模型輸入。

### 1. `clearance_indicator` 實際算出的是 Impulse Indicator（9 支腳本）

```python
# 原始
features[i, 7] = np.abs(data.max() / np.mean(np.sqrt(np.abs(data)**2)))  # clearance_indicator

# 現行
features[i, 7] = np.abs(data.max()) / (np.mean(np.sqrt(np.abs(data))) ** 2)
```

`np.sqrt(np.abs(x)**2)` 恆等於 `np.abs(x)`，所以原始的分母其實是 `mean(|x|)`，整式退化為 `peak / mean(|x|)`——**這正是 Feature 10 Impulse Indicator 的定義**。

論文（表 2）的正確公式是：

$$x_{cli} = \frac{\max|x|}{\left(\frac{1}{n}\sum\sqrt{|x_i|}\right)^2}$$

`sqrt` 要作用在 `|x|` 上，而不是 `|x|²`。

**數值驗證**（10000 點常態隨機訊號）：

| 公式 | 值 |
|------|-----|
| 原始 clearance | 4.354311 |
| impulse | 4.354311 |
| 修正後 clearance | 5.112289 |

**影響：** `extract_statistical_features()` 對 5 個訊號各呼叫一次，因此產生 **5 對完全重複的維度**：

| clearance（錯誤）| impulse（正確）| 訊號 |
|---|---|---|
| Feature 8 | Feature 10 | Current |
| Feature 23 | Feature 25 | Vibration X |
| Feature 48 | Feature 50 | Vibration Y |
| Feature 73 | Feature 75 | Vibration Z |
| Feature 98 | Feature 100 | Delta_T |

105 維特徵向量的**有效唯一維度只有 100 維**，5 維是冗餘的。

#### 修正後仍有一對重複——但這次不是 bug

以修正後重新產生的特徵實測，5 對之中有 **4 對已經分開，Current 那一對仍然相同**：

| 訊號 | clearance 與 impulse 是否仍相同 |
|------|------------------------------|
| Current | **是** |
| Vibration X / Y / Z、Delta_T | 否 |

原因是資料本身的性質，不是公式。由 Jensen 不等式，`mean(sqrt(|x|))² ≤ mean(|x|)`，**等號在 |x| 為定值時成立**。而 Current 訊號近乎定值：

```
Current   min=0.004035  max=0.004089  變異係數 1.55e-03
          mean(sqrt(|x|))² = 0.00406372
          mean(|x|)        = 0.00406372     相對差異 6.05e-07

振動 X     變異係數 5.53
          mean(sqrt(|x|))² = 0.00034536
          mean(|x|)        = 0.00039718     相對差異 13.05%
```

所以**修正把有效唯一維度從 100 提升到 104，而不是 105**。這一點 issue #1 的分析沒有涵蓋——它假設修正後 5 對都會分開。

### 2. `extract_fft_features` 在空頻率區間回傳純量（9 支腳本）

```python
# 原始
if len(freq_indices) == 0:
    fft_max = 0                       # 純量

# 現行
if len(freq_indices) == 0:
    fft_max = np.zeros(Hfeat.shape[1])   # 與其他情況同形狀
```

其他情況下 `fft_max` 是長度等於片段數的陣列。混入一個純量後，末尾的 `np.array(fft_features).T` 會拋出：

```
ValueError: setting an array element with a sequence.
```

### 3. `np.ptp()` 已在 NumPy 2.0 移除（9 支腳本）

```python
# 原始
features[i, 5] = np.ptp(data)          # peak2peak

# 現行
features[i, 5] = data.max() - data.min()
```

數值等價，但 `np.ptp()` 自 NumPy 1.24 起被棄用、2.0 移除。本專案釘的是 NumPy 2.2.6。

### 4. `fourier_transform` 的未使用參數與全域 `freq`（9 支腳本）

移除未使用的 `lenFeature` 參數，並在函式內以 `freq_local` 就地計算頻率軸，取代對模組層級 `freq` 的依賴——後者在資料長度與 `rawdata` 常數不符時會靜默取錯頻率。

### 5. `Delta_t_data.csv` 大小寫不符（2 支腳本）

`6000_2.py` 與 `6000_3.py` 讀取 `Delta_t_data.csv`（小寫 t），但 Step 1 存的是 `Delta_T_data.csv`。在大小寫敏感的檔案系統（Linux）上直接 `FileNotFoundError`。

### 6. `clear_session()` 在 evaluate/save 之前呼叫（45 個 Notebook）

原始版本在訓練後、評估與存檔之前呼叫 `tf.keras.backend.clear_session()`，會清掉計算圖使後續操作作用在失效的模型上。現行版本改為透過 `scripts/notebook_bootstrap.py` 註冊到 `atexit`，只在程序結束時執行。

### 7. Step 5 的 New Faulty 標籤依遞增計數而非固定映射（27 個 Notebook）

```python
# 原始
label_str = f"New Faulty {unknown_id}"      # unknown_id 隨叢集出現順序遞增

# 現行
label_str = UNKNOWN_LABEL_MAP.get(most_common_screw, f"New Faulty {unknown_id}")
```

原始版本的編號取決於 HDBSCAN 回傳叢集的順序，**同一個螺絲配置在不同批次會拿到不同的 New Faulty 編號**，跨批次結果無法對照。現行版本以叢集內最多數的螺絲配置查固定映射表，遞增計數只作為查不到時的後備。

### 8. Step 1 figure 腳本的 `motor_types` 與 save 腳本不一致（6 支腳本）

```python
# 原始 figure_6000_1.py
motor_types = ['A', 'B', 'C']
# 原始 figure_6000_2.py
motor_types = ['B']

# 現行 figure_6000.py（與 save 腳本一致）
motor_types = ['T1']
```

原始的視覺化腳本用的是 `A`/`B`/`C`，而 save 腳本用 `T1`/`T2`/`T3`，因此 figure 腳本的所有路徑都找不到資料。這 6 支後來合併為 3 支（見第一節）。

### 9. Step 6 重複的資料載入函式（27 個 Notebook）

原始版本定義了 `load_and_preprocess_data` 與 `load_and_preprocess_newdata` 兩個**內容完全相同**的函式。現行改為別名：

```python
load_and_preprocess_newdata = load_and_preprocess_data
```

---

## 四、演算法核心未變更

比對過程中特別確認了以下不變量，全數一致——**這些修正都沒有動到方法本身**：

| 不變量 | 原始 | 現行 |
|--------|------|------|
| 取樣率 `Fs = 10000` | ✓ | ✓ |
| 每段 10000 點 | ✓ | ✓ |
| 6000rpm 基頻 100 Hz | ✓ | ✓ |
| 105 個特徵欄位名稱 | 105 | 105 |
| Conv1D 16 filters × 4 層 | ✓ | ✓ |
| Dropout 0.3 | ✓ | ✓ |
| Adam lr=1e-4 | ✓ | ✓ |
| EarlyStopping patience=10 | ✓ | ✓ |
| epochs=100 / batch_size=32 | ✓ | ✓ |
| Step 1 IQR scale=3.0 | ✓ | ✓ |
| HDBSCAN min_cluster_size=25 / min_samples=3 | ✓ | ✓ |
| 馬氏距離閾值第 95 百分位 | ✓ | ✓ |
| 每類取樣上限 60 / 批次上限 450 | ✓ | ✓ |

---

## 五、變更量統計

| 步驟 | 有變更的檔案 | 新增行 | 移除行 |
|------|------------|--------|--------|
| README.md | 1 | +997 | −3 |
| Step 1 | 9 | +1212 | −1006 |
| Step 2 | 9 | +2828 | −2342 |
| Step 3 | 45 | +1981 | −1705 |
| Step 4 | 27 | +325 | −163 |
| Step 5 | 27 | +541 | −270 |
| Step 6 | 27 | +1315 | −1252 |
| T1_T2_T3 | 1 | +11 | −5 |

Step 1/2/3/6 的行數變動較大，主因是每個檔案都加入了日誌 bootstrap 與（Notebook 的）健全性斷言。

---

## 附錄：比對方法

檔名在兩版之間全面更動，`git diff` 無法自動配對，因此比對以程式化方式進行：

1. **建立名稱映射** —— 以正規式把 `Step3_Model 10__OneStage.ipynb` 這類舊名正規化為新名，146 個檔案成功配對，6 個為被合併的 figure 腳本。
2. **只比對程式碼** —— Notebook 以 `json` 解析後抽出 `cell_type == 'code'` 的內容，排除輸出與 metadata 造成的雜訊。
3. **統計變更模式** —— 以 `difflib.SequenceMatcher` 逐檔取 opcodes，彙總最常出現的新增/移除行，據此歸納出上述 12 類變更。
4. **逐項驗證數量** —— 每個宣稱（如「144 處路徑」「72 個 Notebook」）都以述詞函式在兩版上分別計數，而非目測。
5. **確認不變量** —— 對演算法常數做同樣的計數比對，確保修正沒有改動方法本身。

### 修訂：第一版遺漏了整類修正

本文第一版只涵蓋了第二節那 12 項，第三節的 9 項全部遺漏。原因出在步驟 3 的作法：

當時是「彙總最常出現的新增／移除行」來歸納變更模式。這個排序會被樣板碼主導——Step 2 的比對中 `"""` 出現 116 次、`# ====` 出現 54 次，而 `clearance_indicator` 這類**每支腳本只出現一次、全專案共 9 次**的修正被埋在後面看不到。

**問題在於：出現頻率與重要性無關。** 一行公式錯誤影響的是每一筆特徵值，遠比 100 次的註解調整重要。

修訂時改用兩個互補的作法：

- **以已關閉的 issue 為索引反查** —— 逐一針對 #1~#20 的描述寫述詞函式，在兩版分別計數。
- **過濾出「含運算式」的變更行**（排除註解、docstring、空行）再逐行檢視，而不是依頻率排序。

這樣找出的 9 項修正，有 8 項是第一版沒寫到的。列在此處以說明本文的涵蓋範圍是如何確認的。
