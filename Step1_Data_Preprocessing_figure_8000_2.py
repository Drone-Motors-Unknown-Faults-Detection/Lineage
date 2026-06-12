# --- logging bootstrap (auto-added) ---
import atexit
from scripts.logger import redirect_std_to_logger, save_plot, setup_logger

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

# 匯入所需的函式庫
import os
import pandas as pd
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

# 設定根目錄
rootDir = os.getcwd()
dataDir = os.path.join(rootDir, 'data')
stepDir = os.path.join(dataDir, 'Step-1', 'csv')

# 設定數據目錄
motor_types = ['T1']
screws_config = [8, 6, 4, 2]

rawDataDirectories = {
    motor: {
        screws: os.path.join(stepDir, motor, '8000rpm', f'{screws}screws')
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

# 讀取 per-signal CSV（10000 rows × N segments），攤平後組成 dict of Series
signal_map = {
    'Current': 'Current',
    'X': 'Acceleration_X',
    'Y': 'Acceleration_Y',
    'Z': 'Acceleration_Z',
    'Delta_T': 'Delta_T',
}

def process_data(rawDataDirectory):
    if not os.path.exists(rawDataDirectory):
        print(f"Directory does not exist: {rawDataDirectory}")
        return {k: pd.Series([], dtype=float) for k in signal_map}

    motor = os.path.basename(os.path.dirname(os.path.dirname(rawDataDirectory)))
    data = {}
    try:
        for key, signal in signal_map.items():
            file_path = os.path.join(rawDataDirectory, f'{motor}_{signal}_data.csv')
            if not os.path.exists(file_path):
                data[key] = pd.Series([], dtype=float)
                continue
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            flat = pd.Series(df.values.T.flatten())
            # IQR 離群值過濾
            q1, q3 = flat.quantile(0.25), flat.quantile(0.75)
            iqr = q3 - q1
            data[key] = flat[(flat >= q1 - 1.5 * iqr) & (flat <= q3 + 1.5 * iqr)].reset_index(drop=True)
    except Exception as e:
        print(f"Error processing directory {rawDataDirectory}: {e}")
        data = {k: pd.Series([], dtype=float) for k in signal_map}

    return data

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
