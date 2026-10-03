# 平滑L1研究接續紀錄

2026-10-03，Asia/Taipei。exp16尚未使用，先完成手冊及兩份索引，再新增core與12項測試。沒有改exp15或其他sealed依賴。來源與公式圖片核對見exp16手冊及exp15 sources_addendum。

`.venv310/Scripts/python.exe -m unittest tests.test_fault_type_smooth_l1 -q`：12通過、0失敗，0.023秒。
`venv/Scripts/python.exe -m unittest tests.test_fault_type_smooth_l1 -q`：12通過、0失敗，0.020秒。
包含Q／S零值與極端值、distance對原型導數、相對損失含anchor有限差分、mean初始化匹配、收斂／未收斂、tampering、序列化與同seed重現。沒有正式fit或outer score；runner與來源驗證仍待實作。

這部分只提交core／測試／先行手冊及索引。實驗15的外層評估／verify繼續使用其封存SHA；新增測試數不回填之前452項驗收產物。之後完整回歸須報新的實際數字。
