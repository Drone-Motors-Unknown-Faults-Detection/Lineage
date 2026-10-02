# 基線與数学構件的補充來源

補充書目不改已封存 `sources.md`、protocol SHA、方法或係數；仍保持630組同一協定。此文件會以另外的SHA列入交付索引，不能用補文件聲稱先前沒有曝光。

- P29：D. R. Cox (1958), *The Regression Analysis of Binary Sequences*, Journal of the Royal Statistical Society B20:215–232，[原出版頁](https://doi.org/10.1111/j.2517-6161.1958.tb00292.x)。C02 是先前專案的balanced六類 LogisticRegression 基線，不是原文二元實驗的精確重現；多類／L2／lbfgs設定依 [sklearn1.7官方實作](https://scikit-learn.org/1.7/modules/generated/sklearn.linear_model.LogisticRegression.html)。原始專案參數來源 `experiments/fault_type_openset.py:CLASSIFIER_CONFIG` 保留，不調參。
- P30：Claude E. Shannon (1948), *A Mathematical Theory of Communication*, Bell System Technical Journal27:379–423、623–656，[機構全文](https://www.princeton.edu/~wbialek/rome/refs/shannon_48.pdf)。R15 的 `−sum(p log p)/log(K)` 是normalized Shannon entropy，用在C01 posterior作研究信心對照；這不是聲稱Shannon提出此馬達OOD方法，也不代表高entropy一定unknown。
- P31：James MacQueen (1967), *Some methods for classification and analysis of multivariate observations*, Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability1:281–297，[Berkeley機構目錄](https://digicoll.lib.berkeley.edu/record/113015?v=pdf)。目錄可由搜尋核對，直接全文抓取403；不宣稱已讀取全文。R13是每已知類train做2-center sklearn KMeans，n_init10，再接既有pooled-LW距離；是KMeans＋P02/P12的自訂組合，不宣稱原文線上更新演算法或故障偵測的精確重現，實作採sklearn的批次KMeans。
- RobustScaler 的實際median／IQR與預設來源：[sklearn1.7官方文件](https://scikit-learn.org/1.7/modules/generated/sklearn.preprocessing.RobustScaler.html)。所有新表示法只fit train；fusion的center/IQR只用known-cal作固定score校準，並非把cal送classifier或representation擬合。

30篇論文加1項統計會議構件，共31項書目；部分僅方法範圍／排除依據，不等於31套新演算法已實測。sources.md逐列區分實測、歷史只讀與未實測；不得把歷史B5/B6、LMNN、OpenMax、DeepSVDD或CORAL算成此次新runs。
