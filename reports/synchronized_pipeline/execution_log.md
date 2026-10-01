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
