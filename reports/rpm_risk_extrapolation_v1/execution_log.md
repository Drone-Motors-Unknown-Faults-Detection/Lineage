# RPM風險差異執行紀錄

2026-10-04，Asia/Taipei。已重新讀AGENT.md；K27分類器fit完成／known來源重建中。REx正式本文12頁＋supp18頁、原作者固定版本code／README／CC BY-NC4.0與DomainBed固定版本VREx／README／MIT、MSP原文12頁已讀；先寫exp20及兩索引。此時L程式、optimizer fit與162 outer評估均0，不宣稱分數提升。

先行公式固定：2表示法×beta0/1/10×3拒絕器×3fold×3seed，162評估／54optimizer fit；原CONTRACT與historical exposure不改。AGENT要求先提交手冊才改實驗程式；手冊push後接續core公式與合成測試，不修改sealed K/G/H/I/J。所有新撰文字使用繁體中文；API keys／論文標題及程式識別碼可英文輔助。

先行手冊commit `5bbc6d83451a62a40c1adca846c2a633d355d61f`已push／remote一致，才新增REx公式及解析gradient。Python3.10.19及3.14.6各13項合成測試通過，本體0.063／0.066秒；早期測試class繼承重複執行8個公式測試，曾輸出21，提交前改為共享setUp而不繼承測試。這裡13是實際獨立test methods數。涵蓋三RPM／等class手算、三固定beta有限差分、population variance、缺類／環境INCOMPLETE、同known來源ERM warm start、係數重封後actual refit拒絕、optimizer failure及不使用query truth／RPM。尚無L runner、formal optimizer fit或outer成績。

公式commit `02574d0ceb6093e40cb1f118771232482c0af6dd`已push／remote一致。新增run／main runner，封存與逐筆重算沿用exp19流程，公式／fit／MSP與actual source重建按本批先行手冊替換；沒有改sealed K。新用途／來源測試加16項，兩環境各29項通過，本體3.001／2.949秒；MSP strict q0、係數／scaler flags／環境與校準重封篡改、factory reference與空selection都有覆蓋。已驗證兩native help及smoke（17:06:30／17:06:32），只SYNTHETIC_ENGINEERING_ONLY。

17:08:09／17:08:20開始完整acceptance；目前unittest各582項通過、0失敗，本體68.323／70.750秒。pip check及CLI總狀態待完整流程結束核對，不用unittest先推論39命令全通過。formal L optimizer與outer此時均0。

完整acceptance於17:10:14／17:10:39完成，兩native各39命令exit0（pip check、unittest及37既有CLI），tests_passed各582、status=PASS。輸出`output/fault_type_continuous_acceptance_py3_10_19/2026-10-04-17-08-09`及`...py3_14_6/2026-10-04-17-08-20`；新exp20 help／smoke另外核對。測試中的故意bad CLI及常數moment警告保留，沒有忽略失敗。先提交runner／新16測試／582回歸證據；再lock精確162協定。core／factory／原105／linear預設及PolarMap沒有修改，282筆他人刪除未stage。

工程commit `fd5ebd11ad0f9839bde36fa2f32a5f3b0b19b704`已push／remote一致；17:11:45–17:12:10 lock成功，protocol `output/fault_type_risk_extrapolation_lock/2026-10-04-17-11-45/protocol.json`，semantic checksum `20757999cf3795589151c7ab8898746cf7f5539e8f78a9f4b0627293313d5987`。封存本批core／runner／manual SHA、2表示法×3beta×3拒絕器×3fold×3seed=162、54 optimizer planned fit、原CONTRACT與既有N=5來源。此後不修改sealed implementation或手冊；先提交push本協定再formal fit。K逐筆驗證仍在執行，沒有用K測試成績調本批方法。

協定commit `d81df1d9badeb44e551eda170323d1ab3fdc204e`已push／remote一致。17:12:57–17:14:23完成54 planned／54 attempted／54 completed optimizer fit，0失敗；D槽primary與C槽compact lock物理SHA皆`36dd3014e4578a4c4f11d59b9f10900f0979f154b1d510088b90355785e5af21`，semantic locked checksum `83c100b725ec66f4be239318a13a2e4a90b9fbcc329cce73ce6004b63a6d0817`。

本回合後續CLI timestamp為21:32:16–21:33:09，actual known來源重建完成54／54，來源seal `3f92a86e367159aaa0ffa58dd05d4daa21ad2da7aa4d1a1b6d2a42ac8fbf20d7`。獨立重建ERM／REx、representation、MSP calibration及父factory，test_numeric_reads=0，90CSV fingerprint前後皆`c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。來源proof `output/fault_type_risk_extrapolation_source_verify/2026-10-04-21-32-16/source_verified.json`；先提交push此證據再162 outer，沒有L test成績。17:14 fit完成至21:32 source開始的時間間隔不計模型訓練成本。

來源commit `32925fd46d8f47bef2b681e4495a392d6010c309`已push／remote一致後，21:34:45–21:36:28實際完成162／162評估、0失敗，1,561,140records／28,910unique，本體89.885秒。21:36:48–21:38:08逐筆重推完成，本體66.893秒；test IDs／truth mutation／threshold／score／reject／重算metrics與來源SHA全核對。21:40:24–21:43:03完成report，22方法（18L＋4controls）、756配對，原CONTRACT 18L全FAILED。沒有用結果調beta、threshold或改正式預設。

21:40:35 D槽primary三root及21:45:49 C槽protocol／source／report三root封存；21:46:01–21:46:02 fixed_delivery核對6ZIP360members，whole SHA／逐member SHA／CRC全PASS，未刪來源且不是offsite備份。sealed摘要／lock／來源及三compact gz精確SHA見result_index。本回合唯讀remote核對K交付 `f7973c792d027c583784710465e1fb4139e70d16`一致，main AGENT仍blob `8f35a6bf14fa4747d63add1d6bc852b65bcb4784`。新增L完整報告及索引，並更正上一份自己K報告一個誤用字為繁體「實際」，不改模型／sealed摘要／歷史結果。

事後讀取摘要時，三次小型摘要提取腳本分別遇到dict/list格式、nested RPM key及輸出長度限制，均為唯讀失敗；改為按方法分批、只取必要欄位後成功，不改sealed模型或正式預測。一次錯誤將fit audit list當dict列印，輸出截斷；沒有新增研究run，後續source proof只取optimizer欄位。全seed與工況表由封存summary擷取後以apply_patch寫報告，不手改成績。
