# 方法來源與實作範圍

本輪全部候選固定於評估前；參數不是文獻證明的最優值。樹模型在一般表格資料的研究表現僅支持優先做對照，不保證馬達資料改善。已核對現有 sklearn 1.7.2／1.9.1 API，沒有新裝套件。

| 方法 | 原始作者／出版來源 | 本輪實際用途 |
|---|---|---|
| ExtraTrees | Geurts、Ernst、Wehenkel，2006，Machine Learning 63:3–42，[作者機構保存頁](https://orbi.uliege.be/handle/2268/9357) | A5固定200樹、depth12、leaf5；歷史曾試，現在是75維同RPM受控比較 |
| Gradient boosting | Friedman，2001，Annals of Statistics 29:1189–1232，[原論文DOI](https://doi.org/10.1214/aos/1013203451) | A6為[sklearn histogram boosting](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html)，不是逐字重現原論文；early_stopping=False |
| Shrinkage covariance | Ledoit、Wolf，2004，Journal of Multivariate Analysis 88:365–411，[原論文DOI](https://doi.org/10.1016/S0047-259X(03)00096-4) | 原逐類Mahalanobis預設保留；B2/B3以train own-class residual估共同within covariance；A7用shrinkage LDA分類 |
| LDA實作契約 | [sklearn 1.7 LDA官方文件](https://scikit-learn.org/1.7/modules/generated/sklearn.discriminant_analysis.LinearDiscriminantAnalysis.html) | lsqr、shrinkage=auto、uniform priors；只predict，沒有套LDA projection到detector |
| SVM | Cortes、Vapnik，1995，Machine Learning 20:273–297，[原論文DOI](https://doi.org/10.1007/BF00994018) | A8固定RBF、C1、gamma=scale、balanced；historical mixed-RPM版本已試，非首次提出 |
| Conformal | Angelopoulos、Bates，2023，Foundations and Trends in Machine Learning，[教學原稿](https://arxiv.org/html/2107.07511v6) | B5/B6 own-class calibration、>= ties、alpha=.05，score=1-max p；未知跨馬達可交換性，不宣稱固定5%誤報保證 |
| 樹模型優先比較的背景 | Grinsztajn、Oyallon、Varoquaux，NeurIPS 2022，[官方論文頁](https://proceedings.neurips.cc/paper_files/paper/2022/hash/0378c7692da36807bdec87ab043cdadc-Abstract-Datasets_and_Benchmarks.html) | 表格benchmark，不是本專案模型可靠性證據 |

RPM routing、固定移除公式冗餘、train-only signed-log與global-min距離校準是本輪工程消融，不冒稱新學者演算法或order tracking。105維原資料契約不變。

P6僅文獻／研究候選，尚未本輪實作或評估：harmonic band-max shape ratios（不是能量占比）；train-only LMNN/NCA；固定多原型；classifier-conditioned rejection；MSP/Energy/小MLP/OpenMax；Deep kNN；CORAL/DANN；healthy-only異常模型；train內proxy unknown；raw時序方法；ensemble/augmentation。後續最多優先提出兩項，需另封存協定；沒有把P6算進198評估。
