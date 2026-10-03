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
