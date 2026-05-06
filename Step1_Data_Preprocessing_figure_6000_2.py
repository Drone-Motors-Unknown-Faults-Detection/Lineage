# --- logging bootstrap (auto-added) ---
import atexit
from logger import redirect_std_to_logger, save_plot, setup_logger

LOG, RUN_PATHS = setup_logger(__file__)
_redirect_ctx = redirect_std_to_logger(LOG)
_redirect_ctx.__enter__()
atexit.register(_redirect_ctx.__exit__, None, None, None)

# Auto-save matplotlib figures on plt.show()
try:
    import matplotlib.pyplot as plt  # type: ignore

    _orig_show = plt.show

    def _show_and_save(*args, **kwargs):
        try:
            save_plot(plt, LOG, RUN_PATHS)
        except Exception:
            pass
        return _orig_show(*args, **kwargs)

    plt.show = _show_and_save  # type: ignore[assignment]
except Exception:
    pass
# --- end logging bootstrap ---

### 論文馬達研究
### 第一步 資料前處理
### 畫圖
### 6000rpm

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
dataDir = os.path.join(rootDir, 'data')
stepDir = os.path.join(dataDir, 'Step-2')

# 設定數據目錄 (包含 A, B, C 馬達)
# motor_types = ['A', 'B', 'C']
motor_types = ['B']
# screws_config = [8, 7, 6, 5, 4, 3, 2]
screws_config = [8]

rawDataDirectories = {
    motor: {
        **{
            screws: os.path.join(stepDir, motor, '6000rpm', f'{screws}screws')
            for screws in screws_config
        },
        '1': os.path.join(stepDir, motor, '6000rpm', '1screw'),
        '3_14': os.path.join(stepDir, motor, '6000rpm', '3screws_14'),
        '4_146': os.path.join(stepDir, motor, '6000rpm', '4screws_146'),
    }
    for motor in motor_types
}

# 動態設置馬達欄位名稱
signal_columns = {
    'A': ['Current', 'X', 'Y', 'Z', 'Temperature', 'AmbientTemperature', 'Delta_T'],
    'B': ['Current', 'X', 'Y', 'Z', 'Temperature', 'AmbientTemperature', 'Delta_T'],
    'C': ['Current', 'X', 'Y', 'Z', 'Temperature', 'AmbientTemperature', 'Delta_T'],
}

# 使用 IQR 方法檢測並移除離群值
def remove_outliers(df, column):
    """
    移除數據中的離群值。
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]

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
            if signal_columns == 'A':        
                df.drop(['X_Value', 'Comment'], axis=1, inplace=True)
                df.columns = ['Current', 'X', 'Y', 'Z', 'Temperature', 'AmbientTemperature']
                df['Delta_T'] = df['Temperature'] - df['AmbientTemperature']
            elif signal_columns == 'B':
                df.drop(['X_Value', 'Comment'], axis=1, inplace=True)
                df.columns = ['Current', 'X', 'Y', 'Z', 'Temperature', 'AmbientTemperature']
                df['Delta_T'] = df['Temperature'] - df['AmbientTemperature']
            elif signal_columns == 'C':
                df.drop(['X_Value', 'Comment'], axis=1, inplace=True)
                df.columns = ['Current', 'X', 'Y', 'Z', 'Temperature', 'AmbientTemperature']
                df['Delta_T'] = df['Temperature'] - df['AmbientTemperature']

            # 選取相關欄位
            relevant_columns = signal_columns[motor]
            available_columns = [col for col in relevant_columns if col in df.columns]
            df = df[available_columns]

            all_data = pd.concat([all_data, df.reset_index(drop=True)], axis=0)

    except Exception as e:
        print(f"Error processing directory {rawDataDirectory}: {e}")

    return all_data

# 繪製馬達數據
def plot_screws_data(all_data, motor, screws, title_prefix):
    if not all_data.empty:
        # 移除離群值
        for column in all_data.columns:
            all_data = remove_outliers(all_data, column)

        # 1. 繪製三軸振動信號
        vibration_columns = ['X', 'Y', 'Z']
        if all(col in all_data.columns for col in vibration_columns):
            plt.figure(figsize=(12, 8))
            for idx, column in enumerate(vibration_columns):
                plt.subplot(3, 1, idx + 1)
                plt.plot(all_data[column].values, label=f'{motor} {column}', color=['b', 'g', 'r'][idx])
                plt.title(f'{motor} {column} ({screws} Screws)', fontsize=14)
                plt.xlabel('Samples', fontsize=12)
                plt.ylabel('Amplitude', fontsize=12)
                plt.legend()
                plt.grid(True)
            plt.tight_layout()
            plt.suptitle(f'{title_prefix} {motor} Motor Vibration Signals ({screws} Screws)', fontsize=16, y=1.02)
            plt.show()

        # 2. 繪製馬達溫度、環境溫度、溫差
        temp_columns = ['Temperature', 'AmbientTemperature', 'Delta_T']
            
        if all(col in all_data.columns for col in temp_columns):
            plt.figure(figsize=(12, 8))
            for idx, column in enumerate(temp_columns):
                plt.subplot(3, 1, idx + 1)
                plt.plot(all_data[column].values, label=f'{motor} {column}', color=['b', 'c', 'm'][idx])
                plt.title(f'{motor} {column} ({screws} Screws)', fontsize=14)
                plt.xlabel('Samples', fontsize=12)
                plt.ylabel('Temperature (°C)', fontsize=12)
                plt.legend()
                plt.grid(True)
            plt.tight_layout(rect=[0, 0, 1, 0.95])  # 調整 layout，為 suptitle 預留空間
            plt.suptitle(f'{title_prefix} {motor} Temperatures ({screws} Screws)', fontsize=16)
            plt.show()

        # 3. 繪製電流信號
        if 'Current' in all_data.columns:
            plt.figure(figsize=(12, 6))
            plt.plot(all_data['Current'].values, label=f'{motor} Current ({screws} Screws)', color='g')
            plt.title(f'{title_prefix} {motor} Motor Current ({screws} Screws)', fontsize=16)
            plt.xlabel('Samples', fontsize=14)
            plt.ylabel('Current (A)', fontsize=14)
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.show()
# 主程序
for motor, directories in rawDataDirectories.items():
    for screws, directory in directories.items():
        print(f"Processing data for {motor} motor with {screws} screws...")
        all_data = concat_screws_data(directory, motor)
        if not all_data.empty:
            plot_screws_data(all_data, motor, screws, 'Group')