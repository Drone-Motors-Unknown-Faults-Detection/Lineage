### 論文馬達研究
### 第一步 資料前處理
### 畫圖
### 8000rpm

# 匯入所需的函式庫
import os
import numpy as np
import pandas as pd
from natsort import natsorted
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

# 設定根目錄
rootDir = os.getcwd()

# 設定數據目錄 (包含 A, B, C 馬達)
# motor_types = ['A']
motor_types = ['A', 'B', 'C']
screws_config = [8, 6, 4, 2]

rawDataDirectories = {
    motor: {
        screws: os.path.join(rootDir, '階段2', motor, '8000rpm', f'{screws}screws')
        for screws in screws_config
    }
    for motor in motor_types
}

# 使用 IQR 方法檢測並移除異常值
def remove_outliers(df, bounds):
    for column, (lower, upper) in bounds.items():
        df = df[(df[column] >= lower) & (df[column] <= upper)]
    return df

# 計算 IQR 範圍
def calculate_iqr_bounds(df):
    bounds = {}
    for column in ['Current', 'X', 'Y', 'Z', 'Delta_T']:
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        bounds[column] = (Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)
    return bounds

# 處理數據並移除異常值
def process_data(rawDataDirectory):
    data = {'Current': [], 'X': [], 'Y': [], 'Z': [], 'Delta_T': []}

    if not os.path.exists(rawDataDirectory):
        print(f"Directory does not exist: {rawDataDirectory}")
        return data

    rawdataset_list = natsorted(os.listdir(rawDataDirectory))
    for dataset in rawdataset_list:
        try:
            # 讀取數據檔案
            file_path = os.path.join(rawDataDirectory, dataset)
            df = pd.read_csv(file_path, header=22, delimiter='\t', encoding='unicode_escape')

            # 刪除不必要的列，重新命名
            df.drop(['X_Value', 'Comment'], axis=1, inplace=True)
            df.columns = ['Current', 'X', 'Y', 'Z', 'Temperature', 'AmbientTemperature']

            # 計算溫差
            df['Delta_T'] = df['Temperature'] - df['AmbientTemperature']

            # 計算 IQR 範圍並移除異常值
            bounds = calculate_iqr_bounds(df)
            df_cleaned = remove_outliers(df, bounds)

            # 收集清理後的數據
            for key in data.keys():
                data[key].extend(df_cleaned[key])

        except Exception as e:
            print(f"Error processing file {dataset} in directory {rawDataDirectory}: {e}")

    return {key: pd.Series(values) for key, values in data.items()}

# 繪圖函式
def plot_signals(data, title_prefix, motor, screws):
    plt.figure(figsize=(10, 8))
    
    # 信號名稱與標籤
    signals = ['Current', 'X', 'Y', 'Z', 'Delta_T']
    labels = ['Current', 'Vibration X', 'Vibration Y', 'Vibration Z', 'Delta_T']
    colors = ['b', 'g', 'r', 'm', 'c']

    for i, (signal, label, color) in enumerate(zip(signals, labels, colors)):
        plt.subplot(3, 2, i + 1)
        plt.plot(data[signal], label=label, color=color)
        plt.title(f'{title_prefix} {motor} Motor {label} with {screws} screws')
        plt.xlabel('Samples')
        plt.ylabel('Amplitude' if 'Vibration' in label else 'Temperature (°C)' if signal == 'Delta_T' else 'Ampere')
        plt.ylim(data[signal].min() * 0.9, data[signal].max() * 1.1)  # 動態調整 Y 軸範圍
        plt.legend()

    plt.tight_layout()
    plt.show()

# 主程序
for motor, directories in rawDataDirectories.items():
    for screws, directory in directories.items():
        print(f"Processing data for {motor} motor with {screws} screws...")
        processed_data = process_data(directory)
        plot_signals(processed_data, 'Group', motor, screws)
