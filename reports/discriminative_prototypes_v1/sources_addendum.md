# 封存後補讀來源，不變更本批參數

2026-10-03。協定封存後續讀，不將新增來源當成事前選參證據。

Lydia Fischer／Barbara Hammer／Heiko Wersing（2014），*Rejection Strategies for Learning Vector Quantization*，ESANN:41–46，[原始會議PDF](https://www.esann.org/sites/default/files/proceedings/legacy/es2014-131.pdf)，六頁全文含method／benchmark／coverage-accuracy曲線／限制已讀。作者區分歧義與outlier：RelSim=(d_other−d_near)/(d_other+d_near)；本站模糊score是1−RelSim加ε保護，high score拒絕，沒有翻轉test分數。原文nearest-distance與decision-boundary拒絕及其組合是後續機制線索，尚未在本站實測。

原文評估主要是接受子集accuracy／coverage，不是本站全部final decisions的unknown recall或healthy完整誤報。Comb以兩threshold窮舉作參考；本批不照搬test最佳threshold。部分benchmark的RelSim／Dist效果較弱，不把平均曲線當泛化保證。原文圖2只在至少80%runs有值時平均；本站不能省略缺失格，必須列216完整inventory。

2015期刊延伸 *Efficient Rejection Strategies for Prototype-based Classification*，Neurocomputing169:334–342，DOI10.1016/j.neucom.2014.10.092。原Bielefeld連結404後找到[Honda Research Institute合法作者稿](https://www.honda-ri.de/pubs/pdf/2814.pdf)，25頁（含封面），本次續讀方法、ARC評估、資料、結果與限制，並渲染正文p10核對Eq.8。2014／2015延伸去重追蹤。論文的Comb使用兩門檻窮舉作參考；本案不能借outer test重現這種選擇。

公式核對發現：稿中Eq.8分母印為 `2||w+−w−||²`。自行以Euclidean平方距離推導，真正超平面距離為 `|d+−d−|/(2||w+−w−||)`，因此後續若用Dist必須區分照印公式與幾何修正版，不能默默換掉平方。此觀察尚未形成新實驗，實驗15協定及參數完全不變。

Lange／Zühlke／Holz／Villmann（2014），*Applications of lp-Norms and their Smooth Approximations for Gradient Based Learning Vector Quantization*，ESANN:271–276，[會議原文](https://www.esann.org/sites/default/files/proceedings/legacy/es2014-153.pdf)。已讀方法、Eq.1–15、兩項應用與限制，並渲染p274核對Eq.11–15；尚未實作。新機制是用平滑L1減少大偏差維度支配；資料為microarray／GC-MS，不能將其準確率當本案預期。

日本IEICE1999[官方目錄](https://www.ieice.org/jpn/books/ronbunshi-mokuji/1999/04/JDII-04.html)支持Sato／Yamada作品始於650頁；未取得全文，不由目錄推論其公式。原GLVQ年分依1995會議／1996卷出版區分。
