# #30：最新 main 核對與追蹤發布契約

基線為 PR #42 合併後 main `4d1858b830890a761af1dc550e74010db8a4b5f5`，上次完整審閱的 main 為 `4f783c676849a27185cd28d2410b4e76639b7357`。P1-A 開始重新讀 AGENT.md、#26/#27/#28/#30、PR #36 與全部 19 個 issue（含 closed）去重；僅 PR #36 仍 open，未見相同七個範圍的公開 PR，不能據此推論他人沒有未推送工作。

## 17 項接續判定

原始反例與行號見 [上輪完整表](../Andy_20261008_議題交付/audit_followup.md)。`git diff 4f783c6 origin/main --` 下表涉及的科學／載入／Web／環境檔案為空；沿用相同程式的既有反例，不冒稱重跑全部舊 fixtures。重新讀 exp6 matrix、aggregate、data loader，確認檢查範圍與下列追蹤一致。來源 SHA 與函數跨度由 `python -m tests.audit_followup_evidence` 保存。

| 發現 | 最新 main 結論 | 後續分組 |
|---|---|---|
| EXP-002 | exp6 summary 完成檢查未核附帶 CSV/log | R1 |
| DATA-001 | loader 的 105 數值欄不能證明 exact schema；非有限列靜默移除 | R2 |
| DATA-002 | 不等長通道取最短長度，來源差異未完整登錄 | R3 |
| DATA-003 | 缺 manifest 時的 size/mtime 指紋未改為內容 SHA | R4 |
| DATA-004 | 物化 manifest 仍含絕對本機路徑 | R4 |
| SEC-002 | client 錯誤訊息仍可能帶 exception 內容 | 既有 #28／R6 |
| SEC-003 | config 路徑 containment 契約仍不足；尚未證明 root 外寫入 | R3 |
| REPRO-001 | exp1–3 尚無統一來源與環境 metadata | R4，環境政策協調 #26 |
| REPRO-002 | formal benchmark 未完整登錄 packages/OS | R4，協調 #26 |
| ARCH-001 | parser/schema 尚無共用 resolved config | R7 |
| ARCH-002 | orchestration 多責任結構未拆分 | R10 |
| TEST-002 | 導覽／SSE 已補；正式 loader、主 WS/Origin、exp1–3 契約仍缺專項 | 既有 #27／R5 |
| AGG-001 | exp6 manifest 指紋及逐格來源核對缺口；與已完成 exp8 #25 分開 | R1 |
| PERF-001 | CSV cache 未實作；未量測，不稱瓶頸 | R8 |
| PERF-002 | 逐類 kneighbors 結構未改；未做本輪 profiling | R8 |
| DOC-001 | 本輪 main 5 文件／75 個相對目標通過；不保證全部歷史錨點 | 既有 #26／R9 文件流程 |
| DX-001 | Windows／POSIX 安裝政策仍未統一；未刪除舊 venv | 既有 #26／R9 |

## 去重與發布

當次追蹤發布紀錄：R1/R2/R3/R4/R7/R8/R10 各建一個 issue；R5/R6/R9 僅補充 #27/#28/#26。本文下方「已發布清冊」直接連結各 issue／留言，重複本文草稿不另保留。#30 的關單證據見執行紀錄；各缺陷須依其個別驗收判定。

Albert 的 PR #36 與 #24/#28/#35/#37 仍有同檔邊界，本輪不修改 health_monitor.py、web/server.py、index.html、experiments.js，也不合併 #36。會在既有 PR 留下明確請求，請作者選擇重整或關閉，不替作者決定。

## 本輪驗證

PR #42 合併後 main：Python 3.10.19，[162 passed／0 failed/error/skipped 與 pip/CLI](../../output/branch_integration/2026-10-09-11-37-18/validation.json)；[5 文件／75 相對目標／0 失效](../../output/project_closeout_evidence/2026-10-09-11-37-17/evidence.json)。這些是工程測試，不是 17 個問題全部修補或新模型成績。

## 已發布清冊

追蹤契約 commit `1a9c59c15ab1dc31e9017a4c24c49d86fe863a5a` 已 push 並核對遠端。2026-10-09 實際建立以下七個 issue，回讀皆 OPEN；不指定組員、不重開 #25。

| 分組 | 實際追蹤 | 缺口 |
|---|---|---|
| R1 | [#43](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/43) | exp6 矩陣與彙總完整性 |
| R2 | [#44](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/44) | 正式105維資料契約 |
| R3 | [#45](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/45) | containment／不等長通道 |
| R4 | [#46](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/46) | 內容SHA與portable metadata |
| R7 | [#47](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/47) | resolved config／schema |
| R8 | [#48](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/48) | profiling後決定優化 |
| R10 | [#49](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/49) | 小步拆分orchestration |

不新建重複議題：R5 [補入 #27](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/27#issuecomment-6073814615)，R6 [補入 #28](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/28#issuecomment-6073814870)，R9 [補入 #26](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/26#issuecomment-6073815098)。每項包含最小重現、範圍與驗收；各缺陷仍未完成。

[PR #36 協調留言](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/pull/36#issuecomment-6073815390) 已請 Albert 決定重整或關閉；回讀 head `544d4ed...`、DIRTY，目前沒有作者新回覆。本輪不替作者作決定。

提交契約後再跑 `tests.audit_followup_evidence`：[16來源／15相對目標／0失效](../../output/audit_followup_evidence/2026-10-09-11-42-52/evidence.json)；[完整162項與pip/CLI](../../output/branch_integration/2026-10-09-11-42-53/validation.json) 全通過。接續用獨立文件 PR 保存清冊，main 再驗後在 #30 留固定完成證據並關單。#30 completed 僅指重驗與分組追蹤完成，以上修補不會一起變 completed。
