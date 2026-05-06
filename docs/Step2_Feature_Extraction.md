# Step 2：特徵萃取 (Feature Extraction)

## 概述

Step 2 從 Step 1 處理後的訊號片段中萃取時域與頻域特徵，將原始波形轉換為 105 維特徵向量，作為後續機器學習模型的輸入。

---

## 目標

- 計算振動、電流、溫度訊號的統計特徵
- 對振動訊號執行 FFT，萃取諧波頻率幅值
- 輸出結構化特徵矩陣供 Step 3 模型訓練使用

---

## 腳本一覽

| 腳本 | 轉速 | 說明 |
|------|------|------|
| `Step2_Feature_Extraction_6000.py` 系列 | 6000 RPM | 萃取 6000 RPM 資料特徵 |
| `Step2_Feature_Extraction_8000.py` 系列 | 8000 RPM | 萃取 8000 RPM 資料特徵 |
| `Step2_Feature_Extraction_11000.py` 系列 | 11000 RPM | 萃取 11000 RPM 資料特徵 |

共 **9 支腳本**，每個轉速 3 支，對應不同馬達或資料配置。

---

## 特徵總覽

特徵共 **105 維**，依訊號類型分組：

| 訊號 | 統計特徵 | FFT 特徵 | 小計 |
|------|----------|----------|------|
| 電流（Current） | 15 | 0 | 15 |
| 振動 X 軸 | 15 | 10 | 25 |
| 振動 Y 軸 | 15 | 10 | 25 |
| 振動 Z 軸 | 15 | 10 | 25 |
| 溫度差（Delta_T） | 15 | 0 | 15 |
| **合計** | **75** | **30** | **105** |

---

## 特徵定義

### 時域統計特徵（每訊號 15 個）

| 特徵名稱 | 說明 |
|----------|------|
| RMS | 均方根值 |
| Mean | 算術平均值 |
| Kurtosis | 峰態係數（偵測衝擊特性） |
| Std Dev | 標準差 |
| Skewness | 偏態係數 |
| Peak-to-Peak | 峰值差（Max - Min）|
| Crest Indicator | 峰值因數（Peak / RMS）|
| Clearance Indicator | 餘隙指標 |
| Shape Indicator | 波形指標（RMS / Mean Amplitude）|
| Impulse Indicator | 衝擊指標（Peak / Mean Amplitude）|
| Max | 最大值 |
| Min | 最小值 |
| MSA | 均方幅值（Mean Square Amplitude）|
| Variance | 變異數 |
| Mean Amplitude | 平均振幅 |

### 頻域 FFT 特徵（振動三軸各 10 個）

對振動訊號進行 FFT 後，在基頻的 10 個諧波倍頻處提取幅值：

| 轉速 | 基頻 | 諧波頻率範圍 |
|------|------|-------------|
| 6000 RPM | ~100 Hz | 1× ~ 10× 基頻 |
| 8000 RPM | ~133 Hz | 1× ~ 10× 基頻 |
| 11000 RPM | 183 Hz | 183 ~ 1830 Hz |

FFT 參數：
- 取樣率：`Fs = 10000 Hz`
- 頻率解析度：依訊號長度決定
- 頻帶寬容：`dF1 ~ dF5`（可配置）

---

## 處理流程

```
讀取 data/Step-{1|2|3}/csv 資料
    ↓
逐段讀取 10,000 點資料
    ↓
計算 15 項時域統計特徵
    ↓
對振動訊號執行 FFT
    ↓
提取 10 個諧波幅值（三軸各 10 個）
    ↓
組合成 105 維特徵向量
    ↓
移除含 NaN 的列
    ↓
輸出 feature_data.csv
```

---

## 輸出

- **目錄：** `data/Step-{1|2|3}/myfeature/{Motor}/{RPM}/{Screws}/`
- **檔案：** `{Motor}_Group_feature_data.csv`（依 Notebook/腳本設定，可能為 `*_raw.csv` / `*_clean.csv` 等變體）
- **格式：** 每列 = 一個訊號片段，105 個特徵欄位
- **標籤：** 依螺絲配置（故障類別）標記

---

## 程式碼關鍵片段

### FFT 特徵萃取

```python
from scipy.fftpack import fft

N = len(signal)
freq = np.fft.fftfreq(N, d=1/Fs)
fft_vals = np.abs(fft(signal)) / N

# 提取基頻諧波幅值
for harmonic in range(1, 11):
    target_freq = harmonic * base_freq
    idx = np.argmin(np.abs(freq - target_freq))
    feature = fft_vals[idx]
```

### 統計特徵計算

```python
from scipy.stats import kurtosis, skew

rms = np.sqrt(np.mean(signal**2))
mean_amp = np.mean(np.abs(signal))
crest = np.max(np.abs(signal)) / rms
shape = rms / mean_amp
```

---

## 技術依賴

```python
import pandas as pd
import numpy as np
from scipy.fftpack import fft
from scipy.stats import kurtosis, skew
```

---

## 注意事項

- FFT 基頻應依實際轉速換算（RPM / 60）
- 取樣率 `Fs = 10000 Hz` 須與 Step 1 資料一致
- NaN 值以 `dropna()` 直接移除，不進行插補
- 特徵矩陣的欄位順序需與 Step 3 模型輸入保持一致
