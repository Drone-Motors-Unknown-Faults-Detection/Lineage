# 2026-10-09 主線整合與關單紀錄

## P0-A：PR #40 合併前審閱

本輪從 `delivery/issues-30-19-37-29-20261008` 的 `5a54cf1e500ddb8c8f1f031ce3cd0e0282429467` 重跑。遠端 main 為 `4f783c676849a27185cd28d2410b4e76639b7357`；PR #36 仍有衝突，head 為 `544d4ed8c6516622e2f46c095351f9483a61635c`，本輪不修改其待決檔案。

已審閱 `core/monitor.py`、guard 測試、導覽逐筆索引與相關文件。`_require_fitted()` 保護 score、classify、project、summary；重新擬合開始即清除完成旗標，失敗時不沿用舊模型。未發現需先阻擋 PR #40 合併的問題。

Python 為 3.10.19，使用既有 `D:/schoolshit/專題/src/tmp/lineage_integration310/Scripts/python.exe`，沒有重建或刪除環境。資料根目錄為 `D:/schoolshit/專題/src/Lineage/data`，此次導覽覆蓋 T1/8000rpm；來源清冊列出目前 checkout 的 60 份 CSV，不宣稱已驗證另一份 90 CSV 研究資料。

| 指令（`python -m`） | 本輪結果 | 產物 |
|---|---|---|
| `tests.integration_evidence --phase candidate --data-root D:/schoolshit/專題/src/Lineage/data` | 124 passed，0 failed/error/skipped；pip check 與四個 CLI help 成功 | [validation.json](../../output/branch_integration/2026-10-09-04-08-52/validation.json)、[tests.txt](../../output/branch_integration/2026-10-09-04-08-52/tests.txt) |
| `tests.monitor_guard_evidence` | 11 項通過；兩方法 × 兩 seed × 兩階段共 8 組；score 與 PCA 最大差值均為 0，分類、summary、split 相同 | [evidence.json](../../output/monitor_guard_evidence/2026-10-09-04-09-05/evidence.json) |
| `experiments.navigation_regression --data-root D:/schoolshit/專題/src/Lineage/data --seed 42` | Mahalanobis/k-NN 各 595 筆，0 mismatch，來源 SHA 不變 | [summary.json](../../output/navigation_regression/2026-10-09-04-09-06/summary.json) |
| `tests.issue_delivery_evidence --data-root D:/schoolshit/專題/src/Lineage/data` | 16 份來源、6 工況、80 個文件目標核對成功 | [evidence.json](../../output/issue_delivery_evidence/2026-10-09-04-09-10/evidence.json) |
| `tests.guide_delivery_evidence` | 歷史 1,190 筆配對、CSV 與文件 SHA 核對成功；未重新進行瀏覽器驗收 | [evidence.json](../../output/guide_delivery_evidence/2026-10-09-04-09-11/evidence.json) |

`integration_evidence` 的 `main_before` 欄位是工具歷史常數 `64cb71d...`，不能作為本輪 base；本輪實際 base 已列於本頁及 GitHub PR。測試紀錄中的 `head` 是實際受測程式 commit。測試資料採 fixture；真實 CSV 導覽重播另列，兩者不混成研究效能結果。

AGENT.md 指定的《數位時代》寫作文章本輪無法取得全文；依 AGENT.md 明列的五項規則撰寫。正式預設、Ledoit–Wolf、k-NN factory 與 PolarMap 未變。這些驗證支持工程行為一致，不支持 fresh final、來源獨立性或準確率提高。

合併後須在實際 main commit 再測，才關閉 #29；#19、#30、#37 仍有各自缺口。後續紀錄追加於本頁，不改寫既有結果。
