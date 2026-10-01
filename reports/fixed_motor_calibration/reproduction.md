# 重現入口（Windows PowerShell，兩個環境不混載joblib）

## 0. 工作位置與確認

```powershell
Set-Location -LiteralPath 'C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree'
$env:PYTHONIOENCODING = 'utf-8'
$env:MPLCONFIGDIR = Join-Path (Get-Location) 'output/fault_type_mplcache'
git -c safe.directory='C:/Users/andy0/AppData/Local/Temp/codex-d-drive/schoolshit/專題/src/_lineage_compare/p1_worktree' branch --show-current
git -c safe.directory='C:/Users/andy0/AppData/Local/Temp/codex-d-drive/schoolshit/專題/src/_lineage_compare/p1_worktree' status --short
```

須為research-improvements-20260920。舊282個deletions不要reset/checkout復原或全stage。只讀data/formal_local，任何來源SHA或fingerprint不符即停止，不沿用舊結果。固定protocol包含既有實作byte SHA，這份實測是Windows checkout；不要宣稱另一OS/line-ending/runtime自動等價。

## 1. 直接重新核對保存結果（不重新fit）

```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_fixed_report --matrix output/fault_type_matrix/2026-09-30-19-05-42 --ledger output/fault_type_exposure/2026-10-01-01-10-40/exposure_ledger.json.gz --protocol output/fault_type_fixed_calibration/2026-10-01-15-32-22/protocol.json --locked output/fault_type_fixed_calibration/2026-10-01-19-31-08/locked_methods.json --evaluation output/fault_type_fixed_calibration/2026-10-01-19-32-25/evaluation_report.json --historical output/fault_type_representations/2026-10-01-08-38-59/evaluation_report.json
```

會生成新timestamp verified_results.json，不覆盖舊result。驗證36 gzip SHA、346920rows與相同test IDs。舊run數字是歷史對照，不是新的2490run。

## 2. 需要重跑時（探索性，不能變成fresh）

既有protocol已commit。下列fit會在新timestamp產生locked_methods.json，記下log顯示的實際output path。`<new-fit>`與`<new-evaluation>`是要替換的完整時間戳路徑，不可原樣執行。

```powershell
$fixedStudyHead = git -c safe.directory='C:/Users/andy0/AppData/Local/Temp/codex-d-drive/schoolshit/專題/src/_lineage_compare/p1_worktree' rev-parse HEAD
.\.venv310\Scripts\python.exe -m experiments.fault_type_fixed_calibration fit --matrix output/fault_type_matrix/2026-09-30-19-05-42 --ledger output/fault_type_exposure/2026-10-01-01-10-40/exposure_ledger.json.gz --protocol output/fault_type_fixed_calibration/2026-10-01-15-32-22/protocol.json --data-root data/formal_local --code-head $fixedStudyHead
```

封存/提交新lock、驗證model/audit/source SHA及備份後，才執行：

```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_fixed_calibration evaluate --matrix output/fault_type_matrix/2026-09-30-19-05-42 --ledger output/fault_type_exposure/2026-10-01-01-10-40/exposure_ledger.json.gz --protocol output/fault_type_fixed_calibration/2026-10-01-15-32-22/protocol.json --data-root data/formal_local --locked 'output/fault_type_fixed_calibration/<new-fit>/locked_methods.json' --code-head $fixedStudyHead
```

全部36固定格子，無global winner。可用`--prior-manifests PATH0 PATH1 PATH2`替代`--matrix`接收已存在其他N/class manifests；先prepare新protocol、寫明範圍並commit，不能把舊N5 protocol硬套別N。不能挑test較佳的N、labels或seed。

## 3. 封存後只讀診斷

```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_fixed_diagnosis --matrix output/fault_type_matrix/2026-09-30-19-05-42 --ledger output/fault_type_exposure/2026-10-01-01-10-40/exposure_ledger.json.gz --protocol output/fault_type_fixed_calibration/2026-10-01-15-32-22/protocol.json --locked output/fault_type_fixed_calibration/2026-10-01-19-31-08/locked_methods.json --evaluation output/fault_type_fixed_calibration/2026-10-01-19-32-25/evaluation_report.json --data-root data/formal_local
```

生成各label/RPM/raw/ratio統計及4ECDF，不fit、不搜threshold、不覆寫model/predictions。

## 4. 测试與工程fixture

```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_fixed_acceptance
.\venv\Scripts\python.exe -m experiments.fault_type_fixed_acceptance
.\.venv310\Scripts\python.exe -m experiments.fault_type_fixed_smoke
.\venv\Scripts\python.exe -m experiments.fault_type_fixed_smoke
```

acceptance各自執行pip check、完整unittest discovery及9CLI help，command_1.txt保存完整stdout/stderr。3.10.19/3.14.6各自fit/load synthetic models，不混用joblib。smoke的36 evaluations永遠SYNTHETIC_ENGINEERING_ONLY_NOT_RESEARCH，不計正式研究runs。兩個smoke順序執行，避免logger秒級timestamp撞路徑。

## 5. 備份、SHA與恢復

```powershell
.\.venv310\Scripts\python.exe -m experiments.fault_type_fixed_delivery --index output/fault_type_archive/2026-10-01-19-31-56/archive_index.json --index output/fault_type_archive/2026-10-01-19-35-57/archive_index.json --index output/fault_type_archive/2026-10-01-19-39-48/archive_index.json
```

逐ZIPwholeSHA/CRC以及BUNDLE_INDEX每member SHA/length核對。最後驗收新增ZIP索引见result_index.json，舊三份稽核ZIP同樣額外驗證但不覆盖。

模型/fit IDs/manifests/逐樣本predictions完整包在`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-10-01\fixed_motor_calibration`。恢復前先核SHA，不直接解壓覆盖工作树；解壓到专用新目錄检查。BUNDLE_INDEX保留原source_root，每ZIP內部是timestamp目錄；保存JSON绝對路径指向原工作树。若原路径仍在，可以從備份补回**確實缺失**的衍生產物，但必須核對且不能覆盖已有不同bytes。異機恢復須明確重新绑定新root並生成新版本lock/索引，不能直接改舊sealed checksum文件假装原结果。

Git compact報告和SHA索引不是原始數據。移機仍需既有formal CSV與历史baseline artifacts；不把未知raw来源填假资料，不要求新增硬体才能分析现有资料。
