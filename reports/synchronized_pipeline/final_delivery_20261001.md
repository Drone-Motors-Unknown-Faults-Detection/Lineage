# 同步原始訊號與新資料評估：最終交付

日期：2026-10-01，Asia/Taipei。分支：`research-improvements-20260920`。

工程驗收 **ENGINEERING_ACCEPTANCE_PASS**；真實新資料的獨立研究驗證 **BLOCKED_NO_ELIGIBLE_DATA**。
完整程式與 synthetic 端到端測試已完成，但沒有替使用者採集硬體資料、沒有證明模型已可靠。
正式資料、原 classifier/Mahalanobis-LW 預設不換；所有本輪真實資料結果只標 exploratory。

工作 root：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`。
本文的相對產物路徑均以此 root 為準；沒有在落後的 D 槽 Lineage checkout 改碼。
原有 282 個來源不明 tracked deletions 保留且不 stage，沒有復原或刪除使用者資料。

## 1. 沿用與本輪新增

沿用正式90 CSV／28,910 samples、105維歷史語意稽核、class roles、三 motor fold manifests、
2,490 runs、metadata/exposure/ingest/guard 與兩 detector factory，不重建 matrix runner。
本輪新增 raw reader、共同 windows、quality masks、四個分離的105維版本、sidecar/raw重算 preflight、
canonical durable exposure transaction、fresh CLI、獨立3.10.19環境、表示研究入口及完整性驗收。
fresh 的資格判定仍使用原 ingest/guard；共用逐樣本評估計算，不另外發明一套寬鬆資格。
core/experiments 承擔研究邏輯，web 未新增判定逻輯，binary/cold-start與多類別研究不混稱。

## 2. 採集／馬達證據與仍未知的事實

認證 GitHub 查閱 Ancestor 固定 `1ef4a891ae02dc95910f747a5163bb2edd608f28` 的論文 L250–284、
Step1 L65–118 及 issue15；只保存 compact 指標與事實，不提交私有全文。
文件記載10,000Hz、6000/8000/11000RPM及同步量測設計；不能證明每次录製的實際 fs/clock。
欄位含三軸振動、電流、Temp_C/Temp_room、X_Value/Comment；delta_t=Temp_C−Temp_room。
header=22（zero-based）與 skiprows=21 有衝突，需從實際原檔確認，不能推測。
感測器／設備型號照原文保存；內文與圖示的設備角色差異沒有擅自升級成 verified hardware。

T1/T2/T3 是文件支持的不同馬達個體，T1新機、T2/T3老機；沒有序號不等於沒有身分依據。
三折可稱 documented leave-one-motor-out，不是三次新獨立採集。
序號、使用時數、實際老化程度、每配置 session/run 次數、連續錄製範圍、
actual fs/time/stride、原點到清理後點的完整對照、單位／軸向／校正／安裝／負載仍有 unknown。
個體差異與老化混雜，不能量化老化或剩餘壽命。

證據分級 documented / code_setting / file_verified / operator_attested / unknown。
文件同步聲明只支持設計，操作者 attest 不等於程式獨立驗證硬體。
本輪檢索範圍沒有找到合格未清理未切窗 DAQ；不是全世界／所有磁碟皆不存在。
先前未認證404不作資料不存在證據。明細 `reports/synchronized_pipeline/evidence_registry.json`。

## 3. Raw 時間軸、品質與映射的能力邊界

目前支援明確設定的單檔 shared rows，逗號或 Tab；嚴格檢查 delimiter/header/欄位/count。
原物理行號及 sample index 保留，驗證 duplicate/reversal/gap/jitter；不因 X_Value 名稱猜時間。
時間欄位只接受已確認 relative_seconds；相對秒／sample time 不是逐點絕對採集時間。
有確認 fs、alignment引用及uniform grid才具備 attested shared-row alignment 資格，非硬體認證。
分通道原檔若沒有 clock bridge 明確拒絕；本輪未實作分檔 offset/drift 校正。
不截到最短、不跨 recording 拼接、不插值、不補零、不移除點後重新編 index。

NaN/nonfinite、fixed absolute bounds、saturation 與 window mean/DC offset 都保留原位置及理由。
品質標記不是故障標籤；若提供 fitted quality model，只接受有train IDs的train-only fit audit。
窗口以每 recording 的固定 length/stride、reject gap/bad point建立，保存 [start,end)、原行號、
relative time、rawSHA/count、quality checksum/window ID。真实 final 不由该批資料 fit 清理閾值。

實際 DAQ 的新增可驗證 raw-window mapping 為 **0**：沒有原檔就不能倒推被刪的點。
最新 synthetic fixture 完成 **300** 非重疊窗（10labels×2groups×3RPM×5），完整映射只證明工程。
另五窗 corrected CLI 通過；這些不是新真實採集，不能填補歷史 DAQ 的來源缺口。

## 4. 四種105維版本與物理語意

|版本|唯一目的／邊界|
|---|---|
|historical105|保留已稽核歷史公式；非finite明確拒收，不改舊CSV|
|aligned_only|改用共同raw窗，保留歷史公式，隔離alignment影響|
|corrected_formulas|修crest的max-abs、clearance分母及退化moments/ratio；不順便刪除冗餘維度|
|exact_nominal_rpm|只將整數100/133/183改為configured RPM/60；不是 measured order tracking|

仍為 Current15/X25/Y25/Z25/Delta_T15；2|FFT|/n、無 detrending/window function、既有10諧波頻帶。
不足 FFT bins/Nyquist 支援則拒絕，不能把短窗輸出當物理等價。
版本綁四個 extractor 檔SHA、quality/window/settings及numpy/scipy環境；row綁來源SHA及映射。
最新 aligned_only：`aligned105_aligned_only_17b69e9fc20a1905`；
corrected：`aligned105_corrected_formulas_daea2db24e68786d`。
舊 Stage1/2/3 有已知公式/清理差異及實際採集未知，不能宣稱105個欄名一致就物理一致。
新統一實作有數值/axis/FFT/版本測試，尚無真實 raw 對照，因此未完成歷史-vs-aligned效能歸因。

## 5. Fresh 評估、曝光交易與失敗續跑

完整 CLI 提供 init-ledger / validate / evaluate / resume / receipt / recover-ledger。
先核對 schema/registry/feature order、actual raw count/time/window/quality、重算105值與row ID，
再核對模型SHA、同Python/sklearn、known-only fit/cal/selection ID、105尺寸、三fold/N5配置。
真實五項 physical facts 必須有 value/attested level/reference；unknown字串或documented不能充數。
舊模型缺訓練physical contract會拒絕，須由新可追溯train/val/cal或独立bridge先重訓並鎖定。
final不作bridge，檔案路徑/T-code/label編碼不當特徵；trusted local joblib的SHA不保證pickle安全。

真實lock綁 canonical ledger 路徑及歷史 genesis
`4cb30f0a8220891b169ea32fce1fbdc24650d27f64ed8730755ee3dc95d38bdc`，不能空ledger重置曝光。
OS排他鎖＋CAS＋sealed sequential journal；先fsync journal、atomic head及receipt，再predict。
failed prediction仍exposed；並行第二程序stale拒絕，程序終止OS lock釋放；head中斷需recover前推不抹除。
Windows local fsync/atomic replace不保證網路檔案系統、portable directory fsync或硬體斷電。

最新synthetic evaluate/resume各六runs成功，只有一筆canonical exposure；resume不算新fresh。
qualification、execution complete、model reliability 分開；synthetic永遠real final=false。
真實fresh v1限 healthy+5known/4unknown、三fold，每class≥30非重疊窗、≥2合格groups與三RPM；
這是預宣告coverage契約，不是一般統計 power 保證。new session與new motor主張資格不同。

## 6. Train/validation 表示研究與結果

本輪固定原第一個N5組合與三既有motor folds，只變表示；原balanced LogisticRegression、
RobustScaler、Mahalanobis-LW、kNN(k5)、confidence=.95固定。PCA20/full SVD亦只fit train。
Classifier參數C=1.0、class_weight=balanced、solver=lbfgs、max_iter=1000、tol=1e-4；無test調參。
六候選為105baseline、振動75、電流15、溫差15、振動+電流90、train-PCA20。
選擇依known validation equal-fold macro-F1→balanced accuracy→預定tie rank，unknown/test不參與。
validation/calibration共用有相依，不宣稱無偏校準；所有歷史test已曝光，選擇不構成fresh final。
預登錄先push→18 classifier/36 detector fits→lock先push→36 old-test runs，0失敗。
346,920 prediction rows重用28,910 samples，不是新獨立採集。

|同一固定N5組合，equal-fold|105 baseline|validation選定振動75|差異|
|---|---:|---:|---:|
|Validation macro-F1|0.188776|0.216750|+0.027974|
|Test known accuracy|29.6306%|34.1532%|+4.5226百分點|
|Test balanced accuracy|29.7372%|34.5029%|+4.7656百分點|
|Test macro-F1|0.262007|0.302791|+0.040784|
|Mahalanobis unknown AUROC|0.531118|0.574588|+0.043469|
|Mahalanobis unknown recall|15.0702%|18.4367%|+3.3666百分點|
|kNN unknown AUROC|0.504657|0.571053|+0.066396|
|kNN unknown recall|4.4939%|5.4526%|+0.9588百分點|
|kNN healthy FPR|0.2822%|0.7407%|+0.4585百分點（變差）|

不能拿本輪一組34.15%直接減上輪全部126組25.74%。PCA test AUROC較高但known-val較差，沒因test改選。
振動75三motor分類均提高，Mahalanobis未知召回T3=8.4011%、T1=0%、T2=46.9091%，仍不可靠。
振動75 Maha AUPR=.439675、precision=27.8537%、F1=.211959、FPR@95TPR=86.4022%，healthyFPR=0%；
kNN AUPR=.434208、precision=18.0775%、F1=.082427、FPR@95TPR=84.7773%、healthy acceptance=99.2593%。
0healthyFPR不能抵銷低未知召回；只有三motor，列fold/range，不由重複windows/combinations建立窄母體CI。
per-class confusion/recall、motor/RPM/configuration strata與18配對detector差值全部保存並重算核對。

推論：振動可能較貼近鬆動動態；電流/溫差也可能混入工況、motor、溫升，
冗餘維度改變covariance/neighbors幾何；PCA高變異方向不一定是判別方向。
這不是因果證明，不表示電流/溫度永遠無用，也不證明同步問題已修好。
所有六候選及原始baseline保留，不更换production default。詳見 feature_results.md。

老師問題1的healthy+5known/4unknown與N-sweep流程已完成，但label是鬆螺絲配置，不是九種確認物理原因；
可信fault type仍受弱效能、來源及混雜限制。問題2已有有依循的motor分組與資格檢查；
無完整session/raw/physical來源鏈的split仍INCOMPLETE，metadata更正不能自動轉PASS。

## 7. 測試、完整性、備份及精確產物

獨立3.10.19 `.venv310` 與原3.14.6各204完整tests PASS，原venv未改；24依賴constraints、pip check、
editable install與CLI都實測。本機Windows通過不宣稱其他OS、雲端CI或跨runtime pickle相容。
90formal CSV未改；三歷史封存的8,751檔/11,774,540,137 bytes逐檔SHA/length核對一致。
原2,490 runs及manifest/predictions保留，沒有完整重跑研究。實際錯誤/修復見 execution_log.md。

|內容|work root內的精確路徑|
|---|---|
|證據／說明／全部指令|`reports/synchronized_pipeline/evidence_registry.json`、`reproduction.md`、`environment.md`、`feature_results.md`、`execution_log.md`|
|人工填寫起點／machine schema|`examples/raw_config.template.json`、`docs/synchronized_raw_schema.json`|
|預登錄候選|`output/fault_type_representations/2026-10-01-08-37-53/candidate_registry.json`|
|選擇／lock／18模型與fit/cal audits|`output/fault_type_representations/2026-10-01-08-38-17/`|
|36runs／逐樣本predictions|`output/fault_type_representations/2026-10-01-08-38-59/`|
|重算SHA/metrics/strata|`output/fault_type_representation_report/2026-10-01-08-41-08/verified_comparison.json`|
|最新300窗synthetic全鏈與ledger|`output/synchronized_fixture/2026-10-01-08-46-08/`|
|corrected五窗CLI|`output/synchronized_features/2026-10-01-08-48-53/`|
|fresh engineering evaluate／resume|`output/fault_type_fresh/2026-10-01-08-48-55/`、`2026-10-01-08-50-35/`|
|最終3.10.19／3.14.6套件與204tests輸出|`output/synchronized_compatibility/2026-10-01-08-52-27/`、`2026-10-01-08-52-59/`|
|不變性及工程验收|`output/synchronized_acceptance/2026-10-01-08-52-16/acceptance.json`|
|十個主ZIP索引／三個補ZIP＋member驗證|`output/fault_type_archive/2026-10-01-08-51-54/`、`2026-10-01-08-54-20/`|

Selection lock checksum：`bdf471c8e6f86223d61e8fb2c5f134156c01cc24de8148e84c59bcacc9b271c3`。
正式data fingerprint：`c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。

長期備份完整路徑：`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-10-01\synchronized_pipeline`。
共13 ZIP，whole-SHA/CRC/member-SHA全部核對。含 generated synthetic raw，不含實測DAQ/私人全文；
來源不刪。Git存compact設定/報告/索引/日誌，大模型與gz逐樣本結果由D槽ZIP保存。
这是同一D槽備份，不是異地災備；封存保留原absolute root，移機還原需明確path mapping再SHA核對。

## 8. 逐階段 Git 交付

|階段|已推送commit（完整SHA）|
|---|---|
|P0來源核對|`f1d13f12efcdb63088f60ce9766c12105d760515`|
|P1共同raw窗|`8e240d09f4d020ba79ac37c5e5ae34f68df876b5`|
|P2版本與sidecar|`c1ceb0bc2d458a926e438c0ed02a1ef05a5e187a`|
|P3fresh交易|`18b405f29240346775805b7bf3bce02f7716e1b6`|
|P4實際3.10.19|`0d9e1aa913804815c81a8281a09fa0632d6d6ec8`|
|P5預登錄|`568c99e94a3da6d82f6f32827520449d69110456`|
|P5鎖定|`8866c356703d9f97de0a353f986aebcfea00ca0d`|
|P5結果|`ec469826a126dd3a601a1d07869ac2a284d94386`|
|P6最終邊界／204tests|`914cb889b66b9e3a84ad0256b62cda70ce867148`|
|P6最終報告／驗收／13備份證據|`aff0338bc3da703b3dec9e466e0a82bee2c06d65`|

各階段Co-authored-by Codex且push/remoteSHA一致。最終文件/驗收commit及issue9跟進記入execution_log，
避免在尚未commit的文件預填自身SHA。未merge main、未新建PR；使用既有研究缺口issue9。
本輪 issue9 外部留言被 auto-review 拒絕（具體發文授權不足），**沒有發布**；
`issue9_followup_20261001.md` 是已保存草稿，不是已發布留言。需使用者明確批准後才能發文，沒有改走其他管道繞過。
工程交付與研究分支push已完成，僅issue跟進待授權。最後bookkeeping commit自身SHA見Git歷史/最終對話回覆。

## 9. 使用者真正需提供的最小資料與下一步

先提供一份「未刪點、未切窗」的真實原始錄製及以下確認事實，即可驗parser；不必重傳既有ZIP或重證T代碼。

1. recording/motor/session/run 對照、實際sample count、採集日期含timezone、RPM/鬆螺絲配置。
2. 真實delimiter/header/欄位/time意義、actual fs與shared clock/trigger/alignment證據；分檔需clock bridge。
3. 單位、軸向、校正、安裝、負載各value及證據引用；品質界限事先由設備規格或train固定。
4. 同次連續錄製／副本／重疊窗與舊研究曝光關係，哪些是真正獨立session或新motor。

馬達serial與使用時數若不知道可維持unknown，不捏造。只有一份parser樣例不等於正式final coverage。
要完成可靠性研究，還需要獨立且有物理契約的train/validation/calibration（或獨立bridge）供重訓鎖定，
以及符合claim/coverage、未曝光的final。重新split旧錄製不會變fresh。
不能替使用者填採集事實、驗證設備未變或宣稱已完成採集；取得檔案後程式可以完成count/quality/window/feature/guard checks。

Windows逐步可複製指令在 reproduction.md；先選 `.venv310\Scripts\python.exe`，以模板填真實config，
執行 synchronized_raw→synchronized_features→準備獨立known模型與locked config→fresh validate→evaluate。
validate失敗應補事實或修來源，不調低coverage或換空ledger。resume沿用receipt/evaluation ID，不重新宣稱fresh。
synthetic完整示例已實跑，作測試參考不作真實資料替代。

## 10. 驗收結論

可立即完成的程式、測試、備份及受控探索性研究已完成；實測DAQ、來源對照、跨階段物理一致性、
独立新train/val/cal與fresh final仍待資料。当前最合理交付是「工程已完成、獨立研究驗證待資料」，
不是「已得到可信故障診斷模型」。不能因可執行、三fold分类改善或metadata文字更正改稱研究PASS。
