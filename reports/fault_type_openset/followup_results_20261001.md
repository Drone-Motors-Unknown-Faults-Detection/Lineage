# 2026-10-01 接續研究交付（Asia/Taipei）

## 結論與驗收

可由現有資料完成的身分更正、證據metadata、ZIP/processed-window追溯、
特徵契約、exposure ledger、ingest/final-test guard、三候選known-validation
比較、鎖定模型與12次探索性配對評估已完成。**新的獨立final驗證尚未完成**。
模型仍不可靠；ExtraTrees沒有全面改善，正式linear/Mahalanobis預設保持不變。
沒有重跑原2490研究、重建class-role registry或覆寫formal data/舊manifests。

## 1. 文件支持的馬達身分

afcfcc419dab3103a86a8f95601d3af85890eb38的Experiments_Guide L218、230–231
支持T1新機、T2/T3老機、三顆不同個體。90CSV stage/T-code映射一致，支持
documented leave-one-motor-out。沒有serial不是沒有身分；motor ID與完整
raw來源鏈不同。實際工時、老化程度、serial、session/run/recording boundaries
未知；個體与老化混雜，不能當同一顆的壽命軌跡或量化RUL。

詳見provenance_followup.md與motor_evidence.json；historical null欄位不改寫。

## 2. 可恢復與不可恢復的追溯

兩來源root三個ZIP SHA相同：第二份是副本。每root450個processed channel
CSV archive members，不是900次採集。bounded inventory未找到含X_Value/
Comment原DAQ header或txt/lvm/tdms/dat候選，不宣稱任何地方都不存在。

| 映射 | 已恢復 | 層級 |
|---|---:|---|
| Stage1/3 clean→archived unclean-feature ordinal |19053/19053|60CSV，唯一105欄數值匹配|
| Stage2 clean→重算processed-window ordinal |9857/9857|30CSV，完整重現adapter cleaning|
| 原始DAQ source sample intervals |0可驗證|**unknown**；不表示0overlap|

Mapping含source/memberSHA、clean row、processed ordinal、rtol/atol，多重
匹配不得杜撰單一來源。Step1先合併來源再各channel刪點與切窗，且未保留
原始檔案邊界/刪點mask；沒有原DAQ與mask不能補成連續raw interval。

## 3. 特徵一致性與風險

九份Step2腳本statistical及FFT各只有一AST版本。獨立公式驗證36條件：
Stage2全部30配置＋Stage1/3 healthy各三RPM，clean row全部可對回。
Stage1/3其他故障配置只做archived feature映射，沒有冒稱其channel全數重算。
105位置/計算語意有證據；sensor實際單位、方向、校正、安裝、負載未證明。

發現實際寬度差異：T1 healthy11000rpm current596 vs其他600；6000rpm
current595 vs600；T2/6000rpm/7screws current599 vs600。程式裁至最小列數，
裁剪不能恢復各channel刪點造成的時間錯位。FFT依然假設均勻10kHz。

歷史clearance=impulse、crest用abs(max)而非max(abs)、MSA/RMS²與variance/std²
冗餘、Y/Z FFT文字後綴錯字、133/183Hz近似均顯式記入契約，不改原數值。
按檔全量IQR清理亦依賴歷史test分布，非train-fitted部署前處理。
修正共同mask/按run切窗/實際RPM/一般clearance須新的raw可追溯feature版本，
不應重寫baseline後聲稱公平改善。上述為已驗證程式風險，不是效能差的唯一因果。

## 4. Train/validation選擇與參數

第一組原N5 class combination，known1/2/3/3_14/4screws＋healthy；其餘unknown。
選擇不是參考最差label或最佳seed。全3fold train-only RobustScaler105D，
只載入known train/validation；路徑/T-code不作features。共9 candidate-fold fits。

| 已知validation，equal-fold平均 | linear baseline | RBF SVM | ExtraTrees |
|---|---:|---:|---:|
| macro-F1 |.188776|.156778|.236452|
| balanced accuracy |22.5878%|21.9895%|31.9710%|

按先macro-F1、再balanced accuracy、同分較簡單選ExtraTrees，固定200trees/
depth12/minleaf5/sqrt/balanced。其餘參數、引用與完整fold表在
model_selection_followup.md及candidate_registry。Validation macro-F1＋.047676，
balanced accuracy＋9.3832百分點。非linear流程或fault-type可靠性的證明。

原classifier是balanced logistic C1/lbfgs/max_iter1000/tol1e-4。RBF C1/gamma
scale/balanced/probabilityFalse。無額外PCA、feature selection、embedding。
Scaler/classifier/reference只fittrain；detector thresholds只knowncalibration。
Calibration與validation共用，選擇／校準相依；不宣稱無偏校準保證。

## 5. 鎖定後舊test結果：探索性而非freshfinal

Locked config在舊test再分析前commit/push。所有28910samples已於歷史N9三折
當過test。重新切分、換seed、拿unclean rows或duplicateZIP均不算新獨立採集。
12/12 runs完成、0failed：3fold×baseline/selected×2detectors。逐樣本保存並重新
核對全部12份SHA、sample-ID/checksum與實際metrics，沒有依結果改選模型。

| 同一固定組合／test IDs，equal-fold平均 | linear | ExtraTrees | 差值 |
|---|---:|---:|---:|
| Known accuracy |29.6306%|30.7605%|＋1.1299百分點|
| Balanced accuracy |29.7372%|31.1033%|＋1.3661百分點|
| Macro-F1 |.262007|.252613|**−.009394**|

| 原test motor/fold | linear accuracy | ExtraTrees accuracy |
|---|---:|---:|
| T3，seed42 |28.2298%|26.7488%|
| T1，seed123 |37.4558%|32.7211%|
| T2，seed2026 |23.2063%|32.8117%|

兩折退步、T2那折提高帶動總平均；不能只報平均accuracy改善。macro-F1同時
受各類precision/recall影響，所以accuracy與F1可朝不同方向。未知score由
scaler/reference/calibration決定，classifier替換不會改善距離型unknownranking。

| 此固定組合，兩classifier相同detector metrics | Mahalanobis/LW | k-NN |
|---|---:|---:|
| Unknown AUROC |.531118|.504657|
| Unknown AUPR |.428126|.407135|
| Unknown recall |15.0702%|4.4939%|
| Precision |22.6298%|16.8206%|
| Unknown F1 |.168329|.069880|
| FPR@95TPR |90.0393%|98.3827%|
| Healthy FPR |0%|.2822%|

低healthyFPR不抵消大量unknown漏拒。配對方向kNN−Mahalanobis與motor/RPM/
configuration分層保存在report。這是第一組＋3fold，**不能拿來與全部126組
25.744%比較，宣稱＋5.02百分點**。全部126與反覆windows非独立受試者；
只列fold/range，不製造窄populationCI。

## 6. Final guard與最低人工需求

新增sealeddata version、exposure ledger、read-onlyingest與locked-config gate。
阻擋exposedbytes/semanticnumericrow副本、raw overlap、同recording改session/
motor充數、同run跨motor、coverage不足、未locked/config失配。FreshAPI需在
predict前透過durable exposure_sink保存新ledger；即使評估失敗也算已曝光。
不能重建旧ledger擦除history。checksum不能證明硬體facts為真。

目前無合格freshfinal；完成的是工程資格判定與探索研究，不是独立可靠性驗收。
請提供真正未曝光的錄製、motor/session/run/時間、原未刪點訊號、sample rate/
interval/stride/channelalignment、單位/校正/安裝/負載與配置確認，其他保留unknown。
詳見acquisition_contract.md，有JSON契約、seal-copy、ingest與guard指令。
不需要重傳現有ZIP或重證明三顆馬達。未代替使用者完成硬體採集。

老師問題1：已完成healthy+Nknown/heldoutunknown設計與原2490研究；本輪3候選
仍未找到可靠的fault-configuration分類/拒未知。問題2：切分與validator已有
依據；身分更正加强documentedLOMO，但session/raw完整性与freshtest尚不足，
舊全部INCOMPLETE不升PASS，不為PASS放寬門檻。

## 7. 完整可執行重現與artifact路徑

工作根目錄：
`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`
以下路徑皆在此根目錄下；D槽備份完整位置另列。

| Artifact | 根目錄下精確位置 |
|---|---|
| 身分overlay |output/fault_type_provenance/2026-10-01-00-59-11/motor_evidence.json|
|60CSV來源映射 |output/fault_type_source_audit/2026-10-01-01-02-35/source_audit.json|
|105契約/Stage2映射 |output/fault_type_feature_audit/2026-10-01-01-04-50/feature_audit.json|
|exposure ledger |output/fault_type_exposure/2026-10-01-01-10-40/exposure_ledger.json.gz|
|預登錄registry |output/fault_type_model_selection/2026-10-01-01-18-13/candidate_registry.json|
|selection/lock/training |output/fault_type_model_selection/2026-10-01-01-19-31/|
|12runs/逐筆預測 |output/fault_type_controlled_eval/2026-10-01-01-23-25/|
|重新核對的比較 |output/fault_type_followup_report/2026-10-01-01-26-39/verified_comparison.json|
|8份ZIP SHA/CRC索引 |output/fault_type_archive/2026-10-01-01-27-55/archive_index.json|

長期衍生備份：`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-10-01`，
8份主要產物ZIP，全部wholeSHA/CRC及內部memberSHA驗證，含3training joblib/fit-cal audit/12逐樣本預測/
ledger/fullmetadata；另2份成功／失敗驗收ZIP經SHA/CRC驗證，共10份。原檔未刪，raw data未上傳。Git只stage本輪程式、reports、
config、metadata摘要/映射與indices；不stagejoblib/大型predictiongz或舊282deletions。

```powershell
Set-Location -LiteralPath 'C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree'
$env:PYTHONIOENCODING = 'utf-8'
$env:MPLCONFIGDIR = Join-Path (Get-Location) 'output/fault_type_mplcache'
.\venv\Scripts\python.exe -m unittest discover -s tests -q
# 不重跑全量matrix；使用已保存的固定known-validation registry，命令見model_selection_followup.md
# 已鎖定、已曝光test才可顯式exploratory評估
.\venv\Scripts\python.exe -m experiments.fault_type_controlled_eval --data-root data/formal_local --matrix output/fault_type_matrix/2026-09-30-19-05-42 --ledger output/fault_type_exposure/2026-10-01-01-10-40/exposure_ledger.json.gz --locked output/fault_type_model_selection/2026-10-01-01-19-31/locked_config.json --exploratory
.\venv\Scripts\python.exe -m experiments.fault_type_followup_report --evaluation output/fault_type_controlled_eval/2026-10-01-01-23-25/evaluation_report.json --locked output/fault_type_model_selection/2026-10-01-01-19-31/locked_config.json
```

FreshAPI仅供預登錄的新protocol；CLI不能把旧test直接升為fresh。若從D槽備份
恢復到不同worktree，內部path仍是原保存位置，不偷偷改不可變artifact；另做
path mapping並驗證其SHA。不要載入來源不明pickle/joblib。

完整測試及commit/push最終狀態見execution_log.md。Python實跑3.14.6，
pyproject要求3.10.19尚未測試；binary detection/PolarMap/factory包含在回歸suite。
曾有prepare-only欄位命名、followup-report metric-key adapter兩次工程失敗；
均未影響候選選擇或修改data，保留failedlogs並修正，不把失敗從紀錄隱去。
最後另發現一個legacy文字assertion仍要求已撤回的「無馬達身分」敘述；修成
文件支持的motorID加raw provenance unknown，保留INCOMPLETE與group門檻檢查。
完整170tests通過；驗收證據在output/fault_type_followup_acceptance/
2026-10-01-01-35-02/acceptance.json及full_suite.txt。Python3.10仍未驗證。

最後另將成功／失敗驗收證據各保存ZIP（索引output/fault_type_archive/
2026-10-01-01-37-47/archive_index.json），本輪共10份D槽ZIP。失敗記錄未丟棄。

## 8. 逐phase Git交付

研究branch維持research-improvements-20260920；下列均有Codex Co-Author，
每phase push後以ls-remote核對完整SHA，不合併main：

| Phase | Commit（完整SHA見execution_log） |
|---|---|
|1文件身分/overlay|0dcd67b|
|2來源/processed row追溯|a82b833|
|3feature語意/重算|27927a2|
|4exposure/ingest/guard|616aa9b|
|5a訓練前預登錄|d0daccd|
|5b實際selection/lock，舊test之前|ba7e728|
|6受控exploratory結果|8a9bec2|
|7驗收與備份，已push核對|197369f|

驗收提交完整SHA為197369fcf28f01f589a3ef6b5237e8642299e47b；初次push因審批服務用量限制未執行，
於使用者要求繼續後，以正常權限流程成功push，ls-remote核對一致。實際失敗與重試均記於execution_log。
本次交付紀錄的後續commit SHA另於最終回覆核對，不在commit生成前捏造自身SHA。Issue9已新增具體更新comment，保持OPEN：
https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/9#issuecomment-5916453179 。
