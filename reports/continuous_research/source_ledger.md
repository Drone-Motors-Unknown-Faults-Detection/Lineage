# 跨語言來源、閱讀深度與適用邊界

2026-10-02。搜尋覆蓋不等於全文研讀；不同語言摘要/版本按DOI去重。原期刊年代與本文日期不混同；尚未核對的撤稿/更正狀態UNKNOWN。未繞付費牆/下載或執行陌生安裝脚本。
    
## LMNN：第一批核心原始來源
Kilian Q. Weinberger & Lawrence K. Saul (2009), Distance Metric Learning for Large Margin Nearest Neighbor Classification, JMLR10:207–244。
https://www.jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf
英文，合法全文；研讀§3.1/3.2 equations10–14及AppendixA18–20，不宣稱逐頁讀全38頁。固定原空間同類target neighbors，拉近target、hinge推離不同類impostors，學習PSD Mahalanobis。原實驗通用分類非本專案跨motor open-set，不能移用分數；局部metric也不能自行保證domain invariance。
作者方法相關metric-learn0.7官方原始碼：
https://contrib.scikit-learn.org/metric-learn/_modules/metric_learn/lmnn.html
核對_select_targets/_loss_grad；沒有複製或安裝，license檔未取得，license UNKNOWN。不是作者論文唯一原code來源。
本地版本將full PSD限定非負diagonal，mean-normalize pull/hinge、加identity ridge，固定train-only class×RPM subset；paper-inspired，不是完整LMNN復現。optimizer使用已存在SciPy，未知不參與metric。
    
## 支持幅值機制，也提供反例
Tseng & Wang2014, A Diagnostic System for Speed-Varying Motor Rotary Faults, DOI10.1155/2014/310626。
https://onlinelibrary.wiley.com/doi/10.1155/2014/310626
英文台灣作者；閱讀§2方法文字。使用健康均值/std標準化、raw頻譜諧波/HDA；不是提出本文RMS-ratio，不宣稱看過尚未核對圖像中的全部式子。重要反例：幅值可帶故障資訊，全部消除gain可能丟signal。
無因次表示為本地代數改編：既有harmonic69與formal欄位契約基礎，逐row RMS比值的正gain不變性可測；gain是nuisance的物理解釋未證明。

## 其他語言：待研讀或資料不符，沒有計為實測
中文NUAA《基于深度对比迁移学习的变工况下机械故障诊断》：
https://zdxb.nuaa.edu.cn/zdgcxb/article/abstract/202303027
出版社摘要讀，作者/核心式子未核對；source-target轉移有target access，與train-only不同，不實作。
日文土屋雅弘/高木亨之1998，JSME C64(618):465–472，DOI10.1299/kikaic.64.465：
https://www.jstage.jst.go.jp/article/kikaic1979/64/618/64_618_465/_article/-char/ja
摘要/metadata讀，wavelet需可追溯raw；不當formal row序列。
韓文DBpia inwheel logMel候選：
https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE12731193
搜尋摘要，作者與全文未核對，不作演算法原始來源，不執行Mel。
德文Bayreuth2019統計局部ML論文：
https://epub.uni-bayreuth.de/id/eprint/4600/
機構摘要發現，非故障特定；作者與算法式子待核。
法文ENP GMM學位論文：
https://repository.enp.edu.dz/jspui/handle/123456789/8653
發現但全文開啟失敗；GMM已有實測，不能換語言算新法。
西班牙文Villada/Cadavid2007 InfTecnol18(2):105–112，DOI10.4067/S0718-07642007000200016：
https://www.scielo.cl/scielo.php?pid=S0718-07642007000200016&script=sci_abstract
publisher摘要；模擬定子fault/load/voltage neural模式，不同任務且無合法全文方法核對，未復現。
俄文/英文Kozhubaev Yu.N.2026，Computing Telecommunications Control19(1):103–115，DOI10.18721/JCSTCS.19110：
https://elib.spbstu.ru/dl/2/j26-183.pdf/download/j26-183.pdf
13頁全文可得但本輪只核對metadata/abstract/intro；三相電流deep residual fusion不符既有input，混合語言同一篇不算兩篇。
所有後續候選待讀loss/inference/split/cal/target權限再入queue。搜尋結果未核對者不填已讀/已測。

## 現有官方工具
SciPy1.15.3 L-BFGS-B（解析grad/maxiter150/maxfun500/maxls50/ftol1e-9/gtol1e-6）：
https://docs.scipy.org/doc/scipy-1.15.3/reference/optimize.minimize-lbfgsb.html
sklearn1.7.2 KNeighborsClassifier：
https://scikit-learn.org/1.7/modules/generated/sklearn.neighbors.KNeighborsClassifier.html
以上讀參數docs；距離weighted k5/brute/p2/n_jobs1固定。純CPU，無新依賴。現有套件license不因本輪使用而另授權未知repo。

