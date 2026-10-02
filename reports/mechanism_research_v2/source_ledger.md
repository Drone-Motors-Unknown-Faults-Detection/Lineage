# 原始文獻搜尋與閱讀深度（2026-10-02）

本輪依 H-D/H-P/H-G 搜尋：cross-machine bearing fault leakage、RPM partial pooling covariance、LMNN fault collapse、SupCon vibration、closed-set vs open-set、Mahalanobis OOD。僅以原論文/作者/會議/期刊來源支持方法，不以摘要中的外部高分當本站預期。

## 既有31筆來源的深度稽核

`reports/literature_expansion/sources.md` P01–28 與 `sources_addendum.md` P29–31 均已逐列核對對應實作/排除理由。
舊 ledger 沒有逐篇完整全文閱讀證據，**所有31篇的 full-cover reading 狀態仍 UNVERIFIED**。
P11/P13/P20 等有方法查閱與本地公式，但不能據此補寫全文研讀。P10/P31 有抓取限制；P23/P25/P26 未實測。
P01–22/P24/P29–31 的實測範圍以 old registry/result index 為準，不把 entropy/KMeans 的構件書目當新研究arm。
本輪重新深讀 P13/P23/P25/P26，以下增加閱讀範圍；仍沒有宣稱全頁逐字研讀。

## 17個候選／假說的一手來源與取捨

| ID | 原始來源、版本／書目 | 本輪閱讀深度與公式／假設 | 標籤、算力、邊界與採用 |
|---|---|---|---|
| S01 | Weinberger & Saul 2009, JMLR10:207–244, [LMNN PDF](https://www.jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf) | 深讀 §3–4，38頁中的loss/PSD/實驗設定；不是全38頁。L=(1−μ)Σtarget d_M(i,j)+μΣimpostor[1+d_M(i,j)−d_M(i,l)]₊，M≽0；固定初始同類target neighbors。9 datasets，部分PCA控成本。 | known train supervised，target/unknown不必需；k/μ/求解器成本。可改 class collapse，亦可能過fit single motor；本輪沒有已驗證求解依賴，延後，不把已收斂NCA叫LMNN。 |
| S02 | Khosla et al. 2020, NeurIPS33, [SupCon PDF](https://proceedings.neurips.cc/paper/2020/file/d89a66c7c80a29b1bdbab0f2a1a94af8-Paper.pdf) | 深讀 §3/4與eq2/3。L_i=−|P_i|⁻¹Σp log[exp(z_i·z_p/τ)/Σa≠i exp(z_i·z_a/τ)]；positive平均在log外。兩views、normalized encoder2048/project128，project在推論丟棄；CIFAR/ImageNet ResNets。 | known train/batch positives；τ/augmentation/訓練預算。不需要outer未知，但feature的物理augmentation未知；更高capacity也能過fit。延後neural，本輪不任意合成故障。 |
| S03 | Wei, Xie, Cheng, Feng, An & Li 2022, ICML/PMLR162:23631–23644, [LogitNorm](https://proceedings.mlr.press/v162/wei22d/wei22d.pdf) | 深讀 §3/4/討論：CE(f/(τ‖f‖₂)) 是**訓練loss**，epsilon防零；WRN40-2 CIFAR，200epochs/SGD/.9momentum，τ需合法選擇。 | neural trainknown；降低confidence幅度≠修好類別排序。不會事後normalize LDA就冒稱重現。未採用。 |
| S04 | Ren, Fort, Liu, Roy, Padhy & Lakshminarayanan 2021, UDL workshop/preprint, [RMD PDF](https://www.gatsby.ucl.ac.uk/~balaji/udl2021/accepted-papers/UDL2021-paper-007.pdf) | 深讀 §2/3、eq1–3、nearOOD eigenanalysis與設定。d_c=(z−μ_c)ᵀΣ⁻¹(z−μ_c)；RMD_c=d_c−d_0，論文confidence=−minRMD。背景全train、共享within covariance。CIFAR100/10等deepfeatures。 | trainknownlabel、背景trainallknown；不用outer未知。本站novelty=minRMD，signed q95 cal固定。原λ1；G02新分塊LW/per-dim權重為paper-inspired，不是原版。 |
| S05 | Bendale & Boult 2016, CVPR:1563–1572, [OpenMax PDF](https://arxiv.org/pdf/1511.06233) | 深讀 §2 algorithms1/2、activation與尾端Weibull；μ只用正確train，top-α activation重分配unknown mass後softmax。不是mean distance換名。 | known activation與tail η/α/拒絕ε；libMR需驗證。無已驗證deepactivation/tail重現，本輪延後；信心不保證unknown。 |
| S06 | Ruff et al.2018, ICML/PMLR80:4393–4402, [DeepSVDD PDF](https://proceedings.mlr.press/v80/ruff18a/ruff18a.pdf) | 深讀 §3/4及collapse條件。R²+(νn)⁻¹Σ[‖φ(x)−c‖²−R²]₊+weight decay；one-class平均距離版本。固定center、bias限制避免trivial collapse；MNIST/CIFAR/GTSRB設定。 | healthy-only學sphere與此六類fault不同；ν/architecture，neural成本。外部grid的test使用不能照搬。延後，不宣稱自動解fault types。 |
| S07 | Gulrajani & Lopez-Paz2021, ICLR, [DomainBed](https://arxiv.org/pdf/2007.01434) | 深讀 §3–5：7datasets/9algorithms/3selection策略；ERM與DG需一致selection，不確定selection可造成方法效果混淆。不是「所有DG都沒用」定理。 | 多source environments、knowntrain；testoracle違界。目前outer只有一顆trainmotor，RPM不是motor；不將cal當第二train，固定no-selection。 |
| S08 | Friedman1989, JASA84:165–175, [DOI](https://doi.org/10.1080/01621459.1989.10478752), [Stanford1987技術報告](https://statistics.stanford.edu/technical-reports/regularized-discriminant-analysis) | 官方書目/摘要核對；PDF掃描不提供可讀文字、官方存本本輪抓取失敗；**未宣稱本輪深讀原公式**。原RDA是class↔pooled scatter與identity收縮。 | 既有C10–12/C23自改cov參數化已實測；P系列借pooling概念，新增RPM means收縮，不說Friedman提出RPM版本；knowntrain only。 |
| S09 | Vaze, Han, Vedaldi & Zisserman2022, ICLR, [作者頁](https://robots.ox.ac.uk/~vgg/publications/2022/Vaze22/) | 作者頁/摘要；全文連結本輪timeout/不可用。good closed classifier的實證關係不是普遍保證。 | image研究與本站C17反例不同；H-D解耦作本站新組合，不声稱重現其算法。 |
| S10 | Ledoit & Wolf2004, JMVA88:365–411, [作者PDF](https://www.ledoit.net/Well-conditioned2004.pdf), [官方實作](https://scikit-learn.org/1.7/modules/generated/sklearn.covariance.LedoitWolf.html) | 舊ledger方法核對、本輪PDF抓取限制；Σ_LW=(1−ρ)S+ρ tr(S)/D I。原factory逐類，G/P pooled residual估計不是同一cov模型。 | knowntrain，ρ estimator非test調參；CPU小。採用現有sklearn，不增加依賴；rank退化需數值guard。 |
| S11 | Sun, Ming, Zhu & Li2022, ICML/PMLR162:20827–20840, [DeepNN作者會議頁](https://proceedings.mlr.press/v162/sun22d.html) | 摘要/書目。deepembedding上非parametric neighbors；不把正式raw-feature kNN冒稱deep重現。 | train embedding/ref；k與表示依賴。factory k5已實測，D02重用；沒有新深embedding。 |
| S12 | Angelopoulos & Bates2023, FnTML, [Conformal tutorial](https://arxiv.org/html/2107.07511v6) | 方法頁/假設查阅；rank p=(1+Σcal 1[s_i≥s])/(n+1)，exchangeability/有限resolution不可省。 | knowncal，同分處理需固定。跨motor shift未證exchangeable，historicalB5/B6不當5%健康完整誤報保證。未新跑。 |
| S13 | Randall & Antoni2011, MSSP25:485–520, [DOI](https://doi.org/10.1016/j.ymssp.2010.07.017) | 出版摘要/preview，非全文；envelope/band analysis依raw與機械頻率。band-max不是bandenergy。 | timing/rate/RPM/recording mapping未知；raw order/STFT不能由formal欄假造，本輪不適用。 |
| S14 | Wheat, Mohrenschlidt, Habibi & Al-Ani2024, IEEE Access, [DOI](https://doi.org/10.1109/ACCESS.2024.3497716), [機構全文](https://prod-ms-be.lib.mcmaster.ca/server/api/core/bitstreams/464bbf81-0c76-4adc-9942-f07cc5a05954/content) | 讀書目與split/part/run差異結果段；不是逐頁全文。part split比run split更差；bearing shift不等於本站原因證明。 | 原始split來源重要；zero duplicate不證recording独立。採其限制提醒，不把本站window當IID，無虛構session metadata。 |
| S15 | Tong, Li, Zhang & Zhang2018, [DATF作者預印本](https://arxiv.org/abs/1806.01512) | 摘要：marginal/conditional MMD與target pseudo labels。 | 需要target features/refinement；把outertest送入對齊違inductive協定，不採用。 |
| S16 | Sun, Feng & Saenko2016, AAAI30, [CORAL原會議頁](https://ojs.aaai.org/index.php/AAAI/article/view/10306) | 摘要/書目，source-target second-order alignment。 | target無label仍是targetdata，不能偷偷fit test covariance；排除本站此版本，不否定所有source-onlyDG。 |
| S17 | Grinsztajn, Oyallon & Varoquaux2022, NeurIPS Datasets & Benchmarks, [會議頁](https://proceedings.neurips.cc/paper_files/paper/2022/hash/0378c7692da36807bdec87ab043cdadc-Abstract-Datasets_and_Benchmarks.html) | 摘要/設定概述45 tabulardatasets，非全文。trees對typical tabular有效，不是本站crossmotor保證。 | RF/ET/HGB已實測且未解崩潰；不因通用benchmark再加大量tree調參。 |

深讀7篇：S01–07（方法、公式/算法、假設、實驗設定）；其餘有限查閱如表。共17候選，不等於17個新實測方法。
所有引用為paraphrase，外部成績不當作本次改善數字。
