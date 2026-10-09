# output 文件來源檢查

本輪基線為 `5a7865610fff07a455c0a23cec34fc5957ba3569`。依最新 AGENT.md 第八條以程式輸出位置核對，文件與註解只作線索；變動在獨立 cleanup 分支交付，不直接操作 main，每個 commit 只處理本次文件位置清理。

## 從 output 移出的手寫文件

- `output/integration_browser/guide_qa.md` → [導覽 QA](integration_20261008/browser_qa/guide_qa.md)。
- `output/integration_browser/stream_qa.md` → [串流 QA](integration_20261008/browser_qa/stream_qa.md)。

這兩份是操作後人工整理的敘述報告，專案程式沒有產生它們的 writer。移至 docs 保留歷史脈絡，output 不再保留副本；引用及交付 manifest 同步更新。歷史操作描述不升級為本輪重新驗證結果。

## 保留與證據界線

`experiments/aggregate_exp6.py` 明確寫入 `aggregate.md`，因此保留該程式報表。`tests/integration_evidence.py`、`tests/monitor_guard_evidence.py` 明確保存測試 stdout 到 `tests.txt`；其他驗證入口的 `check_N.txt` 同樣屬執行輸出，保留原始失敗紀錄。

CSV、JSON、log、實驗繪圖不因名稱像報告就刪除。瀏覽器截圖是工具擷取的操作證據，沒有把它們當成專案科學演算法產物。`session_analysis` 的歷史圖片未在現行 repo 找到生成程式，來源列為未核實，保留而不推定為手寫。

本輪只清理已確證的手寫文件，沒有證明所有歷史檔案皆可由現行版本完整重算。不同舊 checkout、研究分支、未提交的其他聊天產物及工作區根目錄的 Word 進度報告不混入本 PR。

AGENT.md 指定的寫作文章本輪存取失敗，依文件已列的五條寫作要求撰寫，未聲稱已讀全文。沒有更改資料、模型、指標與實驗結果。

## 接續核對：2026-10-09 14:43（Asia/Taipei）

遠端 main 仍為 `5a7865610fff07a455c0a23cec34fc5957ba3569`；PR #58 開放、尚未合併，原搬移提交 `3656852b2b5e28748621775e5816f0a47ab6602c` 已存在。清理 worktree 是 `D:/schoolshit/專題/src/lineage_output_cleanup_20261009`，接續 #46 的工作樹是 `D:/schoolshit/專題/src/lineage_integration_20261008`。兩者皆只有根目錄 AGENT.md 適用；遠端 main 指引與本機相同。保留 #46 的所有未提交修改，不重做搬移、不建立重複 PR。

新增 `tests.output_inventory_evidence`：逐檔保存原始 bytes SHA、大小、版控狀態、候選 writer 的內容 SHA／寫入行號、對應 log SHA。每份都標 `KEEP`；沒有刪除功能。writer 與檔名／動態模板相符只列 `WRITER_MATCH_HISTORY_UNCONFIRMED`，不聲稱查明歷史執行命令或科學有效性。

- 清理 worktree 初始 522 檔：505 writer 相符、15 份已記錄的外部截圖、2 份歷史來源未核實。
- #46 worktree 初始 689 檔：669 writer 相符、15 外部截圖、2 份已由 PR58 搬移的 QA 舊副本、3 份未核實歷史檔案。舊副本留在此尚未整合 PR58 的 checkout，不再次搬移或刪除，待正常整合候選分支。
- 來源未核實：`exp8_aggregate_baseline/2026-10-09-03-28-48/test_summary.json`、`session_analysis/2026-08-26-14-36-25/session_2026-08-26-14-17_analysis.png`；#46 另有 `ci_failure_download_37891517073/` 下的下載摘要。後者與 `tests.ci_remote_evidence` 的下載流程相容，但未確認該本機下載命令，不當作手寫或刪除。
- `aggregate.md` 由 `experiments/aggregate_exp6.py` 寫入；`tests.txt` 由兩個測試 evidence writer 寫入；exp6 matrix 由 `exp6_matrix.run` 寫 manifest、CSV、summary、run log。Web 串流資料由 `web/live.py` 寫入，guide fit／contract 由 `web/guide.py` 寫入；截圖與它們分開分類。

原始 bytes SHA 不用來判定 CRLF/LF 正規化差異。兩份 QA 的目的檔經 Git filter 正規化後，各與原 blob 相同（`9690f54421ddcdb98581619968d4da327e0f9fd1`、`7f15f2bc0c2a9ec790c7efff3e2e6983e2c86387`）；兩個目的檔存在、output 舊檔不存在，manifest 目標存在，2 個 Markdown 相對連結可解析。其餘原有版控 output 仍與基線相同。可從基線 blob 恢復歷史文件；本輪沒有額外移除項目。

命令：鎖版 Python 3.10.19 執行 `-m unittest tests.test_output_inventory`（2 passed）；`-m tests.output_inventory_evidence` 及 `--root D:/schoolshit/專題/src/lineage_integration_20261008`。初次沙箱解析 D 槽失敗，取得正常權限後成功，未放寬 containment。`git diff --check` 通過。

清冊：[清理初始](../output/output_inventory_evidence/2026-10-09-14-42-09/inventory.json)、[#46 初始](../output/output_inventory_evidence/2026-10-09-14-42-17/inventory.json)、[搬移與引用驗證](../output/output_inventory_evidence/2026-10-09-14-43-18/inventory.json)。最後一次清冊 526 檔包含前兩次程式清冊與環境輸出，沒有新增刪除候選。此階段交付完成後，接回 #46 的內容指紋及來源紀錄，不重跑歷史研究矩陣。
