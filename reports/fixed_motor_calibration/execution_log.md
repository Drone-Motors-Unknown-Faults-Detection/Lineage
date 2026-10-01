# 固定方法、專用馬達校準：執行紀錄

## P0 / 2026-10-01 Asia/Taipei

- 真實 checkout：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`。
- 分支 `research-improvements-20260920`；起始 HEAD `97a4434b97549851b9bae41b8b7dd5836b974f04`；remote 為 Drone-Motors-Unknown-Faults-Detection/Lineage。
- 已完整閱讀 AGENT.md、四份指定研究報告，並檢查 split、manifest、validator、leakage、factory、表示法、受控評估與相關測試。未發現額外子目錄 AGENT/AGENTS 指引。
- 90 CSV / 28,910 rows / 105 維；重新唯讀掃描 fingerprint `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`，與基線一致。
- 原有 282 tracked deletions、158 untracked 路徑保留；本輪只 stage 明列的新增/修改檔案。不處理舊 D 槽 checkout。
- Python 3.10.19 (`.venv310`) 與 3.14.6 (`venv`)；上輪各 217 tests，此數字不是本輪測試結果。
- 歷史來源：matrix `output/fault_type_matrix/2026-09-30-19-05-42`，representation fit `output/fault_type_representations/2026-10-01-08-38-17`、evaluation `2026-10-01-08-38-59`，exposure `output/fault_type_exposure/2026-10-01-01-10-40`。
- 已完成：90 檔副本/數值重複稽核、18 fit / 36 saved prediction 校驗、來源別名 guard。不要重做 2,490 runs。
- 本輪範圍：新 no-selection protocol、36 配對 detector 評估、T1 只讀失敗分析。尚未完成 P1–P5，不宣稱 fresh final validation。
- 不變限制：所有 rows 歷史已曝光，每折只有一顆 test motor；session/raw windows/實際負載與安裝等 UNKNOWN。缺硬體不阻擋本輪探索性研究。

## 提交記錄規則

每階段驗證後 scoped stage / diff --check / Co-author commit / 非 force push / remote SHA 核對。階段 commit 寫入下一次紀錄，避免自我引用 SHA。
