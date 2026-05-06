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
### 8000rpm
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
dataDir = os.path.join(rootDir, 'data')
stepDir = os.path.join(dataDir, 'Step-1')

# 設定數據目錄 (包含 A, B, C 馬達)
# motor_types = ['A', 'B', 'C']
motor_types = ['T1']
# screws_config = [8, 7, 6, 5, 4, 3, 2]
screws_config = [3]

rawDataDirectories = {
    motor: {
        **{
            screws: os.path.join(stepDir, motor, '8000rpm', f'{screws}screws')
            for screws in screws_config
        },
        # '1': os.path.join(stepDir, motor, '8000rpm', '1screw'),
        # '3_14': os.path.join(stepDir, motor, '8000rpm', '3_14screws'),
        # '4_146': os.path.join(stepDir, motor, '8000rpm', '4_146screws'),
    }
    for motor in motor_types
}
# 動態設置馬達溫度欄位名稱
signal_columns = {
    'T1': ['Acceleration_X', 'Acceleration_Y', 'Acceleration_Z', 'Current', 'Temp_C', 'Temp_room', 'Delta_T'],
}

# 使用 IQR 方法檢測並移除離群值
def remove_outliers(df, column):
    """
    移除數據中的離群值。
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 4 * IQR
    upper_bound = Q3 + 4 * IQR
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
            if motor == 'T1':
                df.drop(['X_Value', 'Temp_A', 'Temp_B', 'Comment'], axis=1, inplace=True)
                df.columns = ['Acceleration_X', 'Acceleration_Y', 'Acceleration_Z', 'Current', 'Temp_C', 'Temp_room']
                df['Delta_T'] = df['Temp_C'] - df['Temp_room']
                df.columns = ['Acceleration_X', 'Acceleration_Y', 'Acceleration_Z', 'Current', 'Temp_C', 'Temp_room', 'Delta_T']

            # 選取相關欄位
            relevant_columns = signal_columns[motor]
            available_columns = [col for col in relevant_columns if col in df.columns]
            df = df[available_columns]

            all_data = pd.concat([all_data, df.reset_index(drop=True)], axis=0)

    except Exception as e:
        print(f"Error processing directory {rawDataDirectory}: {e}")

    return all_data

# 繪製馬達數據
def plot_screws_data(all_data, motor, screws):
    if not all_data.empty:

        # 移除離群值
        for column in all_data.columns:
            all_data = remove_outliers(all_data, column)

        # 1. 繪製三軸振動信號
        # # X 軸振動信號
        # vibration_columns = ['Acceleration_X']
        # if all(col in all_data.columns for col in vibration_columns):
        #     plt.figure(figsize=(10, 8))
        #     for idx, column in enumerate(vibration_columns):
        #         plt.plot(all_data[column].values, label=f'{motor} {column}', color=['b'][idx])
        #         plt.title(f'{motor} {column} 8000RPM Healthy', fontsize=14)
        #         plt.xlabel('Samples', fontsize=12)
        #         plt.ylabel('Amplitude(g)', fontsize=12)
        #         plt.legend()
        #         plt.grid(True)
        #     plt.tight_layout()
        #     plt.show()

        # # Y 軸振動信號
        # vibration_columns = ['Acceleration_Y']
        # if all(col in all_data.columns for col in vibration_columns):
        #     plt.figure(figsize=(10, 8))
        #     for idx, column in enumerate(vibration_columns):
        #         plt.plot(all_data[column].values, label=f'{motor} {column}', color=['c'][idx])
        #         plt.title(f'{motor} {column} 8000RPM Healthy', fontsize=14)
        #         plt.xlabel('Samples', fontsize=12)
        #         plt.ylabel('Amplitude(g)', fontsize=12)
        #         plt.legend()
        #         plt.grid(True)
        #     plt.tight_layout()
        #     plt.show()

        # # Z 軸振動信號
        # vibration_columns = ['Acceleration_Z']
        # if all(col in all_data.columns for col in vibration_columns):
        #     plt.figure(figsize=(10, 8))
        #     for idx, column in enumerate(vibration_columns):
        #         plt.plot(all_data[column].values, label=f'{motor} {column}', color=['r'][idx])
        #         plt.title(f'{motor} {column} 8000RPM Healthy', fontsize=14)
        #         plt.xlabel('Samples', fontsize=12)
        #         plt.ylabel('Amplitude(g)', fontsize=12)
        #         plt.legend()
        #         plt.grid(True)
        #     plt.tight_layout()
        #     plt.show()

#         # 2. 繪製馬達溫度、環境溫度、溫差
#         # 馬達溫度
#         if motor == 'T1':
#             temp_columns = ['Temp_C']
            
#         if all(col in all_data.columns for col in temp_columns):
#             plt.figure(figsize=(10, 8))
#             for idx, column in enumerate(temp_columns):
#                 # plt.subplot(3, 1, idx + 1)
#                 plt.plot(all_data[column].values, label=f'{motor} Motor Temperature', color=['deepskyblue'][idx])
#                 plt.title(f'{motor} Motor Temperature 8000RPM Healthy', fontsize=14)
#                 plt.xlabel('Samples', fontsize=12)
#                 plt.ylabel('Temperature (°C)', fontsize=12)
#                 plt.legend()
#                 plt.grid(True)
#             plt.tight_layout(rect=[0, 0, 1, 0.95])  # 調整 layout，為 suptitle 預留空間
#             # plt.suptitle(f'{motor} Temperatures ({screws} Screws)', fontsize=16)
#             plt.show()

#         # 環境溫度
#         if motor == 'T1':
#             temp_columns = ['Temp_room']
   
#         if all(col in all_data.columns for col in temp_columns):
#             plt.figure(figsize=(10, 8))
#             for idx, column in enumerate(temp_columns):
#                 plt.plot(all_data[column].values, label=f'{motor} Ambient Temperature', color=['orange'][idx])
#                 plt.title(f'{motor} Ambient Temperature 8000RPM Healthy', fontsize=14)
#                 plt.xlabel('Samples', fontsize=12)
#                 plt.ylabel('Temperature (°C)', fontsize=12)
#                 plt.legend()
#                 plt.grid(True)
#             plt.tight_layout(rect=[0, 0, 1, 0.95])  # 調整 layout，為 suptitle 預留空間
#             # plt.suptitle(f'{motor} Temperatures ({screws} Screws)', fontsize=16)
#             plt.show()
  
#         # 溫差
#         if 'Delta_T' in all_data.columns:
#             plt.figure(figsize=(10, 8))
#             plt.plot(all_data['Delta_T'].values, label=f'{motor} Delta_T', color='m')
#             plt.title(f'{motor} Delta_T 8000RPM Healthy', fontsize=14)
#             plt.xlabel('Samples', fontsize=12)
#             plt.ylabel('Temperature (°C)', fontsize=12)
#             plt.legend()
#             plt.grid(True)
#             plt.tight_layout()
#             plt.show()


#         # 3. 繪製電流信號
#         if 'Current' in all_data.columns:
#             plt.figure(figsize=(10, 8))
#             plt.plot(all_data['Current'].values, label=f'{motor} Current', color='brown')
#             plt.title(f'{motor} Motor Current 8000RPM Healthy', fontsize=16)
#             plt.xlabel('Samples', fontsize=14)
#             plt.ylabel('Current (A)', fontsize=14)
#             plt.legend()
#             plt.grid(True)
#             plt.tight_layout()
#             plt.show()

# # 主程序
# for motor, directories in rawDataDirectories.items():
#     for screws, directory in directories.items():
#         print(f"Processing data for {motor} motor with {screws} screws...")
#         all_data = concat_screws_data(directory, motor)
#         if not all_data.empty:
#             plot_screws_data(all_data, motor, screws)

def plot_screws_data(all_data, motor, screws):
    if not all_data.empty:
        raw_data = all_data.copy()

        for column in all_data.columns:
            all_data = remove_outliers(all_data, column)

                # === 1. 每個訊號完整疊合圖 + 放大局部比較圖 ===
        vibration_columns = ['Acceleration_X', 'Acceleration_Y', 'Acceleration_Z']
        color_map = {'Acceleration_X': 'blue', 'Acceleration_Y': 'green', 'Acceleration_Z': 'red'}

        for column in vibration_columns:
            if column in all_data.columns:

                # === 全部資料圖 ===
                plt.figure(figsize=(12, 4))
                plt.plot(raw_data[column].values, label='Before IQR', alpha=1.0, linestyle='--', color='gray')
                plt.plot(all_data[column].values, label='After IQR', alpha=0.4, linestyle='-', color=color_map[column])
                plt.title(f'{motor} {column} - 8000RPM Faulty 3 Full Signal', fontsize=15)
                plt.xlabel('Samples')
                plt.ylabel('Amplitude')
                plt.legend()
                plt.grid(True)
                plt.tight_layout()
                plt.show()

                # === 放大前 5000 筆比較圖 ===
                N = 5000
                plt.figure(figsize=(12, 4))
                plt.plot(raw_data[column].values[:N], label='Before IQR', alpha=1.0, linestyle='--', color='gray')
                plt.plot(all_data[column].values[:N], label='After IQR', alpha=0.4, linestyle='-', color=color_map[column])
                plt.title(f'{motor} {column} - 8000RPM Faulty 3 Zoomed First {N} Samples', fontsize=15)
                plt.xlabel('Samples')
                plt.ylabel('Amplitude')
                plt.legend()
                plt.grid(True)
                plt.tight_layout()
                plt.show()


        # ========== 疊合溫度圖 ==========
        if motor == 'T1':
            temp_columns = ['Temp_C', 'Temp_room', 'Delta_T']

        if all(col in all_data.columns for col in temp_columns):
            plt.figure(figsize=(12, 8))
            for idx, column in enumerate(temp_columns):
                plt.subplot(3, 1, idx + 1)
                plt.plot(raw_data[column].values, label='Before IQR', alpha=1.0, color='gray')
                plt.plot(all_data[column].values, label='After IQR', alpha=0.4, color=['b', 'c', 'm'][idx])
                plt.title(f'{motor} {column} ({screws} Screws)', fontsize=14)
                plt.xlabel('Samples', fontsize=12)
                plt.ylabel('Temperature (°C)', fontsize=12)
                plt.legend()
                plt.grid(True)
            plt.tight_layout(rect=[0, 0, 1, 0.95])
            plt.suptitle(f'{motor} Temperatures ({screws} Screws)', fontsize=16)
            plt.show()

        # ========== 疊合電流圖 ==========
        if 'Current' in all_data.columns:
            plt.figure(figsize=(12, 6))
            plt.plot(raw_data['Current'].values, label='Before IQR', alpha=1.0, color='gray')
            plt.plot(all_data['Current'].values, label='After IQR', alpha=0.4, color='g')
            plt.title(f'{motor} Motor Current ({screws} Screws)', fontsize=16)
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
            plot_screws_data(all_data, motor, screws)