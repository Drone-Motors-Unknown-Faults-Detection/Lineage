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
| 基礎設施 | `scripts/logger.py`、`gpu_utils.py`、`notebook_bootstrap.py`、`model_utils.py`、`train_guard.py`、`render_docs.py` | 見下方第三節 |
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

## 三、演算法核心未變更

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

## 四、變更量統計

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
