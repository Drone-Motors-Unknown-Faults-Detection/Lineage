# Lineage 專案健康度與改善空間稽核

## 稽核範圍

本稽核針對目前 `feat/knn-openset-comparison` 最新版本進行，只新增本目錄下的稽核報告，不修改正式資料、演算法核心、既有實驗結果或未提交使用者檔案。已完成的正式資料、Open Set、Mahalanobis、k-NN、PolarMap 與 exp6 工作視為現況基線；只有在有新證據時才列為改善項目。

稽核證據分成三類：

- **已確認**：可由目前程式碼、設定、測試或現有輸出直接重現。
- **需驗證**：合理的風險假設，但目前沒有足夠證據宣稱為 bug；列入驗收測試。
- **已完成現況**：目前已有測試或正式結果支撐，不重新列為待辦。

## 目前基線

| 項目 | 值 |
|---|---|
| Repository | `Drone-Motors-Unknown-Faults-Detection/Lineage` |
| 稽核 worktree | `_lineage_compare/p1_worktree`（detached HEAD，避免碰觸使用者工作樹） |
| 審查分支 | `feat/knn-openset-comparison` |
| 審查起點 HEAD | `44d98daf7eac2d65fc9ea8d8f6b94a43852bf66d` |
| Python 執行環境 | 3.12.14（repo metadata 嚴格宣告 3.10.19） |
| 單元測試 | 28/28 通過，約 2.056 秒（含啟動成本） |
| 語法檢查 | `compileall` 通過 |
| 依賴檢查 | `pip check` 通過 |
| CI | 未發現 `.github/` |
| 正式資料 | repo 工作樹沒有追蹤的 `data/` 檔案；正式資料由外部／忽略路徑提供 |

## 報告索引

- [`findings.csv`](findings.csv)：固定欄位的問題清單、證據、優先級與驗證方式。
- [`test_baseline.md`](test_baseline.md)：可重現命令、退出碼、時間、測試對照與缺口。
- [`architecture.md`](architecture.md)：模組邊界、資料流、實驗流與維護性觀察。
- [`ml_reliability.md`](ml_reliability.md)：資料切分、threshold、指標、seed、正式結果追溯性。
- [`roadmap.md`](roadmap.md)：依依賴關係拆成可獨立交付的改善任務。
- [`progress.json`](progress.json)：分階段進度、命令、commit 與阻塞狀態。

## 目前結論（持續更新）

目前核心 exp6 路徑已有明確 detector factory、正式資料 fingerprint、calibration-only threshold、portable 結果 schema 與 28 個測試；因此本稽核不把這些已被證明的項目當成待辦。主要改善空間集中在：矩陣／resume 證據完整性、資料 schema fail-fast、歷史實驗的可重現 metadata、CI 與高風險邊界測試、Web 展示的網路暴露面、環境鎖定與文件可操作性。

每完成一個稽核階段，報告會先通過 `git diff --check`、敏感資訊／大型檔案檢查，再以單一文件 commit 推送；本輪不會因為發現問題而直接改碼。
