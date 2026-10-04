# RPM風險差異執行紀錄

2026-10-04，Asia/Taipei。已重新讀AGENT.md；K27分類器fit完成／known來源重建中。REx正式本文12頁＋supp18頁、原作者固定版本code／README／CC BY-NC4.0與DomainBed固定版本VREx／README／MIT、MSP原文12頁已讀；先寫exp20及兩索引。此時L程式、optimizer fit與162 outer評估均0，不宣稱分數提升。

先行公式固定：2表示法×beta0/1/10×3拒絕器×3fold×3seed，162評估／54optimizer fit；原CONTRACT與historical exposure不改。AGENT要求先提交手冊才改實驗程式；手冊push後接續core公式與合成測試，不修改sealed K/G/H/I/J。所有新撰文字使用繁體中文；API keys／論文標題及程式識別碼可英文輔助。

先行手冊commit `5bbc6d83451a62a40c1adca846c2a633d355d61f`已push／remote一致，才新增REx公式及解析gradient。Python3.10.19及3.14.6各13項合成測試通過，本體0.063／0.066秒；早期測試class繼承重複執行8個公式測試，曾輸出21，提交前改為共享setUp而不繼承測試。這裡13是實際獨立test methods數。涵蓋三RPM／等class手算、三固定beta有限差分、population variance、缺類／環境INCOMPLETE、同known來源ERM warm start、係數重封後actual refit拒絕、optimizer failure及不使用query truth／RPM。尚無L runner、formal optimizer fit或outer成績。
