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

- Phase1 `fc867c09ac811ae50f216377cf396a1b92cf46d0` commit/push成功，remote完整SHA一致；code/tests/log八檔，沒有stage282既有deletions或data。
- 中間checkpoint Python3.10.19 `output/synchronized_compatibility/2026-10-01-15-03-35/` 完整216tests PASS，之後另發現並修正以下loader前置缺口；因此此環境輸出不是最後程式的驗收證據。

## Phase 1b：Real training copy evidence 缺漏

- 再新增一個red test：改走real-model preflight且training_provenance_status字串為complete，但training_records缺source_sha256/numeric_row_digest，原load_models仍放行。此為synthetic negative fixture驗證程式缺口，不是實測DAQ或真實final已通過。
- 原implementation此1test失敗（FinalTestBlocked not raised，6.035秒）。修core.fresh_data.load_models：real training每record須有合法64hex source_sha256、raw_source_sha256、numeric_row_digest，缺失/invalid即reject。使用既有guard比較副本，不另造資格系統。
- Synthetic model branch保留工程fixture契約，永遠real final=false；沒有替training/採集填未知checksum，沒有將operator status字串當物理認證。
- `test_fresh_data_cli.py` 全15tests PASS（23.545秒），包含新缺欄位拒絕、未曝光副本、durable crash/concurrency及CLI validate/evaluate/resume既有測試。
- 最終舊204＋新增13＝217tests，兩runtime完整驗收接續執行。採集未知、INCOMPLETE及global selector依賴不因guard修正自動轉PASS。

- Phase1b `1ad5db339157afe047fc89fb43b31a31a18649d2` commit/push成功，remote完整SHA一致。

## Phase 2：結果、完整驗收與備份

- 最後frozen code：Python3.10.19完整217tests/pip check/4CLI help PASS，`output/synchronized_compatibility/2026-10-01-15-07-32/`（15:08:08完成）；Python3.14.6亦217tests PASS，`.../2026-10-01-15-08-51/`（15:09:32完成）。原venv/requires-python未改，不宣稱跨runtime pickle、其他OS或雲端CI。
- 前面的216checkpoint保留，不冒充最終217。兩最終environment.json與command_1.txt保存實際完整stdout/stderr；factory/Maha預設/kNN/binary/PolarMap均由整套regression覆蓋。
- Global selector依賴實際ID：T3test9294中5604known、T1test9759中5935known、T2test9857中6007known被別foldvalidation用於共同選擇。Union17546。這不等於同折estimator偷fit test；舊結果只能exploratory，不能將其升為獨立final。
- Shared val/cal6007/5604/5935；每fold一motor；全部28910已曝光。五項session/run/time/raw-source/interval欄位每項28910缺失，保留unknown，不藉metadata或檔數達成獨立group標準。
- 重新核對舊36runs的metrics是同條件描述性對照；修guard本身沒有prediction/model變更，保存預測數值差異0。振動75相對同N5 baseline accuracy+4.5226pp/F1+.040784、MahaAUROC+.043469，但T1unknown recall0、kNNhealthyFPR變差；不更換正式預設。
- 更新feature_results/model_selection_followup/final_delivery中的選擇範圍文字，指出「同折未載入test」不等於「共同選擇與全部outer test獨立」。不改舊locks/metrics/predictions，不重選候選，不重跑2490。
- 15:09:59–15:10:01 `experiments.fault_type_archive`三個明確output roots保存到 `D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-10-01\data_independence`，audit58727bytes/2files、3.10env21598/7files、3.14env21945/7files；CRC/wholeSHA PASS。
- PowerShell再逐ZIP核對16members SHA/length PASS，保存 `output/fault_type_archive/2026-10-01-15-09-59/member_verification.json`。未刪來源、沒有raw/formal/模型檔上傳；這是單一D槽備份，不冒稱異地災備。
- Phase2只stage報告／compact audit/source-checksums／environment stdout／archive索引與日誌；用Co-author、diff --check、commit/push及ls-remote核對交付，实际SHA成功後記錄。使用者先前僅授權那一份issue9摘要，不把本次commit/push請求解讀為再次發文；本輪沒有新增issue留言或對人/其他task發訊息。
