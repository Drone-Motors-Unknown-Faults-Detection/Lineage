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

## P2：RPM／66維／signed-log／分類器

- P1 commit 67ddf2d50bcb09729c52a07be2a30173f2cf2286，push核remote一致；registry SHA/checksum已封存，真實資料仍未fit新模型。
- 新core pipeline固定欄位位置、train冗餘檢查、signed-log scale與RobustScaler train-only擬合、checksum檢查；RPM只作metadata routing，未見RPM拒絕，缺class/cal/k5 reference保留INCOMPLETE。
- 新runner各cell保存實際train/cal IDs、class-frequency來源、模型與transform checksum；A5–A8僅fit新classifier，reference綁A1模型artifact SHA，不重fitdetector。
- 11項新helper/runner tests PASS。首次signed-log fixture把RMS改0卻保留MSA1，contract checker正確拒絕；修正synthetic fixture的MSA=0後通過，未改正式資料或放寬容差。
- 全套Python3.10.19/3.14.6各257tests PASS、pip check及12CLI help PASS，產物 output/fault_type_accuracy_acceptance_py3_10_19/2026-10-01-21-02-56 和 output/fault_type_accuracy_acceptance_py3_14_6/2026-10-01-21-02-57。指令：兩環境各`-m experiments.fault_type_accuracy_acceptance`，完整stdout/exit code/environment保留。原default/PolarMap/binary與最新SHA/alias guards測試未回退。

## P3：新score／共同covariance／Conformal

- P2 commit 793fbe7870cd844371374c0dc97828c761331b64，push核remote一致。
- 新score類型獨立於factory：B1/B4 global min-raw q95；B2/B3 RPM內train own-class residual的共同LW covariance；B5/B6真值class-conditional calibration p值。原factory Maha/kNN公式與default未改。
- 共同中心／covariance來源僅同RPM train，assume_centered=True；cal僅存nonconformity/quantiles。B組共用A1 transformer/references/classifier，以artifact SHA綁定。
- 18新tests（含P0/P1/P2）涵蓋精確distances平方根、global而非own-class校準、>= ties、p=.05拒絕邊界、空/單例/多類集合、小樣本解析度、zero threshold finite及單調global校準不改AUROC。
- 雙環境全套Python3.10.19/3.14.6各264tests PASS，pip check/12CLI help PASS。完整輸出各在 output/fault_type_accuracy_acceptance_py3_10_19/2026-10-01-21-06-40、output/fault_type_accuracy_acceptance_py3_14_6/2026-10-01-21-06-40；不同runtime專用program目錄避免timestamp碰撞。不載入跨runtime joblib。
