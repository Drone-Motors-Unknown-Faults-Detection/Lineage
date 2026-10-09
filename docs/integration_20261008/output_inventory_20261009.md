# output 接續核對紀錄

2026-10-09，Asia/Taipei。本輪開始時遠端 main 為 `5a7865610fff07a455c0a23cec34fc5957ba3569`，PR #58 原提交為 `3656852b2b5e28748621775e5816f0a47ab6602c`，仍開放。根目錄 AGENT.md 與遠端相同，無子目錄指引。指定寫作文章存取失敗，依 AGENT.md 已列的五條規則撰寫，不聲稱讀過全文。

## 範圍與既有成果

清理工作樹 `D:/schoolshit/專題/src/lineage_output_cleanup_20261009`；接續 #46 工作樹 `D:/schoolshit/專題/src/lineage_integration_20261008`。沒有掃描其他 repo 或根工作區 output。保留 #46 的未提交修改。

PR58 已將 `output/integration_browser/guide_qa.md`、`stream_qa.md` 移至 [guide QA](browser_qa/guide_qa.md)、[stream QA](browser_qa/stream_qa.md)，修正引用與 manifest。本輪沒有重新搬移或額外刪檔。兩份目的檔的 Git 正規化 blob 與基線相同（`9690f54421ddcdb98581619968d4da327e0f9fd1`、`7f15f2bc0c2a9ec790c7efff3e2e6983e2c86387`）；output 舊檔不存在、manifest 目標存在。其餘原版控 output 不變；可從基線 blob 恢復歷史文件。原始 bytes SHA 與 Git CRLF/LF 正規化 blob 分開解讀。

## 逐檔清冊與證據界線

`tests.output_inventory_evidence` 唯讀掃描全部檔案，記錄 bytes SHA、大小、版控狀態、writer 的 SHA／寫入行號及對應 log SHA。全部標 KEEP，沒有刪除功能。writer 相符不等於歷史版本、命令、採集來源或科學有效性已證實。

- 清理工作樹初始 522 檔：505 writer 相符、15 已記錄的外部截圖、2 未核實歷史檔案。
- #46 工作樹初始 689 檔：669 writer 相符、15 外部截圖、2 份 PR58 已處理但此 checkout 尚未整合的 QA 文件、3 未核實歷史檔案。
- `aggregate.md` 由 `experiments/aggregate_exp6.py` 寫入；`tests.txt` 由測試 evidence writer 寫入；exp6 matrix 的 manifest、CSV、summary、run log 有對應流程。Web 串流由 `web/live.py` 寫入，guide 的 fit／contract 由 `web/guide.py` 寫入。它們皆保留，截圖不冒稱演算法輸出。
- 未核實且保留：`exp8_aggregate_baseline/2026-10-09-03-28-48/test_summary.json`、`session_analysis/2026-08-26-14-36-25/session_2026-08-26-14-17_analysis.png`。#46 另有 `ci_failure_download_37891517073/` 下載摘要，未確認本機下載命令，不推定手寫或刪除。

清冊：[清理初始](../../output/output_inventory_evidence/2026-10-09-14-42-09/inventory.json)、[#46 初始](../../output/output_inventory_evidence/2026-10-09-14-42-17/inventory.json)、[搬移核對](../../output/output_inventory_evidence/2026-10-09-14-43-18/inventory.json)。最後 526 檔包含前兩次清冊及環境輸出。清冊為程式產物，說明文字只放 docs。

## 命令、失敗與交付

Python 3.10.19：`-m unittest tests.test_output_inventory` 2 passed；`-m tests.output_inventory_evidence` 與 `--root D:/schoolshit/專題/src/lineage_integration_20261008` 成功。初次沙箱解析 D 槽被拒，正常權限重試成功，未放寬 containment。`git diff --check` 通過。沒有改模型、正式資料、預測或失敗紀錄。

本機提交 `5ded768` 推送遇到遠端同時新增 `b61b8964457b53cacaa0e0c18e3c1fae6e6bf7cf`（Albert 刪除舊 `docs/output_cleanup_20261009.md`）而失敗。保留遠端刪除，以此新路徑保存本輪核對，不恢復原文件、不 force push。遠端 main 此時前進至 `6ace108157a7f9e1e03b76d343c93e222020bd41`（PR59）；AGENT.md 仍相同，未改它或 Albert 程式。

清理核對完成後接回 #46 的內容 SHA／來源紀錄提交與驗證，不重新執行歷史 2,490 組研究。
