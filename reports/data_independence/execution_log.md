# 現有資料獨立性／洩漏稽核執行紀錄

2026-10-01，Asia/Taipei；工作 root `C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`。

## Phase 0：核對基線

- 完整讀 AGENT.md，沿用研究分支 `research-improvements-20260920`。fetch/ls-remote確認起點 `ffdf55e71959da1f7e9be56f395cfe424532683f` 與遠端一致。
- 原282個 tracked deletions保持unstaged；不修改舊checkout、formal、既有manifests、locks或predictions。
- 沿用既有catalog、FeatureStore、validator、sealed exposure ledger、factory與saved-prediction report，不重跑2490研究／重建class roles。
- 稽核範圍：完整90檔／28910樣本，原預登錄第一N5組合的三motor folds、18表示fit audits、36保存runs。三fold的基本來源分區是所有N-sweep沿用結構，但本輪不冒称逐一重新稽核全部2490 run。

## Phase 1：可重現缺口與修正

- 新增7個red regression cases並先在原implementation執行：validator4失敗、final guard3失敗。實際缺口為source bytes改名跨split、record SHA與inventory不一致、raw SHA改名隱藏重疊、同raw非重疊仍偽裝獨立，以及未曝光training的numeric/source/sample-ID副本進final。
- 修validator：沿用原error codes，source SHA aliases納入group檢查、record SHA綁inventory；raw SHA/id/path均檢查，重疊以所有已知aliases比較。不將未知raw interval補成0，也不放寬共享val/cal的依賴。
- 修原guard_final_test：同時比較bound training/calibration provenance的sourceSHA、numeric digest、sample IDs及locked selection IDs；不只比較歷史final ledger。新增第8個selection-ID regression case。未知training numeric evidence不能被程式憑空恢復；缺證據的real模型仍需嚴格fresh preflight。
- 新增read-only core.fault_type_leakage與experiments.fault_type_leakage_audit(run/main/setup_run)，使用舊工具核對全部features、saved inputs、paired metrics與global-choice dependence。不擬合、不調門檻、不改候選選擇，不刪除任何資料。
- 新增4個audit tests：exact/12g copy層級、signed-zero數值相等、global-vs-fold-local選擇相依、unknown/missing fit inventory拒絕。
- 修正後targeted validator11tests、final guard20tests PASS；Python3.10.19完整216tests PASS（15:00:59啟動，30.828秒）。已有warnings為歷史退化moments及synthetic單labelconfusion測試；CLI invalid-choice stderr是預期negative test，suite exit0。
- 實際CLI於15:01:18–39完成，20.81秒，exit0，`output/fault_type_leakage_audit/2026-10-01-15-01-18/`。0個file byte aliases／exact105 duplicates／12g duplicates；三fold同折test input交集0、18fit ID audits PASS。
- 同一次重新核對全部36保存predictions SHA/IDs/metrics，346920 records；18model artifact SHA核對，沒有joblib反序列化／重訓。正式fingerprint維持c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d。
- 此phase提交code/tests/log；後續保存完整216tests雙runtime證據、報告与backup。實際commit/push SHA待成功後記錄，不預填。
