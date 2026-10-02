# PowerShell 重現／續跑（科學結果用3.10）

固定工作位置，不在D槽落後checkout改碼：

```powershell
Set-Location -LiteralPath 'C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree'
$env:PYTHONIOENCODING='utf-8'
git branch --show-current
git rev-parse HEAD
git status --short
```

基準重算（624舊saved predictions，沒有refit）：

```powershell
.venv310/Scripts/python.exe -m experiments.fault_type_metrics_v2
.venv310/Scripts/python.exe -m experiments.fault_type_mechanism_diagnosis --data-root data/formal_local
```

**本次sealed protocol已有；不要再生成然後冒充同一SHA。** 若更改模型公式必須新protocol/commit再fit，新output路徑保留舊檔。

```powershell
$taskProtocol='output/fault_type_mechanism_registry/2026-10-02-17-49-29/protocol.json'
$taskLock='output/fault_type_mechanism_fit/2026-10-02-17-50-41/locked_study.json'
$taskEvaluation='output/fault_type_mechanism_evaluate/2026-10-02-17-53-06/evaluation.json'
$taskVerification='output/fault_type_mechanism_verify/2026-10-02-17-55-10/verified.json'
```

重新驗證已保存全部81格（每次建立新verify輸出，不改舊檔）：

```powershell
.venv310/Scripts/python.exe -m experiments.fault_type_mechanism_study verify --protocol $taskProtocol --data-root data/formal_local --lock $taskLock --evaluation $taskEvaluation
```

明確續跑同版本（已完成checkpoint會驗SHA與metrics，不重寫sealed總索引；schema/版本不符拒絕）：

```powershell
.venv310/Scripts/python.exe -m experiments.fault_type_mechanism_study fit --protocol $taskProtocol --data-root data/formal_local --resume output/fault_type_mechanism_fit/2026-10-02-17-50-41
.venv310/Scripts/python.exe -m experiments.fault_type_mechanism_study evaluate --protocol $taskProtocol --data-root data/formal_local --lock $taskLock --resume output/fault_type_mechanism_evaluate/2026-10-02-17-53-06
```

從頭重fit：執行以下，**讀log的新fit輸出locked_study.json，commit+push該lock後才evaluate**；不要仍用舊taskLock表示新fit。

```powershell
.venv310/Scripts/python.exe -m experiments.fault_type_mechanism_study fit --protocol $taskProtocol --data-root data/formal_local
```

配對報告（不重新選模型，不pool跨fold raw scores做ROC）：

```powershell
.venv310/Scripts/python.exe -m experiments.fault_type_mechanism_report --protocol $taskProtocol --evaluation $taskEvaluation --verification $taskVerification --baseline-metrics output/fault_type_metrics_v2/2026-10-02-12-51-52/metrics_v2.json
```

完整驗收＋native合成（不要3.14載入3.10 joblib；synthetic不是研究成績）：

```powershell
.venv310/Scripts/python.exe -m experiments.fault_type_mechanism_acceptance
venv/Scripts/python.exe -m experiments.fault_type_mechanism_acceptance
.venv310/Scripts/python.exe -m experiments.fault_type_mechanism_smoke
venv/Scripts/python.exe -m experiments.fault_type_mechanism_smoke
git diff --check
```

正式default/factory/PolarMap回歸包含在full discovery；直接數學與guards：
`.venv310/Scripts/python.exe -m unittest tests.test_fault_type_mechanisms tests.test_fault_type_metrics_v2 tests.test_fault_type_mechanism_diagnosis tests.test_fault_type_mechanism_report -v`。

所有相對artifact在上述真實repo中解析；最終index列絕對路徑與D包。D包內按timestamp保存、index含每memberSHA，解包需按manifest重新對照原paths，不聲稱原C路徑永久可用。
