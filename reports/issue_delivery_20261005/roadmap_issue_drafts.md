# R1–R10 待開 issue 草稿

只交草稿，不發布、不指派；新程式依使用者分工保留。已存在#24–#29／#35的範圍先補該issue，不建立重複項。證據／行號見main_reaudit.md，main固定64cb71d。

| 草稿 | 仍需處理 | 預定檔案 | 最小驗收與排除 |
|---|---|---|---|
| R1 矩陣證據完整性 | EXP-002／AGG-001 | exp6_matrix、aggregate_exp6 | 缺CSV／log、錯fingerprint／identity拒絕；合法指標不變，舊output不覆寫 |
| R2 正式資料契約 | DATA-001 | core/data或新formal_contract | exact labels／105欄順序／finite／nonempty fixture；保留compatibility分支，不重清data |
| R3 archive與通道政策 | SEC-003／DATA-002 | core/formal_data | config allowlist／resolved containment；unequal widths明確fail或記truncation；先定政策，不猜raw同步 |
| R4 run metadata | DATA-003/004、REPRO-001/002 | metadata＋exp1–3/formal exp6 | same-size/mtime內容不同SHA不同；portable摘要、private sidecar分離；#26整合版本政策 |
| R5 高風險測試 | TEST-002 | tests＋#27既有CI | 補loader、WS／exp1–3正反例，無私有data；先看PR36 iter_run，不重寫同tests |
| R6 client錯誤脫敏 | SEC-002 | web/server，整合#28 | client無path／trace，server保留correlation；PR36同檔留Albert，不能批次重做Web |
| R7 resolved config | ARCH-001 | core/runner/formal exp6 | flags→canonical config→schema一致；#29 fitted guard另項既有issue，不重複 |
| R8 profiling | PERF-001/002 | 小型benchmark／core.data/openset | 先量load walltime、memory、classes/batch/reference；無證據不實作cache／vectorization |
| R9 文件與Windows | DOC-001/DX-001 | README／PS指令，整合#26 | 新current index已有不重建；完整Windows clean smoke仍待做，不執行破壞性venv刪除 |
| R10 orchestration | ARCH-002 | exp6正式／matrix／web.live | 先fixture契約再小步抽helper；metrics/schema/event順序不變，不全repo重構 |

每份草稿的原需求、錯誤fixture與對應main函數都可由重驗索引核對。需要發布時再由使用者決定優先項目及owner；本輪不假裝10個新issue已建立。
