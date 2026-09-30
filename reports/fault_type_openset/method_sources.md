# 方法來源與本專案的實作差異

1. Ledoit–Wolf 共變異數收縮：Olivier Ledoit、Michael Wolf，2004，
   *A well-conditioned estimator for large-dimensional covariance matrices*，
   Journal of Multivariate Analysis 88(2), 365–411。
   [作者公開論文](https://www.ledoit.net/Well-conditioned2004.pdf)。
   本專案逐已知類別估計位置與收縮共變異數，用已知 calibration
   距離的 95% 分位數正規化馬氏距離。這是馬氏距離搭配較穩定的
   共變異數估計，並非取代馬氏距離公式。

2. k-NN 距離作 OOD 檢測的研究依據：Yiyou Sun、Yifei Ming、
   Xiaojin Zhu、Yixuan Li，2022，*Out-of-Distribution Detection with Deep
   Nearest Neighbors*，ICML，PMLR 162, 20827–20840。
   [論文與正式書目](https://proceedings.mlr.press/v162/sun22d.html)。
   本專案是「逐類、5 鄰居平均歐氏距離＋逐類已知校準」的既有變體，
   使用 105 維工程特徵，沒有 neural embedding。不是上述 deep k-NN
   方法的原樣重現，也不能引用該論文的數字當成本資料的改善幅度。

3. 多類別 baseline 使用 scikit-learn regularized logistic regression，
   lbfgs 多類別損失與 balanced 類別權重。balanced 權重只依 train
   類別頻率決定，沒有用 test 標籤重新平衡模型。
   [官方 API 說明](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html)。

4. 分組／區塊切分的依據：David R. Roberts 等人，2017，
   *Cross-validation strategies for data with temporal, spatial, hierarchical,
   or phylogenetic structure*，Ecography 40, 913–929，
   [正式論文](https://doi.org/10.1111/ecog.02881)。資料具有依賴結構時，
   隨機逐列切分可能讓相似來源同時進入訓練與測試，造成過度樂觀的
   泛化估計。本專案依稽核可得的粗採集階段整組保留，而不把相鄰
   特徵列當作獨立採集。這個原則不證明 T-code 就是物理馬達 ID。
   [官方 group/time-series 切分說明](https://scikit-learn.org/stable/modules/cross_validation.html)。
   三個 campaign 的循環留出是跨組分類評估，不是按時間預測未來
   劣化的驗證；目前沒有足夠採集日期或事件邊界支持後者。

原理上的差異可以提出假說，但需與本次測量分開：收縮共變異數能
降低高維估計不穩定；k-NN 參考局部鄰域、較能表達不規則形狀。
兩者都可能受轉速／採集階段分布改變影響，且距離分位數校準不保證
跨階段仍有名目 5% 誤報。若 unknown configuration 與某 known
configuration 在現有特徵空間相近，任何已知類別區域擴大都可能增加
漏拒。這些是待結果與工況分析支持的推論，不是已證實的物理原因。
