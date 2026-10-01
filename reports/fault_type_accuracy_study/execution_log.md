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

## P4：封存、逐樣本評估與獨立重算

- P3 commit a0f2a4aeb3af4490f7ee756c456fb65ffac1f5c5 已push並核remote。
- 首次端到端synthetic CLI在registry重新載入時拒絕：RobustScaler quantile_range tuple經JSON變list。先前in-memory檢查沒有覆蓋roundtrip；新roundtrip測試重現並修補。舊registry保留，不做真實fit；新版 fault_type_accuracy_study_v2_json_contract 使用JSON canonical list，建立sklearn scaler時還原tuple。科學方法、參數、198預算均不變。
- 21:11:58與00:29:23/34失敗synthetic工程輸出完整保留；00:30:45 Python3.10合成198評估端到端PASS（非研究成績），實際198 classifier/180 factory reference/27 pooled reference/90 transform/162 score calibration；原始synthetic資料不stage。
- 新evaluator先查lock seal、runtime、implementation SHA、完整模型inventory、所有fit/cal IDs與joblib SHA；test只推論，逐筆保存raw距離、class thresholds/p值、final label、來源與模型SHA。reporter重算score公式、分類與拒絕指標、配對IDs，沒有selector/winner。
- 新測試覆蓋JSON roundtrip、改參、漏implementation、selector、共用val/cal、reference SHA/來源、prediction truth/score/p值/集合/模型SHA。完整tests與雙runtime smoke狀態依後續實際輸出更新。
- 新版real registry checksum 8418b7539670a3b4fd952e4a087b83bc18cb1870fbc4ef5eb4f44530b9523e5a，output/fault_type_accuracy_registry/2026-10-02-00-32-58/registry.json。Python3.10.19/3.14.6各268 tests、pip check與14 CLI help PASS；完整stdout在output/fault_type_accuracy_acceptance_py3_10_19/2026-10-02-00-31-49與output/fault_type_accuracy_acceptance_py3_14_6/2026-10-02-00-32-00。
- 雙環境各自合成CLI完整198組／71,280筆預測重算PASS：output/fault_type_accuracy_smoke/2026-10-02-00-30-45與00-32-59。版本各自build/fit/load，不跨runtime載入joblib。T1 diagnosis合成38個score/node亦只讀核對PASS，output/fault_type_accuracy_diagnosis/2026-10-02-00-34-07。所有synthetic結果僅工程驗收。
- P4工程＋v2 registry checkpoint 5082df46fd2b605ec2d6aa56c331be943c94b4e5已push，remote一致。真實fit指令：`.\.venv310\Scripts\python.exe -m experiments.fault_type_accuracy_study fit --registry output/fault_type_accuracy_registry/2026-10-02-00-32-58/registry.json --data-root data/formal_local --code-head 5082df46fd2b605ec2d6aa56c331be943c94b4e5`。
- 00:35:14–00:40:13真實train/cal fit完成，81實體bundle／225node audit，198 classifier、180 factory reference、27 pooled reference、90 representations、162新score校準，0缺格／失敗。fit bundle seconds合計287.6584，logger wall約299秒，非串流延遲／峰值記憶體測量。fit後225 audits逐項核對PASS，90formal source前後不變。lock checksum 6cac7419a437779ed4e2e83300ea40895a16a96694720c869b4fffe8906f25a7，output/fault_type_accuracy_study/2026-10-02-00-35-14/locked_study.json；尚未test。
- fit備份包新建D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-02/fault_type_accuracy_study/fault_type_2026-10-02-00-35-14.zip，230,670,782 bytes／83檔；CRC PASS，未覆蓋舊包、未移除来源。archive index在output/fault_type_archive/2026-10-02-00-42-27。whole/member SHA複核依下一筆輸出；lock commit/push後才evaluate。
- P5摘要只產生all methods與描述性Pareto關係，不產生選定模型；新增2項測試。兩環境最後完整270tests、pip check與16 CLI help PASS，stdout在output/fault_type_accuracy_acceptance_py3_10_19/2026-10-02-00-37-47及output/fault_type_accuracy_acceptance_py3_14_6/2026-10-02-00-37-58。
