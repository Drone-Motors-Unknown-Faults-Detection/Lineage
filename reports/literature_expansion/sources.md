# 文獻、方法與改編來源（2026-10-02）

這是有界的文獻導向實測，不是「所有演算法皆已試過」。核對原始論文、作者網站、出版頁與官方實作文件；部分出版頁抓取失敗，改用作者預印本／作者機構存本。書目與方法重點查閱不等於逐字完整閱讀每篇全文。論文在其他資料集的成績不能引用成本站馬達成績。

## 書目與採用範圍

| ID | 作者、年份、論文／刊物與原始來源 | 本次對應與差異 |
|---|---|---|
| P01 | Fisher (1936), *The use of multiple measurements in taxonomic problems*, Annals of Eugenics 7:179–188, [DOI](https://doi.org/10.1111/j.1469-1809.1936.tb02137.x)；[作者作品機構存本索引](https://digital.library.adelaide.edu.au/items/d26c5e1c-2751-472f-9738-9db69dc216f7) | C01/C13–19/C24 使用 sklearn 多類 Gaussian LDA，並非聲稱逐字重現1936二類實驗。 |
| P02 | Ledoit & Wolf (2004), *A well-conditioned estimator for large-dimensional covariance matrices*, Journal of Multivariate Analysis 88:365–411, [作者全文](https://www.ledoit.net/Well-conditioned2004.pdf) | 正式 factory Maha 保留；R01–04/R13 的 train-only pooled LW。 |
| P03 | Friedman (1989), *Regularized Discriminant Analysis*, JASA 84:165–175, [DOI](https://doi.org/10.1080/01621459.1989.10478752)；[Stanford 技術報告](https://statistics.stanford.edu/technical-reports/regularized-discriminant-analysis) | C10–12/C23 是 RDA-inspired 自訂變體：直接凸組合各類 ML covariance 與樣本數加權 pooled covariance，再縮向 trace/D identity；與原作按樣本數混合 scatter 的 lambda 參數化不同。不得宣稱完全重現 Friedman RDA。 |
| P04 | Breiman (2001), *Random Forests*, Machine Learning 45:5–32, [作者全文](https://www.stat.berkeley.edu/~breiman/randomforest2001.pdf) | C04/C21；sklearn200樹、depth12、leaf5、sqrt、balanced 固定，不做 test 搜參。 |
| P05 | Geurts, Ernst & Wehenkel (2006), *Extremely randomized trees*, Machine Learning 63:3–42, [作者機構頁](https://orbi.uliege.be/handle/2268/9357) | C03 混合RPM；沿用先前樹參數，與先前 separate RPM 對照。 |
| P06 | Friedman (2001), *Greedy function approximation: A gradient boosting machine*, Annals of Statistics 29:1189–1232, [出版頁](https://doi.org/10.1214/aos/1013203451) | C05 sklearn histogram boosting；非原文逐步精確演算法的完整重現。 |
| P07 | Cortes & Vapnik (1995), *Support-vector networks*, Machine Learning 20:273–297, [出版頁](https://link.springer.com/article/10.1007/BF00994018) | C06/C22 固定 RBF C1 gamma scale，balanced。 |
| P08 | Cover & Hart (1967), *Nearest Neighbor Pattern Classification*, IEEE Transactions on Information Theory 13:21–27, [作者全文](https://isl.stanford.edu/~cover/papers/transIT/0021cove.pdf) | C07/C08/C20 使用距離加權5/15NN，是 kNN 實作變體；不套用 IID 漸近誤差保證。 |
| P09 | John & Langley (1995), *Estimating Continuous Distributions in Bayesian Classifiers*, UAI:338–345, [作者預印本](https://arxiv.org/abs/1302.4964) | C09 選文中對照 Gaussian 假設，不是該文提出的 kernel density 版本。 |
| P10 | Pearson (1901), *On lines and planes of closest fit to systems of points in space*, Philosophical Magazine 2:559–572, [DOI](https://doi.org/10.1080/14786440109462720) | C19 train-only PCA20，無 whitening；出版頁抓取失敗，書目可核對，非此專案原創 PCA。 |
| P11 | Goldberger, Roweis, Hinton & Salakhutdinov (2004), *Neighbourhood Components Analysis*, NIPS17, [會議全文](https://papers.nips.cc/paper/2566-neighbourhood-components-analysis.pdf) | C20 NCA10；為計算預算固定每類最多60 train rows、50 iterations，保留 subset IDs/收斂狀態，不宣稱全train最佳解。 |
| P12 | Lee, Lee, Lee & Shin (2018), *A Simple Unified Framework for Detecting Out-of-Distribution Samples and Adversarial Attacks*, NeurIPS31, [會議頁](https://proceedings.neurips.cc/paper/2018/hash/abdeb6f575ac5c6676b747bca8d09cc2-Abstract.html) | R01 pooled class distance 作 tabular 改編；未做深網多層特徵、input perturbation 或 supervised OOD fitting。 |
| P13 | Ren, Fort, Liu, Roy, Padhy & Lakshminarayanan (2021), *A Simple Fix to Mahalanobis Distance for Improving Near-OOD Detection*, [作者预印本](https://arxiv.org/abs/2106.09022)；[workshop全文](https://www.gatsby.ucl.ac.uk/~balaji/udl2021/accepted-papers/UDL2021-paper-007.pdf) | R02 採 min MD_c − MD_background；用 LW 與既有特徵，非深網／未正則化 covariance；R03/R04 改背景項係數0.5/2，R18改 harmonic69 表示法。 |
| P14 | Chen, Wiesel, Eldar & Hero (2010), *Shrinkage Algorithms for MMSE Covariance Estimation*, IEEE Transactions on Signal Processing58:5016–5029, [作者預印本](https://arxiv.org/abs/0907.4698) | R05 以 sklearn OAS 代替 pooled LW；[官方文件](https://scikit-learn.org/1.7/modules/generated/sklearn.covariance.OAS.html)註明其計算與原文 Eq23 的小項差異。 |
| P15 | Liu, Ting & Zhou (2008), *Isolation Forest*, ICDM:413–422, [作者全文](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf) | R09 all-known train200樹/max_samples256；獨立known cal q95，而非直接使用套件內 contamination 門檻。 |
| P16 | Breunig, Kriegel, Ng & Sander (2000), *LOF: Identifying Density-Based Local Outliers*, SIGMOD:93–104, [作者機構索引](https://brava.dbs.ifi.lmu.de/publications/676)；[DOI](https://doi.org/10.1145/342009.335388) | R10 sklearn novelty=True,k20；原論文是資料集內離群分數，這是對新樣本 novelty 延伸。[實作文件](https://scikit-learn.org/1.7/modules/generated/sklearn.neighbors.LocalOutlierFactor.html)。 |
| P17 | Schölkopf, Platt, Shawe-Taylor, Smola & Williamson (2001), *Estimating the support of a high-dimensional distribution*, Neural Computation13:1443–1471, [全文存本](https://www.math.univ-toulouse.fr/~agarivie/Telecom/apprentissage/articles/OneClasslong.pdf)；[DOI](https://doi.org/10.1162/089976601750264965) | R11 all-known support nu.05 RBF；不是 healthy-only 故障分類，cal q95獨立。 |
| P18 | Dempster, Laird & Rubin (1977), *Maximum Likelihood from Incomplete Data Via the EM Algorithm*, JRSS B39:1–38, [出版頁](https://doi.org/10.1111/j.2517-6161.1977.tb01600.x) | R12 每已知類2 diagonal Gaussian EM、reg1e-4；sklearn GMM 實作，不是 EM 文獻的故障專用架構。 |
| P19 | Hendrycks & Gimpel (2017), *A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks*, ICLR, [作者預印本](https://arxiv.org/abs/1610.02136) | R14 使用 LDA posterior 的1−MSP，非神經網路重現；R15 entropy、R16 top-two margin 為此研究固定信心對照。 |
| P20 | Liu, Wang, Owens & Li (2020), *Energy-based Out-of-distribution Detection*, NeurIPS33, [會議頁](https://papers.neurips.cc/paper/2020/hash/f5496252609c43eb8a3d147ab9b9c006-Abstract.html) | R19 把−logsumexp 用於實際 LDA affine decision logits,T1；非 energy-based NN training，保留共同logit偏移/gauge限制；未把 log(tree probability)冒稱 logits。 |
| P21 | Wang, Li, Feng & Zhang (2022), *ViM: Out-Of-Distribution with Virtual-logit Matching*, CVPR:4921–4930, [作者預印本](https://arxiv.org/abs/2203.10807) | R20 改用 LDA W,b 與 scaled formal features；principal rank20、train alpha 固定，非原深網；alpha<=0則記失敗，不偷偷abs改符號。 |
| P22 | Angelopoulos & Bates (2023), *A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification*, Foundations and Trends in ML, [作者全文](https://arxiv.org/html/2107.07511v6) | 既有 B5/B6 只讀历史結果；本輪不重跑／不宣稱跨馬達exchangeability。 |
| P23 | Weinberger & Saul (2009), *Distance Metric Learning for Large Margin Nearest Neighbor Classification*, JMLR10:207–244, [作者頁](https://jmlr.org/papers/v10/weinberger09a.html) | LMNN 文獻候選未實測；本輪使用已安裝 sklearn NCA，不把 NCA 改名 LMNN；不新增求解依賴。 |
| P24 | Sun, Ming, Zhu & Li (2022), *Out-of-Distribution Detection with Deep Nearest Neighbors*, ICML/PMLR162:20827–20840, [會議頁](https://proceedings.mlr.press/v162/sun22d.html) | factory kNN 1/5/15為非深度對照，不能冒稱此文深embedding重現。 |
| P25 | Bendale & Boult (2016), *Towards Open Set Deep Networks*, CVPR:1563–1572, [作者預印本](https://arxiv.org/abs/1511.06233) | OpenMax 未實測：無已驗證深activation/Weibull tail實作，本輪不能以原始105D mean distance假冒。 |
| P26 | Ruff et al. (2018), *Deep One-Class Classification*, ICML/PMLR80:4393–4402, [會議頁](https://proceedings.mlr.press/v80/ruff18a.html) | Deep SVDD 未實測：需要新的深網訓練契約；亦非直接多類fault-type classifier。 |
| P27 | Sun, Feng & Saenko (2016), *Return of Frustratingly Easy Domain Adaptation*, AAAI30, [會議頁](https://ojs.aaai.org/index.php/AAAI/article/view/10306) | CORAL 未實測：使用 test batch covariance 的 transductive方法違反目前inductive/cal-only協定；不擅自把test送fit。 |
| P28 | Grinsztajn, Oyallon & Varoquaux (2022), *Why do tree-based models still outperform deep learning on typical tabular data?*, NeurIPS Datasets and Benchmarks, [會議頁](https://proceedings.neurips.cc/paper_files/paper/2022/hash/0378c7692da36807bdec87ab043cdadc-Abstract-Datasets_and_Benchmarks.html) | 候選家族取捨依據，不是本站實測方法或馬達改善保證。 |

## 此研究自行改編／組合的精確位置

`core/fault_type_literature.py`（歷史已封存檔案不修改）：

- `LiteratureRepresentation._raw/fit`：原來源為 `core/fault_type_feature_contract.py` 的105維歷史統計／FFT band-max契約、舊 `StudyRepresentation` robust/signed-log 與 P01/P10/P11。C16把signed66改為混合RPM；C17/C18只把30個band maxima改成每軸相對比例，保留36個非冗餘統計，C17另加3個幅值坐標，C18是移除幅值的對照。不是新物理能量特徵或修復raw alignment。floor完全由train建立；不fit test。
- `BlendedDiscriminant.fit/decision_function`：P01/P03 Gaussian判別的研究改編，pooling=0/.5/1、shrinkage=.1/.5兩層係數及 equal priors 固定；用 log determinant 和 precision 的完整二次判別，不僅換距離名稱。C13–15則只改既有 sklearn LDA shrinkage .1/.5/.9。
- `NoveltyReference.fit/raw`：R03/R04 在P13的background項前加入.5/2；R06將P12 pooled full precision改成 diagonal variance；R13改每類單中心為2個train KMeans中心，沿用P02 pooled precision；R18只換表示法。R07/R08透過正式factory改k1/k15，不重寫近鄰距離。
- `NoveltyReference.calibrate/raw`：R17從min-over-classes改為classifier predicted label reference，cal也依predicted label分組q95，缺組不借真值或其他fold。R21/R22將P02 factory距離與P19 posterior信心，在known-cal robust尺度上用固定.25/.75權重融合。這些是本站改編，不把未發表组合說成已有論文。
- R14–16/R19/R20的parent classifier一律C01；R18一律C17；不是看test後混合最好的classifier與detector。所有scalar分數q95由另一顆馬達已知cal估計；signed分數直接比較，不除負門檻。

`experiments/fault_type_literature_registry.py`：逐ID記錄實值參數、seeds0/1/2、固定3fold、資料／程式SHA；`experiments/fault_type_literature_study.py`：train-fit與cal-only門檻分離、保存模型／逐樣本／分層指標。來源對應不是「學者證明本資料有效」，只能由本次實測回答。

未測 raw CNN/TCN、STFT/wavelet、order tracking、RUL：本輪只有清理後特徵且時序／感測器／原始window證據缺口仍UNKNOWN，不能排列特徵欄假冒時間訊號。其他大型深網、額外軟體／資料、無界超參數搜尋也不是本輪已完成項目。
