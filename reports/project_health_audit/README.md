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

目前核心 exp6 路徑已有明確 detector factory、正式資料 fingerprint、calibration-only threshold、portable 結果 schema 與 28 個測試；因此本稽核不把這些已被證明的項目當成待辦。已確認的改善空間集中在：矩陣／resume／aggregate 證據完整性、資料 schema fail-fast、channel 對齊政策、fallback fingerprint、歷史與正式實驗的可重現 metadata、Stage-2 archive containment、CI 與高風險邊界測試、Web 展示的 origin／錯誤暴露面、環境鎖定、效能 profiling、文件與 Windows onboarding。

每完成一個稽核階段，報告會先通過 `git diff --check`、敏感資訊／大型檔案檢查，再以單一文件 commit 推送；本輪不會因為發現問題而直接改碼。

## 最終評分（本次稽核）

| 項目 | 分數／10 | 證據摘要 |
|---|---:|---|
| Correctness | 8 | 28/28 tests、54/54 formal runs 與 strict exp6 metrics；但 loader schema 與 resume artifacts 仍不完整。 |
| Data Reliability | 7 | formal manifest 實際 9 工況／10 config／90 files、105 維與 archive hashes；缺 class 可被 loader 忽略，channel mismatch 會截斷。 |
| ML／Experiment Reliability | 8 | calibration-only threshold、相同 split/seed/factory 與 paired aggregate 已測試；exp1–3 metadata 與 health-only scope 仍有限制。 |
| Architecture | 7 | detector factory／PolarMap invariant 清楚；設定與 summary schema 分叉，且有三個大型 orchestration function。 |
| Test Coverage | 5 | 28 個測試集中於近期 core/exp6；沒有 CI、coverage、Web、歷史 exp1–3、loader 直接測試。 |
| Reproducibility | 6 | exp6 有 fingerprint/commit/Python，但缺 package/hardware；exp1–3 沒有完整 provenance；Python 3.10 metadata 與 3.12 venv 不一致。 |
| Performance | 7 | formal inference Mahalanobis 0.006262 s、k-NN 0.013440 s 平均；load/reload 與大 reference bank 尚未 profiling。 |
| Security | 5 | secret pattern scan clean、raw/data/zip ignored；Web 無 origin/auth，Stage-2 config path 仍未做 containment。 |
| Documentation | 7 | README 有完整研究脈絡與 exp6 說明；docs 明示歷史 broken links，但缺 current operations/troubleshooting index。 |
| Developer Experience | 6 | 8 CLI help 全通過；主要指令是 POSIX `venv/bin`，Windows setup 與 Python policy 不一致。 |

分數是目前證據的工程判讀，不是對模型研究價值的評分；高分項目仍可有明確 P1 finding。
