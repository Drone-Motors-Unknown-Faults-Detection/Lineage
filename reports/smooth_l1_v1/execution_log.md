# 平滑L1研究接續紀錄

2026-10-03，Asia/Taipei。exp16尚未使用，先完成手冊及兩份索引，再新增core與12項測試。沒有改exp15或其他sealed依賴。來源與公式圖片核對見exp16手冊及exp15 sources_addendum。

`.venv310/Scripts/python.exe -m unittest tests.test_fault_type_smooth_l1 -q`：12通過、0失敗，0.023秒。
`venv/Scripts/python.exe -m unittest tests.test_fault_type_smooth_l1 -q`：12通過、0失敗，0.020秒。
包含Q／S零值與極端值、distance對原型導數、相對損失含anchor有限差分、mean初始化匹配、收斂／未收斂、tampering、序列化與同seed重現。沒有正式fit或outer score；runner與來源驗證仍待實作。

這部分只提交core／測試／先行手冊及索引。實驗15的外層評估／verify繼續使用其封存SHA；新增測試數不回填之前452項驗收產物。之後完整回歸須報新的實際數字。

## runner與來源驗證，2026-10-03

核心先行提交`85a35f96dd893ba83e1aa69bb4bd47ba9db5ffc6`已推送。新增runner共用exp15 parent來源重建、原manifest／factory／metrics；fit與cal實際來源分開，未知不擬合。新增8項來源測試，兩環境各20項通過：cal不能初始化原型、重封SHA仍錯的原型／loss子集、錯誤Q/S與parent inventory／selector／test讀取均拒絕。

最初Python3.10 CLI遇到Python3.11才支援的下標星號展開，改為tuple concatenation；沒有正式資料結果被生成。修正後兩環境`--help`及`smoke`通過，合成smoke為`15-44-27`／`15-44-29`，只作工程測試。保留最初3.14的`15-43-49`smoke與失敗紀錄，不冒稱首次兩環境都通過。

完整命令：兩環境各執行`-m experiments.fault_type_continuous_acceptance`。`output/fault_type_continuous_acceptance_py3_10_19/2026-10-03-15-48-08/environment.json`及`...py3_14_6/2026-10-03-15-48-19/environment.json`實際各472項通過、0失敗，status=PASS；pip check與既有37個CLI皆exit0。exp16 help/smoke另行執行，不灌入37的計數。

此時僅完成工程驗收，108格尚未fit/evaluate。先提交runner與手冊，再生成新protocol並提交推送，之後才正式擬合。正式105／LW／k-NN factory／PolarMap及282筆既有tracked deletions均未改。

runner與472項驗收提交`45411e2c46aa78bbeb26e35036fd4e17b307a2d4`，push成功且remote SHA一致。15:54再次唯讀核對main AGENT blob為`8f35a6bf14fa4747d63add1d6bc852b65bcb4784`，與前次已完整讀取版本相同。沒有建立issue／PR或向其他對話傳訊息。

事前lock命令見手冊，實際輸出`output/fault_type_smooth_l1_lock/2026-10-03-15-53-46/protocol.json`；鎖定程式HEAD為45411e2。方法固定12、fold3、seed0/1/2，共108格；selection空、歷史曝光不清除。協定推送後才開始fit，沒有先看本批test成績。
