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
