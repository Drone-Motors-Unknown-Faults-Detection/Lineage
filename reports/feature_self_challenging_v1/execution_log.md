# 特徵自挑戰接續紀錄

2026-10-04，Asia/Taipei。L交付commit `8dca5c0d885a8188973e6799ef6cb24a67ace2e5`已push／remote一致；162評估、756配對、18FAILED、6ZIP360members已完成。開始RSC原文／作者碼與有限表格改編來源卡及exp21先行手冊，此時M程式／fit／outer均0。

重新完整讀AGENT.md，remote main blob仍`8f35a6bf14fa4747d63add1d6bc852b65bcb4784`。依AGENT先手冊＋兩索引再改碼；PDF技能只唯讀核對公式／閱讀深度，沒有新增PDF輸出或安裝。SOURCE cards保留取得逾時、partial reading、作者碼與本文差異，以及參數選擇限制。固定216計畫：2表示法×4training variants×3拒絕器×3fold×3seed，90訓練程序含18ERM warm＋72fixed horizon；原CONTRACT／105正式預設／factory與PolarMap不改。先提交本文件，再實作與公式合成測試，不先讀本批test。

先行手冊commit `a210b7a41dd50a28b2168663722a043fcb9be1c2`已push／remote一致後，新增獨立NumPy/SciPy公式及17項合成測試。Python3.10.19／3.14.6各17 passed、0 failed，本體0.504／0.491秒。核對signed非abs、exact ties、不遮全部、negative probability drop保留、matched random count、解析masked CE gradient、trace eta手算、same known ERM source/seed、history／係數重封後actual refit拒絕及predict無query RPM/truth。200step標FIXED_HORIZON_COMPLETE，不宣稱optimizer收斂；此時尚無runner／formal fit或outer成績。核心小測試通過後先commit/push，再新增封存與實驗入口；sealed exp20未改。

核心commit `bc8eed323cdd9adaf95cf283e06b04e81c1de59e`已push／remote一致。新增run／main、24方法registry、72fine fit＋18known ERM warm計數、actual known重fit／MSP與factory重建、預測／逐筆重推／報告／backup。封存流程改編本站exp20並保留原檔SHA；FILES包含本批core／runner／manual及唯讀warm依賴，source/config/manifest來源校驗照既有guard。

首次runner小測試兩native各20測試、1個setUpClass error：機械改寫測試時將n=36誤改成38，但RPM仍36長度。這是合成fixture錯誤，非正式optimizer未收斂；恢復36且修正新random控制配對斷言後，兩native各36 passed／0failed，本體9.629／9.359秒。其中17核心＋19runner新測試涵蓋actual重fit、cal/scaler/warm/history/coeff重封、未知用途、空selector及inference不得呼叫train mask。21:56:59／21:57:01 native smoke只SYNTHETIC_ENGINEERING_ONLY，兩help通過。L六compact檔SHA再次核對未變。

21:58:39／21:58:50啟動完整acceptance，目前執行中；未提前宣稱全套通過或開始正式M fit。曾在unittest輸出檔尚未產生時唯讀讀取，得到file-not-found，沒有重跑或更改測試；以完成後environment.json作驗收。先完成驗收、commit/push工程，再lock協定與逐階段正式執行。

22:00:48／22:01:09完整acceptance完成；Python3.10.19／3.14.6各618 passed、0 failed，unittest本體75.999／76.890秒；各39命令exit0，pip check／37既有CLI與完整tests均PASS。本批help及smoke另行驗證，未混進既有39命令數。早期mechanical replacement誤把protocol version留下exp20，封存前改為exp21，沒有生成錯版formal lock。來源／score／policy程式與兩native驗收證據先提交push，再lock精確216條件。新fit預計72fixed-horizon＋18ERM warm，不把重推算新fit。
