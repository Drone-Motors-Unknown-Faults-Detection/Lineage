# 重現／交接操作（PowerShell）

研究工作樹：`C:/Users/andy0/AppData/Local/Temp/codex-d-drive/schoolshit/專題/src/_lineage_compare/p1_worktree`。
只在此最新checkout執行，不使用落後D槽checkout；不要處理原282個tracked deletions。
正式CSV唯讀；新執行一律由logger建立新的output/logs時間目錄，不覆寫歷史模型／預測／registry。

## 1. 核對環境與來源

```powershell
$studyRepo = 'C:/Users/andy0/AppData/Local/Temp/codex-d-drive/schoolshit/專題/src/_lineage_compare/p1_worktree'
Set-Location -LiteralPath $studyRepo
$env:PYTHONIOENCODING = 'utf-8'
$studyPython = Join-Path $studyRepo '.venv310/Scripts/python.exe'
& $studyPython --version
& $studyPython -m pip check
& $studyPython -m experiments.fault_type_accuracy_acceptance
& (Join-Path $studyRepo 'venv/Scripts/python.exe') -m experiments.fault_type_accuracy_acceptance
git -c "safe.directory=$studyRepo" branch --show-current
git -c "safe.directory=$studyRepo" status --short
```

科學結果使用Python3.10.19/sklearn1.7.2；3.14.6/sklearn1.9.1只做独立工程相容性驗收。不得跨runtime載入joblib；不要默默升級環境。既有來源fingerprint必須為`c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`，runner會核對90份CSV SHA。

## 2. 重算已封存結果（不重新訓練）

以下指令從本報告result_index.json取得實際完整路徑；先確認模型／audit／預測已在索引指向位置存在。

```powershell
$studyIndex = Get-Content -LiteralPath 'reports/fault_type_accuracy_study/result_index.json' -Raw | ConvertFrom-Json
& $studyPython -m experiments.fault_type_accuracy_report --registry $studyIndex.paths.registry --locked $studyIndex.paths.locked --evaluation $studyIndex.paths.evaluation
& $studyPython -m experiments.fault_type_accuracy_diagnosis --registry $studyIndex.paths.registry --locked $studyIndex.paths.locked --verified $studyIndex.paths.verified --data-root $studyIndex.paths.formal_data
& $studyPython -m experiments.fault_type_accuracy_summary --registry $studyIndex.paths.registry --locked $studyIndex.paths.locked --verified $studyIndex.paths.verified --diagnosis $studyIndex.paths.diagnosis
```

reporter核對seal、完整198 run inventory、225 audits、實際joblib來源SHA、逐樣本ID/truth/score/threshold/p值/集合大小、全部指標與配對。diagnosis只讀model並重算T1分數，沒有threshold search或再fit。summary是描述性all-method/Pareto，不產生可部署winner。

## 3. 如要完全重跑198組

先保留這輪結果，只生成新run。用已推送registry執行fit：

```powershell
$studyHead = git -c "safe.directory=$studyRepo" rev-parse HEAD
& $studyPython -m experiments.fault_type_accuracy_study fit --registry $studyIndex.paths.registry --data-root $studyIndex.paths.formal_data --code-head $studyHead
```

記下logger印出的新fit目錄；確認0 failures與198 classifier/180 factory/27 pooled/90 representation/162 score calibration。新lock/audits/model做備份與SHA核對；只stage自己的lock/index/log，不stage大型joblib、raw/formal或其他dirtyfiles。commit使用`Co-authored-by: Codex <codex@openai.com>`、push研究分支並核remote SHA後，才可對新lock執行evaluate。

evaluate參數：`-m experiments.fault_type_accuracy_study evaluate --registry <同一registry> --locked <新fit目錄/locked_study.json> --data-root data/formal_local --code-head <lock提交HEAD>`。括號欄位必須填剛剛logger/commit的實際值，不能複製舊lock冒充新fit。然後依第2節用新evaluation跑report/diagnosis/summary；全部仍為歷史曝光探索性比較。

## 4. 備份檢查／恢復限制

```powershell
foreach ($studyArchiveIndex in $studyIndex.paths.archive_indices) {
    & $studyPython -m experiments.fault_type_fixed_delivery --index $studyArchiveIndex
    if ($LASTEXITCODE -ne 0) { throw 'Archive verification failed' }
}
```

備份工具核whole SHA、CRC、每個member SHA與inventory；沒有刪除來源。所有大型衍生結果保存於D槽新版本目錄，並非異地備援。ZIP內部BUNDLE_INDEX保留原絕對source root；要恢復時先驗證包，再在不覆蓋既有資料的目錄解壓。封存JSON仍綁定原絕對路徑，不能改路徑後直接重封裝宣稱同一registry。移植到別台電腦需另立可追溯restoration／registry版本，保留舊source/hash映射；不要繞過trusted-root與SHA檢查。

## 5. 未執行擴展

本輪只主要N5的一組class manifest，不是重新執行126組N5或所有N。P6候選、10組N5擴展均未執行；任何後续比較須先固定全部候選與預算、commit/push，再跑。不可依本輪最佳motor/RPM、seed或unknown結果挑有利組合。
