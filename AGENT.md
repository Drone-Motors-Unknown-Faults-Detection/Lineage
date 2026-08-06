# AGENT.md — Agent 指引文件

本文件為 AI Agent（含 Claude Code 等自動化工具）提供操作本專案所需的背景知識、慣例說明與建議行為準則。

---

## 專案定位

**Lineage** 是一套馬達故障診斷研究專案，實作了從原始訊號到持續學習的完整 PHM（預後健康管理）流程。研究目標是在已知故障分類的基礎上，自動偵測並學習未知的新型故障，實現開放集（Open-Set）故障診斷。

---

## 目錄結構

```
/home/albert/Lineage/
├── Step1_Data_Preprocessing_figure_{6000,8000,11000}.py  # 資料視覺化腳本（×3）
├── Step1_Data_Preprocessing_save_*.py     # 資料儲存腳本（×9）
├── Step2_Feature_Extraction_*.py          # 特徵萃取腳本（×9）
├── Step3_Model_{01..09}.ipynb                      # 從頭訓練，基礎版本（×9）
├── Step3_Model_{10..27}_OneStage.ipynb             # OneStage 遷移學習（×18）
├── Step3_Model_{10..27}_TwoStage.ipynb             # TwoStage 遷移學習（×18）
├── Step4_Model_{01..27}_Detecting.ipynb            # 未知故障偵測（×27）
├── Step5_Model_{01..27}_Random_Detecting.ipynb     # 隨機取樣偵測（×27）
├── Step6_Model_{01..27}_Retrain.ipynb              # 模型重訓練（×27）
├── T1_T2_T3.ipynb                         # 健康度退化建模
├── Step{1..6}*.sh                         # 各步驟的批次執行入口
├── scripts/
│   ├── logger.py                          # 自訂日誌框架
│   ├── gpu_utils.py                       # GPU/CPU 自動選擇模組
│   └── notebook_bootstrap.py              # Notebook 共用初始化
├── pyproject.toml                         # 套件依賴與 Python 版本（3.10.19）
├── build_uv.sh / build_venv.sh            # 建立 venv
├── README.md                              # 專案說明
├── AGENT.md                               # 本文件
└── docs/
    ├── Step1_Data_Preprocessing.md
    ├── Step2_Feature_Extraction.md
    ├── Step3_Model_Training.md
    ├── Step4_Unknown_Detection.md
    ├── Step5_Random_Sampling_Detection.md
    ├── Step6_Model_Retraining.md
    └── Tensorflow.md                      # TensorFlow / GPU 使用指南
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
| Step 1 | `data/Step-{1..3}/{Motor}/{RPM}/{Screws}/` 原始 CSV | `data/Step-{1..3}/csv/` |
| Step 2 | `data/Step-{1..3}/csv/` | `data/Step-{1..3}/myfeature/` |
| Step 3 | `data/Step-{1..3}/myfeature/` | `data/Step-{1..3}/model/*.keras` |
| Step 4 | *.keras + 未知資料 | 偵測結果、叢集模型 |
| Step 5 | Step 4 的叢集模型 | 偵測結果（隨機批次）|
| Step 6 | 原始已知 + 未知資料 | 重訓練 *.keras 模型 |

---

## 模型編號系統

Step3 共 45 個 Notebook（基礎 9 + OneStage 18 + TwoStage 18），對應不同的實驗配置：

Model 01 ~ 27 是三個維度的完整交叉組合：

```
編號 N  →  馬達時期 = 01-09:T1 / 10-18:T2 / 19-27:T3
           轉速     = ((N-1) // 3) % 3  →  0:8000rpm  1:6000rpm  2:11000rpm
           架構     = (N-1) % 3         →  0:CNN  1:ResNet  2:VGG16
```

**資料夾 T 碼與模型檔名字母碼是反的**（最容易踩到的一點）：

| 資料目錄 | 馬達時期 | 模型檔名字母 |
|----------|----------|--------------|
| `data/Step-1/` | T1 | `*_C*.keras` |
| `data/Step-2/` | T2 | `*_B*.keras` |
| `data/Step-3/` | T3 | `*_A*.keras` |

只有 Model 01 ~ 03 從頭訓練，產出的 `{ARCH}_C8000.keras` 是全專案唯一的 baseline，其餘 24 組皆由此遷移（凍結前 50% 層）。OneStage 存檔帶 `_1`，TwoStage 不帶；8000rpm 的 TwoStage 其實與 OneStage 載入同一個模型，只有 6000/11000rpm 組才是真正的兩階段。Step 4/5 一律載入 OneStage 產物。

**重要：** Step N（N = 3~6）的 Notebook 編號必須對應，`Step3_Model_05.ipynb` 對應 `Step4_Model_05_Detecting.ipynb` 等。

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

## 模型規格

每個組合都會以 **CNN / ResNet / VGG16** 三種架構各訓練一次（論文稱 CNN_11 Layers / CNN_Res / CNN_VGG），輸入輸出與訓練設定一致，只有中間結構不同。以下為 CNN 基準架構：

```python
# CNN 架構（Step 3 / Step 6 共用）
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
6. **資料路徑：** 所有腳本使用相對路徑（以 `os.getcwd()` 為基準），並統一從 `data/` 目錄讀寫；請確保在專案根目錄執行（例如 `.../Lineage/`）。
7. **兩種特徵檔不可混用：** Step 3/6 讀 `*_Group_feature_data.csv`，Step 4/5 讀 `*_Group_feature_data_clean.csv`（IQR scale=1.5 逐列過濾後的版本）。
8. **掃描設定值時要排除註解：** 腳本裡留有不少被註解掉的舊設定（例如 `# groups = ['A', 'B', 'C']`），用 grep 判斷生效值時容易誤判。
9. **`logs/` 與 `output/` 納入版控：** 每次執行的紀錄會產生新檔案，提交前確認要不要一併帶上。

---

## 環境需求

套件與 Python 版本定義在 `pyproject.toml`（Python 釘在 3.10.19），依平台分成 `.[linux]`（`tensorflow[and-cuda]`）與 `.[mac]`（`tensorflow` + `tensorflow-metal`）兩組。

安裝：

```bash
./build_uv.sh        # Linux
./build_uv_mac.sh    # macOS
./build_venv.sh      # 標準 venv
```

執行時一律使用 `venv/bin/python` 與 `venv/bin/jupyter`，各步驟的 `.sh` 入口已經這樣寫，不需要先 activate。

### GPU 支援

本專案透過 `scripts/gpu_utils.py` 統一管理 GPU/CPU 選擇。所有 TensorFlow Notebook 在頂部匯入：

```python
from scripts.gpu_utils import device_scope, DEVICE
```

訓練區塊以 `with device_scope():` 包裹，有 GPU 時自動使用 `/GPU:0`，否則回退至 `/CPU:0`，不需手動修改任何參數。詳細說明見 [docs/Tensorflow.md](docs/Tensorflow.md)。

### GitHub

1. 允許在完成改動後進行 commit and push，但應該建立 PR 或 issues。
2. 允許 logs 和 output 推送至 GitHub，不需要加入至 .gitignore。
3. Agent 在進行 GitHub 相關操作的時候，將自己加入 Co-Authors。