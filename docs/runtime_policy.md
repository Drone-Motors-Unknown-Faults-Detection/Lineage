# 執行環境契約：#26 第一階段

2026-10-09，事前基線 main `ebb702dae4fe2a79df44d78738d1412b0c24bd2e`。本階段只處理 Python、依賴、非破壞安裝與共用環境紀錄，不修改資料、模型、切分、門檻或 Albert PR #36 的待決檔案。

## 支援範圍與唯一版本來源

正式安裝範圍為 CPython **3.10.x**，移除 `==3.10.19` 的 patch 限制。先驗證 Windows x86-64／3.10.19；Linux 與 macOS 的指令可提供，實際支援證據須等 CI 或實機完成。歷史研究曾用 3.14，不能據此宣稱 main 的全部依賴可在 3.14 安裝。本輪先不把 3.14 放進正式安裝範圍，也不以 `--ignore-requires-python` 繞過政策；相容性工作另行驗證。

選用單一 `runtime-constraints.txt`，不另外維護 uv.lock。`pyproject.toml` 宣告直接依賴的可維護範圍；constraints 固定正式環境的直接、傳遞與建置工具版本。安裝必須顯式傳 `-c runtime-constraints.txt`；單獨 `pip install .` 不能稱為鎖版重現。constraints 控制版本、不自動要求安裝所有列出的套件，依 [pip 官方說明](https://pip.pypa.io/en/stable/user_guide/#constraints-files)。本輪固定版本，尚無 wheel 雜湊或離線封存，不宣稱位元級供應鏈重現。

八個現有直接依賴都有現行 import：numpy、pandas、matplotlib、scipy、scikit-learn、hdbscan、loguru、tornado。既有環境的 cloudpickle 未被本專案或這八項的正式依賴使用，不納入新的最小環境。TensorFlow／Jupyter 的 legacy extras 保留為歷史相容入口，**不屬於本輪正式 lock 的驗證範圍**，不修改 Ancestor。

## 安裝契約

使用 [Python 官方 venv](https://docs.python.org/3/library/venv.html) 建立新的目錄，已存在的目錄一律拒絕，不刪除或覆寫既有 venv。Windows 增加 `build_uv.ps1`；Linux／macOS 保留原 shell 入口名稱，使用明確 Python executable、相同 constraints 與 `python -m pip`。安裝建置工具後用 `--no-build-isolation`，避免另一套未鎖定的建置依賴。

Windows 預定入口：

```powershell
./build_uv.ps1 -Python 'C:/path/to/python3.10.exe' -VenvDir '.venv310'
./.venv310/Scripts/python.exe -m unittest discover -s tests -t .
./.venv310/Scripts/python.exe -m pip check
```

POSIX 預定入口（尚未在本機驗證）：

```bash
./build_uv.sh --python python3.10 --venv .venv310
.venv310/bin/python -m unittest discover -s tests -t .
.venv310/bin/python -m pip check
```

`--legacy` 仍可用，但新增 extras 的傳遞依賴未完整固定；須明列為非正式環境，不能用於本輪科學結果的正式重現。更新 constraints 必須用新環境解析、pip check、全部 fixture、CLI 及數值回歸，再獨立 PR；保留原鎖版與負面紀錄，不在舊 venv 原地升級。

## 環境紀錄與未完成邊界

新增 `core/runtime_environment.py`，只讀取 Python 版本／實作、OS／架構、已安裝套件名稱與版本、實際 Git HEAD／dirty、constraints SHA。禁止記錄使用者名稱、環境變數、token、絕對 executable／資料路徑。Git 不可用時保存 UNKNOWN 與原因，不能偽造 commit。`setup_run()` 自動在既有 output 寫 `environment.json`；`make_output=False` 仍在 log 記錄相同資料。此步只新增執行證據，不改數值運算。

覆蓋範圍限於實際呼叫 `setup_run()` 的入口。`health_index_benchmark`、`health_index_matrix`、`health_monitor` 尚未統一此入口；直接呼叫未初始化的 `run()` 也不能宣稱每次都有環境 sidecar。這些缺口與 #24／PR #36 相依，**#26 保持 OPEN**。本階段不為了關單去修改待決的 `health_monitor.py` 或另造隱式包裝。

## 事前驗收

- 新環境拒絕覆寫；Python 非 3.10 時在建立前失敗。
- 全部必要正式依賴版本與 constraints 相符；pip check、完整 fixture 與四個 CLI help 成功。
- metadata 可測無 Git／未安裝套件、dirty、make_output=False、JSON 欄位與隱私；不依賴 ignored data。
- 新環境與既有環境使用同 fixture／seed 核對 guard 分數、PCA、分類與 split；預設不變。
- 保存實際命令、Python、套件、受測 commit 與成功／失敗產物；不引用先前 162 項作新結果。
- 此頁先 commit／push，實作後更新實測區，不改寫事前門檻。

## 檔案範圍

會改 `pyproject.toml`、`build_uv.sh`、`build_uv_mac.sh`、`core/logger.py`、README；會新增 `runtime-constraints.txt`、`build_uv.ps1`、`core/runtime_environment.py` 與 fixture／驗證入口。輸出沿用 `logs/`、`output/`。本階段為工程契約，不占 exp9–12，不新增研究方法。

## 實測區

尚未執行新的安裝／程式測試；結果待本階段實作追加。
