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
