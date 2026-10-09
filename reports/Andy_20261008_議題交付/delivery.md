# #30／#19／#37／#29 統一交付

交付日期2026-10-09（Asia/Taipei），執行始於2026-10-08。工作樹`D:/schoolshit/專題/src/lineage_integration_20261008`；獨立分支`delivery/issues-30-19-37-29-20261008`，基線main `4f783c676849a27185cd28d2410b4e76639b7357`。所有手寫文件在docs；不恢復研究分支的reports。本輪建立PR供審閱，不直接推main、不合併、不關issue、不發布issue留言或更新checkbox。

已建立[交付PR #40](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/pull/40)，目前OPEN，未合併。

## 四部分與逐階段推送

| 部分 | 實際完成／限制 | 提交（已push並核對遠端相同SHA） |
|---|---|---|
| #30 | 17項差異表、五份固定來源、R1–R10去重草稿；health_and_reports §2.2更新；發布草稿仍待使用者確認 | 6863cda42280156bbe33689e2c889ad22062d220 |
| #19 | exp24繼承引用與9條核心來源、README過度主張修正；Page／Gebraeel全文、Wang舊指涉、Ye裸引與Ancestor參考表尚未核實，不關閉 | c003e63a2506c5d89f991c33158a80f55d9558a9 |
| #37 | 瀏覽器功能檢查、逐列ledger、Maha／kNN各595筆配對；原首頁直接入口未完成、引擎完整版本UNKNOWN，不關閉 | e5a09d87789dbbfcc2e254051dd707bb9eebc7d0 |
| #29 | 四推論／摘要入口完整擬合guard、11項專屬測試、失敗refit拒絕混用舊模型；固定配對輸出不變，待PR合併及使用者授權才更新issue | 071d80498701ab524e181bf2f9fab28f4d4c54a6 |

各階段指令、失敗與修正均在[執行紀錄](execution_log.md)。最後整理提交只補交付索引與紅燈文字的一個尾端空白，沒有改研究數值。

## 驗證與效能差異

Python **3.10.19**；完整主線 **124 passed／0 failed／0 errors／0 skipped**，pip check成功，exp1／exp4／compare_openset／web.server四CLI `--help`成功。包含openset／PolarMap／HTTP／WebSocket回歸。未在本輪重建或驗證第二Python環境。

```powershell
python -m tests.monitor_guard_evidence
python -m tests.integration_evidence --phase candidate --data-root D:/schoolshit/專題/src/Lineage/data
python -m experiments.navigation_regression --data-root D:/schoolshit/專題/src/Lineage/data --seed 42
python -m tests.issue_delivery_evidence --data-root D:/schoolshit/專題/src/Lineage/data
```

固定舊版monitor比較2方法×2seeds×2階段、各16列fixture；score／PCA最大差0，classify／summary／splits完全相同。改guard後真實T1/8000再做1190筆配對，整份JSON SHA與改前完全一致。**沒有準確率提高的主張，也沒有profiling成績**。

資料唯讀：T1/T3×三RPM六工況60CSV，fingerprint `82534111c7901bfe0709637f4979976ce73445a54353e7c377e71e40b4cf2abd`不變；不是歷史90CSV全量重跑。未知原始視窗與session來源留UNKNOWN，fresh final仍INCOMPLETE。

## 證據位置

下面均相對本repo；本機絕對根為`D:/schoolshit/專題/src/lineage_integration_20261008`。

- [稽核與去重草稿](audit_followup.md)、[引用判定與剩餘清單](citation_followup.md)、[導覽QA](guide_acceptance.md)、[未擬合契約](monitor_guard.md)。
- 最後完整測試：`output/branch_integration/2026-10-09-03-11-15/{validation.json,tests.txt}`、對應`logs/branch_integration/2026-10-09-03-11-15.log`。
- guard紅／綠燈：`output/monitor_guard_evidence/2026-10-08-22-01-46`、`22-02-10`；原紅燈有subTest failures/errors，保留不改成PASS。
- 導覽修改前後1190筆ledger：`output/navigation_regression/2026-10-08-21-52-04/summary.json`及`2026-10-09-03-13-18/summary.json`；SHA `dbae28737e288cbf46d4dedd8d352dfce884b82a28ff4daa4a9f36b94139e8e0`。
- 外部瀏覽器截圖已移至 [驗收附件](browser_screenshots)；模型與fit仍在`output/web_guide/2026-10-08-21-50-53`、`21-55-14`。3CSV尾筆423／160／260與19檔SHA的歷史核對：`output/guide_delivery_evidence/2026-10-08-21-59-04/evidence.json`（保留當時路徑，搬移後對照由`tests.output_inventory_evidence`產生）。
- 來源與相對目標：`output/issue_delivery_evidence/2026-10-09-03-13-37/evidence.json`，73個檔案目標0失效；不等同全部歷史遠端連結／Markdown錨點皆通過。

## 排除的重疊與後續

PR36仍open，head544d4ed；沒有修改`web/server.py`、`web/static/index.html`、`experiments.js`、`experiments/health_monitor.py`與健康串流。#35保留；#24／#28與公開PR同檔，等後續協調。未知未推送工作與實際所有權不猜測。

正式105維、Mahalanobis／LW／q95預設、kNN factory／k5、PolarMap幾何與原切分均未改。#30文件與#29工程驗收可交付審閱；#19／#37仍有列出的缺口。所有issue草稿先留文件，待使用者確認才發布。

下一個可獨立安排的小任務是#25：先固定已存健康評估資料、指紋與指標定義，再重算aggregate並核對逐run一致；本輪只建議，不宣稱已接手，也不與R1的formal exp6完整性問題混同。#26環境決策另排，#27依賴該決策。

給老師的入口：[七問導覽](../../docs/navigation/exp24_README.md)，原始逐題回覆仍在[固定研究提交](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/b3d68f145cfa187e208e38cae74bf33f68d7c367/reports/teacher_reply_20261005/reply.md)。本輪是工程交付，不代表已取得可靠跨馬達fault-type模型或RUL。

Co-authored-by: Codex <noreply@openai.com>
