# RPM工況原型執行紀錄

2026-10-03，Asia/Taipei。先行手冊／來源commit `1dd0040f22251744a60eb0f02d9e63714c2b7a72`已push且remote相符，才新增core／tests。沒有修改exp15／16的sealed程式與手冊。

20:18–20:19：兩環境各`-m unittest tests.test_fault_type_context_prototypes -q`，11項通過、0失敗，Python3.10.19為0.020秒，3.14.6為0.018秒。包含一次／二次含aux有限差分、degree0退化至pooled GLVQ、二次static等於各RPM每類均值、手算距離、RPM合法性、缺工況支持、序列化、同seed重現與未收斂禁止推論。

第一次合成routing測試的工況位移未跨越pooled分類邊界，預期「錯誤RPM必定造成錯分類」不成立，兩環境各11項中1項失敗。改合成資料的已知工況位移向量`[2,-.5,1]`為`[3,-.5,2]`，使錯RPM路由確實可觀察；公式／formal資料／方法參數未改。保留失敗解釋，不將合成測試調整包裝成真實模型提升。

目前runner未完成、尚未lock／fit／evaluate本批formal資料。下一步按手冊實作明確RPM推論路徑、來源重建與封存矩陣；完整測試稍後報實際新數目，不能沿用上一批472項冒稱全部已驗證。

## runner工程完成

core／11測試commit `53b0bba3fb437f0160a6dfc2abb79f9206d261f9`已push／remote一致。新增runner雙介面／checkpoint／來源重建，RPM input為既有三code解碼，不允許未知RPM、motor或fault label代替。每class/RPM初始化用全部known train，loss／metric用原subset；cal只parent C02/M detector校準，classifier不讀cal fit。

新增9項source/purpose測試，含錯train/cal RPM、重封coeff、cal初始化、unknown/test motor污染、global winner／假fresh拒絕與空selection。最初synthetic protocol fixture缺known_labels欄位造成兩環境各1error，改測試adapter映射既有manifest的known roles；未放寬real protocol guard。之後兩環境各20通過，1.861／1.922秒。

兩環境exp17 help/smoke通過，output `fault_type_context_prototypes_smoke/2026-10-03-20-24-15`／`20-24-16`，SYNTHETIC_ENGINEERING_ONLY。完整`-m experiments.fault_type_continuous_acceptance`各492通過、0失敗，Python3.10.19／3.14.6，所有39命令exit0（pip／37既有CLI）。`output/...py3_10_19/2026-10-03-20-26-06/environment.json`及`...py3_14_6/2026-10-03-20-26-17/environment.json`已隨H結果提交；沒有把新module help算入舊37個CLI。

截至此段尚無I formal protocol、fit或outer結果。smoke／tests屬未提交runner工程驗證，正式lock須在code提交後生成；source SHA將由lock保存。exp16結果交付commit `e5f8a5b7f8bea6accebd0de669d78fc023ee44d7`已push且remote一致，12方法均FAILED，下一批不挑H最好seed作參數。

runner commit `4ccaed0b04dc916c2cb63627dbc38d046974cd5a`已push／remote一致；20:33:01執行手冊lock命令，output `fault_type_context_prototypes_lock/2026-10-03-20-33-01/protocol.json`，20:33:23封存完成。source inventory包含I core/runner/manual及只讀H parent helper的SHA，依原G protocol/lock/actual source綁定。協定固定I01–12×3fold×seeds0/1/2、selection空、historical exposure保留；提交推送後才開始fit。

事前協定commit `b2896ebac31e9f944babf5b3f560023681cddfe7`已push／remote一致，protocol semantic checksum `f2c3d40bddc99066e2a94fa0bc9b240b35cfd1c8e62a1ce8297c99ac4addef25`。20:34:21執行`fit --protocol output/fault_type_context_prototypes_lock/2026-10-03-20-33-01/protocol.json --data-root data/formal_local`，20:37:21完成9個fold/seed bundles、108個模型，全數收斂，最大172次迭代。lock semantic checksum `66c265da94df081dbadfb97807ad8f199c6afba8ea91a28d2ec30748d2315b6a`，formal資料前後checksum相同。模型在D槽，C槽保留`output/fault_type_context_prototypes_fit/2026-10-03-20-34-21/{locked_study,artifact_location}.json`。

20:38:00開始`source-verify --protocol output/fault_type_context_prototypes_lock/2026-10-03-20-33-01/protocol.json --lock output/fault_type_context_prototypes_fit/2026-10-03-20-34-21/locked_study.json --data-root data/formal_local`。另以GitHub唯讀API確認main的AGENT.md blob仍為`8f35a6bf14fa4747d63add1d6bc852b65bcb4784`，未改規定。outer test尚未執行；不能將收斂與工程測試當作辨識改善。

20:40:01：108模型由實際known train/cal/RPM逐一重建，state與train predictions一致，test_numeric_reads=0，formal checksum前後不變。`output/fault_type_context_prototypes_source_verify/2026-10-03-20-38-00/source_verified.json`保存逐模型證據。此處VERIFIED僅涵蓋可取得的數值來源；raw/session/window獨立性仍UNKNOWN。先提交這份重建與fit索引，再執行outer；未讀I test成績。

來源commit `0462e4b97c988476e4ad222ca596d8c93060fa52`已push／remote一致。20:40:45–20:42:30執行`evaluate`，108/108格完成、0失敗、1,040,760預測、28,910唯一ID；20:42:59–20:44:33執行`verify`，所有108格完整reinfer／truth mutation／來源與保存指標重算一致。參數除新增`--evaluation D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/context_prototypes_v1/workspace/output/fault_type_context_prototypes_evaluate/2026-10-03-20-40-45/evaluation.json`外，沿source-verify命令的protocol／lock／source-verification／data-root。實際CLI logs保存完整版本。

20:44:37–20:45:35 `report`指定上列protocol、D槽evaluation／`...fault_type_context_prototypes_verify/2026-10-03-20-42-59/verified.json`、`--baseline output/fault_type_metrics_v2/2026-10-02-12-51-52/metrics_v2.json --previous output/fault_type_mechanism_evaluate/2026-10-02-17-53-06/evaluation.json --euclidean D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/discriminative_prototypes_v1/workspace/output/fault_type_discriminative_prototypes_evaluate/2026-10-03-15-33-56/evaluation.json`。12方法全部FAILED；沒有selector或新部署model。

20:44:56–20:45:03 `backup`三個D槽已完成action根，28+218+2files；20:47:05–20:47:07 `fault_type_archive`三個C槽protocol／source／report根1+1+2files；20:47:22 `fault_type_fixed_delivery`核對兩archive_index，6ZIP／252members SHA與CRC PASS，source_files_removed=false。index和完整檔案SHA見result_index.json；不將semantic seal當完整file SHA。

人類報告兩次唯讀摘要命令未成功：第一次在report尚未完成時讀summary，FileNotFound；第二次使用不存在的motor_macro_by_seed key，改讀per_seed_motor_macro。另一次PowerShell輸出超過budget被截斷，僅降低所讀摘要欄位。未改sealed模型、資料、公式或成績；最終表格由完整已封存summary的精確值生成。
