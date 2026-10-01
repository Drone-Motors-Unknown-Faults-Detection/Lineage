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
這些是工程相容性，不是馬達模型效能證明。後續新增P5測試將再次完整驗收。

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
