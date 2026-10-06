# 固定範圍文獻清冊

存在與內容分開。B01–B40保留歷史來源，S為人工核對補充，P為自動候選；P不代表獨立論文數。全部未核內容仍UNVERIFIED，#19保持OPEN。

| ID | 題名／原引用 | 存在 | 內容 | 閱讀與適配 |
|---|---|---|---|---|
| B01 | [Fisher, R. A. (1936). The use of multiple measurements in taxonomic problems. Annals of Eugenics 7, 179–188.](https://doi.org/10.1111/j.1469-1809.1936.tb02137.x) | UNVERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；LDA 的歷史來源；本站使用多類 Gaussian 判別及收縮 |
| B02 | [A well-conditioned estimator for large-dimensional covariance matrices](https://www.ledoit.net/Well-conditioned2004.pdf) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；逐類與 pooled 共變異數的不同適配 |
| B03 | [Nearest neighbor pattern classification](https://isl.stanford.edu/~cover/papers/transIT/0021cove.pdf) | VERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；近鄰分類的基礎；本站距離加權 k-NN 與拒絕分數不同 |
| B04 | [The Regression Analysis of Binary Sequences](https://doi.org/10.1111/j.2517-6161.1958.tb00292.x) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；logistic 基礎來源；六類 L2／lbfgs 依既有 sklearn 契約 |
| B05 | [Geurts, P., Ernst, D. & Wehenkel, L. (2006). Extremely randomized trees. Machine Learning 63, 3–42.](https://orbi.uliege.be/handle/2268/9357) | UNVERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；ExtraTrees 固定參數對照 |
| B06 | [Breiman, L. (2001). Random Forests. Machine Learning 45, 5–32.](https://www.stat.berkeley.edu/~breiman/randomforest2001.pdf) | VERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；RandomForest 固定參數對照 |
| B07 | [Greedy function approximation: A gradient boosting machine.](https://doi.org/10.1214/aos/1013203451) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；sklearn histogram boosting 的思想來源，非原演算法逐步重現 |
| B08 | [Support-vector networks](https://doi.org/10.1007/BF00994018) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；RBF 與 precomputed invariant kernel SVC |
| B09 | [Estimating Continuous Distributions in Bayesian Classifiers](https://arxiv.org/abs/1302.4964) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；採 Gaussian 對照，不是該文提出的 kernel density 版本 |
| B10 | [LIII. On lines and planes of closest fit to systems of points in space](https://doi.org/10.1080/14786440109462720) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；train-only PCA，不 whitening |
| B11 | [Goldberger, J., Roweis, S., Hinton, G. & Salakhutdinov, R. (2004). Neighbourhood Components Analysis. NIPS 17.](https://papers.nips.cc/paper/2566-neighbourhood-components-analysis.pdf) | VERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；NCA10，固定 train 子集與迭代預算；不同於 LMNN |
| B12 | [Regularized Discriminant Analysis](https://doi.org/10.1080/01621459.1989.10478752) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；本站 covariance 凸混合與 RPM pooling 為有限適配 |
| B13 | [A Simple Unified Framework for Detecting Out-of-Distribution Samples and Adversarial Attacks](https://proceedings.neurips.cc/paper/2018/hash/abdeb6f575ac5c6676b747bca8d09cc2-Abstract.html) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；pooled Mahalanobis 表格適配，無深層特徵或 input perturbation |
| B14 | [A Simple Fix to Mahalanobis Distance for Improving Near-OOD Detection](https://www.gatsby.ucl.ac.uk/~balaji/udl2021/accepted-papers/UDL2021-paper-007.pdf) | VERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；RMD 背景距離相減及本站係數／分塊消融 |
| B15 | [Shrinkage Algorithms for MMSE Covariance Estimation](https://arxiv.org/abs/0907.4698) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；sklearn OAS 的有限實作差異保留 |
| B16 | [Isolation Forest](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf) | VERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；all-known train，另一馬達 known-cal q95 |
| B17 | [LOF](https://doi.org/10.1145/342009.335388) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；新樣本 novelty 延伸，不冒稱原 transductive LOF |
| B18 | [Estimating the Support of a High-Dimensional Distribution](https://doi.org/10.1162/089976601750264965) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；all-known One-Class SVM，非 healthy-only 多類分類器 |
| B19 | [Maximum Likelihood from Incomplete Data Via the                     <i>EM</i>                     Algorithm](https://doi.org/10.1111/j.2517-6161.1977.tb01600.x) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；每類 diagonal GMM 的 EM 構件 |
| B20 | [A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks](https://arxiv.org/pdf/1610.02136v3) | METADATA_ONLY | PARTIAL | v3 §3 baseline 與 PR 定義；1−MSP/q95 的本地適配；MSP 啟發；LDA／softmax 表格版本及 q95 為本站適配 |
| B21 | [Shannon, C. E. (1948). A Mathematical Theory of Communication. Bell System Technical Journal 27, 379–423 and 623–656.](https://www.princeton.edu/~wbialek/rome/refs/shannon_48.pdf) | VERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；normalized entropy 構件，不是故障 OOD 保證 |
| B22 | [Energy-based Out-of-distribution Detection](https://papers.neurips.cc/paper/2020/hash/f5496252609c43eb8a3d147ab9b9c006-Abstract.html) | VERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；actual LDA affine logits 的有限 score 適配 |
| B23 | [ViM: Out-Of-Distribution with Virtual-logit Matching](https://arxiv.org/abs/2203.10807) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；LDA W、b／rank20／train alpha 的有限表格適配 |
| B24 | [MacQueen, J. (1967). Some methods for classification and analysis of multivariate observations. Fifth Berkeley Symposium 1, 281–297.](https://digicoll.lib.berkeley.edu/record/113015?v=pdf) | UNVERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；sklearn 批次 KMeans 多中心，非原線上更新逐步重現 |
| B25 | [A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification](https://arxiv.org/html/2107.07511v6) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；歷史 B5／B6；跨馬達 exchangeability 未證明 |
| B26 | [Distance Metric Learning for Large Margin Nearest Neighbor Classification](https://www.jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf) | VERIFIED | PARTIAL | §3.1–3.2 Eq.10–13、§4.1 Eq.15、Appendix A；非負 diagonal／mean／identity ridge／固定子集的 LMNN-inspired 版本 |
| B27 | [Fast maximum margin matrix factorization for collaborative prediction](https://home.ttic.edu/~nati/Publications/RennieSrebroICML05.pdf) | VERIFIED | PARTIAL | §3.3 Eq.9；只取 scalar loss，沒有 MMMF；只移用 scalar smooth loss 到 triplet，未實作 MMMF |
| B28 | [A Diagnostic System for Speed‐Varying Motor Rotary Faults](https://onlinelibrary.wiley.com/doi/10.1155/2014/310626) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；幅值可能帶故障訊息的動機，RMS 比值不是原文方法 |
| B29 | [Sugiyama, M. (2007). Dimensionality Reduction of Multimodal Labeled Data by Local Fisher Discriminant Analysis. JMLR 8, 1027–1061.](https://www.jmlr.org/papers/volume8/sugiyama07b/sugiyama07b.pdf) | VERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；固定 ridge／子集／正方向秩的 LFDA，配 PCA 控制 |
| B30 | [Sato, A. & Yamada, K. (1995 conference, 1996 volume). Generalized Learning Vector Quantization. NIPS 8, 423–429.](https://proceedings.neurips.cc/paper_files/paper/1995/file/9c3b1830513cc3b8fc4b76635d32e692-Paper.pdf) | VERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；固定 sigmoid(4mu)、epsilon、L-BFGS-B／anchor 為本站改編 |
| B31 | [Lange, M., Zühlke, D., Holz, O. & Villmann, T. (2014). Applications of lp-Norms and their Smooth Approximations for Gradient Based Learning Vector Quantization. ESANN, 271–276.](https://www.esann.org/sites/default/files/proceedings/legacy/es2014-153.pdf) | VERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；Q／S、alpha20，本站固定幾何與原型訓練適配 |
| B32 | [AGLVQ - Making Generalized Vector Quantization Algorithms Aware of Context](https://www.esann.org/sites/default/files/proceedings/2021/ES2021-40.pdf) | VERIFIED | PARTIAL | 原 PDF 六頁，Eq.4；登錄題名變體另記；單截距 RPM 多項式／平方距離／固定 aux 的有限適配 |
| B33 | [Efficient rejection strategies for prototype-based classification](https://www.honda-ri.de/pubs/pdf/2814.pdf) | VERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；distance／1−RelSim／固定 q95 OR，不復現原 threshold grid search |
| B34 | [Invariant kernel functions for pattern analysis and machine learning](https://lmb.informatik.uni-freiburg.de/papers/download/ha_bu_MachineLearning6807.pdf) | METADATA_ONLY | PARTIAL | Eq.2、Proposition 11；S3 有限群與共享 scaler 條件；S3 軸排列群平均、共享 scaler 與 RKHS 拒絕器的本站適配 |
| B35 | [Out-of-Distribution Generalization via Risk Extrapolation (REx)](https://proceedings.mlr.press/v139/krueger21a.html) | METADATA_ONLY | PARTIAL | §2.5、§3.1 Eq.8、§3.2；mean/sum 與 RPM domain 適配；等 RPM／等類 CE、population variance、線性 softmax、ridge 的本站適配 |
| B36 | [Self-Challenging Improves Cross-Domain Generalization](https://publications.ri.cmu.edu/self-challenging-improves-cross-domain-generalization) | METADATA_ONLY | PARTIAL | arXiv v1 §3.1 Eq.1–5、Algorithm 1；固定手工特徵 200 steps；手工特徵、四遮蔽控制、固定 200 steps；無 CNN／Adam／curriculum |
| B37 | [Distributionally Robust Neural Networks for Group Shifts: On the Importance of Regularization for Worst-Case Generalization](https://arxiv.org/pdf/1911.08731) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；已規劃未實作，本階段收尾，未進入訓練或測試 |
| B38 | [In Search of Lost Domain Generalization](https://arxiv.org/abs/2007.01434) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；一致模型選擇流程的限制提醒，不移植外部排名 |
| B39 | [Vaze, S., Han, K., Vedaldi, A. & Zisserman, A. (2022). Open-Set Recognition: A Good Closed-Set Classifier Is All You Need? ICLR.](https://robots.ox.ac.uk/~vgg/publications/2022/Vaze22/) | UNVERIFIED | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；D01 解耦的研究動機，不是本站效果保證 |
| B40 | [Why do tree-based models still outperform deep learning on typical tabular data?](https://proceedings.neurips.cc/paper_files/paper/2022/hash/0378c7692da36807bdec87ab043cdadc-Abstract-Datasets_and_Benchmarks.html) | METADATA_ONLY | UNVERIFIED | 本輪未精讀；見 prior_reading_claim；樹模型比較動機，非跨馬達可靠性證據 |
| S01 | [Cross‐validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure](https://doi.org/10.1111/ecog.02881) | METADATA_ONLY | PARTIAL | 出版摘要與結構化切分條件；非全文；teacher 第4節的群組切分理由 |
| S02 | [Impact of Data Leakage in Vibration Signals Used for Bearing Fault Diagnosis](https://doi.org/10.1109/ACCESS.2024.3497716) | METADATA_ONLY | PARTIAL | 作者機構頁及摘要／切分問題；不移植成績；teacher 第5節資料洩漏研究背景 |
| S03 | [Out-of-Distribution Detection with Deep Nearest Neighbors](https://proceedings.mlr.press/v162/sun22d.html) | METADATA_ONLY | PARTIAL | §方法的 normalized deep embedding／第k距離；非全文；factory 逐類 mean-k 距離與原法差異 |
| S04 | [Overcoming catastrophic forgetting in neural networks](https://doi.org/10.1073/pnas.1611835114) | METADATA_ONLY | PARTIAL | 出版摘要與 EWC 權重保護方法說明；非全文；rehearsal 不等於 EWC |
| S05 | [iCaRL: Incremental Classifier and Representation Learning](https://openaccess.thecvf.com/content_cvpr_2017/html/Rebuffi_iCaRL_Incremental_Classifier_CVPR_2017_paper.html) | METADATA_ONLY | PARTIAL | 官方摘要及 exemplar／representation 方法；非全文；全資料重fit不是完整iCaRL |
| S06 | [Visualizing Data using t-SNE](https://jmlr.org/papers/v9/vandermaaten08a.html) | METADATA_ONLY | PARTIAL | 官方書目與摘要；不以投影證明分類可靠；issue #16 的可視化背景；未接手其程式 |
| S07 | [Density-Based Clustering Based on Hierarchical Density Estimates](https://doi.org/10.1007/978-3-642-37456-2_14) | METADATA_ONLY | UNVERIFIED | 出版書目與摘要；全文訂閱受限；HDBSCAN原始來源；本站參數階梯屬本地約定 |
| S08 | 題名未能辨識 | AMBIGUOUS | UNVERIFIED | README只給作者年份，未能唯一定位；退化模型背景，身分 AMBIGUOUS |
| S09 | 題名未能辨識 | AMBIGUOUS | UNVERIFIED | README只給作者年份；可能候選未作唯一合併；退化模型背景，身分 AMBIGUOUS |
| S10 | [A review on machinery diagnostics and prognostics implementing condition-based maintenance](https://doi.org/10.1016/j.ymssp.2005.09.012) | METADATA_ONLY | UNVERIFIED | 出版書目與摘要；非全文；PHM背景，不能支持本資料RUL |
| S11 | [Prognostics and health management design for rotary machinery systems—Reviews, methodology and applications](https://doi.org/10.1016/j.ymssp.2013.06.004) | METADATA_ONLY | UNVERIFIED | 出版書目與摘要；非全文；PHM背景，不保證本站健康指數已具真值 |
| S12 | [Machinery health prognostics: A systematic review from data acquisition to RUL prediction](https://doi.org/10.1016/j.ymssp.2017.11.016) | METADATA_ONLY | UNVERIFIED | 出版書目與摘要；非全文；RUL所需資料背景 |
| S13 | [A review of novelty detection](https://doi.org/10.1016/j.sigpro.2013.12.026) | METADATA_ONLY | UNVERIFIED | 出版書目與摘要；非全文；冷啟動未知偵測背景 |
| S14 | [Support Vector Data Description](https://research.tudelft.nl/en/publications/support-vector-data-description/) | METADATA_ONLY | UNVERIFIED | 作者機構書目；非全文；未當作已用 OC-SVM 的相同方法 |
| S15 | [The Mahalanobis–Taguchi Strategy: A Pattern Technology System](https://onlinelibrary.wiley.com/doi/book/10.1002/9780470172247) | METADATA_ONLY | UNVERIFIED | 出版社書目與介紹；全書未取得；背景，不等同本站逐類LW |
| S16 | [Stochastic modelling and analysis of degradation for highly reliable products](https://doi.org/10.1002/asmb.2063) | METADATA_ONLY | UNVERIFIED | 出版社書目；online2014／volume2015分開；背景；本站無退化生命週期 |
| P003 | [Sparsity-based Algorithm for Detecting Faults in Rotating Machines](https://arxiv.org/abs/1511.00067) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P004 | [Detection of Faults in Rotating Machinery Using Periodic Time-Frequency Sparsity](https://arxiv.org/abs/1511.00393) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P005 | [Bearing fault diagnosis based on spectrum images of vibration signals](https://arxiv.org/abs/1511.02503) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P006 | [Towards Open Set Deep Networks](https://arxiv.org/abs/1511.06233) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P008 | [Bearing fault diagnosis based on domain adaptation using transferable features under different working conditions](https://arxiv.org/abs/1806.01512) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P015 | [Understanding Why Generalized Reweighting Does Not Improve Over ERM](https://arxiv.org/abs/2201.12293) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P017 | [Primary accelerometer calibration with two-axis automatic positioning stage](https://arxiv.org/abs/2204.09212) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P018 | [Improved Group Robustness via Classifier Retraining on Independent Splits](https://arxiv.org/abs/2204.09583) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P019 | [MetaMax: Improved Open-Set Deep Neural Networks via Weibull Calibration](https://arxiv.org/html/2211.10872v2) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P020 | [Fine-Grained Open-Set Fault Diagnosis via Metric-Guided Time-Frequency Configuration Selection and Class-Specific Autoencoders](https://arxiv.org/html/2607.13368) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P022 | [Multivariate Estimation with High Breakdown Point](https://doi.org/10.1007/978-94-009-5438-0_20) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P023 | [Principal Component Analysis](https://doi.org/10.1007/b98835) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P025 | [題名未能辨識](https://doi.org/10.1007/s10994-006-6226-1) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P027 | [Reprint of: Mahalanobis, P.C. (1936) "On the Generalised Distance in Statistics."](https://doi.org/10.1007/s13171-019-00164-5) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P029 | [Rolling element bearing diagnostics—A tutorial](https://doi.org/10.1016/j.ymssp.2010.07.017) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P031 | [Generalized relevance learning vector quantization](https://doi.org/10.1016/S0893-6080(02)00079-5) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P032 | [Control Chart Tests Based on Geometric Moving Averages](https://doi.org/10.1080/00401706.1959.10489860) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P033 | [A Fast Algorithm for the Minimum Covariance Determinant Estimator](https://doi.org/10.1080/00401706.1999.10485670) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P036 | [CONTINUOUS INSPECTION SCHEMES](https://doi.org/10.1093/biomet/41.1-2.100) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P040 | [Toward Open Set Recognition](https://doi.org/10.1109/TPAMI.2012.256) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P049 | [Efficient algorithms for mining outliers from large data sets](https://doi.org/10.1145/342009.335437) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P053 | [回転機械の振動音響診断技術 : ウェーブレット変換による回転機械の故障診断](https://doi.org/10.1299/kikaic.64.465) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P055 | [題名未能辨識](https://doi.org/10.18721/JCSTCS.19110) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P056 | [The Proof and Measurement of Association between Two Things](https://doi.org/10.2307/1412159) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P057 | [Diagnostico de Fallas en Motores de Inducción Mediante la Aplicación de Redes Neuronales Artificiales](https://doi.org/10.4067/S0718-07642007000200016) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P058 | [題名未能辨識](https://brava.dbs.ifi.lmu.de/publications/676) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P059 | [題名未能辨識](https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P062 | [題名未能辨識](https://digital.library.adelaide.edu.au/items/d26c5e1c-2751-472f-9738-9db69dc216f7) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P063 | [題名未能辨識](https://docs.scipy.org/doc/scipy-1.15.3/reference/optimize.minimize-lbfgsb.html) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P064 | [題名未能辨識](https://elib.spbstu.ru/dl/2/j26-183.pdf/download/j26-183.pdf) | VERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P065 | [題名未能辨識](https://epub.uni-bayreuth.de/id/eprint/4600/) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P071 | [題名未能辨識](https://jpn.nec.com/rd/people/atsushi_sato.html) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P073 | [題名未能辨識](https://link.springer.com/article/10.1007/s10845-024-02395-2) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P075 | [題名未能辨識](https://neurips.cc/virtual/2021/35514) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P076 | [題名未能辨識](https://numpy.org/doc/stable/reference/routines.fft.html) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P077 | [題名未能辨識](https://ojs.aaai.org/index.php/AAAI/article/view/10306) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P079 | [題名未能辨識](https://openreview.net/pdf?id=ryxGuJrFvS) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P082 | [題名未能辨識](https://papers.nips.cc/paper/2017/file/cb8da6767461f2812ae4290eac7cbc42-Paper.pdf) | VERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P084 | [Diagnostics for Mechanical Systems with Unknown Fault Modes: A Novel Open Set Recognition Approach](https://papers.phmsociety.org/index.php/phme/article/view/5015) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P086 | [題名未能辨識](https://proceedings.neurips.cc/paper/2020/file/d89a66c7c80a29b1bdbab0f2a1a94af8-Paper.pdf) | VERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P089 | [題名未能辨識](https://proceedings.neurips.cc/paper_files/paper/2021/file/cdfa4c42f465a5a66871587c69fcfa34-Paper.pdf) | VERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P091 | [題名未能辨識](https://prod-ms-be.lib.mcmaster.ca/server/api/core/bitstreams/464bbf81-0c76-4adc-9942-f07cc5a05954/content) | VERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P093 | [Reconnaissance de défauts dans les machines tournantes par apprentissage machine : cas des roulements](https://repository.enp.edu.dz/jspui/handle/123456789/8653) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P094 | [題名未能辨識](https://revistas.unal.edu.co/index.php/dyna/article/view/979) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P097 | [인휠 모터 구동 차량의 심층 학습 기반 로그-멜 스펙트로그램 활용 고장 진단 알고리즘 ](https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE12731193) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P100 | [題名未能辨識](https://www.esann.org/sites/default/files/proceedings/legacy/es2014-131.pdf) | VERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P104 | [題名未能辨識](https://www.ieice.org/jpn/books/ronbunshi-mokuji/1999/04/JDII-04.html) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P107 | [題名未能辨識](https://www.math.univ-toulouse.fr/~agarivie/Telecom/apprentissage/articles/OneClasslong.pdf) | VERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P108 | [題名未能辨識](https://www.ms.k.u-tokyo.ac.jp/sugi/publications.html) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P109 | [題名未能辨識](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12115238/) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P111 | [題名未能辨識](https://www.researchgate.net/publication/377416125_OWFD-UCPM_An_open-world_fault_diagnosis_scheme_based_on_uncertainty_calibration_and_prototype_management) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P112 | [題名未能辨識](https://www.scielo.cl/scielo.php?pid=S0718-07642007000200016&script=sci_abstract) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P113 | [題名未能辨識](https://www.sciencedirect.com/science/article/abs/pii/S0263224124020177) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P114 | [題名未能辨識](https://www.sciencedirect.com/science/article/abs/pii/S0888327024004229) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P115 | [題名未能辨識](https://www.sciencedirect.com/science/article/abs/pii/S1474034625009097) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P116 | [題名未能辨識](https://www.semanticscholar.org/paper/Towards-Open-Set-Deep-Networks-Bendale-Boult/d094fb0af5bc6a26fa9c27d638c4a3a0725d8b5c) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P118 | [題名未能辨識](https://zdxb.nuaa.edu.cn/zdgcxb/article/abstract/202303027) | UNVERIFIED | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P120 | [An Investigation of Why Overparameterization Exacerbates Spurious Correlations](https://proceedings.mlr.press/v119/sagawa20a.html) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P122 | [Just Train Twice: Improving Group Robustness without Training Group Information](https://proceedings.mlr.press/v139/liu21f.html) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P124 | [Mitigating Neural Network Overconfidence with Logit Normalization](https://proceedings.mlr.press/v162/wei22d/wei22d.pdf) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
| P125 | [Deep One-Class Classification](https://proceedings.mlr.press/v80/ruff18a.html) | METADATA_ONLY | UNVERIFIED | 本輪尚未核對全文；歷史聲明另存；候選來源；是否為論文及本地取用待核對 |
