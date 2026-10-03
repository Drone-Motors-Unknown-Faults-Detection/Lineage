# 封存後補讀來源，不變更本批參數

2026-10-03。協定封存後續讀，不將新增來源當成事前選參證據。

Lydia Fischer／Barbara Hammer／Heiko Wersing（2014），*Rejection Strategies for Learning Vector Quantization*，ESANN:41–46，[原始會議PDF](https://www.esann.org/sites/default/files/proceedings/legacy/es2014-131.pdf)，六頁全文含method／benchmark／coverage-accuracy曲線／限制已讀。作者區分歧義與outlier：RelSim=(d_other−d_near)/(d_other+d_near)；本站模糊score是1−RelSim加ε保護，high score拒絕，沒有翻轉test分數。原文nearest-distance與decision-boundary拒絕及其組合是後續機制線索，尚未在本站實測。

原文評估主要是接受子集accuracy／coverage，不是本站全部final decisions的unknown recall或healthy完整誤報。Comb以兩threshold窮舉作參考；本批不照搬test最佳threshold。部分benchmark的RelSim／Dist效果較弱，不把平均曲線當泛化保證。原文圖2只在至少80%runs有值時平均；本站不能省略缺失格，必須列216完整inventory。

2015期刊延伸 *Efficient Rejection Strategies for Prototype-based Classification*，Neurocomputing169:334–342，DOI10.1016/j.neucom.2014.10.092，[作者稿](https://www.techfak.uni-bielefeld.de/~hwersing/FischerHammerWersing_Neurocomputing2015.pdf)。本次只核對出版頁／摘要，不宣稱全文已精讀，不當另一份獨立採用方法。2014／2015延伸去重後按版本追蹤。

日本IEICE1999[官方目錄](https://www.ieice.org/jpn/books/ronbunshi-mokuji/1999/04/JDII-04.html)支持Sato／Yamada作品始於650頁；未取得全文，不由目錄推論其公式。原GLVQ年分依1995會議／1996卷出版區分。
