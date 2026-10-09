# Python 環境操作

正式安裝要求 CPython 3.10.x（見 `pyproject.toml`）。環境管理使用 uv，版本以 `runtime-constraints.txt` 約束；未合併的環境政策不得當作現行入口。legacy extras 與 Python 3.14 不在此正式驗證範圍。

## 安裝與檢查

先安裝 uv，指定實際 Python executable，目的環境目錄必須不存在。入口拒絕刪除或覆寫既有環境；失敗目錄保留供診斷。

```bash
./build_uv.sh --python python3.10 --venv .venv310
uv run --no-project --no-sync --python .venv310/bin/python python -m pytest tests -ra --tb=short
uv run --no-project --no-sync --python .venv310/bin/python python -m ruff check .
uv pip check --python .venv310/bin/python
```

Windows PowerShell 7：

```powershell
./build_uv.ps1 -Python 'C:/path/to/python3.10.exe' -VenvDir '.venv310'
uv run --no-project --no-sync --python .venv310/Scripts/python.exe python -m pytest tests -ra --tb=short
uv run --no-project --no-sync --python .venv310/Scripts/python.exe python -m ruff check .
uv pip check --python .venv310/Scripts/python.exe
```

`build_uv.sh`／`build_uv.ps1` 使用 `uv venv --seed`，再以 `uv pip install --python <環境內的Python> -c runtime-constraints.txt` 安裝建置工具與 `.[test]`。測試 extras 包含 pytest、ruff。`--no-build-isolation` 避免另建未鎖版的建置環境。constraints 限制解析版本，不自動要求安裝全部列出的套件；單獨安裝專案不能稱為鎖版重現，也沒有 wheel 雜湊或離線封存保證。

`build_uv_mac.sh` 轉呼叫 legacy-mac 安裝分支；legacy extras 的依賴衝突與平台可用性須另驗，不代表正式鎖版支援。若使用預設 `venv` 目錄，也可執行 `./run_pytest.sh` 與 `./run_ruff.sh`；兩者固定呼叫 `venv/bin/python`，不會自動尋找 `.venv310` 或 Windows Scripts 路徑。

## 執行環境紀錄

`core.runtime_environment.collect_environment()` 收集 Python、OS、架構、套件版本、Git HEAD／tracked dirty 與 constraints SHA；不保存環境變數、token、使用者名稱或絕對 executable／資料路徑。Git 無法讀取時記 UNKNOWN。

`core.logger.setup_run()` 將紀錄寫入該 run 的 `environment.json`；`make_output=False` 則寫 log。安裝入口呼叫 `python -m core.runtime_environment`，寫入 `logs/environment_install/` 與 `output/environment_install/`。直接呼叫未初始化的 API，或未使用 setup_run 的入口，沒有自動保存 sidecar 的保證；缺口見 [#24](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/24)。

## 更新與支援邊界

版本變更須用另一個環境驗證依賴、完整 pytest、ruff、CLI 與數值回歸後交付 PR，不原地升級研究環境。現行 [CI](ci_contract.md) 僅跑 Ubuntu，不能由其成功宣稱 Windows／macOS 全部已驗證；skip 須分開回報。

單次安裝失敗、修補與當時實測見 [固定版本紀錄](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/42ee1b7abee92f85088b6150d64e113931104203/docs/runtime_policy.md)。這些歷史結果不能代替當前環境的重新檢查。
