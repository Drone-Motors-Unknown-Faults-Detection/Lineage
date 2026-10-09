# #29：未擬合推論契約（先於程式修改）

2026-10-08。影響範圍僅`core/monitor.py`、專屬測試與證據入口；不改detector、校準、PolarMap、切分或105維資料。公開PR36不含monitor，但未知未推工作仍不能判定所有權。

`score`、`classify`、`project`、`summary`需要完整成功擬合。建構後或一次擬合途中失敗時，四者均應丟`RuntimeError`，明確要求`fit_initial()`。不捕捉所有例外，不以假模型掩飾錯誤。`fit_initial`重建一開始即撤銷已擬合旗標；`_refit`一開始撤銷，只有所有擬合與摘要狀態建立完才設true。失敗後不允許把前次模型與新scaler混合推論，需要重新成功建立基準。

其他公開介面：`holdout(config)`讀現有splits，不加推論guard，未註冊仍保留原KeyError；pools/config/seed設定讀取不變。`add_class`保留既有註冊與重擬合語意，無效／重複配置在註冊前失敗時原有效模型仍可用；真正refit失敗則推論禁用。沒有新增原子回滾，失敗時已變動的known/splits不冒充有效模型。

驗證先寫測試並保留紅燈，再加最小guard。Maha與kNN都測四個未擬合入口、初次／再次／新增類別失敗、成功後推論、holdout與配置語意。固定fixture seed7，模型seed42/123，明確synthetic配置／列ID，對`4f783c676849a27185cd28d2410b4e76639b7357:core/monitor.py`舊類別：初始健康與加入已確認fault兩階段比較score、classify、PCA、summary、train/cal/holdout。事前浮點容差`atol=rtol=1e-12`，不能看結果後放寬。樣本ID是fixture列，不是實際採集。

執行入口`python -m tests.monitor_guard_evidence`使用setup_run保存tests.txt與差異JSON；最後`tests.integration_evidence --phase candidate`全套回歸。實測／提交另記[執行紀錄](execution_log.md)。#29可發布草稿須等成功驗證才補，不自行關閉。

## 已完成的結果與尚未發布的草稿

2026-10-08 22:01:46先跑11個test methods，14個failure entries／18個error entries為各方法的subTest反例，不能加總成32個不同測試；保留紅燈紀錄。加guard後22:02:10的11項全通過。2026-10-09接續完整主線124 passed，0 failed/errors/skipped，pip check與四CLI通過，含既有openset／PolarMap／Web回歸。

固定8組條件（2方法×2seeds×2階段），各16個相同fixture列ID，分數與PCA最大絕對差均0，classify／summary／train-cal-holdout完全相同。容差仍為事前1e-12，不調寬、不聲稱準確率提高。產物在`output/monitor_guard_evidence/2026-10-08-22-01-46`、`22-02-10`，全套在`output/branch_integration/2026-10-09-03-11-15`。

給#29的草稿：已加入完整擬合旗標與一致的RuntimeError；score／classify／project／summary都有Maha與kNN測試；失敗refit不允許混用殘留模型，holdout與配置讀取維持原語意。固定舊版配對差0，完整124測試通過。待PR審閱／合併並由使用者確認發布後，再更新checkbox與判定關閉；本輪未發布或關閉。
