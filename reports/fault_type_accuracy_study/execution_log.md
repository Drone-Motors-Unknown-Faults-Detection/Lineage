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
- fit archive整包SHA 7f0b17c7697e1f81bc46a002b93134d159c80b2cfa6784198f069a8d5dc155a0，output/fault_type_fixed_delivery/2026-10-02-00-42-49確認83 members whole SHA/CRC/member SHA全PASS。lock checkpoint 0a08a3b57173eb9de46f710c14c7d1069af34643已push/remote核對一致，00:43:18才開始evaluate。指令：`.\.venv310\Scripts\python.exe -m experiments.fault_type_accuracy_study evaluate --registry output/fault_type_accuracy_registry/2026-10-02-00-32-58/registry.json --data-root data/formal_local --locked output/fault_type_accuracy_study/2026-10-02-00-35-14/locked_study.json --code-head 0a08a3b57173eb9de46f710c14c7d1069af34643`。
- P5摘要synthetic CLI首次發現A0歷史run沒有頂層samples欄位，改用已核prediction_artifact.rows，新增筆數篡改回歸測試；輸出formatter修補不改fit/scoring/evaluation，故無需重跑受影響模型（沒有）。00:44:37合成24方法摘要PASS。最終完整271tests、pip check／16 CLI help在兩環境皆PASS，輸出output/fault_type_accuracy_acceptance_py3_10_19/2026-10-02-00-44-50與output/fault_type_accuracy_acceptance_py3_14_6/2026-10-02-00-45-01；不把software test count當效能提升。
- 摘要相容性修補checkpoint 2431ef62e5d664aadb20da4a9a96b9812c04113b已push/remote一致；evaluation依然綁0a08a3b模型lock及未更改的pipeline/scoring implementation SHA，沒有因formatter修補重fit或選seed。
- 00:43:18–00:51:11實際evaluate 198/198、0失敗，1,908,060新預測；90formal來源before/after一致。reporter於00:51:38–00:56:52核對198完整inventory、28,910unique IDs、72 shared reference checks、225 paired differences全PASS。report checksum afc7887098bc5161d7819bcbc60facdf0e444f1fe34be5340086b2ff1e2cb11b。未重跑歷史2490，也未fitA0。
- evaluation備份432,846,530 bytes／199檔，whole SHA c3093e1fecfbe2b778ff8e75645a98b6bf5f3a6d8171a4e171592b3608067f19，output/fault_type_archive/2026-10-02-00-51-48；member verification output/fault_type_fixed_delivery/2026-10-02-00-52-20 PASS。完整30,524,506-byte verified JSON也另備份，不把大JSON stage；index output/fault_type_archive/2026-10-02-00-57-45及verification output/fault_type_fixed_delivery/2026-10-02-00-58-30 PASS。
- 00:57:33–01:00:20只讀T1診斷38個score/node，source before/after一致，train/cal/test actual-model scores吻合saved predictions；diagnosis checksum d940baa61f0fccc83c4e6bfa7b15000ad38e9a29d963ee8032a3b0048f33116c。沒有threshold search、test fit、反向分數、刪寬類或硬體主張。
- 真實24方法摘要於01:01:35生成，checksum d72ae718b04dac97ba5ad3c2b1ba25b1515d7afbe31efaa4bcc63174880767e7，完整JSON17,259,960 bytes、lossless gzip426,342 bytes（Git保存gzip＋索引）。新增gzip roundtrip test後最後兩環境各272tests、pip check／16 CLI help PASS，完整stdout在output/fault_type_accuracy_acceptance_py3_10_19/2026-10-02-00-58-31及output/fault_type_accuracy_acceptance_py3_14_6/2026-10-02-00-58-42。
- diagnosis與summary新包index output/fault_type_archive/2026-10-02-01-02-00；所有新包位於D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-02/fault_type_accuracy_study，保留來源、不覆蓋舊包。完整最後whole/member SHA驗收依下一筆輸出。

## P5：報告與交付

- P4 verified-results checkpoint 9bcd4e735655d3d46f9d9531643699840780f037 已push/remote核對一致。首次scoped add受全域*.gz ignore中止；只用`git add -f -- output/fault_type_accuracy_summary/2026-10-02-01-01-35/summary.json.gz`加入已驗證426KB摘要。沒有force push，沒有stage大型pred/model／raw／formal，沒有改ignore規則。
- 最後delivery output/fault_type_fixed_delivery/2026-10-02-01-02-41确认5新ZIP／286members的whole SHA、CRC、逐member SHA全PASS；沒有刪來源、沒有覆蓋歷史包。
- final_report.md列全24方法、純fault與healthy+known、selective/coverage、三motor及九工況、T1所有score/RPM、zero-class recall、來源限制與描述性Pareto。result_index.json提供完整絕對路徑、seal/checksum、各phase checkpoints與備份索引；limitations.md對照老師兩個問題，methods_sources.md附原始作者/論文/API，reproduction.md提供實際PowerShell入口。
- 結果：A7純fault accuracy26.61→30.91%（+4.30pp），但T1 34.67→25.10%，healthy+known34.15→32.17%，未取得全面可靠升級。A4/K的T1 recall75.60%伴healthy FPR63.87%；B1/B2/B3部分改善T1操作點/排序，分類器依然弱。沒有將test觀察再寫回本輪方法，也没有P6新實作或126/N-sweep新全量執行。
- P5交付核對腳本確認所有index路徑存在、summary gzip SHA/seal/JSON無損、198/216new+baseline inventory、24方法、28,910 IDs／1,908,060新predictions、兩runtime272tests及5ZIP／286members一致PASS。最後git diff --check PASS；原282 tracked deletions再次確認保留且未stage。
- P5成果commit 8a69b2cbd1b5a26faee6e68e11074b100e51c321已push，remote research-improvements-20260920 SHA一致。本收據只補記已驗證commit/狀態，不更改模型/資料/結果；收據本身SHA以Git最後commit及最終remote核對辨識，不以自我引用hash無限提交。P0–P5 bounded工程／實驗／報告交付完成；研究可靠性依舊INCOMPLETE，P6沒有執行。
