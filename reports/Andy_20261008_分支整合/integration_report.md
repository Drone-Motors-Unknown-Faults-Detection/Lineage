# Lineage 分支整合報告

2026-10-08，Asia/Taipei。候選程式版本：`5aaf48a8a96d92997c359fcaf709e2145f41e66d`。下列保留合併前驗收紀錄；PR #38 已於21:19合併，main `e1668cb` 的111項合併後測試通過，完整交付狀態見 [delivery.md](delivery.md)。

## 完成範圍

本報告保留 2026-10-08 的整合邊界。串流抽取來源為 JW-Albert 的 PR #36／544d4ed，原共同作者為 Claude Opus 5.5；當次只納入 exp1／3／4，不含後來才合併的健康監測串流。事前配對要求及當時 localhost QA 命令見 [固定原契約](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/1fa9431bb7b86959f29540d07b2b9290ab39ce42/docs/integration_20261008/streaming_contract.md)。現行操作以實驗手冊為準，不用這份歷史範圍判定當前功能。

已備份整合前 main、盤點全部分支、分批抽取獨立導覽與 exp1/3/4 SSE，完成真實資料配對及瀏覽器操作。沒有整批合併研究分支，沒有修改原分支或刪分支。每批 commit/push 與遠端 ref 相符。PR 必須核對最新 main、候選 head、保護與 reviews/checks 後才合併。

- [遠端備份](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/tree/backup/main-before-integration-20261008-131410)：`64cb71d84663e1745ec54db74abad68def67e8e6`，等於 MAIN_BEFORE；不使用落後的本機 main 當備份來源。
- [全部分支矩陣](branch_inventory.md)、[執行紀錄](execution_log.md)、[機器索引](manifest.json)、[串流事前契約](../../docs/experiments/README.md#web-串流生命週期)。
- 給老師先讀 [exp24 導覽入口](../../docs/navigation/exp24_README.md)，再看實驗總覽、白話解讀及示範腳本。老師問題的原逐項說明仍保留在[固定研究版本 teacher reply](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/b3d68f145cfa187e208e38cae74bf33f68d7c367/reports/teacher_reply_20261005/reply.md)。

## 分支最終處理決策

| 原分支 | 本輪決策 | 證據／保留原因 |
|---|---|---|
| feat/web-experiment-pages | 先前已整合，不重套 | #33 MERGED、tip 是 main 祖先 |
| feat/web-fit-notice | 先前已整合，不重套 | #34 MERGED、tip 是 main 祖先且 tree 相同 |
| refactor/exp8-health-into-experiments | 先前已整合，不倒退 | #32 MERGED；保留 experiments/health 搬家 |
| research-improvements-20260920 | 僅抽取導覽、來源契約、配對入口與 exp24 文件 | 固定 b3d68f；其餘3128檔完整tip差異含大量研究輸出、刪除、舊AGENT/health/Web。其他研究模組及guards未完成主線相依閉包驗證，留原分支；負面研究以固定連結保存，FAILED不換成正式winner |
| feat/web-streaming | 僅抽取 exp1/3/4、SSE及背景小窗 | 固定544d4ed；health_monitor與health串流旗標排除。#35索引缺陷仍OPEN。#36保留OPEN，避免把部分抽取冒稱整個PR完成 |
| backup_260806 | 歷史備份保留 | 舊Notebook，不作功能合併來源 |
| main | 被備份的整合基底 | 候選只加合格內容，透過PR更新，不force push |

研究分支其餘部分分類為「未完成主線整合驗證」，不等於全部不可用。Group DRO 是規劃，未實作／未實測；各FAILED家族、sealed protocol、引用卡、來源卡與原產物仍在固定研究提交及D槽。沒有用舊研究版本覆蓋 main 新架構，亦沒有替 Albert 完成其他 programming issue。

## 測試與實際效能差異

宣告與實際均 Python **3.10.19**；獨立環境 `D:/schoolshit/專題/src/tmp/lineage_integration310`。原環境3.12.14缺loguru，沒有把pip check當版本驗收。

| 驗證 | 實際結果 | 保存位置 |
|---|---|---|
| 整合前 main 的既有測試 | 76 passed、0 failed/errors/skipped | output/branch_integration/2026-10-08-13-21-54 |
| 導覽候選 | 98 passed、0 failed/errors/skipped | 2026-10-08-13-30-10 |
| 完整已提交候選5aaf48a | 111 passed、0 failed/errors/skipped；pip check與四CLI通過 | 2026-10-08-13-41-48 |
| 導覽逐樣本配對 | Maha/kNN各595、合計1190筆，差異0；重跑相同、來源未變 | output/navigation_regression/2026-10-08-13-42-01/summary.json |
| exp1/3/4 對原main配對 | 5組：exp1/3各Maha與kNN、exp4全部三段；原run、新run、iter_run結果全相同 | output/stream_integration_regression/2026-10-08-13-36-22/summary.json |
| 真實瀏覽器 | 導覽的build/confirm/reset/mode/dataset/reload、A/B停止；原首頁、背景小窗、三實驗完成、停止、錯誤後舊入口恢復 | [手寫導覽紀錄](browser_qa/guide_qa.md)、[手寫串流紀錄](browser_qa/stream_qa.md)；9張外部工具截圖在 [驗收附件](browser_qa/screenshots) |
| 原封存摘要 | exp6=54runs、exp8=54列可讀；SHA保留、檔案未改 | manifest.json |

Windows暫存權限造成的首次12 errors、沙箱TCP停滯ABORTED、串流首次3個test methods／5failure entries均保存，沒有刪除負面證據。串流修補只處理close例外鎖釋放及非有限速率／非物件JSON；保存路徑測試改為正確解讀ROOT相對路徑。未調模型、門檻或資料讓成績對齊。

同工況exp1本輪UI的healthy FP=7/64=10.9375%、九配置unknown拒絕100%、AUROC1，與原main相同；**差異0百分點**。這不是跨馬達fault-type分類或已解決T1跨馬達未知召回問題。A/B是CSV劇本，延遲單位是筆數；沒有物理退化真值、每小時誤報或RUL。

完整候選中 `core/`、`web/live.py`、`experiments/exp2_scale_growth.py`、`experiments/health/`、`health_monitor.py`、`pyproject.toml`、`AGENT.md` 相對MAIN_BEFORE零diff。正式105維、LW預設、q95、kNN5 factory、PolarMap與未知不fit規則不變。exp1/3/4只由run抽成iter_run，共用相同計算。

## 資料、來源與未知限制

實際唯讀資料根 `D:/schoolshit/專題/src/Lineage/data` 為**60份**clean CSV：T1/T3 ×三RPM ×十配置。完整清冊SHA `82534111c7901bfe0709637f4979976ce73445a54353e7c377e71e40b4cf2abd`，前後相同。本輪沒有重建T2，不能冒充歷史90檔指紋，也未重新執行2490次研究或完整九工況回歸。

原始session、錄製邊界、重疊窗口、清理遮罩、設備／負載等仍UNKNOWN；歷史曝光與fresh INCOMPLETE保留。T1/T2/T3為不同馬達，不能串成一顆馬達生命週期。舊main展示保留的「每點1秒」等文案屬既有設定，未由本輪資料來源證明；獨立導覽明示CSV筆數與這些限制。確認後用完整標記配置池重擬合是oracle展示，不稱arrival-only學習。

## 備份、工作區與回復

- 工作樹：`D:/schoolshit/專題/src/lineage_integration_20261008`。
- 原checkout：`D:/schoolshit/專題/src/Lineage`，仍保留dda8910，未切branch、未修改data、原status無dirty。
- 新D槽證據包：`D:/schoolshit/專題/src/lineage_integration_backups/2026-10-08-134300/validated_evidence.zip`；29entries、全包CRC通過、SHA見manifest。沒有覆蓋歷史備份。
- 抽查舊 `lineage_fault_type_artifacts/2026-09-30/fault_type_2026-09-30-23-49-34.zip`：11entries、CRC通過；其他三份共約11GB只盤點路徑／大小，未全包CRC或重訓，不能聲稱全部恢復驗證。
- Git備份僅保留tracked內容，不含data、venv、其他ignored模型、未提交修改。未發現LFS、submodule或gitlink。
- 候選無意外tracked deletions；282項舊刪除未帶入。小型log／output／截圖入Git，大型來源ZIP與raw data未stage。

需要回復時先查PR的merge SHA及父提交，用新分支做正常revert並建PR；merge commit需核對mainline-parent。不要reset/force push main到備份。備份分支可建立獨立checkout查閱；它不能代替資料或大型外部產物備份。

## 執行入口

```powershell
# 先進工作樹，啟用宣告版本環境；data根保持唯讀
python -m tests.integration_evidence --phase candidate --data-root D:/schoolshit/專題/src/Lineage/data
python -m experiments.navigation_regression --data-root D:/schoolshit/專題/src/Lineage/data --seed 42
python -m tests.stream_regression --data-root D:/schoolshit/專題/src/Lineage/data --seed 42
python -m web.guide --data-root D:/schoolshit/專題/src/Lineage/data --port 8601 --seed 42
python -m web.server --bind-address 127.0.0.1 --data-root D:/schoolshit/專題/src/Lineage/data --port 8600 --seed 42
```

工程測試需要完整Git歷史中的MAIN_BEFORE。合併後執行用 `--phase post_merge`。本輪沒有部署、對外開放QA服務、聯繫老師／作者或其他聊天室。
