# RPM原型拒絕執行紀錄

2026-10-03，Asia/Taipei。先行手冊commit `4951a3138949c827e0e005c8acafa6a7c6a1ac13`已push／remote一致，才新增core／tests。當時exp17 outer仍執行，沒有讀I成績挑父模型。

20:43左右：兩環境core最初12項測試均通過，Python3.10.19用0.003秒，3.14.6用0.002秒。後續靜態檢查加上距離和overflow拒絕與測試，不更改cal quantile或score定義；在協定前修補，尚無本批formal結果。下一步runner需完整purpose／SHA／來源重建與paired replay，不能把core測試當作已執行324評估。
