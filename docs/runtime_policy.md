# Python 環境安裝與版本紀錄

正式範圍為 CPython 3.10.x，依 pyproject.toml 的 >=3.10,<3.11；3.14與legacy extras不在正式鎖版範圍。runtime-constraints.txt 固定建置、執行及test套件版本，不另維護 uv.lock。

## 安裝到新目錄

POSIX：

```bash
./build_uv.sh --python python3.10 --venv .venv310
.venv310/bin/python -m pip install -c runtime-constraints.txt pytest
.venv310/bin/python -m pytest tests -ra --tb=short
.venv310/bin/python -m pip check
```

Windows PowerShell：

```powershell
./build_uv.ps1 -Python 'C:/path/to/python3.10.exe' -VenvDir '.venv310'
./.venv310/Scripts/python.exe -m pip install -c runtime-constraints.txt pytest
./.venv310/Scripts/python.exe -m pytest tests -ra --tb=short
./.venv310/Scripts/python.exe -m pip check
```

替換Python executable，目的目錄必須尚未存在。安裝程式拒絕覆寫，失敗時保留新目錄供診斷，不刪既有venv來隱藏差異。macOS另有 build_uv_mac.sh，仍需確認實際平台套件可用。

安裝入口預設只安裝執行依賴、不自動安裝pytest，上述測試安裝步驟不可省略。直接 pip install . 不等於鎖版安裝。正式指令用同一Python的 -m pip，建置採 --no-build-isolation 避免另一套未鎖定工具。constraints限制版本，不自動要求安裝每一列，也沒有wheel hash／離線封存保證。

## 執行紀錄

core.runtime_environment.collect_environment()收集Python／OS／架構、套件版本、Git HEAD與tracked dirty及constraints SHA，不保存環境變數、token、使用者名稱或絕對executable／資料路徑；Git不可讀時保留UNKNOWN。

core.logger.setup_run()將紀錄寫入該run的environment.json；make_output=False則寫log。安裝程式呼叫 python -m core.runtime_environment，輸出到logs/environment_install/及output/environment_install/。

直接呼叫未初始化的API，或沒用setup_run的入口，沒有每次保存sidecar的保證。三支原health CLI尚未全數統一，由 [#24](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/24) 與 [#26](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/26) 追蹤。

## 更新與支援邊界

更新constraints應在另一個新環境安裝、pip check、完整pytest及CLI／數值回歸後，以獨立PR交付；不要原地升級保留中的研究環境。現行 [CI](ci_contract.md) 只跑Ubuntu，不能由它宣稱Windows或macOS已驗證；本機skip須列明。

預期成果是能回讀受測環境與版本差異，不是資料獨立性或模型效能證明。舊安裝失敗、依賴更正與成功紀錄見 [改寫前固定版本](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/791216cf5602c370091fa516264f1ce6aaad6ab1/docs/runtime_policy.md)，原venv、logs/output與負面結果保留。
