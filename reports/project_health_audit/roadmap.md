# 改善 Roadmap（稽核期間持續更新）

本文件先建立索引，待 correctness、architecture、test、performance、security 與文件階段完成後填入完整 PR-sized 任務。每個任務會包含目標、範圍／非範圍、檔案、步驟、測試、驗收、依賴、rollback、commit 拆分、effort 與 risk。

## 目前候選主線

1. P0/P1 correctness：矩陣 resume artifact 完整性與失敗狀態驗證。
2. P1 data：formal dataset schema／9 工況／class mapping fail-fast validator。
3. P1 reproducibility：統一 exp1–3／exp6 resolved metadata 與環境紀錄。
4. P1 test／CI：Linux + Windows 合理 Python 版本、高風險邊界測試、coverage gate。
5. P1 security：Web origin／auth 邊界、錯誤訊息脫敏、archive output containment。
6. P2 maintainability／performance／docs：設定 schema、資料讀取 profiling/cache、文件與 troubleshooting。

## 非本輪範圍

本輪只寫稽核報告，不直接修改上述程式、資料、threshold、split 或正式結果；roadmap 完成後停止，等待使用者選擇實作順序。
