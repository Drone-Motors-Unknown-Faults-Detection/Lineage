# 工況相關原型：來源、工具與閱讀邊界

2026-10-03，Asia/Taipei。原始來源／作者程式查核，尚無新formal成績。AGLVQ已是exp15來源queue，本次讀實際context實作，沒有把重讀同一論文算成新論文。

## paper card與適配

Graeber等，ESANN2021，557–562，DOI10.14428/esann/2021.ES2021-40，英文六頁全文：[原始PDF](https://www.esann.org/sites/default/files/proceedings/2021/ES2021-40.pdf)。w(c)=ws+wa(c)提供context-dependent prototype；人工資料與輪胎聲譜、車速工況，與本案馬達配置不同。原文沒有完整公開輪胎採集／motor/window分組依據；不能移植其headline accuracy或獨立保證。其實際輪胎資料A-GLVQ／A-GRLVQ改善不如matrix版本，relevance可能collapse；本站凍結幾何與低階RPM，列為可反駁假說。

作者公開repo `graebe/aglvq`固定commit `9f0ee487948803ddf9b4e97fc1d9a8e4d0c64836`，MIT。已完整讀proto.py、layers.py、losses.py、distance.py、model.py、initializer.py、constraints.py、basic_model.py與setup.py。只唯讀API，未執行作者程式、未安裝依賴。舊TF2.1／Keras2.3.1／Python3.6不適合直接塞進本案兩環境。

實碼Polynomial每冪有bias與weight，ProtoAdd合static原型；distance.py取sqrt(sum(square))；model.py用swish(mu)，aux對true prototype MSE並以pretrain_ratio切前段training。本站改用單一截距、全known train最小平方初始化、平方距離、平均sigmoid(4mu)、原分層loss子集、L-BFGS-B與固定aux=.01。不是作者程式faithful reproduction；不複製外部程式。精確改編、梯度及匹配控制見exp17手冊。

## 查詢coverage

20:14前後以web搜尋`AGLVQ Kontext Prototypen`（德文／英文）、`learning vector quantization context fault speed`（英文）、`ベクトル量子化 文脈 プロトタイプ 学習`（日文），另讀ESANN全文與作者repo。工具未提供可靠總命中數，保留UNKNOWN；沒有把索引返回筆數當全球文獻數。日文查詢主要回語言模型／CPC／量子化來源，與本批有標籤的工況原型不符，未據此實作；德文查詢未補到不同的可用機制。作者程式web cache失敗後用GitHub唯讀API，固定SHA追溯；不繞過付費牆。

目前這一batch僅核對AGLVQ可用context機制，不能稱已窮盡多語言或故障領域文獻。原始stream／tachometer來源不足的方向仍UNKNOWN；本案RPM代碼只支援既有三離散工況的探索比較。
