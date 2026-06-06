# Issues & 修改建議

> 審查對象：Step1 ~ Step6 所有 `.py` 腳本與全部 108 個 Notebook（Step3×27、Step4×27、Step5×27、Step6×27），以及 `docs/` 文件。
> 優先級：🔴 明顯錯誤 / 🟡 繞路或不直觀 / 🔵 文件與程式碼不符

---

## 🔴 明顯錯誤

### 1. `clearance_indicator` 公式計算錯誤
**影響範圍：** 所有 `Step2_Feature_Extraction_*.py`（9 支），`extract_statistical_features()` line 154

**問題：**
```python
# 現有程式碼（錯誤）
features[i, 7] = np.abs(data.max() / np.mean(np.sqrt(np.abs(data)**2)))
```
`np.sqrt(np.abs(data)**2)` 恆等於 `np.abs(data)`（因為 `sqrt(|x|²) = |x|`），所以這行實際上計算的是：
```
peak / mean(|x|)
```
這正是 **Impulse Indicator**（feature 10）的公式，而非 Clearance Indicator。所有依賴此特徵的模型訓練都使用了錯誤的 Feature 8。

**論文公式**（論文全文.md 表 2）：

$$x_{cli} = \frac{max|x|}{\left(\frac{1}{n} \sum_{i=1}^{n} \sqrt{|x_i|}\right)^2}$$

**修正：**
```python
# 修正後：分母是 mean(sqrt(|x|)) 的平方，注意 sqrt 在 |x| 外
features[i, 7] = np.abs(data.max()) / (np.mean(np.sqrt(np.abs(data))) ** 2)
```

### 下游影響分析

#### 受影響的特徵位置

`extract_statistical_features()` 對全部 5 個訊號呼叫，每個訊號各產生一對重複特徵，共 **5 對（10 個維度中有 5 個是重複值）**：

| clearance_indicator（錯誤，值同 impulse）| impulse_indicator（正確）| 訊號 |
|----------------------------------------|--------------------------|------|
| Feature 8（index 7） | Feature 10（index 9） | Current |
| Feature 23（index 22）| Feature 25（index 24）| Vibration X |
| Feature 48（index 47）| Feature 50（index 49）| Vibration Y |
| Feature 73（index 72）| Feature 75（index 74）| Vibration Z |
| Feature 98（index 97）| Feature 100（index 99）| Delta_T |

105 維特徵向量的**有效唯一維度為 100 維**，5 個 clearance_indicator 欄位數值與對應的 impulse_indicator 完全相同。

#### Step3 模型訓練

- CNN 輸入的 105 維中有 5 維與其他維完全重複，RobustScaler 正規化後仍維持重複
- CNN 訓練時會將重複維度的權重趨近為零或平均分配，浪費部分模型容量
- 5 類分類任務相對簡單，其餘 100 個正確特徵已足以區分，**對分類準確率的實際影響可能不顯著**（論文報告 ~100% 準確率）
- 若任務複雜度提升（如更多類別、跨工況泛化），重複特徵的負面影響將更明顯

#### Step4/5 未知故障偵測

- HDBSCAN 聚類使用 CNN Flatten 層的 176 維輸出，而非原始 105 維特徵
- Flatten 特徵由在錯誤輸入上訓練的 CNN 學習，特徵表示可能略遜於正確訓練版本
- Mahalanobis 距離計算對輸入品質敏感；若 CNN 因重複特徵學到較差的表示，閾值的泛化能力可能受到輕微影響
- 由於所有模型共用同一套錯誤特徵，**結果在內部是自洽的（internally consistent）**，但與理論最優結果存在偏差

#### Step6 重訓練

- 重訓練使用的特徵資料來自相同的 Step2 pipeline，同樣含有 5 對重複特徵
- 10 類分類仍基於有效 100 維特徵，影響程度與 Step3 相似

#### 修正後的連鎖影響

修正 Step2 後需重新執行整個 pipeline：
1. 重新執行所有 `Step2_Feature_Extraction_*.py`（9 支）以生成新特徵 CSV
2. 重新訓練所有 Step3 notebook（27 個）
3. 重新執行所有 Step4/5 notebook（54 個）
4. 重新執行所有 Step6 notebook（27 個）

---

### 2. `docs/Step2_Feature_Extraction.md` 對 MSA 的描述有誤（程式碼本身正確）
**影響範圍：** `docs/Step2_Feature_Extraction.md`

**說明：** 程式碼計算 `np.mean(data**2)`，與論文表 2 的公式完全一致：

$$x_{msa} = \frac{1}{n} \sum_{i=1}^{n} x_i^2 \quad \text{（Mean Square Amplitude）}$$

程式碼**正確**。但 `docs/Step2_Feature_Extraction.md` 的特徵表將 Feature 13 描述為「MSA = 平均絕對偏差 = `mean(|x - mean(x)|)`」，此描述與論文及程式碼均不符，是文件本身的錯誤。

**修正：** 更新文件，將 Feature 13 說明改為「Mean Square Amplitude = $\frac{1}{n}\sum x_i^2$」。

---

### 3. `clear_session()` 在錯誤位置，導致後續 cell 失效
**影響範圍：** 所有 `Step3_Model_*.ipynb`（27 個），Cell 17

**問題：** `tf.keras.backend.clear_session()` 被放在獨立 cell（訓練完成後的 Cell 17），此操作清除 Keras session 後，後續所有 cell 的模型操作均受影響：

| Cell | 操作 | 後果 |
|------|------|------|
| 18 | `cnn_model.summary()` | 可能輸出空架構 |
| 19 | `cnn_model.evaluate(...)` | 評估結果不可信 |
| 21 | `cnn_model.predict(...)` | 預測結果不可信 |
| 22 | `cnn_model.save(...)` | 儲存的是無效模型 |

Bootstrap 中已透過 `atexit.register(tf.keras.backend.clear_session)` 在程式結束時自動清除，Cell 17 的手動呼叫完全多餘且有害。

**修正：** 直接刪除 Cell 17 的 `tf.keras.backend.clear_session()` 呼叫。

---

### 4. `Delta_T` 檔名大小寫不一致，導致 FileNotFoundError
**影響範圍：** `Step2_Feature_Extraction_6000_2.py`，`process_group()` line 226

**問題：**
```python
df_temp = pd.read_csv(os.path.join(group_csv_dir, f'{group_label}_Delta_t_data.csv'))
#                                                                         ↑ 小寫 t
```
`Step1_Data_Preprocessing_save_6000_2.py` 的 `signal_columns['T2']` 定義欄位名稱為 `'Delta_T'`（大寫 T），輸出檔案為 `T2_Delta_T_data.csv`。在大小寫敏感的系統（Linux）上讀取 `Delta_t` 會直接 FileNotFoundError；需確認其他轉速的對應腳本是否有相同問題。

**修正：** 將讀取路徑改為 `Delta_T_data.csv`（大寫 T）。

---

### 5. `extract_fft_features` 空頻率區間時型別不一致
**影響範圍：** 所有 `Step2_Feature_Extraction_*.py`（9 支），`extract_fft_features()` line 208–210

**問題：**
```python
if len(freq_indices) == 0:
    fft_max = 0                              # 純量 scalar
else:
    fft_max = Hfeat[freq_indices, :].max(axis=0)  # shape (n_cols,) 的 array
fft_features.append(fft_max)
```
當某諧波頻率找不到對應區間時，`fft_max` 為純量 `0`；否則為 1D array。後續 `np.array(fft_features).T` 因形狀不一致而產生 object array 或 ValueError。

**修正：**
```python
if len(freq_indices) == 0:
    fft_max = np.zeros(Hfeat.shape[1])  # 保持形狀一致
else:
    fft_max = Hfeat[freq_indices, :].max(axis=0)
```

---

### 6. 特徵萃取器使用 `max_pooling1d` 而非文件所述的 `flatten` 層
**影響範圍：** 所有 `Step4_Model_*_Detecting.ipynb` 與 `Step5_Model_*_Random_Detecting.ipynb`（共 54 個）

**問題：** 文件（`Step4_Unknown_Detection.md`）及 Step3 文件均說明以 **Flatten 層**輸出作為 HDBSCAN 的特徵輸入（176 維）：
```python
# 文件所述寫法
feature_extractor = keras.Model(inputs=model.input,
                                outputs=model.get_layer('flatten').output)
```
但所有 Step4/5 notebook 實際使用的是：
```python
feat_model = Model(inputs=cnn.input,
                   outputs=Flatten()(cnn.get_layer("max_pooling1d").output))
```
此處在 `get_layer("max_pooling1d").output` 之上再加一個新的 `Flatten()` 運算，而非直接取已訓練模型中的 Flatten 層輸出。兩者在維度上可能一致，但建立了一個與原始訓練模型不相連的新節點，語意上不直觀，且若模型架構改變（層名稱變動）會靜默地返回不同維度的特徵。

**建議：** 確認兩種寫法在數值上是否等價，並統一為文件描述的 `model.get_layer('flatten').output`，或至少確認 `max_pooling1d` 層名稱在所有 27 個模型中都能正確對應。

---

## 🟡 繞路 / 不直觀

### 7. 雙重 LabelEncoding（多餘操作）
**影響範圍：** 所有 `Step3_Model_*.ipynb`（27 個）和所有 `Step6_Model_*_Retrain.ipynb`（27 個），Cells 8–9

**問題：** Cell 8 已用 `label_mapping` 將字串標籤映射為整數（0~4 或 0~9），Cell 9 再對已是整數的欄位做 `LabelEncoder.fit_transform()`：
```python
# Cell 8：手動 mapping，字串 → 整數
label_mapping = {screw: idx for idx, screw in enumerate(desired_order)}
combined_data['screws'] = combined_data['screws'].map(label_mapping)

# Cell 9：對整數再做 LabelEncoder，多餘
le_screws = LabelEncoder()
combined_data['screws'] = le_screws.fit_transform(combined_data['screws'])
```
額外影響：`le_screws.classes_` 變成 `[0, 1, 2, ...]`（整數），不是原始字串標籤；後續混淆矩陣 tick labels 無法顯示有意義的類別名稱。Cell 10 印出的 label_mapping 也無法反映實際使用的編碼。

**建議：** 刪除 Cell 9 的 `LabelEncoder` 步驟。若需要 `le_screws` 用於 decode，改用 `desired_order` 列表直接索引。

---

### 8. `load_and_preprocess_data` 與 `load_and_preprocess_newdata` 完全相同
**影響範圍：** 所有 `Step6_Model_*_Retrain.ipynb`（27 個），Cells 3–4

**問題：** 兩個函數邏輯逐行相同，僅命名不同，造成維護困難。

**建議：** 合併為一個函數，分別傳入不同的 `screws_list`：
```python
def load_feature_data(base_dir, screws_list):
    ...

datasets_known   = load_feature_data(myfeatureDirectory,  screws_list_known)
datasets_unknown = load_feature_data(myfeatureDirectory2, screws_list_unknown)
```

---

### 9. `fourier_transform` 有未使用的參數 `lenFeature`
**影響範圍：** 所有 `Step2_Feature_Extraction_*.py`（9 支），`fourier_transform()` line 112

**問題：** 函數定義包含 `lenFeature` 參數，但函數體內從未使用，所有呼叫點也都傳入 `df_x.shape[1]` 等值只是形式上佔位。

**建議：** 移除此參數及所有呼叫點對應的引數。

---

### 10. `np.ptp(data)` 已棄用
**影響範圍：** 所有 `Step2_Feature_Extraction_*.py`（9 支），`extract_statistical_features()` line 152

**問題：** `np.ptp` 自 NumPy 1.24 起已 deprecated，NumPy 2.0 中移除。

**修正：**
```python
features[i, 5] = data.max() - data.min()  # peak2peak
```

---

### 11. Step1 切割末段長度不足 10000 點靜默保留
**影響範圍：** 所有 `Step1_Data_Preprocessing_save_*.py`（9 支），`slice_and_save()` line 123–126

**問題：** IQR 濾除後資料長度通常不是 10000 的整倍數，末段 `iloc[i:i+10000]` 可能不足 10000 點。concat 後形成含 NaN 的末欄，雖 Step2 `drop_missing_values()` 會清除，但沒有任何警告，且若末段極短（如 200 點），特徵萃取前不會有任何提示。

**建議：** 跳過長度不足的末段：
```python
for i in range(0, len(raw_data) - 10000 + 1, 10000):
    sliced_chunk = raw_data.iloc[i:i+10000].reset_index(drop=True)
    ...
```

---

### 12. `fourier_transform` 使用全域 `freq` 存在潛在不匹配
**影響範圍：** 所有 `Step2_Feature_Extraction_*.py`（9 支），`fourier_transform()` line 116–122

**問題：** 函數內部重新計算 `rawdata = len(data)`、`rawdata2 = rawdata // 2`，但 `plt.plot(freq, myfft2[:, 0])` 使用**全域** `freq` 陣列。若輸入資料列數與全域 `rawdata` 不同，長度不匹配將引發 ValueError。

**建議：** 在函數內部計算局部 `freq`，不依賴全域變數：
```python
freq_local = np.linspace(0, rawdata2 - 1, rawdata2) * (Fs / rawdata)
plt.plot(freq_local, myfft2[:, 0])
```

---

### 13. Step5 `evaluate_unknown_batch2()` 的未知標籤依賴遞增計數而非固定映射
**影響範圍：** 所有 `Step5_Model_*_Random_Detecting.ipynb`（27 個）

**問題：** 函數在距離超過閾值時，以 `unknown_id += 1` 遞增方式命名 "New Faulty N"，但 N 取決於 cluster 的出現順序而非螺絲類型本身。若同一批次中兩個 cluster 都超過閾值，兩者分別被標記為 "New Faulty 1"、"New Faulty 2"，即使它們都屬於同一種未知螺絲類型，或順序與 `UNKNOWN_LABEL_MAP` 的定義不一致。

**建議：** 根據 cluster 內最多數的螺絲配置，使用 `UNKNOWN_LABEL_MAP` 映射到固定標籤：
```python
most_common_screw = Counter(screws_in_cluster).most_common(1)[0][0]
label_str = UNKNOWN_LABEL_MAP.get(most_common_screw, "Unknown ?")
```

---

### 14. Step5 未設定 `random.seed()`，結果無法重現
**影響範圍：** 所有 `Step5_Model_*_Random_Detecting.ipynb`（27 個）

**問題：** 所有 Step5 notebook 的隨機抽樣邏輯均未設定 `random.seed()`，每次執行產生不同的未知故障組合，無法重現實驗結果。

**建議：** 在抽樣前加入固定種子（如 `random.seed(42)`），或在文件中明確說明此步驟設計為隨機不可重現，並提供多次執行取平均的評估建議。

---

### 15. `build_cnn_model` 內 Dense 層注解誤標為「卷積層」
**影響範圍：** `Step3_Model_*.ipynb` 中使用基礎 CNN 架構的 notebook（Model 1、4、7、10、13、16、19、22、25 等），`build_cnn_model()` 函數

**問題：** Dense 層的注解寫成「第五層卷積層」與「第六層卷積層」。使用 VGG/ResNet 架構的 notebook（Model 3、8、13…）注解為「全連接層」是正確的，但基礎 CNN 的 notebook 有此錯誤。

---

## 🔵 文件與程式碼不符

### 16. 論文表 2 的 Shape Indicator 公式有 typo（程式碼正確）
**影響範圍：** `論文全文.md` 表 2

**說明：** 論文表 2 中 Shape Indicator 公式為：

$$x_{si} = \frac{\frac{1}{n}\sum|x_i|}{\frac{1}{n}\sum|x_i|}$$

分子分母相同，恆等於 1，顯然是排版 typo。標準 Shape Indicator 定義應為 RMS 除以 Mean Amplitude：

$$x_{si} = \frac{x_{rms}}{\frac{1}{n}\sum|x_i|}$$

程式碼實作為 `np.sqrt(np.mean(data**2)) / np.mean(np.abs(data))`，與標準定義一致，**程式碼正確**，論文需修正。

---

### 17. `header=22` vs 文件說的 `skiprows=21`
**影響範圍：** 所有 `Step1_Data_Preprocessing_save_*.py`（9 支）line 91 vs `docs/Step1_Data_Preprocessing.md`

**說明：**
- 文件：「以 `skiprows=21` 跳過前 21 行說明文字」（header 在第 22 行，1-indexed）
- 程式碼：`pd.read_csv(file_path, header=22, ...)`（header 在第 23 行，1-indexed，差 1 行）

`header=22` 等效於 `skiprows=22, header=0`，而文件描述的 `skiprows=21` 等效於 header 在 row index 21。兩者差 1 行，其中一個必定不符合實際資料格式。

**建議：** 以實際原始 CSV 驗證正確的 header 位置，統一文件與程式碼。

---

### 17. Step3 notebook 載入的不是 `_clean.csv`，且 Step2 未生成該檔
**影響範圍：** 所有 `Step3_Model_*.ipynb`（27 個）及 `Step6_Model_*_Retrain.ipynb`（27 個）

**說明：** 文件（`Step3_Model_Training.md`）強調「務必使用 `*_clean.csv`，而非 `*_data.csv`」，但所有 notebook 載入的都是 `T{N}_Group_feature_data.csv`（無任何後綴）。

此外，Step2 的程式碼本身只輸出一個檔案，從未生成 `_raw.csv` 或 `_clean.csv`，文件描述的「三種輸出格式」與實際程式碼不符。可能有額外的特徵清理步驟未納入版本控制。

---

### 18. Step6 未真正使用 Step4/5 偵測結果，直接讀取 ground truth 特徵
**影響範圍：** 所有 `Step6_Model_*_Retrain.ipynb`（27 個），Cell 6

**說明：** 文件（`Step6_Model_Retraining.md`）說「將 Steps 4-5 偵測到的未知故障資料納入訓練集」，但 notebook 直接從 `myfeature/` 目錄讀取 `5screws`、`6screws` 等配置的 ground truth 特徵資料，相當於假設偵測完全正確，並未真正接入 Step4/5 的輸出。

這可能是研究設計（以 oracle label 評估上界效能），但文件描述與實作落差大，建議在文件中補充說明。

---

### 19. `train_test_split` 缺少 `stratify`
**影響範圍：** 所有 `Step3_Model_*.ipynb`（27 個）及所有 `Step6_Model_*_Retrain.ipynb`（27 個），共 54 個 notebook

**說明：** 文件說明使用 `stratify=True` 分層抽樣，但全部 54 個 notebook 的 `train_test_split` 均未指定 `stratify`：
```python
# 現有（缺 stratify）
X_train, X_test, y_train_screws, y_test_screws = train_test_split(
    X, y_screws, test_size=0.2, random_state=42
)
# 修正
X_train, X_test, y_train_screws, y_test_screws = train_test_split(
    X, y_screws, test_size=0.2, random_state=42, stratify=y_screws
)
```
在類別分佈不均時，缺乏 stratify 可能導致測試集某些類別樣本過少，混淆矩陣結果不具代表性。

---

### 20. Step4 特徵萃取層與文件定義（Flatten 輸出 176 維）不一致
此議題已在 **Issue 6** 詳細說明。

---

## 問題彙總

| # | 問題 | 影響範圍 | 優先級 |
|---|------|----------|--------|
| 1 | `clearance_indicator` 公式錯誤（計算成 Impulse Indicator）| Step2 全部 9 支 | 🔴 |
| 2 | docs/Step2 對 MSA 描述有誤（程式碼正確，文件需修正）| docs/Step2_Feature_Extraction.md | 🔵 |
| 3 | `clear_session()` 在評估/儲存前呼叫 | Step3 全部 27 個 | 🔴 |
| 4 | `Delta_T` 檔名大小寫不一致 | Step2_6000_2.py | 🔴 |
| 5 | FFT 空區間時 scalar/array 混型 | Step2 全部 9 支 | 🔴 |
| 6 | 特徵萃取器用 `max_pooling1d` 而非 `flatten` | Step4/5 全部 54 個 | 🔴 |
| 7 | 雙重 LabelEncoding（多餘且破壞 classes_ 可讀性）| Step3 全部 27 個、Step6 全部 27 個 | 🟡 |
| 8 | 兩個完全相同的 load 函數 | Step6 全部 27 個 | 🟡 |
| 9 | `fourier_transform` 未使用的 `lenFeature` 參數 | Step2 全部 9 支 | 🟡 |
| 10 | `np.ptp` 已棄用 | Step2 全部 9 支 | 🟡 |
| 11 | 末段短片段靜默保留 | Step1 全部 9 支 | 🟡 |
| 12 | 全域 `freq` 潛在長度不匹配 | Step2 全部 9 支 | 🟡 |
| 13 | Step5 未知標籤依遞增計數非固定映射 | Step5 全部 27 個 | 🟡 |
| 14 | Step5 未設定 `random.seed()` | Step5 全部 27 個 | 🟡 |
| 15 | Dense 層注解誤寫成「卷積層」| Step3 基礎 CNN notebook | 🟡 |
| 16 | `header=22` vs 文件說 `skiprows=21` | Step1 全部 9 支 | 🔵 |
| 17 | notebook 載入非 `_clean.csv`，且 Step2 未生成該檔 | Step3/6 全部 54 個 | 🔵 |
| 18 | Step6 未接入 Step4/5 偵測輸出 | Step6 全部 27 個 | 🔵 |
| 19 | `train_test_split` 缺少 `stratify` | Step3/6 全部 54 個 | 🔵 |
