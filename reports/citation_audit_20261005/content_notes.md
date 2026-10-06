# 原始文獻內容、適配與主張稽核

工作始於2026-10-05，部分交付跨至2026-10-06（Asia/Taipei）。範圍與候選擷取見exp23手冊；書目驗證與內容判定分開。原來源題名與作者保持原文，新筆記使用繁體中文。下列是本輪實際核對的關鍵章節，不繼承前回合「全文閱讀」作本輪重新逐頁閱讀聲明。

## 六項直接取用來源

### B26：LMNN

Weinberger與Saul（2009），JMLR10:207–244，[原文](https://jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf)。本輪查§3.1–3.2、Eq.10–13、§4.1 Eq.15、Appendix A；原法固定同類target neighbors，使用拉近距離與推離impostors的hinge，學PSD metric。原方法是已知分類，不保證新motor或unknown辨識。

本站core/fault_type_continuous.py、fault_type_smooth_margin.py、fault_type_metric_classifiers.py將metric限制為非負對角，採mean-scaled loss、identity ridge、class×RPM子集及固定optimizer。E02／E04把收斂hard600接5NN；E08另取Eq.15三項energy分類。判定PARTIAL／明確改編，不是忠實full-PSD重現。收斂只是訓練問題成功，不是泛化成功。

### B27：MMMF的單一smooth loss

Rennie與Srebro（2005），ICML，[作者稿](https://home.ttic.edu/~nati/Publications/RennieSrebroICML05.pdf)。查§3.3、Eq.9：shifted generalized logistic為γ⁻¹log(1+exp(γ(1−z)))。本站只取scalar，把z對應負／正距離差，τ=.1與γ=10相對應；另保留本站pull、mean與ridge。沒有rating matrix、低秩factorization或MMMF推論。判定PARTIAL；不得將27個solver診斷稱27次完整MMMF實測。

### B34：Invariant Kernel

Haasdonk與Burkhardt（2007），Machine Learning68:35–61，[作者稿](https://lmb.informatik.uni-freiburg.de/papers/download/ha_bu_MachineLearning6807.pdf)。查Eq.2、Proposition11及有限群平均條件。本站core/fault_type_axis_kernel.py使用S3軸排列、共享同名特徵scaler與RBF；共同正交置換使雙群平均可化為六項。α=1才對完整排列群不變，α=.5只是混合。既有105→66抽取、參數、RKHS拒絕是本站適配，不支持任意連續旋轉、安裝變動或真正物理一致性。判定PARTIAL；代數不變不等於診斷可靠。

### B35：REx

Krueger等（2021），ICML／PMLR139:5815–5826，[原文](https://proceedings.mlr.press/v139/krueger21a/krueger21a.pdf)。查§2.5模型選擇、§3.1 Eq.8、§3.2理論限制。Eq.8為風險sum＋β variance；本站core/fault_type_risk_extrapolation.py為三RPM等類risk的mean＋β population variance＋ridge。固定mean不是逐式相同：乘三後，相當於原sum式variance係數3β及相應ridge。RPM不是三個獨立motor環境；因果介入與同方差假設未獲證明。判定PARTIAL。risk variance降低不能被寫成跨motor因果或可靠性已成立。

### B36：RSC

Huang、Wang、Xing、Huang（2020），ECCV，[arXiv v1](https://arxiv.org/pdf/2007.02454v1)。查§3.1 Eq.1–5、Algorithm1與遮蔽條件；原法以learned image representation的true-class signed梯度遮蔽特徵再更新網路。本站core/fault_type_self_challenging.py在固定手工特徵與linear softmax上做200固定SGD steps、exact-ceil比例、stable ties、train-only ERM warm及四個controls。貢獻遮蔽另列variant，不冒稱唯一原RSC。最後iterate不代表收斂，影像理論不自動移植；判定PARTIAL。M24方法全部FAILED只否定本站有限條件，不反證原文章的影像實驗。

### B20：MSP

Hendrycks與Gimpel（2017），ICLR，[v3原文](https://arxiv.org/pdf/1610.02136v3)。查§3 baseline、正負score與PR定義。原MSP以最大softmax判別；本站NoveltyReference用1−MSP，另一motor known-only q95是本地校準約定。LDA／線性手工特徵不同於原深網路。MSP不是已校準信心；q95不保證跨motor5%FPR。判定PARTIAL，未知positive AUPR須報prevalence。

## 其他需同步更正的主張

| ID | 專案原位置／主張 | 判定 | 正確界線 |
|---|---|---|---|
| C01 | main README.md「T1/T2/T3三個壽命期、run-to-failure模板」 | CONTRADICTED | 固定Guide支持不同個體，沒有時間／failure endpoint，不支持生命週期串接 |
| C02 | README.md「7→1 screws天然嚴重度階梯」 | UNVERIFIED | 配置數量／位置不是經量測的損傷嚴重度，不能據此RUL |
| C03 | README.md持續學習引EWC／iCaRL支持完整rehearsal | PARTIAL | [EWC原文](https://doi.org/10.1073/pnas.1611835114)為權重保護；[iCaRL原文](https://openaccess.thecvf.com/content_cvpr_2017/html/Rebuffi_iCaRL_Incremental_Classifier_CVPR_2017_paper.html)含exemplar／representation learning。本站全資料重fit不是這兩法，也無跨域不忘保證 |
| C04 | 原始Mahalanobis1936引用2019 DOI | SUPPORTED_WITH_VERSION_NOTE | 10.1007/s13171-019-00164-5為重印，不是1936原始DOI；現main實驗手冊已注明 |
| C05 | factory k-NN引用Cover／Ramaswamy／Sun | PARTIAL | [Sun2022](https://proceedings.mlr.press/v162/sun22d/sun22d.pdf)為normalized deep embedding第k距離；本站逐類平均k距離＋known校準，不是其完整方法或同資料成績 |
| C06 | q95＝5%跨motor誤報保證、conformal可保證跨motor | CONTRADICTED_IF_ASSERTED | [Conformal原來源](https://arxiv.org/html/2107.07511v6)需對應exchangeability；本站未證明，不給coverage保證 |
| C07 | core數值改編等同原論文全部算法 | PARTIAL | 上述六卡逐一列來源與差異；新文件不得省略adaptation |
| C08 | OpenSet_Recognition.md的2607.13368不存在 | NOT_A_VALID_CRITICISM | [原arXiv](https://arxiv.org/abs/2607.13368)確認Jeon／Lee，2026-07-15；查§3.1–3.5，需raw STFT與CSAE，不是本站既有105維忠實實測 |
| C09 | MetaMax是OpenMax後續、已在本站做過 | METADATA_SUPPORTED_ONLY | [arXiv](https://arxiv.org/abs/2211.10872)作者Lyu／Gutierrez／Beksi，v1 2022、v2 2026；本輪摘要與HTML方法局部查核，不冒稱本站實作 |
| C10 | 樹模型／DG原文headline可保證本站提升 | UNVERIFIED | 資料、架構、切分與模型選擇不同；只能作候選動機，本站以封存實測判定 |
| C11 | LOF兩個ACM DOI是誤引 | NOT_A_VALID_CRITICISM | 335191.335388為SIGMOD Record、342009.335388為proceedings登錄；保留manifestation，不將其計成兩個新方法 |
| C12 | AGLVQ DOI登錄題名與PDF不同 | METADATA_VARIANT | 登錄含「Algorithms」，原PDF題名為Making Generalized Learning Vector Quantization Aware of Context；以[原PDF](https://www.esann.org/sites/default/files/proceedings/2021/ES2021-40.pdf)為本文題名，不把差異寫成不存在 |

上述勘誤在新研究交付稿與老師回覆中生效；不改sealed模型或覆寫歷史README、manifest、prediction。main／Albert文件的文字修正列為清楚的後續patch範圍，沒有直接覆寫PR #36所涉文件。

另外兩項關鍵未解：C13為Ancestor固定1ef4a891的論文轉錄（論文全文.md／html）缺參考文獻表，末節只指向原稿p.89；正文部分作者年分無法辨識。判定UNVERIFIED，不猜唯一論文或聲稱捏造。C14為Ancestor摘要約99.90%與本期跨馬達25%直接比較：資料角色、類別、表示與unknown評估不同，判定UNVERIFIED_COMPARISON；不能繼承原成績或計算純演算法下降。

## 全部清冊的未解界線

paper_catalog保留舊40筆B來源及新找到的出版／DOI／arXiv／作者來源。citation_occurrences逐筆保留ref、Git blob/file SHA、路徑、line/cell、source IDs及待判定狀態；非論文software、repo與schema另標，不把所有URL當論文。

未取得全文的書、付費文章、只有搜尋摘要的跨語言候選，以及README只有作者年分的Wang2008等，不能填SUPPORTED。王姓2008PHM雖有可能題名，但原文未給唯一ID，不能用猜測合併。多語言候選不是多語言演算法實測；不清除未解條目，不把全部候選自動改VERIFIED。

因此本輪可交付完整固定範圍清冊、核心六來源內容與重大主張勘誤，但#19的「全部內容相符」仍未驗收。保留OPEN，精確未解由catalog、search_log與unresolved索引追蹤。頁面403、SSL錯誤、429或沒有citation tags只表示取得受限，不作論文不存在的判決。未繞付費牆或停用TLS驗證。
