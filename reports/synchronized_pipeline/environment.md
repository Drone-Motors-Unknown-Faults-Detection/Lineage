# Windows Python3.10.19實測相容性

原venv Python3.14.6保留。找到既有Astral CPython3.10.19，建立獨立`.venv310`，
安裝實際可用wheels、pip check無衝突；`pip install -e . --no-deps`成功，requires-python不改。
constraints-win-py31019.txt為實際解析版本，不宣稱Linux/macOS或跨版本pickle相容。
NumPy2.2.6、pandas2.3.3、SciPy1.15.3、sklearn1.7.2、hdbscan0.8.44、matplotlib3.10.9，完整24依賴見constraints。

初次完整195tests PASS在`output/synchronized_compatibility/2026-10-01-08-32-32/`；
增加SHA/rollback測試後197tests PASS在`.../2026-10-01-08-35-28/`。
含binary/PolarMap/factory及synthetic subprocess validate/evaluate/resume、同環境fit/joblib round trip。
實際fixture `output/synchronized_fixture/2026-10-01-08-34-56/`；raw CLI 5windows PASS，
fresh synthetic評估 `output/fault_type_fresh/2026-10-01-08-35-25/` 6runs完成，real final=false。
這些是當時的工程相容性，不是馬達模型效能證明；以下最終驗收取代初次測試數量。

## 最終驗收（2026-10-01，Asia/Taipei）

Python **3.10.19 與 3.14.6 各 204 項完整測試通過**，不是只有 CLI help。
最終完整 stdout/stderr、pip check、四個新入口 help 與套件清單分別位於：

- `output/synchronized_compatibility/2026-10-01-08-52-27/`（3.10.19）。
- `output/synchronized_compatibility/2026-10-01-08-52-59/`（3.14.6）。

原 170 tests + 新 34 tests（raw 10、feature 7、fresh/transaction 14、representation 3）。
既有 binary detection、PolarMap、Mahalanobis 預設及 k-NN factory regression 包含在完整 suite 中。
最新 fixture `output/synchronized_fixture/2026-10-01-08-46-08/` 在 3.10.19 重新 fit/load；
evaluate `output/fault_type_fresh/2026-10-01-08-48-55/` 與 resume `.../2026-10-01-08-50-35/`
各完成六個工程 runs，共用一筆 exposure，real final=false。舊 fixture 不冒充最新 extractor。

aligned_only 版本 `aligned105_aligned_only_17b69e9fc20a1905`；corrected CLI 的五窗版本
`aligned105_corrected_formulas_daea2db24e68786d`。兩者都不是實測 DAQ。
最終驗收 JSON 與兩套 runtime 輸出另已封存 D 槽；archive/member 核對見最終交付報告。

```powershell
# 在研究worktree根目錄；首次建立需要正常網路安裝權限
.\build_research310.ps1 -Python310Path 'C:\Users\andy0\AppData\Roaming\uv\python\cpython-3.10.19-windows-x86_64-none\python.exe'
.\.venv310\Scripts\python.exe -m experiments.synchronized_compatibility
```

VS Code：Ctrl+Shift+P → Python: Select Interpreter → Enter interpreter path →
選目前研究worktree的`.venv310\Scripts\python.exe`，不是D槽舊checkout，也不是原venv。
所有Python命令可直接使用完整interpreter路徑，不需要activate。
fresh joblib須同Python/sklearn版本且可信本機來源；跨環境須重新訓練，不直接載入歷史3.14模型。
本repo沒有既有`.github` CI，本輪提供可重現本機check，不聲稱雲端CI已測試。

## 後續獨立性修正驗收（2026-10-01 下午）

上方204tests為同步管線交付快照。新增13項獨立性／來源副本回歸後，
Python3.10.19與3.14.6各 **217完整tests PASS**，最終環境／stdout保存於
`output/synchronized_compatibility/2026-10-01-15-07-32/`、`2026-10-01-15-08-51/`。
中途216 checkpoint保留但不取代最後證據。原venv未改，研究模型沒有重新fit。
修正與資料资格限制詳見 `reports/data_independence/audit_20261001.md`。
