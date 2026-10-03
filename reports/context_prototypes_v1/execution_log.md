# RPM工況原型執行紀錄

2026-10-03，Asia/Taipei。先行手冊／來源commit `1dd0040f22251744a60eb0f02d9e63714c2b7a72`已push且remote相符，才新增core／tests。沒有修改exp15／16的sealed程式與手冊。

20:18–20:19：兩環境各`-m unittest tests.test_fault_type_context_prototypes -q`，11項通過、0失敗，Python3.10.19為0.020秒，3.14.6為0.018秒。包含一次／二次含aux有限差分、degree0退化至pooled GLVQ、二次static等於各RPM每類均值、手算距離、RPM合法性、缺工況支持、序列化、同seed重現與未收斂禁止推論。

第一次合成routing測試的工況位移未跨越pooled分類邊界，預期「錯誤RPM必定造成錯分類」不成立，兩環境各11項中1項失敗。改合成資料的已知工況位移向量`[2,-.5,1]`為`[3,-.5,2]`，使錯RPM路由確實可觀察；公式／formal資料／方法參數未改。保留失敗解釋，不將合成測試調整包裝成真實模型提升。

目前runner未完成、尚未lock／fit／evaluate本批formal資料。下一步按手冊實作明確RPM推論路徑、來源重建與封存矩陣；完整測試稍後報實際新數目，不能沿用上一批472項冒稱全部已驗證。
