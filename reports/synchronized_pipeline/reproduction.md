# 同步raw／特徵／fresh評估入口

以下命令在研究worktree根目錄執行。真實研究目前為 `BLOCKED_NO_ELIGIBLE_DATA`。
P0硬體文件級別見evidence_registry.json；不是每次錄製的verified facts。

## 原始契約

raw config包含recording_id/motor_id/session_id/run_id、raw_sample_count（實讀必須一致）、
sample_rate_hz、rpm、label、acquisition_timestamp（timezone）、attestation、physical_contract，
parser/layout=single_file_shared_rows、明確delimiter/header_row_0_based/expected_columns/channels。
time_column僅接受已確認relative_seconds；不因X_Value名稱推斷。sample_index_column選填。
Temp_C/Temp_room可映射motor_temp/room_temp，原列計算delta_t。
evidence.sample_rate/alignment必須包含level與reference。documented/code_setting只preview，
operator_attested/file_verified須有真實證據引用；fixture_attested永遠synthetic。
quality固定absolute_bounds（單位對應），windows正整数length/stride、gap_rule=reject、bad_point_rule=reject。
目前拒絕多行CSV記錄、空行、ragged rows與分檔channel，避免假原index／沒有clock bridge卻truncate。
quality不是motor故障標籤；不刪點、不補零、不插值、不跨recording。
機器可讀格式見docs/synchronized_raw_schema.json，人工填寫起點見examples/raw_config.template.json。
模板null必須依真實檔案／操作者事實填寫，不能直接當完成採集；serial/hours可保留null。
正式physical_contract五項須各為`{value:..., level:operator_attested或file_verified, reference:...}`，
literal unknown、僅documented或沒有引用皆阻擋。這是外部attestation資格，不是電腦替硬體驗證。
quality亦可固定saturation_bounds與window_mean_bounds記錄saturation/DC offset原因，不由final全檔估計。

```powershell
$env:PYTHONIOENCODING='utf-8'
$env:MPLCONFIGDIR=Join-Path (Get-Location) 'output/fault_type_mplcache'
$python='.\.venv310\Scripts\python.exe'
# 真實檔案必須先以自己的確認事實製作config；不能直接用fixture參數當採集證據
& $python -m experiments.synchronized_raw --raw-file 'incoming/raw.csv' --config 'incoming/raw_config.json'
# incoming-root需同時包含raw與新output，以相對路徑連結，不複製raw
& $python -m experiments.synchronized_features --raw-file 'incoming/raw.csv' --config 'incoming/raw_config.json' --incoming-root . --variant aligned_only
```

版本：historical105保留legacy數值（非finite明拒），aligned_only保留公式但共同raw窗，
corrected_formulas只修crest/clearance與degenerate moments，exact_nominal_rpm只改configured RPM/60。
105順序Current15/X25/Y25/Z25/Delta_T15；scaling 2|FFT|/n、無detrending/window、10諧波既有bandwidth，
頻率bin不足直接拒絕，不聲稱真正order tracking。每row保留rawSHA/interval/time/quality與physical契約。
version registry綁extractor四份程式SHA/settings；新features不寫入formal_local。
Quality/window設定由raw config納入版本；數值numpy/scipy版本亦綁定pipeline ID。
feature_row_id與window時間／原index／quality sidecar會在fresh preflight重算核對，不只看有沒有欄位。

## 可複製synthetic工程端到端

```powershell
& $python -m experiments.synchronized_fixture
$fixture=(Get-ChildItem output/synchronized_fixture -Directory | Sort-Object Name | Select-Object -Last 1).FullName
$ledger=Join-Path $fixture 'canonical_ledger.json'
& $python -m experiments.fault_type_fresh init-ledger --ledger $ledger --seed-ledger "$fixture/seed_ledger.json"
$argsFresh=@('--ledger',$ledger,'--incoming-root',$fixture,'--manifest',"$fixture/features/manifest.json",'--registry',"$fixture/features/version_registry.json",'--locked',"$fixture/locked_config.json",'--training-artifacts',"$fixture/models",'--claim','new_motor','--evaluation-id','synthetic-engineering-001')
& $python -m experiments.fault_type_fresh validate @argsFresh
& $python -m experiments.fault_type_fresh evaluate @argsFresh
$eval=(Get-ChildItem output/fault_type_fresh -Directory | Sort-Object Name | Select-Object -Last 1).FullName
& $python -m experiments.fault_type_fresh resume @argsFresh --resume-receipt "$eval/exposure_receipt.json"
```

fixture為300非重疊windows、10labels、2synthetic groups、3RPM，模型只fit獨立synthetic known train/cal。
不是三顆新真實馬達，不代表任何真实健康／故障效能。N5三fold是CLI v1明確範圍，其餘拒絕。
真實canonical ledger應在長期可寫local disk（例如D槽artifacts），初始歷史使用先前exposure ledger。
不得換一個空ledger繞過歷史。真實lock必須綁定canonical_ledger_path，genesis必須為已驗證的
4cb30f0a8220891b169ea32fce1fbdc24650d27f64ed8730755ee3dc95d38bdc歷史ledger；CLI拒絕空白真實seed。
Synthetic可用明確fixture seed，報告永遠不是real final。現行歷史model lock沒有training physical契約，fresh CLI會拒絕，
必須用可追溯新train/val/cal或獨立bridge預先重訓鎖定；final不能用作bridge。
joblib只從使用者明確信任的本機產物root載入，checksum不是pickle安全保證。
跨Python/sklearn直接拒絕，對應環境重新訓練。

## 交易／失敗與resume

validate不predict不改ledger。所有模型/欄位/環境/raw-count/特徵重算/coverage核對完成後，
在OS排他鎖下compare-and-swap、existing guard資格、record_final_exposure、journal fsync、atomic head。
成功才predict，失敗仍exposed。每evaluation一次曝光供所有模型/detectors共用。
並行競爭的第二個stale head拒絕，不lost update；程序終止OS lock自動釋放。
Windows文件fsync＋local atomic replace，無可攜directory fsync；不保證網路檔案系統或硬體断電。
journal已寫而head未完成會block；recover-ledger只前推head保留曝光，不删除history。
receipt可由`receipt --ledger ... --evaluation-id ...`取回，resume必須相同bundle/lock/claim/evaluation ID。
qualification／EXECUTION_COMPLETE／model_reliability分開；eligible不等於可靠性PASS。
resume仍是同一已登錄評估，fresh_evaluation_started_this_invocation=false；若真實且原資格成立，
成功resume可完成該次final execution，不能重新稱一批fresh資料。Synthetic永遠real final=false。
舊`fault_type_controlled_eval --exploratory`保持相容；舊fresh API因缺raw/physical preflight改為拒絕。

最少需真實一份未刪點未切窗raw及上述確認欄位；一份parser樣例不等於final coverage。
正式final每class至少30非重疊窗與2符合claim的groups及3RPM，是此protocol門檻不是通用power保證。
