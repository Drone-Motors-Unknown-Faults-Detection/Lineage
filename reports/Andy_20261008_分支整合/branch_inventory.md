# 2026-10-08 分支整合盤點

## 備份與工作區

整合前遠端 main：`64cb71d84663e1745ec54db74abad68def67e8e6`。
第一個必要寫入為建立本機 `backup/main-before-integration-20261008-131410`，已推送；`git ls-remote` 與 GitHub ref API 均確認其 SHA 與 main 相同。
[備份分支](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/tree/backup/main-before-integration-20261008-131410)。

獨立工作樹：`D:/schoolshit/專題/src/lineage_integration_20261008`，分支 `integration/branches-20261008-131410`，由備份 SHA 建立。原 `D:/schoolshit/專題/src/Lineage` 保持 `dda8910b7807431544ce1646f9b6bf776f2e29d5`，未提交修改為零，未切換或還原。暫存研究鏡像缺少 Git 控制檔，未將它當成有效工作樹，也未還原先前提及的 282 項刪除。

## 全部分支

以下 behind / ahead 相對整合前 main；tree diff 是兩個 tip 的完整檔案差異，與 compare API 的前進差異不同。`git cherry` 未發現需以 patch 等價另行去重的前進提交。祖先分支的成果已在 main，但後續 main 可另有修改，故不倒退合併其 tip。

| 分支 | head SHA | behind / ahead；tree diff | PR／決策 | 相依與驗證 |
|---|---|---|---|---|
| main | 64cb71d84663e1745ec54db74abad68def67e8e6 | 0 / 0；0 | 整合基準 | 完整測試、CLI、factory、Web 基準待本輪執行 |
| backup_260806 | 3a699ab81c16503fff4ba2c2b8ec566202c24d7d | 115 / 0；1327 | 歷史備份，永久保留 | 舊 Notebook 架構，不是功能候選 |
| feat/web-experiment-pages | 926da639c76e3642c5854c541fc732bb3eac6c55 | 4 / 0；12 | #33 已合併，祖先證明；不重套 | 保留 main 的實驗頁及 API |
| feat/web-fit-notice | f65ab1538c7c973085ca2674c4f601692d2ac14c | 1 / 0；0 | #34 已合併，tree 等同 main | 不重套 |
| refactor/exp8-health-into-experiments | 12c97d6adbd954c23a78bb29cc09e27be8bc13eb | 9 / 0；22 | #32 已合併，祖先證明 | 保留 experiments/health 與 main 文件規範 |
| feat/web-streaming | 544d4ed8c6516622e2f46c095351f9483a61635c | 0 / 1；15 | #36 OPEN；先驗證，必要時只抽取合格部分 | exp1/3/4/8-3 iter_run、SSE、共用鎖；#35 健康索引套到短故障池未解決；不得冒稱修復 |
| research-improvements-20260920 | b3d68f145cfa187e208e38cae74bf33f68d7c367 | 29 / 183；3128 | 部分抽取，禁止整批 merge | 舊檔刪除、health 路徑、Web 與 AGENT 都和 main 衝突；先整合可獨立驗證的導覽／工具，研究成績保留固定來源，不換正式預設 |
| backup/main-before-integration-20261008-131410 | 64cb71d84663e1745ec54db74abad68def67e8e6 | 0 / 0；0 | 本輪已驗證備份 | 不整合、不刪除 |
| integration/branches-20261008-131410 | 基準為 64cb71d84663e1745ec54db74abad68def67e8e6 | 本輪產物 | 新整合分支 | 每批限定檔案、測試、commit、push |

本機原 main 雖落後遠端，仍保留其正式 commit；它是本機 checkout 狀態，不是另一個新功能分支。遠端完整分支查詢未超過一頁；所有既有 PR 查詢涵蓋 #1 至 #36，其中唯一 OPEN PR 是 #36。

## 指引差異與權限

main、兩個 Web 已合併分支及 streaming 的 AGENT blob 相同：`8f35a6bf14fa4747d63add1d6bc852b65bcb4784`，完整讀取 main 一份即涵蓋相同內容。exp8 refactor blob `39199ecf498aabcc9b429a50eafe1033c99eda4d` 與研究分支 blob `f3b92347582bceff98ede6513f06458cdefdeac5` 亦完整讀取。研究分支仍是舊 health/ 路徑與文件編號規則，整合以 main 的 experiments/health、expN 文件命名和 reports 範圍為準，不回寫舊 AGENT。

帳號有 push 權限；main protection API 回覆 Branch not protected，rulesets 為空。PR #36 無 review／評論／check runs；status API 的 pending 搭配零 statuses，不代表 CI 成功。沒有啟用 admin bypass。寫作指定文章無法由瀏覽工具取得，未宣稱全文已讀；沿用 AGENT 已列明的五個寫作規則。

## 資料與整合邊界

本輪不重新訓練歷史 2,490 次研究，不替換 Mahalanobis–Ledoit–Wolf／PolarMap，不變更未知資料擬合規則。D 槽原 checkout 掃描到 60 個 clean CSV，尚不能當成歷史 90 檔正式資料版本；需要另查來源與 checksum，未用歷史指紋冒充此目錄。Python 原 venv 實際為 3.12.14，與 main 宣告 3.10.19 不同；pip check 通過不等於版本契約通過，將用獨立相符環境驗證。

備份分支只保留 Git 追蹤內容，不包含原 data、未提交修改、venv、gitignored 模型、外部 ZIP。遠端各分支樹未發現 .gitattributes、.gitmodules 或 gitlink，不需另取 LFS／submodule 物件。大型研究產物及無授權全文不搬入 main。採集 session／原始視窗獨立性仍為 UNKNOWN；工程整合不使探索性結果成為 fresh final。

## 批次順序

1. 此盤點先 commit + push 工作分支。
2. 建立 main 基準與唯讀資料索引，鎖定可抽取的獨立工具／文件。
3. 對研究導覽與 streaming 分別驗證，相容改動限定 import、路徑、編排與文件；#35 或其他驗證不足的部分保留來源分支。
4. 完整候選回歸、PR、合格批次實際合入 main，再核對 main 及受影響 smoke。所有分支保留。

## 整合後覆核（21:19–21:20，Asia/Taipei）

PR #38 已 MERGED，main 為 `e1668cb48b91520d2500be643351d9c4c8d9494b`。研究導覽與 exp1/3/4 串流已實際整合，不再只是候選。原分支清單再次完整查詢，所有原 head SHA 與上表相同，備份仍等於 MAIN_BEFORE。PR #36 仍 OPEN、head 544d4ed 不變；issue #35 仍 OPEN。其他研究模組仍未完成主線相依驗證，沒有藉本次合併宣稱完成。完整合併後111測試與五組真實配對通過，見 [交付紀錄](delivery.md)。本節更新不改動原盤點時點的 ahead/behind。
