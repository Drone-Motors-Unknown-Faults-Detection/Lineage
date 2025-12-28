### 論文馬達研究
### 第二步 特徵提取
### 6000rpm

import os
import numpy as np
import pandas as pd
from scipy.fftpack import fft
import matplotlib.pyplot as plt
from scipy.stats import kurtosis, skew
from natsort import natsorted
import warnings

warnings.filterwarnings("ignore")

# ========================
# 設定參數與路徑
# ========================
rootDir = os.getcwd()
csvDirectory = os.path.join(rootDir, '階段3', 'csv')
myfeatureDirectory = os.path.join(rootDir, '階段3', 'myfeature')

rawdata = 10000  # 每個檔案的點數
rawdata2 = rawdata // 2
Fs = 10000       # 取樣率
T = 1 / Fs
dF = Fs / rawdata  # 頻率解析度
t = np.linspace(0, rawdata - 1, rawdata) * T
freq = np.linspace(0, rawdata2 - 1, rawdata2) * dF

rpm = 6000
baseFreq1 = 100  # 基頻
dFreq1, dFreq2, dFreq3, dFreq4, dFreq5 = 5, 8, 10, 12, 15  # 頻率範圍

feature_name = [
    # Current features
    '1-Current-rms','2-Current-mean','3-Current-kurtosis','4-Current-std','5-Current-skewness',
    '6-Current-peak2peak','7-Current-crest_indicator','8-Current-clearance_indicator',
    '9-Current-shape_indicator','10-Current-impulse_indicator','11-Current-max',
    '12-Current-min','13-current-msa','14-current-variance','15-current-mean_amplitude',

    # Vibration_X features
    '16-Vibration_X-rms','17-Vibration_X-mean','18-Vibration_X-kurtosis','19-Vibration_X-std',
    '20-Vibration_X-skewness','21-Vibration_X-peak2peak','22-Vibration_X-crest_indicator',
    '23-Vibration_X-clearance_indicator','24-Vibration_X-shape_indicator',
    '25-Vibration_X-impulse_indicator','26-Vibration_X-max','27-Vibration_X-min',
    '28-Vibration_X-msa','29-Vibration_X-variance','30-Vibration_X-mean_amplitude',
    '31-Vibration_X-FFT1X','32-Vibration_X-FFT2X','33-Vibration_X-FFT3X','34-Vibration_X-FFT4X',
    '35-Vibration_X-FFT5X','36-Vibration_X-FFT6X','37-Vibration_X-FFT7X','38-Vibration_X-FFT8X',
    '39-Vibration_X-FFT9X','40-Vibration_X-FFT10X',

    # Vibration_Y features
    '41-Vibration_Y-rms','42-Vibration_Y-mean','43-Vibration_Y-kurtosis','44-Vibration_Y-std',
    '45-Vibration_Y-skewness','46-Vibration_Y-peak2peak','47-Vibration_Y-crest_indicator',
    '48-Vibration_Y-clearance_indicator','49-Vibration_Y-shape_indicator',
    '50-Vibration_Y-impulse_indicator','51-Vibration_Y-max','52-Vibration_Y-min',
    '53-Vibration_Y-msa','54-Vibration_Y-variance','55-Vibration_Y-mean_amplitude',
    '56-Vibration_Y-FFT1X','57-Vibration_Y-FFT2X','58-Vibration_Y-FFT3X','59-Vibration_Y-FFT4X',
    '60-Vibration_Y-FFT5X','61-Vibration_Y-FFT6X','62-Vibration_Y-FFT7X','63-Vibration_Y-FFT8X',
    '64-Vibration_Y-FFT9X','65-Vibration_Y-FFT10X',

    # Vibration_Z features
    '66-Vibration_Z-rms','67-Vibration_Z-mean','68-Vibration_Z-kurtosis','69-Vibration_Z-std',
    '70-Vibration_Z-skewness','71-Vibration_Z-peak2peak','72-Vibration_Z-crest_indicator',
    '73-Vibration_Z-clearance_indicator','74-Vibration_Z-shape_indicator',
    '75-Vibration_Z-impulse_indicator','76-Vibration_Z-max','77-Vibration_Z-min',
    '78-Vibration_Z-msa','79-Vibration_Z-variance','80-Vibration_Z-mean_amplitude',
    '81-Vibration_Z-FFT1X','82-Vibration_Z-FFT2X','83-Vibration_Z-FFT3X','84-Vibration_Z-FFT4X',
    '85-Vibration_Z-FFT5X','86-Vibration_Z-FFT6X','87-Vibration_Z-FFT7X','88-Vibration_Z-FFT8X',
    '89-Vibration_Z-FFT9X','90-Vibration_Z-FFT10X',

    # Delta_T features
    '91-Delta_T-rms','92-Delta_T-mean','93-Delta_T-kurtosis','94-Delta_T-std','95-Delta_T-skewness',
    '96-Delta_T-peak2peak','97-Delta_T-crest_indicator','98-Delta_T-clearance_indicator',
    '99-Delta_T-shape_indicator','100-Delta_T-impulse_indicator','101-Delta_T-max',
    '102-Delta_T-min','103-Delta_T-msa','104-Delta_T-variance','105-Delta_T-mean_amplitude'
]

# ========================
# 定義函式
# ========================

def fourier_transform(data, lenFeature, group_label, rpm, screws, feature_type='Vibration_X'):
    """
    對原始信號進行傅立葉變換並繪製頻譜圖，並在圖表上標示 rpm 和 screws 信息
    """
    rawdata = len(data)
    rawdata2 = rawdata // 2
    myfft = np.abs(fft(data, axis=0)) * 2 / rawdata  # 計算 FFT 並取得幅值
    myfft2 = myfft[:rawdata2, :]  # 只保留前半部分頻譜數據

    plt.figure(figsize=(10, 6))
    plt.plot(freq, myfft2[:, 0])  # 繪製第一個特徵的頻譜圖
    plt.ylabel('Amplitude')
    plt.xlabel('Hz')
    
    # 建立標題，包含 feature_type, group_label, rpm 和 screws 信息
    title = f'Group {group_label} - {feature_type} - {rpm}rpm {screws}'
    plt.title(title)
    
    # 可選：在圖表內部添加文字標籤
    plt.text(0.95, 0.95, f'{rpm}rpm {screws}', horizontalalignment='right',
             verticalalignment='top', transform=plt.gca().transAxes,
             fontsize=12, bbox=dict(facecolor='white', alpha=0.5))
    
    plt.grid(True)
    plt.show()

    return myfft2

def extract_statistical_features(df, num_features):
    """
    提取統計特徵
    """
    features = np.zeros((df.shape[1], num_features))
    for i in range(df.shape[1]):
        data = df.iloc[:, i]
        features[i, 0] = np.sqrt(np.mean(data**2))  # rms
        features[i, 1] = np.mean(data)              # mean
        features[i, 2] = kurtosis(data, fisher=False)  # kurtosis
        features[i, 3] = np.std(data)               # std
        features[i, 4] = skew(data)                  # skewness
        features[i, 5] = np.ptp(data)                # peak2peak
        features[i, 6] = np.abs(data.max() / np.sqrt(np.mean(data**2)))  # crest_indicator
        features[i, 7] = np.abs(data.max() / np.mean(np.sqrt(np.abs(data)**2)))  # clearance_indicator
        features[i, 8] = np.sqrt(np.mean(data**2)) / np.mean(np.abs(data))  # shape_indicator
        features[i, 9] = np.abs(data.max() / np.mean(np.abs(data)))        # impulse_indicator
        features[i, 10] = data.max()              # Max
        features[i, 11] = data.min()              # Min
        features[i, 12] = np.mean(data**2)        # MSA (Mean Square Amplitude)
        features[i, 13] = np.var(data)            # Variance
        features[i, 14] = np.mean(np.abs(data))   # Mean Amplitude
    return features

def handle_missing_values(df, method="mean"):
    """
    處理缺失值
    :param df: 包含缺失值的 DataFrame
    :param method: 缺失值處理方法
        - "mean": 用列的均值填充
        - "median": 用列的中位數填充
        - "mode": 用列的眾數填充
    :return: 缺失值處理後的 DataFrame
    """
    if method == "mean":
        return df.fillna(df.mean())
    elif method == "median":
        return df.fillna(df.median())
    elif method == "mode":
        return df.fillna(df.mode().iloc[0])  # 取第一個眾數
    else:
        raise ValueError("Invalid method. Choose from 'mean', 'median', or 'mode'.")
    
def drop_missing_values(df):
    """
    刪除所有包含空值的 row
    """
    return df.dropna()

def extract_fft_features(Hfeat, base_freq, d_freqs, num_fft_features=10):
    """
    從傅立葉變換結果中提取 FFT 特徵
    """
    fft_features = []
    for i in range(1, num_fft_features + 1):
        target_freq = base_freq * i
        d_freq = d_freqs[i-1] if i-1 < len(d_freqs) else d_freqs[-1]
        freq_range = ((target_freq - d_freq), (target_freq + d_freq))  # 保留實際頻率範圍
        freq_indices = np.where((freq >= freq_range[0]) & (freq <= freq_range[1]))[0]
        if len(freq_indices) == 0:
            fft_max = 0
        else:
            fft_max = Hfeat[freq_indices, :].max(axis=0)
        fft_features.append(fft_max)
    return np.array(fft_features).T  # 轉置以匹配特徵數量

def process_group(group_label, screws):
    """
    處理單一群組的數據
    """
    print(f"開始處理群組 {group_label}，螺絲數量: {screws}...")
    group_csv_dir = os.path.join(csvDirectory, group_label, '6000rpm', screws)
    group_feature_dir = os.path.join(myfeatureDirectory, group_label, '6000rpm', screws)
    os.makedirs(group_feature_dir, exist_ok=True)
    
    try:
        # 讀取數據
        df_current = pd.read_csv(os.path.join(group_csv_dir, f'{group_label}_Current_data.csv'))
        df_x = pd.read_csv(os.path.join(group_csv_dir, f'{group_label}_X_data.csv'))
        df_y = pd.read_csv(os.path.join(group_csv_dir, f'{group_label}_Y_data.csv'))
        df_z = pd.read_csv(os.path.join(group_csv_dir, f'{group_label}_Z_data.csv'))
        df_temp = pd.read_csv(os.path.join(group_csv_dir, f'{group_label}_Delta_t_data.csv'))

        # 傅立葉變換並繪圖
        VibrationDataset_X = df_x.values
        VibrationDataset_Y = df_y.values
        VibrationDataset_Z = df_z.values

        Hfeat_xVibration = fourier_transform(VibrationDataset_X, df_x.shape[1], group_label, rpm, screws, feature_type='Vibration_X')
        Hfeat_yVibration = fourier_transform(VibrationDataset_Y, df_y.shape[1], group_label, rpm, screws, feature_type='Vibration_Y')
        Hfeat_zVibration = fourier_transform(VibrationDataset_Z, df_z.shape[1], group_label, rpm, screws, feature_type='Vibration_Z')

        # 提取統計特徵
        feature_Current = extract_statistical_features(df_current, 15)
        feature_X = extract_statistical_features(df_x, 15)
        feature_Y = extract_statistical_features(df_y, 15)
        feature_Z = extract_statistical_features(df_z, 15)
        feature_Temp = extract_statistical_features(df_temp, 15)

        # 提取 FFT 特徵
        fft_features_X = extract_fft_features(Hfeat_xVibration, baseFreq1, [dFreq1, dFreq2, dFreq3, dFreq4, dFreq4, dFreq4, dFreq5, dFreq5, dFreq5, dFreq5])
        fft_features_Y = extract_fft_features(Hfeat_yVibration, baseFreq1, [dFreq1, dFreq2, dFreq3, dFreq4, dFreq4, dFreq4, dFreq5, dFreq5, dFreq5, dFreq5])
        fft_features_Z = extract_fft_features(Hfeat_zVibration, baseFreq1, [dFreq1, dFreq2, dFreq3, dFreq4, dFreq4, dFreq4, dFreq5, dFreq5, dFreq5, dFreq5])

        # 合併統計特徵與 FFT 特徵
        feature_X = np.hstack((feature_X, fft_features_X))
        feature_Y = np.hstack((feature_Y, fft_features_Y))
        feature_Z = np.hstack((feature_Z, fft_features_Z))

        # 合併所有特徵
        feature_data = np.hstack((feature_Current, feature_X, feature_Y, feature_Z, feature_Temp))
        feature_data = pd.DataFrame(feature_data, columns=feature_name)

        # # 處理缺失值：用列的均值替補
        # feature_data = handle_missing_values(feature_data, method="mean")

        # 處理缺失值：刪除整行
        feature_data = drop_missing_values(feature_data)

        # 儲存特徵數據
        output_csv = os.path.join(group_feature_dir, f'{group_label}_Group_feature_data.csv')
        feature_data.to_csv(output_csv, index=False)
        print(f"特徵數據已保存為 CSV 文件: {output_csv}")

    except FileNotFoundError:
        print(f"找不到群組 {group_label} 在 {screws} 的資料檔案，無法讀取檔案!!!")

# ========================
# 主程式
# ========================

if __name__ == "__main__":
    # 定義所有群組
    groups = ['T3']
    # 定義所有螺絲數量
    screws_list = ['8screws', '7screws', '6screws', '5screws', '4screws', '3screws', '2screws', '1screws', '3_14screws', '4_146screws']
    # 迭代處理每個群組和每個螺絲數量
    for group in groups:
        for screws in screws_list:
            process_group(group, screws)
