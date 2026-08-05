# Lineage 全流程執行報告

> 執行分支：`docs/sync-with-code`（疊了 #45 / #46 / #47，等於目前所有修正都在內）
> 開始時間：2026-08-05 15:00（本機時間）

---

## 執行前盤點

### ⛔ Step 1 無法執行 — 原始量測資料不存在

Step 1 的腳本讀的是這個路徑：

```python
rawDataDirectories = {
    motor: {screws: os.path.join(stepDir, motor, '6000rpm', f'{screws}screws') ...}
}
# → data/Step-1/T1/6000rpm/8screws/ ...
```

實際上 `data/Step-1/` 底下**只有 `csv/`、`model/`、`myfeature/` 三個目錄**，沒有 `T1/`、`T2/`、`T3/`：

```
$ ls data/Step-1/
csv  model  myfeature

$ ls -d data/Step-1/T1
ls: cannot access 'data/Step-1/T1': No such file or directory
```

專案根目錄的 `data.zip`（4.9 GB）也不是原始資料。它的內容是：

```
data/階段1.zip   1.6 GB  →  階段1/{csv.zip, model.zip, myfeature.zip}
data/階段2.zip   1.6 GB
data/階段3.zip   1.7 GB
```

也就是說，`data.zip` 存的是 **Step 1 的產物（csv）以及 myfeature、model 的備份**，不是 Step 1 的輸入。原始量測檔（tab 分隔、標頭在第 22 行的那種）在 repo 與壓縮檔裡都找不到。

**結論：Step 1 無法執行。** 但它的產物已經齊全，可以直接作為 Step 2 的輸入：

| 目錄 | 檔數 | 大小 |
|---|---|---|
| `data/Step-1/csv/` | 150 | 9.3 GB |
| `data/Step-2/csv/` | 150 | 9.2 GB |
| `data/Step-3/csv/` | 150 | 9.3 GB |

因此本次實際執行範圍為 **Step 2 → Step 6**。

### 環境

| 項目 | 值 |
|---|---|
| Python | 3.10.19 |
| TensorFlow | 2.21.0（CUDA 12.5.1 / cuDNN 9）|
| GPU | NVIDIA L40S，46 GB VRAM |
| 磁碟可用 | 272 GB |

---

## 執行計畫

| # | 步驟 | 標的 | 狀態 |
|---|---|---|---|
| 1 | Step 1 | 12 支腳本 | ⛔ 略過（無原始資料）|
| 2 | Step 2 | 9 支特徵萃取腳本 | ⏳ 待執行 |
| 3 | Step 3 | 45 個訓練 Notebook | ⏳ 待執行 |
| 4 | Step 4 | 27 個偵測 Notebook | ⏳ 待執行 |
| 5 | Step 5 | 27 個隨機驗證 Notebook | ⏳ 待執行 |
| 6 | Step 6 | 27 個重訓練 Notebook | ⏳ 待執行 |

各步驟以對應的 `.sh` 依序執行；`.sh` 內含 `set -e`，任一支失敗會立刻中止，便於定位問題。

### 預期的資料變動

- **Step 2 會覆寫 `myfeature/` 全部內容。** T1/T3 現有的 `_clean.csv` 是 2025-05 的產物、早於 commit 6dcf371 的 bug 修正，會被重新產生；先前 Step 4/5 的結果因此無法重現。T2 則會**第一次**擁有 `_clean.csv`。
- **Step 3 / Step 6 會覆寫 `model/` 的 .keras 檔。**

---

## 執行紀錄

（以下隨執行進度更新）

### 2026-08-05 15:02 — 開跑前先撞到一個 runner 腳本的 bug

第一次啟動 Step 2 時，腳本在 0 秒內就結束、什麼都沒做。原因是六支 `.sh` 的開頭都是：

```bash
set -e

clear
```

在沒有 TTY 的環境（`nohup`、cron、CI）下 `TERM` 不會被設定，`clear` 會印出 `TERM environment variable not set.` 並**回傳 1**，於是 `set -e` 立刻中止整支腳本：

```
$ env -u TERM clear; echo "離開碼 = $?"
TERM environment variable not set.
離開碼 = 1
```

失敗是完全靜默的——`step2.out` 裡只有那一行 TERM 訊息，沒有任何錯誤堆疊，也沒有「開始執行」的字樣。

**繞法：** 執行時補上 `TERM=xterm`。本次全流程都以這個方式啟動。

**建議修正：** `clear` 改成 `clear 2>/dev/null || true`，讓腳本在非互動環境下也能跑。這會影響全部六支 runner 腳本，另外開 issue 追蹤。

---

### Step 2：特徵萃取

- 啟動：2026-08-05 15:02（`TERM=xterm ./Step2_Feature_Extraction.sh`）
- 狀態：🔄 執行中

### 15:03 — Step 2 中止：`drop_feature_outliers` 未定義（我在 PR #43 留下的 bug）

第 3 支腳本一啟動就炸：

```
Traceback (most recent call last):
  File "Step2_Feature_Extraction_6000_3.py", line 265, in process_group
    clean_data = drop_feature_outliers(feature_data)
NameError: name 'drop_feature_outliers' is not defined
```

盤點 9 支腳本後發現**只有 5 支真的有函式定義**，另外 4 支只加了呼叫端：

| 腳本 | 定義 | 呼叫 |
|---|---|---|
| `6000_1` / `6000_2` / `8000_1` / `8000_3` / `11000_1` | ✓ | ✓ |
| `6000_3` / `8000_2` / `11000_2` / `11000_3` | **✗** | ✓ |

**成因：** PR #43 以 `def align_rows(*arrays):` 當插入錨點，但這 4 支腳本結構不同、根本沒有 `align_rows`。`str.replace` 找不到目標時不報錯、原樣返回，定義就被靜默丟棄。

**為什麼當初的驗證沒抓到：** 只做了 `ast.parse`（NameError 是執行期錯誤，語法檢查必過），加上一支隔離的端對端試跑——而那支剛好是有定義的 5 支之一。

**修正（PR #48）：** 改以 `def process_group(...)` 為錨點（9 支都有），插入後斷言定義存在。驗證方式改成實際 import 9 支模組並呼叫函式，203 → 199 列，9/9 通過。

**Step 2 已從頭重跑。**

---

### Step 2：特徵萃取（第二次）

- 啟動：2026-08-05 15:12
- 狀態：🔄 執行中

**✅ 完成** 2026-08-05 15:20（約 8 分鐘）

全量驗證：90 個配置（9 組合 × 10 螺絲）全部產出 `.csv` 與 `_clean.csv`，維度皆為 105，無缺檔、無錯誤。

| 組合 | 配置 | raw 列 | clean 列 | 保留 |
|---|---|---|---|---|
| T1/6000rpm | 10 | 5950 | 3354 | 56% |
| T1/8000rpm | 10 | 5918 | 3049 | 52% |
| T1/11000rpm | 10 | 5800 | 3349 | 58% |
| T2/6000rpm | 10 | 5989 | 3186 | 53% |
| T2/8000rpm | 10 | 5970 | 3249 | 54% |
| T2/11000rpm | 10 | 5990 | 3417 | 57% |
| T3/6000rpm | 10 | 5993 | 2939 | 49% |
| T3/8000rpm | 10 | 5988 | 3221 | 54% |
| T3/11000rpm | 10 | 5990 | 3127 | 52% |
| **合計** | **90** | **53588** | **28891** | **54%** |

重點成果：

- **T2 首次擁有 `_clean.csv`**（先前 0 份），Step 4/5 的 Model 10–18 終於有資料可讀。
- **T1/8000rpm 的 baseline 特徵已更新**，不再是 2025-04-23 的舊檔（#36 修正生效，`_raw.csv` 不再產生）。
- 殘留一個孤兒檔 `data/Step-1/myfeature/T1/8000rpm/8screws/T1_Group_feature_data_raw.csv`（2026-06-12），已無任何讀取端，可刪。

---

### Step 3：模型訓練（45 個 Notebook）

- 啟動：2026-08-05 15:21
- 狀態：🔄 執行中

### 15:26 — Step 3 中止：baseline 訓練出 NaN 模型（既有 bug）

Step 3 跑到 8/45 時，我檢查 Model 01 的訓練紀錄發現：

```
Step3_Model_01   Loss: nan, Accuracy: 0.2017
```

**0.2017 正好是 5 類的隨機猜測水準。** 模型照樣存檔、notebook 照樣「成功」結束，`set -e` 完全不會觸發——這種失敗只會在準確率上顯示為「剛好等於 1/類別數」。已立即中止 Step 3，否則會白白產出 45 個廢模型（Model 01~03 是 baseline，後面 24 組全部由它衍生）。

**根因：** `Step2_Feature_Extraction_8000_1.py` 第 305 行的缺失值處理被註解掉：

```python
# 處理缺失值：刪除整行
# feature_data = drop_missing_values(feature_data)
```

9 支腳本裡只有這一支是註解狀態，其餘 8 支都生效。偏偏這支產出的是 **T1/8000rpm**，也就是全專案唯一的 baseline 訓練資料。

`8screws` 最後一列的 `3-Current-kurtosis` 與 `5-Current-skewness` 是 NaN，直接寫進特徵檔。2972 × 105 個值裡只要有一個 NaN，梯度更新就會把整個網路汙染。

**這是既有 bug，不是前面幾個 PR 造成的。**

**修正（PR #49）：** 取消該行註解並重跑該支腳本。T1/8000rpm/8screws 從 600 列回到 **599 列**、clean **313 列**——與 2025-04-23 那份歷史特徵檔完全一致，佐證這正是原本應有的行為。

**複驗：** 全專案 90 個配置，含 NaN 的列數 **0**。


**修正後複驗 baseline：**

| | Loss | Accuracy |
|---|---|---|
| 修正前 | `nan` | 0.2017（= 1/5，隨機猜測）|
| **修正後** | **0.0003** | **1.0000** |

已另開兩個 issue：
- **#50** 訓練出 NaN 模型不會失敗，只會靜默產出隨機水準準確率 → 建議在 Step 3/6 加訓練前後斷言
- **#51** 9 支 runner 腳本在非互動環境下因 `clear` + `set -e` 靜默失敗

---

### Step 3：模型訓練（第二次，45 個 Notebook）

- 啟動：2026-08-05 15:30
- 狀態：🔄 執行中

**✅ 完成** 2026-08-05 15:52（約 22 分鐘）

| 指標 | 結果 |
|---|---|
| 取得結果的 Notebook | **45 / 45** |
| Loss 為 NaN | **0** |
| 準確率 ≤ 0.25（未收斂） | **0** |
| 準確率範圍 | 0.9883 ~ 1.0000，平均 **0.9986** |
| 準確率 = 1.0000 | 31 個 |
| 產出模型檔 | **45**（Step-1: 9、Step-2: 18、Step-3: 18）|

準確率最低的五個（全部仍在 0.98 以上）：

| Notebook | Loss | Accuracy |
|---|---|---|
| `Step3_Model_24_TwoStage` | 0.0440 | 0.9883 |
| `Step3_Model_27_TwoStage` | 0.0622 | 0.9900 |
| `Step3_Model_27_OneStage` | 0.0495 | 0.9917 |
| `Step3_Model_23_OneStage` | 0.0243 | 0.9933 |
| `Step3_Model_23_TwoStage` | 0.0276 | 0.9933 |

順帶驗證到的修正：

- **`data/Step-2/model/` 原本不存在**（issue #35），這次靠 `os.makedirs(exist_ok=True)` 自動建立，18 個 T2 模型全部落地。
- VGG16 的 notebook 用 `Screw Number Loss: ... Screw Number Accuracy: ...` 這種輸出格式，與 CNN/ResNet 不同；清點時需同時涵蓋兩種格式。

---

### Step 4：未知故障偵測（27 個 Notebook）

- 啟動：2026-08-05 15:53
- 狀態：🔄 執行中
- 重點：這是 T2 的 `_clean.csv` 第一次被使用（Model 10–18）

### 15:55 — Step 4 中止：ResNet 沒有 flatten 層（既有 bug）

Step 4 跑到第 2 個 notebook 就整批中止：

```
ValueError: No such layer: flatten. Existing layers are:
['input_layer', 'conv1d', 'batch_normalization', ... 'global_average_pooling1d', 'Screw_Number_Output']
```

**根因：** Step 4/5 硬編死中間層名稱 `cnn.get_layer('flatten')`，但三種架構的特徵層並不同名——ResNet 用 Global Average Pooling，根本沒有 Flatten 層。

| 模型 | 層數 | 特徵層 | 維度 |
|---|---|---|---|
| `CNN_C8000` | 12 | `flatten` | 176 |
| `VGG16_C8000` | 25 | `flatten` | 48 |
| **`ResNet_C8000`** | **69** | **`global_average_pooling1d`** | **128** |

影響 18 個 notebook（Step4/5 各 9 個）。因為 `.sh` 有 `set -e`，27 個裡只有第 1 個跑得完。

**修正（issue #52 / PR #53）：** 新增 `scripts/model_utils.py`，依序嘗試候選層名、找不到再退回輸出層前一層。54 個 notebook 的 81 處呼叫全部改用 `get_feature_layer(cnn)`。

**驗證：** 實跑先前失敗的 `Step4_Model_02`（ResNet），離開碼 0，偵測結果分離乾淨——已知叢集距離 2.57~2.99，未知叢集 17.86~41.50。

**順帶發現（尚未處理）：** 27 個 Step 4 notebook 裡**只有 `Step4_Model_01` 有 `plt.show()`**，其餘 26 個完全不繪圖，只把叢集距離印進 log。Step 5 則 27 個都有繪圖。README 描述的「長條圖：各未知螺絲配置的叢集中心距離 vs. 閾值」實際上只有 1/27 會產出。

**另註：** README 寫「Flatten 層的 176 維輸出作為無監督特徵空間」，實際三種架構維度不同（176 / 128 / 48），文件待更新。

---

### Step 4：未知故障偵測（第二次）

- 啟動：2026-08-05 16:20
- 狀態：🔄 執行中

**✅ 完成** 2026-08-05 16:35（約 15 分鐘）

| 指標 | 結果 |
|---|---|
| 完成的 Notebook | **27 / 27** |
| ValueError / Traceback | **0** |
| 「缺少檔案」警告 | **0** |
| 判定 Known 的叢集次數 | 9137 |
| 判定 New Fault 的叢集次數 | 3652 |
| 存下的圖 | 11 張（全部來自 Model_01）|

重點驗證：

- **T2（Model 10–18）第一次真的有資料可跑。** 修正前 T2 完全沒有 `_clean.csv`，這 9 個 notebook 只會印一串「缺少檔案」然後拿空 DataFrame 往下走。這次「缺少檔案」出現 **0 次**，叢集大小 61~74、距離 2.4~3.0，資料確實讀進去了。
- **ResNet 的 9 個 notebook（#53）全部通過**，先前它們 100% 拋 `ValueError`。
- 偵測邏輯本身有效，已知與未知的馬氏距離分離明確（例：Model_02 已知 2.57~2.99、未知 17.86~41.50）。

已知缺口：**27 個 notebook 裡只有 `Model_01` 會繪圖**，其餘 26 個只把距離印進 log，所以「存下的圖」只有 11 張。

---

### Step 5：隨機取樣驗證（27 個 Notebook）

- 啟動：2026-08-05 16:36
- 狀態：🔄 執行中

### 16:37 — Step 5 中止：27 個 notebook 全缺 `import random`（既有 bug）

第 1 個 notebook 就 `NameError: name 'random' is not defined`。

**根因：** commit 738a603（`cleanup: remove unused imports`）把 `import random` 當成未使用的 import 移除，但它其實有用到——`random.randint`、`random.sample`、`random.seed`，隨機取樣正是 Step 5 的核心。**自那次之後 Step 5 就沒辦法執行過。**

順手做了全面掃描（Step3~6 全部 notebook 的「使用但未綁定的名稱」靜態檢查）：

```
[27 個 notebook] 缺：['random']
```

只有這一項，738a603 其他的移除都是正確的。

**修正（issue #54 / PR #55）：** 27 個 notebook 補回 `import random`。修正後靜態掃描 0 項。

**驗證：** 實跑 `Step5_Model_01`，離開碼 0，輸出 `▶ mcs=25 | conf=0.95 | thr=16.40`，產出 3 張圖。

---

### Step 5：隨機取樣驗證（第二次）

- 啟動：2026-08-05 16:45
- 狀態：🔄 執行中

**✅ 完成** 2026-08-05 16:57（約 12 分鐘）

| 指標 | 結果 |
|---|---|
| 完成的 Notebook | **27 / 27** |
| 錯誤 | **0** |
| 馬氏距離閾值 | 7.55 ~ 18.40，平均 13.00 |
| 存下的圖 | **81 張**（每個 notebook 各 3 張，全數齊全）|

與 Step 4 的對照很明顯：Step 5 的 27 個 notebook 都有繪圖，Step 4 只有 1 個。

---

### Step 6：模型重訓練（27 個 Notebook）

- 啟動：2026-08-05 16:58
- 狀態：🔄 執行中
- 重點：這是 `train_guard`（#50 / PR #56）第一次在整批執行中受檢驗——27 個 notebook 都帶著訓練前後的斷言

**✅ 完成** 2026-08-05 17:12（約 14 分鐘）

| 指標 | 結果 |
|---|---|
| 完成的 Notebook | **27 / 27** |
| `train_guard` 攔截 | **0**（無誤判）|
| 10 類準確率 | 0.9983 ~ 1.0000，平均 **0.9998** |
| 準確率 = 1.0000 | 21 個 |
| 準確率 ≤ 0.15（隨機水準） | **0** |
| 產出 `*_retrained.keras` | **27**（Step-1/2/3 各 9 個）|

兩項修正在此步驟得到驗證：

- **issue #33（Step 6 沒有存檔）** —— 修正前 27 個 notebook 全都沒有 `model.save()`，重訓練結果只存在記憶體、notebook 結束就消失。這次 27 個 `*_retrained.keras` 全部落地，命名規則 `{ARCH}_{LETTER}{RPM}_retrained.keras`。
- **issue #50（`train_guard`）** —— 27 個正常訓練連續通過、零誤判。防護誤擋正常訓練比不擋還糟，這點通過了考驗。

---
---

# 全流程總結

**執行日期：** 2026-08-05 15:00 – 17:12（約 2 小時 12 分）
**分支：** 依序疊加各修正分支，最終為 `fix/step5-missing-random-import`

## 一、執行結果

| 步驟 | 標的 | 結果 | 耗時 |
|---|---|---|---|
| Step 1 | 12 支腳本 | ⛔ **無法執行**——原始量測資料不存在 | — |
| Step 2 | 9 支特徵萃取 | ✅ 90 個配置全數產出，NaN 0 列 | 8 分 |
| Step 3 | 45 個訓練 Notebook | ✅ 45/45，準確率 0.9883~1.0000 | 22 分 |
| Step 4 | 27 個偵測 Notebook | ✅ 27/27，錯誤 0 | 15 分 |
| Step 5 | 27 個隨機驗證 | ✅ 27/27，錯誤 0 | 12 分 |
| Step 6 | 27 個重訓練 | ✅ 27/27，準確率 0.9983~1.0000 | 14 分 |

**產出：** 特徵檔 181 個、模型檔 74 個（含 27 個 `*_retrained.keras`）、執行紀錄 181 份、圖 777 張。

### Step 1 為什麼跑不了

腳本讀 `data/Step-1/{T1}/{rpm}/{screws}/`，但該層不存在——`data/Step-1/` 底下只有 `csv/`、`model/`、`myfeature/`。根目錄的 `data.zip`（4.9 GB）內容是 `階段{1,2,3}.zip` → 各自的 `{csv,model,myfeature}.zip`，也就是 **Step 1 的產物備份，不是它的輸入**。原始量測檔（tab 分隔、標頭在第 22 行、含 `X_Value`/`Temp_A`/`Temp_B`/`Comment` 欄）在 repo 與壓縮檔裡都找不到。

Step 1 的產物齊全（三個 `csv/` 各 150 檔、共 28 GB），因此改由 Step 2 起跑。若日後補上原始資料，Step 1 可獨立補跑。

## 二、發現並修正的 6 個既有 bug

跑之前這條產線**沒有任何一步能完整跑完**。

| # | Issue | 問題 | 影響 | PR |
|---|---|---|---|---|
| 1 | #51 | 9 支 `.sh` 因 `clear` + `set -e` 在非互動環境靜默失敗 | 所有背景/排程執行 | 未修（繞法：`TERM=xterm`）|
| 2 | — | 4 支 Step2 腳本漏掉 `drop_feature_outliers` 定義 | Step 2 跑到第 3 支中止 | #48 |
| 3 | #49 | `8000_1` 的 `drop_missing_values` 被註解，baseline 含 NaN | **45 個模型全部變成隨機猜測水準** | #49 |
| 4 | #52 | Step4/5 硬編 `get_layer('flatten')`，ResNet 沒有該層 | 18 個 notebook 100% 拋 ValueError | #53 |
| 5 | #54 | Step 5 的 27 個 notebook 全缺 `import random` | Step 5 自 738a603 起從未跑成功過 | #55 |
| 6 | #50 | NaN 訓練不會失敗，只靜默產出隨機水準模型 | 讓上述第 3 項難以察覺 | #56 |

其中第 2 項是我自己在 PR #43 留下的（錨點不存在時 `str.replace` 靜默無作用），其餘五項都是既有問題。

### 最值得記的一個

**第 3 項**：`Step2_Feature_Extraction_8000_1.py` 第 305 行的 `drop_missing_values` 被註解掉——9 支腳本裡只有這一支。偏偏它產出的是 T1/8000rpm，全專案唯一的 baseline。

一列 NaN（2972 × 105 個值裡的 2 個）就讓 `Step3_Model_01` 訓練出：

```
Loss: nan, Accuracy: 0.2017      # 0.2017 = 1/5，隨機猜測
```

模型照樣存檔、notebook 照樣「成功」結束、`set -e` 不觸發。若沒有中途比對訓練 log，會白白產出 45 個廢模型並往下汙染 Step 4/5/6。這正是 #50 `train_guard` 要防的情境。

## 三、先前修正在真實執行中的驗證

| Issue | 修正內容 | 驗證方式 |
|---|---|---|
| #34 | Step 2 產生 `_clean.csv` | T2 首次有 clean 檔，Step 4 的 Model 10–18 「缺少檔案」0 次、叢集大小 61~74 |
| #35 | `data/Step-2/model/` 自動建立 | 18 個 T2 模型全部落地 |
| #33 | Step 6 補上 `model.save()` | 27 個 `*_retrained.keras` 全部產出 |
| #36 | `_raw.csv` 檔名統一 | baseline 特徵已更新，不再是 2025-04-23 的舊檔 |
| #50 | `train_guard` | 27 個正常訓練零誤判 |
| #52 | 依架構取特徵層 | ResNet 的 18 個 notebook 全數通過 |

## 四、待處理

**尚未修正：**

- **#51** 9 支 runner 腳本的 `clear` + `set -e`（本次以 `TERM=xterm` 繞過）
- **#37 / #38** 已有 PR #46 / #47

**本次新發現、尚未開 issue：**

1. **27 個 Step 4 notebook 裡只有 `Model_01` 會繪圖**，其餘 26 個完全沒有 `plt.show()`，只把叢集距離印進 log。README 描述的「距離長條圖」實際上只有 1/27 產出。（Step 5 則 27 個都有，共 81 張。）
2. **README 寫「Flatten 層的 176 維輸出作為無監督特徵空間」**，實際三種架構維度不同：CNN 176、ResNet 128、VGG16 48。
3. **孤兒檔** `data/Step-1/myfeature/T1/8000rpm/8screws/T1_Group_feature_data_raw.csv`，已無任何讀取端。

**資料層面：**

- T1/T3 的 `_clean.csv` 已全部重新產生，先前 Step 4/5 的結果無法重現（但那些本來就是拿修 bug 前的特徵算的）。
- `data/Step-3/model/` 裡過期的 `VGG16_A8000_1.keras`、`VGG16_A6000_1.keras` 已被本次執行覆蓋為正確版本。
