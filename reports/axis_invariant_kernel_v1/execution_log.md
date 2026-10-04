# 三軸排列核執行紀錄

2026-10-03，Asia/Taipei。先讀AGENT.md及寫作規則；exp18正執行324評估。本批原始TI paper已讀32頁；exp19手冊及兩索引先寫，尚無新core／runner／formal fit。下一步手冊commit／push後實作公式與合成測試，再建立source／purpose runner。原正式預設與282筆無關tracked deletions保留。

尚未執行81 detector評估，不宣稱新方法提高分數。方法依歷史失敗與文獻事前固定；所有28,910資料已曝光，無fresh或可靠性PASS。

先行手冊commit `c307712f86453da39d86c86809f315c3e3474705`已push／remote一致，才新增core／tests。2026-10-04接續實作，兩native環境各23項formula／source小測試通過，Python3.10.19本體0.080秒、Python3.14.6本體0.105秒。涵蓋共享尺度交換、六項等於36項平均、對稱／PSD、核對角非1、SVC確定性／nonconvergence拒絕、actual train重fit重建與重封coeff拒絕、private coeff tamper、centroid手算／q0／NaN／overflow。此階段尚無runner／formal fit；全套回歸待runner實作後執行。

core階段commit `9f11645d0f0f16aabf3f2148e2359426640c8f24`已push／remote一致。runner共用G的已驗證來源、保存、逐筆metrics／replay流程，不修改sealed G／H／I／J。初稿report仍有G的prototype variant配對欄位，靜態審查於formal lock前修正為固定alpha0消融，新增42配對組合測試；沒有任何formal結果需作廢。

兩native CLI help與smoke通過，output `fault_type_axis_kernel_smoke/2026-10-04-16-33-02`／`16-33-12`，只SYNTHETIC_ENGINEERING_ONLY。新runner／用途／actual source加10測試，兩環境各33小測試通過（本體2.458／2.655秒）。涵蓋重封cal threshold、變動known cal／factory reference拒絕、unknown／test motor進development拒絕、三拒絕器classifier共享、nonconvergence INCOMPLETE、global winner／假fresh拒絕。

J完整結果交付commit `e471393f0e77054c98e18f8853244a4466affef4`已push／remote一致。2026-10-04 16:41:57／16:41:58開始本批完整acceptance，結果待完成後記錄。新kernel／runner未formal lock／fit，沒有用J外部成績挑alpha或門檻。

完整acceptance完成：Python3.10.19於16:43:56、Python3.14.6於16:44:07，各553 tests通過、0失敗，unittest本體63.772／64.776秒。各39命令exit0，包含pip check、unittest及37既有CLI；新exp19 help／smoke另外核對。工程驗收產物`output/fault_type_continuous_acceptance_py3_10_19/2026-10-04-16-41-57`及`...py3_14_6/2026-10-04-16-41-58`。先提交推送runner／回歸證據，再lock協定；此時formal K fit／outer均0。
