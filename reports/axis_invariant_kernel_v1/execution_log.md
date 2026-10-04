# 三軸排列核執行紀錄

2026-10-03，Asia/Taipei。先讀AGENT.md及寫作規則；exp18正執行324評估。本批原始TI paper已讀32頁；exp19手冊及兩索引先寫，尚無新core／runner／formal fit。下一步手冊commit／push後實作公式與合成測試，再建立source／purpose runner。原正式預設與282筆無關tracked deletions保留。

尚未執行81 detector評估，不宣稱新方法提高分數。方法依歷史失敗與文獻事前固定；所有28,910資料已曝光，無fresh或可靠性PASS。

先行手冊commit `c307712f86453da39d86c86809f315c3e3474705`已push／remote一致，才新增core／tests。2026-10-04接續實作，兩native環境各23項formula／source小測試通過，Python3.10.19本體0.080秒、Python3.14.6本體0.105秒。涵蓋共享尺度交換、六項等於36項平均、對稱／PSD、核對角非1、SVC確定性／nonconvergence拒絕、actual train重fit重建與重封coeff拒絕、private coeff tamper、centroid手算／q0／NaN／overflow。此階段尚無runner／formal fit；全套回歸待runner實作後執行。
