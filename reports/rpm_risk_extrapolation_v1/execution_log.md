# RPM風險差異執行紀錄

2026-10-04，Asia/Taipei。已重新讀AGENT.md；K27分類器fit完成／known來源重建中。REx正式本文12頁＋supp18頁、原作者固定版本code／README／CC BY-NC4.0與DomainBed固定版本VREx／README／MIT、MSP原文12頁已讀；先寫exp20及兩索引。此時L程式、optimizer fit與162 outer評估均0，不宣稱分數提升。

先行公式固定：2表示法×beta0/1/10×3拒絕器×3fold×3seed，162評估／54optimizer fit；原CONTRACT與historical exposure不改。AGENT要求先提交手冊才改實驗程式；手冊push後接續core公式與合成測試，不修改sealed K/G/H/I/J。所有新撰文字使用繁體中文；API keys／論文標題及程式識別碼可英文輔助。

先行手冊commit `5bbc6d83451a62a40c1adca846c2a633d355d61f`已push／remote一致，才新增REx公式及解析gradient。Python3.10.19及3.14.6各13項合成測試通過，本體0.063／0.066秒；早期測試class繼承重複執行8個公式測試，曾輸出21，提交前改為共享setUp而不繼承測試。這裡13是實際獨立test methods數。涵蓋三RPM／等class手算、三固定beta有限差分、population variance、缺類／環境INCOMPLETE、同known來源ERM warm start、係數重封後actual refit拒絕、optimizer failure及不使用query truth／RPM。尚無L runner、formal optimizer fit或outer成績。

公式commit `02574d0ceb6093e40cb1f118771232482c0af6dd`已push／remote一致。新增run／main runner，封存與逐筆重算沿用exp19流程，公式／fit／MSP與actual source重建按本批先行手冊替換；沒有改sealed K。新用途／來源測試加16項，兩環境各29項通過，本體3.001／2.949秒；MSP strict q0、係數／scaler flags／環境與校準重封篡改、factory reference與空selection都有覆蓋。已驗證兩native help及smoke（17:06:30／17:06:32），只SYNTHETIC_ENGINEERING_ONLY。

17:08:09／17:08:20開始完整acceptance；目前unittest各582項通過、0失敗，本體68.323／70.750秒。pip check及CLI總狀態待完整流程結束核對，不用unittest先推論39命令全通過。formal L optimizer與outer此時均0。

完整acceptance於17:10:14／17:10:39完成，兩native各39命令exit0（pip check、unittest及37既有CLI），tests_passed各582、status=PASS。輸出`output/fault_type_continuous_acceptance_py3_10_19/2026-10-04-17-08-09`及`...py3_14_6/2026-10-04-17-08-20`；新exp20 help／smoke另外核對。測試中的故意bad CLI及常數moment警告保留，沒有忽略失敗。先提交runner／新16測試／582回歸證據；再lock精確162協定。core／factory／原105／linear預設及PolarMap沒有修改，282筆他人刪除未stage。
