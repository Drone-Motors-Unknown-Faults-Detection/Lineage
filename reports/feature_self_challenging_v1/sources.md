# RSC來源核對與有限改編卡

2026-10-04，Asia/Taipei。paper_id=Huang2020RSC；英語原文，同ECCV／arXiv去重。作者Zeyi Huang／Haohan Wang／Eric P. Xing／Dong Huang；正式機構出版資料https://publications.ri.cmu.edu/self-challenging-improves-cross-domain-generalization 。arXiv v1 https://arxiv.org/pdf/2007.02454v1 全20頁841文字行（本文／附錄／refs）已讀；ECCV16頁647行只0–390已讀，後段timeout。未做完整圖像QA，不將文字抽取當版面完整證明。全文反證：比例太大可能喪失訊號，二元理論及不變性等假設未證明適用本站。

原方法：PACS等影像跨domain分類，CNN learned representation；true-class logit signed gradient top percentile muting，再更新network。模型選擇與fraction依其影像protocol，不借作者headline accuracy推定motor結果；不使用本案unknown選參。原Eq.2 percentile ties與更新作者碼strict ties／curriculum不同。需可微classifier與feature；不能將105欄視為時間序列或空間CNN像素。

作者碼固定https://github.com/DeLightCMU/RSC/tree/bf6d280c5d74910f009ea8963c59167252659666 ：README／根LICENSE BSD-2-Clause／Domain_Generalization/models/resnet.py完整讀，未宣稱整repo都讀。作者碼依梯度channel mean產生spatial activation×gradient或channel mask，Python random選variant、epoch batch curriculum、softmax下降選rows；本文signed gradient與新版碼空間貢獻分開。沒有copy／execute／權重下載；本站NumPy/SciPy獨立改編，所有隨機性default_rng(seed)。

閱讀深度與機制證據沿前回合web全文讀取保存，當前回合再查機構出版、arXiv metadata及官方repo頁；不是重新完整跑歷史實驗。英文、日文、德文查詢已於前段讀取時執行；本回合補繁體中文「特徵 自我挑戰 RSC 領域泛化 ECCV Huang 2020 論文」。索引未回傳全域總數，result_count=UNKNOWN，不填0或假造篇數。日文query=RSC 表現 自己 挑戦 ドメイン汎化 ECCV 2020 論文；德文query=Repräsentations Selbstherausforderung Domänengeneralisierung RSC 2020 Original；英語query=Representation Self-Challenging Domain Generalization Huang Wang Jin Zhu 2020 ECCV original paper。最後query含不正確作者猜測，依primary修正為實際四作者，保留搜尋線索以供追溯。

反證query=Representation Self Challenging DomainBed negative results RSC Gulrajani Lopez-Paz；追到Gulrajani／Lopez-Paz，*In Search of Lost Domain Generalization* https://arxiv.org/abs/2007.01434 。本回合只摘要／metadata，不宣稱完整讀該篇、不引用其RSC-specific表格數字，列全文queue。摘要指出不同架構與選模造成公平比較困難；本批用same-source warm與matched controls，不把no-selection流程與作者最佳影像選模結果混報。沒有宣稱已窮盡所有語言／方法。

改編卡SC21：固定手工base75／harmonic69與六known linear softmax，18次train-only ERM warm、72次200step再訓練。unmasked／random／signed gradient／contribution四固定variant；exact ceil 1/3 features與1/3 rows，負softmax下降保留並報A4 violations；train-only解析上界eta，.001 ridge，固定最後iterate無best epoch。原CNN learned representation／Adam／空間kernel／curriculum未移植。不是faithful reproduction；若失敗只否定本地限定改編，不能說原RSC普遍失效。

依賴最小流程：formal known train → train-only表示法/scaler → 三RPM等class ERM → known gradient／contribution／random masks → masked CE更新 → unmasked inference；另一motor known cal只設MSP或既有factory拒絕門檻；第三motor全部labels只評估。predict不收query truth／RPM。詳式、實值、216矩陣與否證見exp21手冊；正式預設不變。
