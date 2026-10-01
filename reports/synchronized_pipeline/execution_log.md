# 同步管線研究執行紀錄（2026-10-01，Asia/Taipei）

## P0 — 接續基線與認證來源

- 工作區：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`。
- branch `research-improvements-20260920`；起點及 ls-remote 均為 `eab735a782b4017c5c42ce348a54b94661cf4f1c`。282 個既有未stage刪除保留。
- 已完整閱讀本輪附件、AGENT.md、現行資料與評估入口，讀取 Questions 最新核對結果；沒有另開聊天室或對其他聊天室傳訊息。
- 正常權限 gh api 成功核對指定 Ancestor 固定commit的兩份文件及 issue15；compact registry 保存 Git blob 與證據級別，不提交私人全文。
- 先前未登入404不是不存在；本輪已認證可讀。有同步文字不等於逐run alignment verified。
- `venv\Scripts\python -m unittest discover -s tests -q` 基線驗證；沿用已完成2490研究，不重跑。
- P1/P2/P3 synthetic工程先行；新真實資料與物理相容性仍是研究驗收條件。P4使用獨立環境，P5必須先保存並提交預登錄。

- P0 `f1d13f12efcdb63088f60ce9766c12105d760515` push成功，ls-remote完整SHA一致。

## P1 — 原始位置保留與共同切窗

- configured single-file shared-row reader，明確header/delimiter/欄位/時間意義；驗證實際count、duplicate/reversal/gap/jitter，不猜X_Value。
- 分通道檔案沒有clock bridge則拒絕；不裁最短、不跨錄製、不插值。NaN／固定界限保留原index與per-channel原因，estimated quality model要求train-only audit。
- 9項單元測試：邊界、壞點、clock、header、sample count、relative time、缺實測證據、決定論。
- 初次Tab fixture因Windows文字寫入換行重複形成空行而失敗；修正fixture寫入newline，parser亦明確拒絕空行／多行／ragged rows避免虛構原行號。沒有放寬實際sample count條件。

- P1 9tests PASS，`8e240d09f4d020ba79ac37c5e5ae34f68df876b5` push成功／remote一致。

## P2 — 獨立105維版本

- historical105保留已稽核公式版本；aligned_only只更換共同視窗來源；corrected_formulas獨立修正crest/clearance與零分母／退化moments；exact_nominal_rpm獨立改用configured RPM/60，不冒稱measured order tracking。
- 每row綁rawSHA、actualcount、原[start,end)、原行號、quality/time evidence、feature_row_id與physical contract；manifest保存raw parser configs，可重讀核對而非只信declared count。
- extractor四份程式SHA、settings、quality/window契約參與pipeline identity。未知physical可preview，但ingest／fresh仍阻擋；historical非finite特徵明確拒收，不改舊CSV。
- 7tests PASS：historical數值reference、正弦幅度/DC/constant/負峰、axis隔離、只變宣告positions、sidecar與版本變化、FFT不足拒絕。常數legacy moment警告保留，corrected定義明確。
- 獨立`.venv310`安裝進行中，原venv不改動。

- P2 `c1ceb0bc2d458a926e438c0ed02a1ef05a5e187a` push成功／remote一致。

## P3 — Fresh CLI／durable exposure

- init-ledger/validate/evaluate/resume/receipt/recover-ledger完整CLI，既有ingest/guard/record_final_exposure為唯一資格邏輯；IncomingStore讀incoming root，不誤用formal FeatureStore。
- raw再讀count/time/quality/windows並重算features，schema2/column/extractorSHA/pipeline一致；synthetic不得改標真實。模型必須綁3distinct folds、N5、known-only fit/cal ID、physical訓練契約、scaler/classifier/detector參數與維度、joblibSHA及同Python/sklearn。
- 舊fresh API缺raw/physical前置核對改為拒絕，explicit exploratory CLI沿用；shared paired computation不重建原matrix。
- OS鎖＋CAS＋順序sealed journal/fsync/atomic head，receipt在predict前；第二程序stale ledger拒絕，預測失敗exposure保留；head寫入失敗需recover，不重置／删除history。
- 300windows/2groups/3RPM synthetic generator及獨立known-only fitting用於工程測試，非真實效能。
- 初次CLI test遇Windows預設cp950讀UTF8報告；修成明確UTF8。加強preflight時一處縮排錯誤由import test立即捕捉並修復。相關9tests已PASS，另增SHA/physical與rollback測試；失敗不隱去。
- 加強後11fresh/transaction tests與2既有controlled eval測試PASS。所有新scope與序列化contract測試不使用真實final。Python3.10完整第一輪195tests PASS（後續新增測試會再完整驗收）。

- P3 `18b405f29240346775805b7bf3bce02f7716e1b6` push成功，remote一致。

## P4 — 實測Python3.10.19

- 找到既有`.../uv/python/cpython-3.10.19-windows-x86_64-none/python.exe`，正常權限建立獨立`.venv310`並安裝24實際解析依賴；pip check PASS。原venv不修改。
- 正常網路權限`pip install -e . --no-deps`成功，沒有改requires-python。記錄constraints、環境inventory/fingerprint與Windows build/interpreter指引。
- compatibility CLI完整195tests後197tests PASS、4新CLI help PASS、pip check PASS；完整stdout/stderr與versions在output/synchronized_compatibility/08-32-32與08-35-28（完整日期2026-10-01）。
- 實際synthetic generator08:34:56產生300windows/3本環境models；raw CLI08:35:22、canonical init08:35:24、fresh evaluate08:35:25–27六配對runs完成。sythentic=true且real_final=false；不是硬體採集或可信研究驗證。
- 原3.14相關測試已PASS，最終會再執行兩個runtime完整suite。沒有既有CI，不宣稱雲端CI或跨pickle相容。

- P4 `0d9e1aa913804815c81a8281a09fa0632d6d6ec8` push成功，remote一致。

## P5a — 表示研究預登錄

- 原第一個N5 class role、全部3原motor folds，固定balanced linear classifier和factory Mahalanobis/kNN，只改表示。
- 6固定候選：105baseline、vibration75、current15、delta_t15、vibration+current90、train-only PCA20。known validation macro-F1/BA/tie_rank；no unknown/test selection；保存所有候選。
- 3tests PASS：子集位置／train-only PCA、pool拒絕test load、unknown或變更候選拒絕、全部18fit artifacts。測試資料為synthetic，非本輪研究fit。
- prepare初稿08:34:27尚未commit/fit；增加implementation SHA綁定後重新prepare，再提交最終registry。raw-alignment真實對照因無可驗證raw未執行，不將processed channels標成同步。

- P5a最終registry08:37:53與程式 `568c99e94a3da6d82f6f32827520449d69110456` 已push/remote核對，正式fit在此之後。

## P5b — Known-validation鎖定

- 08:38:17–25 Python3.10.19 fit exit0，6representations×3folds全部18fits及36factory detector fits完成，沒有讀test或unknown選擇。
- 依預登錄known validation規則選vibration75。保存所有候選scores/folds、18同環境joblibs與fit/cal ID audits，不更新production default。
- locked_config/selection_report位於output/fault_type_representations/2026-10-01-08-38-17，接著先commit/push lock再探索性test。

- P5b `8866c356703d9f97de0a353f986aebcfea00ca0d` push/remote一致，lock checksum bdf471c8e6f86223d61e8fb2c5f134156c01cc24de8148e84c59bcacc9b271c3。

## P5c — 探索性結果與逐樣本核對

- 08:38:59–08:39:33 evaluate exit0，36/36 completed、0failed。346920prediction records重用28910舊sample IDs，不是新採集。
- 08:41:08–17 report exit0：全部36gzip SHA/count/IDs/lock/metrics重新核對；相同seed跨12runs test一致。
- 選定vibration75 accuracy29.6306→34.1532%、BA29.7372→34.5029%、F1.262007→.302791；MahaAUROC.531118→.574588、recall15.0702→18.4367%。三fold分類均提高，但T1 unknown recall仍0。
- kNN healthyFPR.2822→.7407%，unknown recall仍5.4526%；PCA test AUROC較高但沒有依test改選PCA。所有候選與motor/RPM/config strata保留，production不換。
- 原105baseline本輪新3.10 fit數值與上一輪此固定組合一致，非全量／跨pickle相容保證。

- P5c `ec469826a126dd3a601a1d07869ac2a284d94386` push/remote一致。

## P6a — 最終邊界稽核／加強

- Real lock必須綁一個canonical ledger path，genesis須為已驗證4cb30f0...歷史ledger，避免另建空檔抹除曝光；synthetic seed明確隔離。新增測試。
- Physical contract非空字串unknown不是證據：真實五項都要求value/attested-level/reference；documented不能替代。Sidecar時間/index/quality/window ID/feature-row ID重新核對，少mapping直接拒絕。
- 修正API僅傳variant時quality/window沒有進version identity的缺口：生成器從config綁設定並檢查每錄製一致；numpy/scipy亦入pipeline identity。固定saturation／mean-offset原因、relative_end_time與strict count/id type補齊，不fit final閾值。
- 上述是工程版本改進，不重寫baseline。舊synthetic fixture版本保留，產生新的08:46:08 fixture，不能用改版code偽裝舊extractor。
- Full suite Python3.10.19與3.14.6各204tests PASS（08:46:12、08:46:44）；原venv維持。Raw→corrected feature CLI08:48:53五windows完成；fresh synthetic evaluate08:48:55及resume08:50:35各6runs完成、只有1ledger exposure，real final=false。
- Raw schema／未填事實模板與執行範例完成。兩次無效文件patch因多餘空hunk被工具拒絕，未修改檔案；修正後成功，不繞過工具或权限。
- Archive index顯式標明synthetic raw fixtures，沒有真實DAQ／私人repo資料。接續backup及原2490 artifacts逐byte核對，不重跑研究。

- P6a `914cb889b66b9e3a84ad0256b62cda70ce867148` commit/push 成功，remote 完整 SHA 一致。

## P6b — 完整性、備份與交付文件

- `experiments.synchronized_acceptance` 08:52:16 exit0：90 正式 CSV 未改；三個歷史 ZIP 的 8,751 個來源檔、11,774,540,137 bytes 全部逐檔 SHA/length 相同。既有 756+1014+720=2,490 runs 不重跑、不重寫。
- 主備份索引 `output/fault_type_archive/2026-10-01-08-51-54/archive_index.json` 保存十個新產物 ZIP；acceptance JSON 逐 ZIP SHA、CRC、member SHA 全通過。
- 最後凍結程式再跑 `experiments.synchronized_compatibility`，Python3.10.19 08:52:27、3.14.6 08:52:59 各204tests PASS，pip check/help 均 exit0，沒有改舊 venv。
- 補備份 `output/fault_type_archive/2026-10-01-08-54-20/archive_index.json` 三 ZIP：acceptance、兩套 final runtime。PowerShell 再核對3全檔SHA＋15 members SHA/byte length PASS，結果保存 member_verification.json。
- 共13 ZIP 位於 `D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-10-01\synchronized_pipeline`。沒有刪除來源；生成的 synthetic raw 明確標記，沒有真實 DAQ／私有文件上傳。這是單一 D 槽備份，不宣稱異地災備。
- 最終報告區分 ENGINEERING_ACCEPTANCE_PASS 與 BLOCKED_NO_ELIGIBLE_DATA，列出最小原檔/採集事實、fresh training/bridge 契約及可複製 CLI。formal/manifests/predictions 舊版本未覆寫，282 既有 deletions 不 stage。
- 本階段僅增補報告及 compact 驗收證據；程式碼自 P6a 完整測試後不變。提交後另記實際 SHA、push 與 issue9 連結，不預填成功。
