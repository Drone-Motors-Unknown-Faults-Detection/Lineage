# 執行環境契約：#26 第一階段

2026-10-09，事前基線 main `ebb702dae4fe2a79df44d78738d1412b0c24bd2e`。本階段只處理 Python、依賴、非破壞安裝與共用環境紀錄，不修改資料、模型、切分、門檻或 Albert PR #36 的待決檔案。

## 支援範圍與唯一版本來源

正式安裝範圍為 CPython **3.10.x**，移除 `==3.10.19` 的 patch 限制。先驗證 Windows x86-64／3.10.19；Linux 與 macOS 的指令可提供，實際支援證據須等 CI 或實機完成。歷史研究曾用 3.14，不能據此宣稱 main 的全部依賴可在 3.14 安裝。本輪先不把 3.14 放進正式安裝範圍，也不以 `--ignore-requires-python` 繞過政策；相容性工作另行驗證。

選用單一 `runtime-constraints.txt`，不另外維護 uv.lock。`pyproject.toml` 宣告直接依賴的可維護範圍；constraints 固定正式環境的直接、傳遞與建置工具版本。安裝必須顯式傳 `-c runtime-constraints.txt`；單獨 `pip install .` 不能稱為鎖版重現。constraints 控制版本、不自動要求安裝所有列出的套件，依 [pip 官方說明](https://pip.pypa.io/en/stable/user_guide/#constraints-files)。本輪固定版本，尚無 wheel 雜湊或離線封存，不宣稱位元級供應鏈重現。

八個現有直接依賴都有現行 import：numpy、pandas、matplotlib、scipy、scikit-learn、hdbscan、loguru、tornado。直接依賴保留八項；完整傳遞依賴以真實新安裝與 metadata 再核，不只檢查第一層。TensorFlow／Jupyter 的 legacy extras 保留為歷史相容入口，**不屬於本輪正式 lock 的驗證範圍**，不修改 Ancestor。

## 安裝契約

使用 [Python 官方 venv](https://docs.python.org/3/library/venv.html) 建立新的目錄，已存在的目錄一律拒絕，不刪除或覆寫既有 venv。Windows 增加 `build_uv.ps1`；Linux／macOS 保留原 shell 入口名稱，使用明確 Python executable、相同 constraints 與 `python -m pip`。安裝建置工具後用 `--no-build-isolation`，避免另一套未鎖定的建置依賴。

Windows 預定入口（PowerShell 7）：

```powershell
./build_uv.ps1 -Python 'C:/path/to/python3.10.exe' -VenvDir '.venv310'
./.venv310/Scripts/python.exe -m pytest tests
./.venv310/Scripts/python.exe -m pip check
```

POSIX 預定入口：

```bash
./build_uv.sh --python python3.10 --venv .venv310
.venv310/bin/python -m pytest tests
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

第一輪既有環境已完成 13 個新增 fixture 與完整 175 項測試，0 failed/error/skipped，pip check／四個 CLI help 成功。真實乾淨安裝第一次在 pip 23.0.1 的 cp950 預設解碼失敗；[失敗產物](../output/runtime_policy_evidence/2026-10-09-11-59-40/evidence.json) 與該新環境保留。修正 constraints 的 UTF-8 coding 宣告並新增最小回歸，第二次必須使用另一個全新目錄，不覆寫失敗環境。這是安裝問題，未涉及資料或模型。

第二次 [實際安裝成功](../output/runtime_policy_evidence/2026-10-09-12-01-15/evidence.json)。原先只盤點八項直接依賴的 metadata，誤判 cloudpickle 不必要；新環境解析結果與 `joblib 1.6.0` 的 `Requires-Dist: cloudpickle>=3.0` 證實它是第二層正式依賴。已補固定 `cloudpickle==3.1.2`，新增完整 active dependency closure 回歸。此更正以實際安裝證據為準，不為了精簡去刪除必要套件；最終鎖版仍須再驗證。

新環境第一次測試 [失敗紀錄](../output/runtime_policy_evidence/2026-10-09-12-06-39/evidence.json) 是測試引用 pip 23 的私有解碼模組，該模組在固定 pip 25.3 已移除。正式依賴版本均相符，工程測試仍記 FAILED；修正 fixture 改驗公開的 coding 宣告與標準庫解碼，不依賴 pip 私有 API。新乾淨安裝仍會從 bootstrap pip 23 實際讀取這份檔案，提供真正安裝回歸。

修正後新環境 `lineage_clean310_20261009_retry1` 完成 [179 項全套測試](../output/branch_integration/2026-10-09-12-08-25/validation.json)，0 failed/error/skipped，pip check 與四個 CLI help 成功；[17 個環境 fixture 與固定版本核對](../output/runtime_policy_evidence/2026-10-09-12-08-22/evidence.json) 無 constraints 差異。guard [11 項及 8 組](../output/monitor_guard_evidence/2026-10-09-12-08-53/evidence.json) 與封存基線相同，score／PCA 最大差值均為 0。這些產物是在事前契約 HEAD `49fec06` 加上程式 working-tree 差異下執行，正式程式 commit 封存後另測。

## 環境管理工具改為 uv（2026-10-10）

Python 環境管理工具固定改為 [uv](https://docs.astral.sh/uv/)，取代先前「改用官方 venv」的決定（本頁上方歷史記錄保留不改，這是後續決定）。`build_uv.sh`／`build_uv.ps1`（`build_uv_mac.sh` 透過 `--legacy-mac` 轉呼叫 `build_uv.sh`，不必另改）改成：

1. `uv venv --seed --python <PYTHON_BIN> <VENV_DIR>`：建立新環境，`--seed` 讓 pip／setuptools／wheel 隨 venv 一起裝進去（純 `uv venv` 不帶這三個套件，既有測試與 `core/runtime_environment.py` 都假設它們在使用中的直譯器裡可被 `importlib.metadata` 查到）。
2. `uv pip install --python <VENV_DIR>/bin/python -c runtime-constraints.txt pip setuptools wheel`：把 `uv venv --seed` 裝的最新版換成 constraints 鎖定的版本。
3. `uv pip install --python <VENV_DIR>/bin/python --no-build-isolation -c runtime-constraints.txt .`（或 `.[legacy-linux]`／`.[legacy-mac]`）：沿用同一份 `runtime-constraints.txt`，不新增 `uv.lock`。

沒有改用 `uv lock`／`uv sync` 的專案原生工作流：`pyproject.toml` 的 `legacy-linux`／`legacy-mac` extras 要求的 numpy 範圍跟主依賴衝突（tensorflow 2.18 要 `numpy<2.1`，主依賴鎖 `numpy>=2.2,<2.3`），`uv lock` 預設會嘗試算出一份能滿足「任意 extras 組合同時成立」的 universal lock，這兩個 extra 本來就無法在這個前提下解出來（`uv lock` 直接報 unsatisfiable）。既有政策本來就寫明 legacy extras「未完整鎖版、非本輪正式驗證範圍」，所以維持 `uv pip install -c runtime-constraints.txt ".[extra]"` 這種單次解析、不進 universal lock 的路徑，不勉強湊一份涵蓋 legacy 的鎖檔。

CI（`.github/workflows/ci.yml`）改用官方 [astral-sh/setup-uv](https://github.com/astral-sh/setup-uv) action 安裝 uv（取代 `actions/setup-python`），用 `uv python install 3.10` 下載受管的 CPython 3.10，其餘步驟與本機 `build_uv.sh` 相同指令。

### 實測

本機（既有 CPython 3.10.19，`~/.local/share/uv/python/cpython-3.10-linux-x86_64-gnu/`）：

- `uv lock` 若保留 `legacy-linux`／`legacy-mac` 在 `[project.optional-dependencies]`：確認真的無解（`Because lineage[legacy-mac] depends on tensorflow==2.18.0 ... we can conclude that your project's requirements are unsatisfiable`），因此不採 `uv lock`／`uv.lock` 路徑。
- `uv venv --seed --python 3.10 <dir>` + 上述三個 `uv pip install` 步驟，重建出的環境與既有 `runtime-constraints.txt` 版本逐一比對 `pip`／`setuptools`／`wheel`／`numpy`／`pytest` 均相符。
- 同一環境跑 `python -m pytest tests -ra -q`：230 passed、3 skipped（Windows 專用案例）、0 failed、160 subtests passed，46~53 秒；`test_active_dependency_closure_is_pinned`（需要 `pip`/`setuptools`/`wheel` 的 metadata 可查）通過，確認 `--seed` 補的三個套件版本正確。
- 實跑 `build_uv.sh --venv .venv_script_test`（已刪除，非正式環境）：`pip check` 通過、`core.runtime_environment` 寫出 `output/environment_install/2026-10-09-15-13-28/environment.json`，記錄的套件版本與上一步一致。
- 尚未在真實 GitHub Actions 跑過改用 `astral-sh/setup-uv` 後的 workflow；下一次 push／PR 的 Actions run 是第一次真實驗證，macOS 與 Windows 的 uv 路徑本輪同樣未在實機驗證，風險與既有「macOS 未驗證」相同。
