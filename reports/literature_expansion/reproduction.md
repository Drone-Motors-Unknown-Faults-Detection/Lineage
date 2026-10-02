# 重現入口與界線

## 工作樹與版本

研究 repo：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`。分支 `research-improvements-20260920`，沿用已存在 checkout，沒有另建repo。指定 science interpreter `.venv310\Scripts\python.exe`（3.10.19/sklearn1.7.2）；`venv\Scripts\python.exe`（3.14.6/sklearn1.9.1）只做相容性與它自己fit的synthetic，不載入3.10 joblib。

原正式CSV唯讀根目錄：上述repo內 `data\formal_local`。新protocol最終使用 `output\fault_type_literature_registry\2026-10-02-01-26-16\protocol.json`，checksum `bf98e897a1d984a8e72e521cb184636f3d1e2df6cd377b071ee2a1d99670f4ba`。不能使用01-19-40初版工程registry；source SHA已不同。正式90CSV指紋仍 c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d。

## 固定用途

| fold | train | known-only calibration | test |
|---|---|---|---|
| fixed-fold0 | T1 | T2 | T3 |
| fixed-fold1 | T2 | T3 | T1 |
| fixed-fold2 | T3 | T1 | T2 |

validation/selection空；無共同表示法winner。已知label為healthy8screws及1screws、2screws、3_14screws、3screws、4screws；unknown為4_146screws、5screws、6screws、7screws（精確編碼順序見protocol）。metadata/路徑/T-code/label不是模型特徵；僅C24使用RPM固定路由。train/cal未使用的unknown不fit任何步驟。

## 可執行指令（PowerShell）

```powershell
$studyRepo = 'C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree'
Set-Location -LiteralPath $studyRepo
$env:PYTHONIOENCODING = 'utf-8'
$env:MPLCONFIGDIR = Join-Path $studyRepo 'output/fault_type_mplcache'
$studyPython = Join-Path $studyRepo '.venv310/Scripts/python.exe'
& $studyPython -m unittest discover -s tests -v
& $studyPython -m pip check
& $studyPython -m experiments.fault_type_literature_registry --help
& $studyPython -m experiments.fault_type_literature_study --help
& $studyPython -m experiments.fault_type_literature_report --help
& $studyPython -m experiments.fault_type_literature_smoke --help
& $studyPython -m experiments.fault_type_literature_diagnosis --help
```

正式完成後 `result_index.json` 收錄所有絕對路徑，使用其封存protocol與lock：

```powershell
$studyIndex = Get-Content -LiteralPath 'reports/literature_expansion/result_index.json' -Raw | ConvertFrom-Json
& $studyPython -m experiments.fault_type_literature_study verify --protocol $studyIndex.paths.protocol --locked $studyIndex.paths.locked --evaluation $studyIndex.paths.evaluation --data-root $studyIndex.paths.data_root
& $studyPython -m experiments.fault_type_literature_report --protocol $studyIndex.paths.protocol --locked $studyIndex.paths.locked --verified $studyIndex.paths.verified --prior $studyIndex.paths.prior_summary
& $studyPython -m experiments.fault_type_literature_diagnosis --protocol $studyIndex.paths.protocol --locked $studyIndex.paths.locked --verified $studyIndex.paths.verified --data-root $studyIndex.paths.data_root
```

若要另跑而非驗證，先確認目前code與protocol記錄的source SHA/依賴版本相同，再 `fit` 到setup_run新timestamp目錄，commit該lock後才 `evaluate --locked <新的locked_study.json>`；`verify` 必須同一protocol/lock/evaluation。不要用當前HEAD冒充原fit HEAD；不要改歷史lock或模型路徑來繞過SHA guard。新run只能exploratory，不能因另存路徑、新seed或洗牌變fresh。

## Synthetic（不是研究成績）

```powershell
& $studyPython -m experiments.fault_type_literature_smoke --fixture 'output/fault_type_accuracy_smoke/2026-10-02-00-30-45'
& 'venv/Scripts/python.exe' -m experiments.fault_type_literature_smoke --fixture 'output/fault_type_accuracy_smoke/2026-10-02-00-32-59'
```

各自使用先前已存在且來源契約吻合的synthetic CSV/index，只reusefixture，不載入旧runtime模型；新630組模型均由自己的runtime重fit。3.14若讀3.10的fixture契約會拒絕，不能關掉runtime guard。

## 產物與恢復

logs/output依AGENT慣例；大型joblib、逐樣本jsonl.gz、full verified與readable summary保存D槽新版本archive，Git保留compact summary、protocol、lock與SHA索引。恢復先用既有 `experiments.fault_type_fixed_delivery --index <archive_index.json>` 驗whole ZIP SHA、CRC及member SHA；不覆蓋data或舊output。封存路徑保持原绝對位置；改路径需新的明示artifact移轉契約，不手改sealed lock。D槽同機備份不是異地備援。

所有最高分是posthoc描述性比較；3motor、未知window依賴不支持窄逐窗IID CI、部署泛化、5%固定誤報、退化百分比或RUL。

## 歷史控制的可比範圍

C02與A0為同混合RPM完整pipeline，可比較所有保存指標。C24與A7只在closed-set分類器／表示法／train／test角色相同：A7共用mixed-RPM A1 reference，C24從事前protocol起就是classifier與detector均按RPM分fit/cal。報告保留所有實際差異，但不能把其開集差異說成完全相同流程的重現或純classifier效應。這項事後解读澄清不改已封存protocol、不改門檻，不覆寫舊A7；新runner只讀正式CSV。
