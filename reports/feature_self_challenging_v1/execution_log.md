# 特徵自挑戰接續紀錄

2026-10-04，Asia/Taipei。L交付commit `8dca5c0d885a8188973e6799ef6cb24a67ace2e5`已push／remote一致；162評估、756配對、18FAILED、6ZIP360members已完成。開始RSC原文／作者碼與有限表格改編來源卡及exp21先行手冊，此時M程式／fit／outer均0。

重新完整讀AGENT.md，remote main blob仍`8f35a6bf14fa4747d63add1d6bc852b65bcb4784`。依AGENT先手冊＋兩索引再改碼；PDF技能只唯讀核對公式／閱讀深度，沒有新增PDF輸出或安裝。SOURCE cards保留取得逾時、partial reading、作者碼與本文差異，以及參數選擇限制。固定216計畫：2表示法×4training variants×3拒絕器×3fold×3seed，90訓練程序含18ERM warm＋72fixed horizon；原CONTRACT／105正式預設／factory與PolarMap不改。先提交本文件，再實作與公式合成測試，不先讀本批test。

先行手冊commit `a210b7a41dd50a28b2168663722a043fcb9be1c2`已push／remote一致後，新增獨立NumPy/SciPy公式及17項合成測試。Python3.10.19／3.14.6各17 passed、0 failed，本體0.504／0.491秒。核對signed非abs、exact ties、不遮全部、negative probability drop保留、matched random count、解析masked CE gradient、trace eta手算、same known ERM source/seed、history／係數重封後actual refit拒絕及predict無query RPM/truth。200step標FIXED_HORIZON_COMPLETE，不宣稱optimizer收斂；此時尚無runner／formal fit或outer成績。核心小測試通過後先commit/push，再新增封存與實驗入口；sealed exp20未改。

核心commit `bc8eed323cdd9adaf95cf283e06b04e81c1de59e`已push／remote一致。新增run／main、24方法registry、72fine fit＋18known ERM warm計數、actual known重fit／MSP與factory重建、預測／逐筆重推／報告／backup。封存流程改編本站exp20並保留原檔SHA；FILES包含本批core／runner／manual及唯讀warm依賴，source/config/manifest來源校驗照既有guard。

首次runner小測試兩native各20測試、1個setUpClass error：機械改寫測試時將n=36誤改成38，但RPM仍36長度。這是合成fixture錯誤，非正式optimizer未收斂；恢復36且修正新random控制配對斷言後，兩native各36 passed／0failed，本體9.629／9.359秒。其中17核心＋19runner新測試涵蓋actual重fit、cal/scaler/warm/history/coeff重封、未知用途、空selector及inference不得呼叫train mask。21:56:59／21:57:01 native smoke只SYNTHETIC_ENGINEERING_ONLY，兩help通過。L六compact檔SHA再次核對未變。

21:58:39／21:58:50啟動完整acceptance，目前執行中；未提前宣稱全套通過或開始正式M fit。曾在unittest輸出檔尚未產生時唯讀讀取，得到file-not-found，沒有重跑或更改測試；以完成後environment.json作驗收。先完成驗收、commit/push工程，再lock協定與逐階段正式執行。

22:00:48／22:01:09完整acceptance完成；Python3.10.19／3.14.6各618 passed、0 failed，unittest本體75.999／76.890秒；各39命令exit0，pip check／37既有CLI與完整tests均PASS。本批help及smoke另行驗證，未混進既有39命令數。早期mechanical replacement誤把protocol version留下exp20，封存前改為exp21，沒有生成錯版formal lock。來源／score／policy程式與兩native驗收證據先提交push，再lock精確216條件。新fit預計72fixed-horizon＋18ERM warm，不把重推算新fit。

工程commit `9e086915f1f305ab0b0c982809ea0f4b907e0ee8`已push／remote一致；22:01:49–22:02:11 lock完成，`output/fault_type_self_challenging_lock/2026-10-04-22-01-49/protocol.json`，semantic checksum `e3099ce35f8c8d4bf71ccb71c314d475b56e98fba1c211c202643100fc596f4d`。封存五份implementation來源SHA、固定參數／216方法格、原CONTRACT及歷史曝露。此後不修改sealed core／runner／manual／warm依賴；先提交push本協定再fit data/formal_local。當前formal M fit與outer均0。

協定commit `5d4893b7ac89d4570cc764703952354841058592`已push／remote一致。22:03:00–22:09:16 formal fit完成：9 bundle、72 fine固定200step全部完成、18 ERM warm完成；兩類計數分開，不把source proof重建算新增研究fit。C compact lock `output/fault_type_self_challenging_fit/2026-10-04-22-03-00/locked_study.json`，semantic checksum `dd4049ee4f4112a806baa5027310552431273575acd396eea8a1b9a5b650a7b1`。前後90 CSV／fingerprint c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d相同。22:09:26啟動actual known source refit，尚未讀本批outer結果。

接續本回合完整讀AGENT.md，remote main blob仍8f35a6bf14fa4747d63add1d6bc852b65bcb4784；HEAD／branch／remote／282既有deletions不變。PDF技能唯讀核對Group DRO原論文與固定作者碼，新增獨立source card；尚無該支線manual／程式／protocol／formal runs，不修改sealed M。新文件用繁體中文，author英文術語作輔助。

fit與來源卡commit `ffbc0aac9bea74f70f5f4bd151653a3b0f7efa07`已push／remote一致。22:09:26–22:14:59 actual known source proof完成，9格72 fine及18 warm重建，加原factory／MSP與scaler重建，`test_numeric_reads=0`，status VERIFIED_AVAILABLE_NUMERIC_SOURCES，checksum `1353d36ec855ad005ed1d5aa2d497660126c6edcbca78283d4edbc1bd36c6aac`。這是來源驗證重建，不算新candidate fits。先提交push proof後才outer；五份sealed來源與正式指紋仍不變。

M來源重建期間依exp20既有結果／Group DRO原文寫exp22先行手冊與兩索引，N程式／protocol／fit／outer均0，M outer仍0；M與N提交範圍分開。本回合有一次JavaScript輔助輸出把已存object當array.slice，讀檔／變更前即TypeError；改為Object.keys，未改正式模型或評估。

proof commit `e0798d72254b03bd3177aa5dd00d965cfec6a93f`已push／remote一致，22:16:34開始M216 evaluate。下一批N先行手冊commit `9aba063e82c4a61228cd4e46c21a927abddc56c0`已push／remote一致；只文件，尚無N程式／fit／outer。sealed M五來源不變。簡體字掃描曾把共用「出」誤列，人工確認為繁體也使用的正常字，不因此改寫實驗；exp22草稿「参数」提交前改為「參數」。

2026-10-05 收尾：既有 evaluate／verify 都已完成 216 格，2,081,520 records／28,910 unique rows；過期 state 的 0 更正，不重訓。evaluation seal 697dae9a02e2ff29e0b3989b2ec91c242ab9d1d6df265072348a92953185103c；verification seal df87512beddb7d30f8312578eb259a2a193b0fc93c777b0295d6f0f1f404f152。verification 檔案 SHA 5f2124752c31b6281d1a53b4eff3c3f9ca958b418455a9586ed7aa5f3beda472，與語意 seal 分開。

22:17:39–22:27:41 沿原 report 子命令重算 1,134 配對，24 方法全部 FAILED，report seal 81f8952b904ed4b24983013632f25c5a20983c2cb053ca8e12ff9998d1cfb22b。全 seeds 的最差類別召回都為零；健康總誤報 motor-macro 29.75%–84.28%，未通過原 10% 最差工況保護。結果、全 seeds 與逐方法 reasons 保存 final_findings.md 及 result_index.json；採 B 路徑。

22:24:22／22:28:54 新增六份備份，22:32:32 fixed_delivery 核對 6 ZIP／468 members，whole／member SHA／CRC PASS。舊 ZIP、models、predictions、locks 與正式資料都保留。來源重建仍為 known-only，0 test numeric reads；72 fine 與18 warm 不加計來源重建。原 618 科學測試雙環境先前已 PASS，本輪盤點9項在兩環境 PASS，未重跑618。N只有計畫，本階段封存，不寫成實測 FAILED。
