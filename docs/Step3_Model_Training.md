# Step 3：模型訓練 (Model Training)

## 概述

Step 3 使用 Step 2 萃取的 105 維特徵向量，訓練一維卷積神經網路（1D CNN），建立馬達故障類型的分類模型，可辨識 5 種已知故障狀態。

---

## 目標

- 訓練 CNN 模型區分已知的 5 種故障類別
- 儲存訓練好的模型供 Step 4 偵測使用
- 建立中間層特徵萃取器用於異常偵測
- 評估模型在測試集上的表現

---

## Notebook 一覽

| 模型範圍 | 說明 |
|----------|------|
| Model 1 ~ 9 | 基礎版本，對應不同轉速 / 馬達配置組合 |
| Model 10 ~ 18 | OneStage 變體 |
| Model 19 ~ 27 | TwoStage 變體 |

共 **27 個 Jupyter Notebook**（Step3_Model 1.ipynb ~ Step3_Model 27.ipynb）

---

## 分類目標

| 類別標籤 | 螺絲配置 | 狀態說明 |
|----------|----------|----------|
| 0 | 8 screws | 健康（Healthy）|
| 1 | 1 screw | 故障 1（Faulty 1）|
| 2 | 2 screws | 故障 2（Faulty 2）|
| 3 | 3 screws | 故障 3（Faulty 3）|
| 4 | 4 screws | 故障 4（Faulty 4）|

---

## CNN 模型架構

輸入：`105 × 1`（105 維特徵向量，重塑為 1D 序列）

```
Input (105, 1)
    ↓
Conv1D(16 filters, kernel=3, padding='same', ReLU)
    ↓
Conv1D(16 filters, kernel=3, ReLU) → MaxPooling1D(2)
    ↓
Conv1D(16 filters, kernel=3, ReLU) → MaxPooling1D(2)
    ↓
Conv1D(16 filters, kernel=3, ReLU) → MaxPooling1D(2)
    ↓
Flatten
    ↓
Dense(16, ReLU)
    ↓
Dropout(0.3)
    ↓
Dense(5, Softmax)   ← 5 類輸出
```

**層數：** 11 層（含 4 個卷積層、3 個池化層、Flatten、2 個全連接層、1 個 Dropout）

---

## 訓練配置

| 參數 | 值 |
|------|----|
| 優化器 | Adam（learning_rate = 1e-4）|
| 損失函數 | Sparse Categorical Crossentropy |
| 訓練週期 | 最多 100 epochs |
| 批次大小 | 32 |
| 訓練/測試比例 | 80 / 20 |
| 早停策略 | EarlyStopping（patience = 10）|

---

## 訓練流程

```
讀取 feature_data.csv
    ↓
資料標準化（視模型配置）
    ↓
訓練/測試集切割（80/20）
    ↓
模型建構（Keras Sequential）
    ↓
模型訓練（fit with EarlyStopping）
    ↓
評估：混淆矩陣、學習曲線
    ↓
儲存完整模型（.keras）
    ↓
建立中間層萃取器（Flatten 層輸出）
```

---

## 模型輸出

| 輸出物 | 說明 |
|--------|------|
| `*.keras` | 完整分類模型 |
| 中間層萃取器 | 用於 Step 4 HDBSCAN 輸入的特徵萃取子模型 |
| 混淆矩陣圖 | 測試集各類別預測結果 |
| 學習曲線圖 | Accuracy 與 Loss 隨 epoch 的變化 |

---

## 模型表現

- 測試集準確率：通常達到 **100%**
- 早停機制有效防止過擬合
- Dropout(0.3) 增強模型泛化能力

---

## OneStage vs TwoStage 說明

| 類型 | 說明 |
|------|------|
| 基礎（Model 1-9） | 單一 CNN 直接分類 5 類 |
| OneStage（Model 10-18） | 調整資料組合策略，一階段偵測 |
| TwoStage（Model 19-27） | 兩階段設計：先判定健康/故障，再細分故障類型 |

---

## 技術依賴

```python
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
```

---

## 注意事項

- 模型儲存路徑需與 Step 4 讀取路徑一致
- 中間層（Flatten 層）輸出用作 Step 4 的無監督特徵空間
- Step 6 重訓練時，輸出層需從 5 類擴充為 10 類
- 各 Model 編號對應不同的轉速、馬達類型或資料切割方式，需對照索引表確認對應關係
