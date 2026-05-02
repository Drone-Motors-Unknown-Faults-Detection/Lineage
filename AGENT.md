# AGENT.md — Agent 指引文件

本文件為 AI Agent（含 Claude Code 等自動化工具）提供操作本專案所需的背景知識、慣例說明與建議行為準則。

---

## 專案定位

**Ancestor** 是一套馬達故障診斷研究專案，實作了從原始訊號到持續學習的完整 PHM（預後健康管理）流程。研究目標是在已知故障分類的基礎上，自動偵測並學習未知的新型故障，實現開放集（Open-Set）故障診斷。

---

## 目錄結構

```
e:\Ancestor\
├── Step1_Data_Preprocessing_figure_*.py   # 資料視覺化腳本（×6）
├── Step1_Data_Preprocessing_save_*.py     # 資料儲存腳本（×9）
├── Step2_Feature_Extraction_*.py          # 特徵萃取腳本（×9）
├── Step3_Model *.ipynb                    # CNN 模型訓練（×27）
├── Step4_Model *__Detecting.ipynb         # 未知故障偵測（×27）
├── Step5_Model *__Random_Detecting.ipynb  # 隨機取樣偵測（×27）
├── Step6_Model *__Retrain.ipynb           # 模型重訓練（×27）
├── T1_T2_T3.ipynb                         # 健康度退化建模
├── README.md                              # 專案說明
├── AGENT.md                               # 本文件
└── docs/
    ├── Step1_Data_Preprocessing.md
    ├── Step2_Feature_Extraction.md
    ├── Step3_Model_Training.md
    ├── Step4_Unknown_Detection.md
    ├── Step5_Random_Sampling_Detection.md
    └── Step6_Model_Retraining.md
```

---

## 流程依賴關係

各步驟具有嚴格的前後依賴，修改任一步驟前應確認下游影響：

```
Step 1 → Step 2 → Step 3 → Step 4 → Step 5
                                ↓
                           Step 6 → (回到 Step 4 下一輪)
```

| 步驟 | 輸入來源 | 輸出目標 |
|------|----------|----------|
| Step 1 | 原始 CSV（raw_data/）| stage1/csv/ |
| Step 2 | stage1/csv/ | feature_data.csv |
| Step 3 | feature_data.csv | *.keras 模型 |
| Step 4 | *.keras + 未知資料 | 偵測結果、叢集模型 |
| Step 5 | Step 4 的叢集模型 | 偵測結果（隨機批次）|
| Step 6 | 原始已知 + 未知資料 | 重訓練 *.keras 模型 |

---

## 模型編號系統

27 個模型編號（Model 1 ~ 27）對應不同的實驗配置：

| 編號範圍 | 類型 | 說明 |
|----------|------|------|
| 1 ~ 9 | 基礎版本 | 對應不同轉速 / 馬達組合 |
| 10 ~ 18 | OneStage 變體 | 調整資料組合的一階段偵測 |
| 19 ~ 27 | TwoStage 變體 | 兩階段故障診斷策略 |

**重要：** Step N（N = 3~6）的 Notebook 編號必須對應，`Step3_Model 5.ipynb` 對應 `Step4_Model 5__Detecting.ipynb` 等。

---

## 資料慣例

### 螺絲配置與故障狀態對應

| 螺絲配置 | 整數標籤 | 語意標籤 | 已知/未知 |
|----------|----------|----------|----------|
| 8screws | 0 | Healthy | 已知 |
| 1screws | 1 | Faulty 1 | 已知 |
| 2screws | 2 | Faulty 2 | 已知 |
| 3screws | 3 | Faulty 3 | 已知 |
| 4screws | 4 | Faulty 4 | 已知 |
| 5screws | 5 | New Faulty 1 | 未知 |
| 6screws | 6 | New Faulty 2 | 未知 |
| 7screws | 7 | New Faulty 3 | 未知 |
| 3_14screws | 8 | New Faulty 4 | 未知 |
| 4_146screws | 9 | New Faulty 5 | 未知 |

### 特徵向量格式

- 維度：**105 維**（固定，所有步驟共用此格式）
- 欄位順序：Current(15) → Vib_X(25) → Vib_Y(25) → Vib_Z(25) → Delta_T(15)
- 不得任意增減特徵維度，否則與已訓練模型不相容

### 資料取樣率

- **Fs = 10,000 Hz**（所有腳本共用，不得修改）
- 每段訊號：**10,000 點**（= 1 秒資料）

---

## CNN 模型規格

```python
# 標準架構（Step 3 / Step 6 共用）
Input:    (105, 1)
Conv1D:   16 filters, kernel=3, padding='same', ReLU
Conv1D:   16 filters, kernel=3, ReLU  → MaxPool(2)
Conv1D:   16 filters, kernel=3, ReLU  → MaxPool(2)
Conv1D:   16 filters, kernel=3, ReLU  → MaxPool(2)
Flatten
Dense:    16, ReLU
Dropout:  0.3
Dense:    N, Softmax   # N=5 (Step3) or N=10 (Step6)
```

**中間層萃取：** Step 4/5 使用 `Flatten` 層輸出作為無監督特徵空間。

---

## 異常偵測參數

| 參數 | 值 | 說明 |
|------|----|------|
| HDBSCAN min_cluster_size | 25 | 最小叢集大小 |
| HDBSCAN min_samples | 3 | 核心點最小樣本數 |
| 馬氏距離閾值 | 第 95 百分位數 | 訓練資料距離分布 |
| 每類取樣上限 | 60 | 平衡取樣 |
| 最大組合樣本 | 450 | 批次上限 |

---

## 常見操作指引

### 新增轉速實驗

1. 在 Step 1 新增對應 `save_*RPM.py`，調整 `base_freq` 與目錄路徑
2. 在 Step 2 新增對應腳本，更新 FFT 基頻計算
3. 以新資料執行 Step 3 建立新模型編號

### 新增故障類型

1. 收集新故障的原始訊號，放入對應目錄
2. 執行 Step 1 / Step 2 生成 feature_data.csv
3. 若為「未知」故障：先執行 Step 4/5 偵測，再以 Step 6 重訓練
4. 若為「已知」故障：直接修改 Step 3 輸出層類別數，重新訓練

### 修改偵測閾值

閾值定義在 Step 4 Notebook 中：

```python
threshold = np.percentile(train_distances, 95)  # 可調整百分位數
```

調高百分位數 → 降低誤報（False Positive），但可能增加漏報（False Negative）。

---

## 注意事項與限制

1. **模型版本對應：** 各 Step 的 Notebook 編號必須一致，不可混用不同編號的模型。
2. **特徵維度固定：** 105 維特徵結構不可在中途修改，否則已存模型無法讀取。
3. **HDBSCAN 隨機性：** 叢集結果可能略有差異，建議固定 `random_state` 或多次執行取平均。
4. **協方差矩陣奇異性：** 若特徵高度共線，馬氏距離計算可能失敗，需先以 PCA 降維。
5. **Step 6 從頭重訓練：** 目前不使用 Fine-tuning，若資料量大，訓練時間較長。
6. **資料路徑：** 所有腳本中的路徑為相對路徑，請確保在 `e:\Ancestor\` 目錄下執行。

---

## 環境需求

```
Python >= 3.8
TensorFlow >= 2.x
hdbscan
scikit-learn
scipy
pandas
numpy
matplotlib
seaborn
jupyter
```

安裝：

```bash
pip install tensorflow hdbscan scikit-learn scipy pandas numpy matplotlib seaborn jupyter
```
