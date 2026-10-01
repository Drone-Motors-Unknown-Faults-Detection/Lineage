# 有界準確率研究：執行紀錄

## P0：接續與診斷驗證

- 起始 HEAD c4767e35eca4fa5f43fe323059090b80210871ae；工作樹為既有 p1_worktree，分支 research-improvements-20260920，origin 為組織 Lineage。
- 完整閱讀 AGENT.md、指定基線文件、feature contract 與既有 fixed runner/report/validator/tests。282 個既有 tracked deletions 保留，不 stage。
- 既有 Python 3.10.19 / sklearn 1.7.2 與 Python 3.14.6 / sklearn 1.9.1。已核對 sklearn 1.7 官方 HGB/LDA 契約，無新增依賴；LDA lsqr 僅 predict，不使用 transform。
- 新 baseline runner 只重算保存的 36 組預測並檢查 SHA／IDs／指標／曝光，不重新訓練；新 helper 補 selective accuracy/coverage 與 healthy 對 known accuracy 的貢獻。
- 固定去冗餘欄位由公式位置決定：每軸 clearance、MSA、variance，共移除9維。只在 train 檢查關係，rtol=1e-8、atol=1e-10；不以 test 相關性選欄位。
- 本輪 P0–P5 預算198新增邏輯評估；P6僅候選，不執行搜尋。所有結果維持 EXPLORATORY_HISTORICAL_TEST_EXPOSED、獨立資格 INCOMPLETE、採集未知 UNKNOWN。
- P0 helper 2 tests PASS；20:57:02–50 baseline CLI 成功核對36組／346,920筆／28,910 unique IDs，90來源fingerprint前後不變，9組train公式關係通過。產物：output/fault_type_accuracy_baseline/2026-10-01-20-57-02/baseline_index.json；沒有新增baseline fit。執行指令：`.\.venv310\Scripts\python.exe -m experiments.fault_type_accuracy_baseline --data-root data/formal_local --code-head c4767e35eca4fa5f43fe323059090b80210871ae`。

## P1：封存registry

- P0 commit 3737fc216f002cc98ef1155967db46bae2ab8f08，push核remote一致。
- 20:59:27 prepare-only封存registry e705ca32f119b3cc2f7a9254e4263e22d56c0be0937ebe9d7d0ab1d7d9238869：output/fault_type_accuracy_registry/2026-10-01-20-59-27/registry.json，完整198邏輯評估、欄位位置、fixed classifier resolved params、公式／quantile linear／eps／conformal ties等已寫入，未fit。
- registry builder與check重建比對一致；helper/registry tests 3項通過後提交。HGB early_stopping=False，LDA uniform prior，SVM probability=False；未默默增加依賴或隱藏校準early stop。
