# 分支整合交付紀錄

2026-10-08，Asia/Taipei。合格內容已透過 [PR #38](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/pull/38) 真正進入 main。功能合併 SHA `e1668cb48b91520d2500be643351d9c4c8d9494b`，於21:19:08合併；此 SHA 的完整測試已通過。這份交付文件及合併後證據以後續文件PR保存，不改模型或功能；最新 main 可比功能合併多一個證據提交。

## 已驗證

- 整合前 main `64cb71d84663e1745ec54db74abad68def67e8e6` 已推送至 [backup/main-before-integration-20261008-131410](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/tree/backup/main-before-integration-20261008-131410)，遠端 SHA 相符。
- 研究來源 b3d68f 的獨立導覽、exp24七問文件；Albert來源544d4ed的exp1/3/4 iter_run、SSE及背景小窗完成相容整合。
- 原main76測試全通過；新完整候選與合併後各111 passed、0 failed/errors/skipped。Python3.10.19，pip check與四CLI exit0。GitHub未配置checks/reviews，不能稱CI已通過。
- 確切PR候選92a9ba5驗收：[validation](../../output/branch_integration/2026-10-08-21-17-25/validation.json)、[逐項結果](../../output/branch_integration/2026-10-08-21-17-25/tests.txt)。合併後main e1668cb驗收：[validation](../../output/branch_integration/2026-10-08-21-19-15/validation.json)、[逐項結果](../../output/branch_integration/2026-10-08-21-19-15/tests.txt)。
- 導覽Maha/kNN共1190筆配對差異0；合併後exp1/3兩detectors與exp4三段共[五組原main配對](../../output/stream_integration_regression/2026-10-08-21-19-45/summary.json)均相同。同條件準確率差異0百分點。
- 正式core、105維、Mahalanobis-LW/q95、kNN5 factory、PolarMap、health搬家、未知不fit等保留。60份唯讀來源完整清冊SHA `82534111c7901bfe0709637f4979976ce73445a54353e7c377e71e40b4cf2abd` 不變。
- 所有原分支與備份保留；原 `D:/schoolshit/專題/src/Lineage` clean且仍dda8910，未切換；本輪工作樹 `D:/schoolshit/專題/src/lineage_integration_20261008`。

## 排除與限制

- PR #36部分抽取，仍OPEN；health_monitor與health串流未整合，issue #35索引缺陷仍OPEN。沒有接手Albert其他未完成功能。
- 研究分支其他演算法、資料guard與大量產物尚未完成main相依閉包驗證，保留固定來源，不整批覆蓋。FAILED結果、GroupDRO未實作狀態不變。
- 目前真實回歸只有T1/T3三RPM的60檔，非歷史90檔。沒有重跑2490研究，未修復T1跨馬達未知召回問題；原始採集與窗口獨立性UNKNOWN、fresh final INCOMPLETE。
- CSV劇本不是物理退化生命週期；操作員確認後完整標記池擬合是oracle展示。沒有部署、硬體實驗或對外開放QA服務。

## 檔案與備份

- 給老師入口：[exp24_README](../navigation/exp24_README.md)，內含七問總覽、白話解讀與操作腳本；原逐題回覆仍在[固定研究版本](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/b3d68f145cfa187e208e38cae74bf33f68d7c367/reports/teacher_reply_20261005/reply.md)。
- [整合報告](integration_report.md)、[分支矩陣](branch_inventory.md)、[機器索引](manifest.json)、[逐階段紀錄](execution_log.md)。
- D槽證據包：`D:/schoolshit/專題/src/lineage_integration_backups/2026-10-08-134300/validated_evidence.zip`，29entries、CRC通過、SHA d62021a86273c6d6f69122a65f69ab2adce1015c6683407b024290e8798c6982。此包保存當時合併前證據，不含之後PR/merge產物；後者由本次Git文件PR封存。
- Git備份不含data、venv、未提交修改與ignored大型模型；未將大型ZIP/raw/secrets帶入Git。回復使用核對parent後的正常revert PR，不force push或reset main。

## 交付證據 PR 驗收規則

文件PR只允許本目錄交付文件及上述小型logs/output證據。合併前再次核對其程式tree與e1668cb完全相同、main未前進、沒有新增required checks/reviews，正常merge且保留head。合併後核對PR state、最新main ref、e1668cb祖先鏈及CLI smoke；最後SHA以GitHub PR mergeCommit及遠端ref為準，避免在提交內填寫尚不存在的自身SHA。

交付證據PR為 [#39](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/pull/39)。文件候選0edb4d8的完整111測試保存於[驗收結果](../../output/branch_integration/2026-10-08-21-22-14/validation.json)，0 failed/errors/skipped，四CLI及pip check通過。最後證據提交不改程式；PR最終head另以完整unittest查核，公開合併狀態及最終SHA可直接從該PR核對。
