### 論文馬達研究
### 第一步 資料前處理
### 存檔
### 11000rpm
### 馬達

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
# 設定儲存數據的目錄
save_base_dir = os.path.join(rootDir, '階段1', 'csv')

# 設定數據目錄
motor_types = ['T1']
screws_config = [8, 7, 6, 5, 4, 3, 2]

rawDataDirectories = {
    motor: {
        **{
            screws: os.path.join(rootDir, '階段1', motor, '11000rpm', f'{screws}screws')
            for screws in screws_config
        },
        '1': os.path.join(rootDir, '階段1', motor, '11000rpm', '1screw'),
        '3_14': os.path.join(rootDir, '階段1', motor, '11000rpm', '3_14screws'),
        '4_146': os.path.join(rootDir, '階段1', motor, '11000rpm', '4_146screws'),
    }
    for motor in motor_types
}

# 動態設置馬達欄位名稱
signal_columns = {
    'T1': ['Acceleration_X', 'Acceleration_Y', 'Acceleration_Z', 'Current', 'Delta_T'],
}

# 使用 IQR 方法檢測並移除離群值
def iqr(series, scale=3.0):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - scale * IQR
    upper = Q3 + scale * IQR
    return series[(series >= lower) & (series <= upper)]


# 合併單一螺絲數配置的馬達數據
def concat_screws_data(rawDataDirectory, motor):
    all_data = pd.DataFrame()
    try:
        rawdataset_list = natsorted(os.listdir(rawDataDirectory))

        for dataset in rawdataset_list:
            # 讀取數據
            file_path = os.path.join(rawDataDirectory, dataset)
            df = pd.read_csv(file_path, header=22, delimiter='\t', encoding='unicode_escape')

            # 刪除不必要的列，重新命名
            df.drop(['X_Value', 'Temp_A', 'Temp_B', 'Comment'], axis=1, inplace=True)
            df.columns = ['Acceleration_X', 'Acceleration_Y', 'Acceleration_Z', 'Current', 'Temp_C', 'Temp_room']
            df['Delta_T'] = df['Temp_C'] - df['Temp_room']
            # 選取相關欄位
            relevant_columns = signal_columns[motor]
            available_columns = [col for col in relevant_columns if col in df.columns]
            df = df[available_columns]

            all_data = pd.concat([all_data, df.reset_index(drop=True)], axis=0)

    except Exception as e:
        print(f"Error processing directory {rawDataDirectory}: {e}")

    return all_data


# 切割數據並儲存為 CSV
def slice_and_save(all_data, save_directory, motor, screws):
    os.makedirs(save_directory, exist_ok=True)

    for column in all_data.columns:

        raw_data = all_data[column]

        # ---------- 濾除離群值 ----------
        raw_data = iqr(raw_data, scale=3.0)

        # 切割數據並水平合併
        sliced_data = pd.DataFrame()
        for i in range(0, len(raw_data), 10000):
            sliced_chunk = raw_data.iloc[i:i+10000].reset_index(drop=True)
            sliced_data = pd.concat([sliced_data, sliced_chunk], axis=1)

        # 儲存數據
        file_name = f"{motor}_{column}_data.csv"
        save_path = os.path.join(save_directory, file_name)
        sliced_data.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"Data saved for {motor}, {column}, {screws} screws: {save_path}")


# 主程序
for motor, directories in rawDataDirectories.items():
    for screws, directory in directories.items():
        print(f"Processing data for {motor} motor with {screws} screws...")
        all_data = concat_screws_data(directory, motor)
        if not all_data.empty:
            save_directory = os.path.join(save_base_dir, motor, '11000rpm', f'{screws}screws')
            slice_and_save(all_data, save_directory, motor, screws)