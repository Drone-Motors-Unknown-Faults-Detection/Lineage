# RPM風險差異：來源與閱讀紀錄

2026-10-04，Asia/Taipei。K outer尚未執行時研究；新L方法尚未實作或測試。

- REx：Krueger等（2021），ICML／PMLR139:5815–5826。[本文](https://proceedings.mlr.press/v139/krueger21a/krueger21a.pdf)12頁及[補充](https://proceedings.mlr.press/v139/krueger21a/krueger21a-supp.pdf)18頁完整閱讀；2020預印本是同方法，不重複計數。Eq.8與補充27–30、DomainBed無穩定優勢、異質雜訊反證及test-tuning限制已核對。線性softmax、等RPM／等class、ridge、train-only warm start與固定beta為本站改編，詳exp20手冊。
- [原作者release](https://github.com/capybaralet/REx_code_release/tree/47dfb3a2f93a195389a9c933a66482eee455c720)：colored_mnist/main.py全文295行、README及子目錄CC BY-NC4.0完整閱讀。式子為兩風險sum與平方差；存在Adam／waterfall及highest-test記錄。本案不移植最高test選擇，不複製或執行該程式。原supp匿名網址與公開release不冒稱已做整repo逐byte等同性。
- [DomainBed](https://github.com/facebookresearch/DomainBed/tree/b93c22a1cfc3b2428398272c1a116c8de1f4139e)：VREx類別676–714、README135行與MIT授權完整核對；mean loss＋population variance，非torch.var的unbiased預設。沒有閱讀整個2316行algorithms檔，也未下載／執行其ResNet網路。REx原論文的DomainBed結果為負面證據；另一篇DomainBed論文目前只核對引用資訊，不算新全文閱讀。
- Hendrycks／Gimpel（2017），ICLR，[作者v3](https://arxiv.org/pdf/1610.02136v3)12頁含附錄／references全文重新核對。MSP不是校準信心；本案使用既有NoveltyReference的1−MSP與已知cal q95，不複製作者code，沒有實作auxiliary decoder。馬達特徵softmax與原網路不同，不能移用其影像／語音成績。

實際查詢：英文`Risk Extrapolation REx Krueger 2021 PMLR ICML official code`、德文`Risikoextrapolation REx Domänengeneralisierung Krueger 2021`、日文`REx リスク外挿 ドメイン汎化 原論文`、繁體中文`風險外推 REx 跨域泛化 原始論文`。非英文查詢有REx縮寫碰撞，無關LLM／機器人／RNA結果未採用。只引用作者／刊物／原作者程式，沒有採二手排行榜。

RVP arXiv2006.07544及RSC arXiv2007.02454目前只搜尋到摘要，保留待讀，不稱已實作或排除效能。原作者colored_mnist授權首次web讀取Cache miss，改以公開GitHub API固定SHA完整讀取；先輸出base64後解碼核對，未把未解碼資料當已讀正文。未安裝新套件或要求新motor。
