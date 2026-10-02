# Lineage：文獻方法、係數改編與實測結案

產出：2026-10-02，Asia/Taipei。**有局部改善；沒有找到全面可靠的最佳模型。** 本輪已實作、測試、正式執行與逐筆驗證，不只提出候選清單。所有結果都是已曝光資料的探索性比較，正式預設未替換。

## 一、結論先看

所有下列百分比均為三顆test馬達等權平均、每顆取三個seed均值，不挑最佳seed。pp表示百分點，不是相對增加百分比。

| 比較面向 | 同條件75維linear基線C02 | 本輪結果 | 解讀 |
|---|---:|---:|---|
| healthy＋5 known配置accuracy | 34.15% | C17：39.29%，+5.13pp | 新表示法＋LDA確有局部提高 |
| 只看已知fault配置accuracy | 26.61% | C17：30.43%，+3.82pp | 不把healthy容易分的貢獻冒充fault改善 |
| fault balanced accuracy | 26.78% | C17：30.80%，+4.02pp | 仍偏弱，非可信診斷達標 |
| fault macro-F1 | .2404 | C17：.2852 | 改善但仍有類別零召回 |
| 歷史／本輪最高fault-only accuracy | — | C24/A7：30.91% | C17未超過已存在的RPM分開LDA；不能說創下全指標新最佳 |
| unknown AUROC | C02/M：.5746 | R09 Isolation Forest：.6043 | 最高排序不等於最好操作點或全流程 |
| unknown recall | C02/M：18.44% | R18：22.68%，+4.24pp | 健康unknown-FPR由0升至9.49%；不可只報召回提升 |
| 最終含unknown分類accuracy | C02/M：24.85% | R18：30.62%；C17/M：27.14% | R18有誤報代價；兩者均不足以證明可部署 |

`M`=正式factory Mahalanobis–LW，`K`=正式factory k-NN。C17/M的unknown recall只有8.44%，比C02/M的18.44%低；**已知分類改善不等於未知偵測改善**。C17/M觀察到的健康unknown-FPR為0，但T1的健康classifier recall只有68.42%：31.58%健康樣本被分成已知fault。既有`healthy_safety.false_positive_rate`只計healthy被拒為unknown，不包含被classifier分成known fault；這兩種錯誤必須分開讀。

完整24個classifier pipelines、70個classifier/score組合、每motor、每seed與每配置的表：[全部方法比較](../../output/fault_type_literature_report/2026-10-02-12-26-09/report.md)。lossless compact summary含逐RPM、每類support/recall與confusion matrices；絕對路徑／SHA見[result_index.json](result_index.json)。沒有selected_representation/global_winner/deployment winner。

## 二、實際做了多少，不把重複資料當新實驗

固定protocol `literature_expansion_v1_fixed_no_selection`：24 pipelines×2官方detectors＋22額外score variants，3motor folds×3seeds，**計畫630格，實際624完成、6格INCOMPLETE**。正式保存並逐筆核驗6,013,647個prediction records，仍只有28,910個unique樣本、90CSV；資料指紋c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d未變。

9個實體bundles共享234次classifier node fit、81次representation fit、180次factory reference fit。174個額外score物件建立／校準含不需額外統計fit的MSP/entropy，不是174個獨立訓練資料集。physical bundle fit合計169.748秒；fit 12:01:19–12:04:42，evaluate 12:09:14–12:16:07，重推論verify 12:16:33–12:24:15。這是批次成本，含稽核與I/O，不是串流警報延遲；沒有量測峰值記憶體。

R17在fold0/T3與fold2/T2各三seeds缺少某些classifier-predicted calibration groups，六格保留NA/INCOMPLETE、沒有fallback。T1三格可以計算，但recall仍0、健康unknown-FPR5.15%；不能只報T1三格當完整三motor方法。全部失敗原因留在lock/evaluation/verified/summary。

歷史2490次N-sweep／126組N=5沒有全量重跑；先前198次方法研究只讀summary作控制。C02/A0與C24/A7四組控制的18項平均指標全部相同（差值絕對值<1e-12）。舊A1的`rpm_strategy=separate`，A7共用的是per-RPM A1 reference；共享模型不等於RPM混合。先前誤認mixed的報告解讀已撤回並記在execution log，未改模型追求重現。

## 三、比較的演算法與來源

31項書目逐篇列作者、年份、刊物／會議、原始連結、使用／改編／未測範圍：[28项封存來源](sources.md)、[3項補充來源](sources_addendum.md)。查核書目與方法重點，不宣稱31篇全文逐字通讀，也不把論文別的資料集成績移植到馬達資料。

| 類別 | 本輪實測ID | 原來源／實作與固定參數摘要 |
|---|---|---|
| 多類linear baseline | C02 | Cox1958為基礎來源；既有sklearn多類LR C1、balanced、lbfgs1000，不是二元原文精確重現 |
| LDA與shrinkage變體 | C01、C13–19、C24 | Fisher1936 Gaussian判別延伸；lsqr、uniform priors，auto或固定.1/.5/.9 |
| Extremely Randomized Trees | C03 | Geurts/Ernst/Wehenkel2006；200樹、depth12、leaf5、sqrt、balanced |
| Random Forest | C04、C21 | Breiman2001；同固定樹參數，原75與harmonic69對照 |
| Histogram Gradient Boosting | C05 | Friedman2001思想、sklearnhist實作；.05、200iteration、15leaves、l2=1、無內部early stopping選參 |
| RBF SVM | C06、C22 | Cortes/Vapnik1995；C1、gamma scale、balanced，兩表示法 |
| 距離加權k-NN分類 | C07、C08、C20 | Cover/Hart1967基礎；5/15NN，Euclidean、distance weights；C20另做NCA |
| Gaussian Naive Bayes | C09 | John/Langley1995中的Gaussian對照，不是其kernel proposal；uniform priors、var_smoothing1e-9 |
| RDA-inspired本站改編 | C10–12、C23 | Friedman1989來源；見下一節，非原論文scatter權重完全重現 |
| PCA20／NCA10 | C19／C20 | Pearson1901／Goldberger等2004；fit train-only，NCA每類最多60個train row、共360、max_iter50 |
| factory Maha／k-NN與鄰居數 | 全部C×M/K、R07/R08 | Ledoit/Wolf2004與既有core.openset；k1/5/15，known-cal .95，未重寫另一套factory |
| pooled／relative／OAS／diagonal／雙中心距離 | R01–06、R13、R18 | Lee等2018、Ren等2021、Chen等2010、MacQueen1967與LW組合；tabular adaptation |
| Isolation Forest／LOF／OCSVM／class GMM | R09–12 | Liu/Ting/Zhou2008；Breunig等2000；Schölkopf等2001；Dempster等1977 EM。固定known-train，獨立known-cal q95 |
| 信心／entropy／margin | R14–16 | Hendrycks/Gimpel2017、Shannon1948；使用LDA posterior，非深網重現 |
| predicted-label calibration／融合 | R17、R21/22 | 本站改編LW／MSP組合；固定.25/.75，不從test選權重 |
| Energy／ViM | R19/20 | Liu等2020／Wang等2022；actual LDA logits與線性子空間adaptation，不是原deep training |

本輪正式研究有六種表示法：base75、signed66、harmonic69、harmonic66、PCA20、NCA10；base66另有工程測試與歷史研究，沒有冒稱本輪新增一個standalone base66 arm。資料層輸入仍105維，沒有改正式CSV欄位。

未實測：LMNN、OpenMax、DeepSVDD、raw CNN/TCN、wavelet/STFT/order tracking、transductive CORAL、RUL。原因分別是沒有相應已驗證求解／deep activation契約、現有資料不是可證實原始時序、或需要test batch covariance而違反目前inductive協定。這不是「都測過但不好」，也不是不適用於所有未來資料。

## 四、我改編了哪裡，係數試了哪些版

所有版在本輪test前寫入protocol；參考了已曝光歷史結果，因此不是盲測。實作位置為`core/fault_type_literature.py`及`experiments/fault_type_literature_registry.py`；函數級來源也列於sources.md。

1. `LiteratureRepresentation._raw/fit`：三軸各10個歷史FFT band maxima改為`abs(maxima)/sum(abs(maxima))`，floor由train估計；保留36個非冗餘統計，再加每軸`log1p(sum/floor)`，得到C17的69維。C18只保留66維、不加幅值，是固定消融對照。不是新能量特徵、不是order tracking。C17 vs C18的fault accuracy30.43% vs25.83%、healthy+known39.29% vs33.83%；表示「保留幅值有幫助」的探索性證據，不是物理因果證明。C01同LDA/75為16.25%與22.98%；分類器同條件下新表示法局部有效。
2. `BlendedDiscriminant.fit/decision_function`：先`(1-pooling)S_class+pooling*S_pooled`，再以shrinkage縮向`trace(S)/D * I`；完整Gaussian logdet＋二次項、uniform prior。四版(pooling,shrinkage)=(.5,.1)、(.5,.5)、(0,.1)、(1,.1)。最佳這族C11 fault accuracy26.12%、healthy+known32.83%，未贏C02；其餘也如實保留。直接凸組合ML covariance，不冒稱Friedman原lambda參數化。
3. `classifier`的LDA shrinkage .1/.5/.9：fault accuracy15.74%／23.98%／27.69%；.9仍未超過歷史C24的30.91%，healthy+known29.71%也低於C02。沒有因此把正式LW替換成.9。
4. `NoveltyReference.fit/raw`的relative score：`min_class MD² - λ*background MD²`，兩個reference都fit known train，cal僅定q95。原來源Ren2021；λ=.5/1/2三版的AUROC .5643/.5901/.4714、unknown recall13.37%/14.51%/8.80%；λ=2健康unknown-FPR15.65%。λ=1比pooled-only R01的AUROC .5579、recall11.47%好，但未全面勝過正式逐類Maha。R18另改用harmonic69＋λ1；與C17/M同classifier，純比較score也不是偷偷換最佳分類器。
5. R13將每類單中心改成2個train KMeans中心，接pooled precision；結果AUROC .5574，沒有改善R01的.5579。R05換OAS、R06換diagonal；全結果表保留，不假稱每個修改都有效。
6. R17以classifier predicted class路由cal分组，不用true test class路由；六格缺組被拒。R21/22用known-cal median/IQR固定尺度融合Maha與1−MSP，距離權重.25/.75；AUROC .4902/.4900、recall均4.49%，失敗。不得從test重新選較好的權重。
7. R19/20把原Energy/ViM深網分數改用實際LDA affine logits、ViM主空間rank20與train alpha；AUROC .4677/.4952、recall1.95%/7.92%，本資料不支持採用。signed scores直接`raw > q95`，不除負門檻；數學/來源/保存預測已測試，不用翻轉符號救分。

NCA本輪9個optimizer各3–10iterations，沒有觸及50iteration預算；但只使用360個分層train row，沒有宣稱全資料全域最優或完整論文重現。正式fit warnings為空。

## 五、三顆馬達與九個工況，不只看平均

三顆馬達各有6000／8000／11000rpm：9工況是motor×RPM，不是9fault causes。

| test motor | 所有test / known / unknown | C02 fault accuracy | C17 fault accuracy | C17 healthy+known accuracy | C17/M recall | R02 recall / healthy unknown-FPR | R18 recall / healthy unknown-FPR |
|---|---|---:|---:|---:|---:|---:|---:|
| T1 | 9759 / 5935 / 3824 | 34.67% | 32.91% | 38.84% | 0% | 8.03% / 0% | 15.35% / 17.76% |
| T2 | 9857 / 6007 / 3850 | 22.07% | 28.88% | 38.37% | 13.22% | 18.86% / 0% | 11.14% / 0% |
| T3 | 9294 / 5604 / 3690 | 23.10% | 29.50% | 40.65% | 12.09% | 16.64% / 0% | 41.54% / 10.72% |

C17並未改善每顆motor：T1的known accuracy從45.48%降至38.84%，fault-only也降。C17的2screws classifier recall三motor均0；T2的3screws也是0。不能用平均39.29%宣稱所有配置可以辨識。

| motor/RPM | test樣本数 | C17 fault accuracy | C17/M unknown recall | R18 unknown recall | R18 healthy unknown-FPR |
|---|---:|---:|---:|---:|---:|
| T1/6000 | 3358 | 42.89% | 0% | 11.63% | 52.81% |
| T1/8000 | 3049 | 38.19% | 0% | 0% | 0% |
| T1/11000 | 3352 | 18.12% | 0% | 33.67% | 1.96% |
| T2/6000 | 3189 | 1.22% | 0% | 0% | 0% |
| T2/8000 | 3250 | 26.91% | .17% | 4.70% | 0% |
| T2/11000 | 3418 | 57.60% | 34.68% | 25.58% | 0% |
| T3/6000 | 2941 | 48.73% | 0% | 31.98% | 7.96% |
| T3/8000 | 3225 | 40.23% | 0% | 20.38% | 0% |
| T3/11000 | 3128 | .56% | 36.23% | 73.19% | 23.33% |

這些C17/R18是確定性三seed相同的實值；不報虛構變異。Isolation Forest的T2/11000rpm健康unknown-FPR達100%（三seed均值），即使其全motor AUROC最高仍有不能忽略的局部失敗。全部方法每seed及其他指標在summary；seeds SD不是motor母體信賴區間。unknown prevalence各motor約39.1%–39.7%；PR指標須連同此比例解讀。

## 六、T1零召回的只讀失敗分析

固定fold1=train T2、cal T3、test T1。diagnosis只讀封存模型，13固定方法×9bundles×train/cal/test共351個分布集合，不是351組新研究runs；不掃threshold/k/feature subset，不修改本輪結果。

- **工程錯誤未發現**：unknown3824的四label為4_146screws1028、5screws874、6screws944、7screws978；truth/score direction/finite/strict >以及保存來源均通過。C02/M的全部T1 score最大.956730<1，unknown四組最大.596/.569/.593/.437，所以0召回是實際計算結果，不是NaN或報表漏算。C17/M全部T1最大.901414<1，仍0召回。
- **排序不足有支持**：C02/M的T1 AUROC .5074、C17/M .5033，接近隨機排序；只降低threshold不能同時保證未知召回與健康安全。R02的T1 AUROC .5448、recall8.03%；R18的AUROC .4812、recall15.35%，更多拒絕伴隨17.76%健康拒絕，不是更好的排序。
- **跨motor分布／calibration transfer有支持**：pooled R01同一train reference下，健康raw squared distance median由T2 train36.76變成T3 cal585.06、T1 test1076.55；known-cal q95=6124.64，而T1四unknown最大3039.62／3557.54／4677.34／3532.10都小於它。閾值位置與跨motor尺度漂移同時存在，但不能將尺度差直接歸因老化、安裝或單位。
- **背景扣除只局部有用**：R02 λ1 cal q95=1160.91；T1的5screws recall34.44%、6screws .64%，另外兩unknown仍0，合計8.03%。R18 q95=730.51，T1健康median617.15、max854.98，造成17.76%被拒；T1/6000還達52.81%。因此不能只展示有被抓到的一類。
- **特徵重疊／方法限制有支持但非唯一因果**：多個模型同時有class零召回、未知/known排序接近隨機；band比例與背景扣除可以改變部分工況，沒有消除所有motor/RPM失敗。未知也可能落在某已知配置的特徵支持範圍；沒有原始錄製邊界／感測器真值，不能確定是哪一物理原因造成重疊。
- **UNKNOWN**：session/run、原始視窗重疊、刪點/IQR遮罩、時間、實測取樣率、單位、感測器方向/校正/安裝與負載、實際年齡使用時數。只有三顆不同motor，不能串成同一顆退化生命週期；不算每小時誤報、警報延遲、退化百分比或RUL。

尚未實作驗證的下一輪最多兩案：①以固定兩分支classifier/detector組合，維持同來源role audit且預先鎖定，再做探索性比較；②用已知train的class-conditional feature/score標準化處理不同RPM幅值，預先固定公式並保留故障幅值對照。不能把這兩案算成本輪改善或用T1 threshold掃描取代驗證。

## 七、有效性、老師建議與驗收分類

| 項目 | 狀態 | 已做／仍有限制 |
|---|---|---|
| healthy＋5known／4unknown實測 | VERIFIED（工程／執行） | 本輪固定主配置624格實跑；全126組／其他N本輪未重跑，歷史實驗保留 |
| train/cal/test用途與無global selection | VERIFIED | fold0=T1/T2/T3；fold1=T2/T3/T1；fold2=T3/T1/T2；validation與selection空；三用途motor不同 |
| train-only scaler/embedding/classifier/reference | VERIFIED | 234node audits，known-cal只設固定score門檻；unknown開發rows unused；cal不進reference fit |
| test ID、來源SHA、預測與指標 | VERIFIED | 624格、6013647 records逐筆重推論與重算；paired test IDs相同 |
| 可辨識所有已知配置／所有工況 | FAILED | accuracy仍低、2screws等零召回、RPM .56%與1.22%等失敗；沒有可靠最佳winner |
| 每類至少兩個獨立test groups | INCOMPLETE | 每fold只有一顆test motor；沒有降低guard門檻換PASS |
| 真正fresh final test | INCOMPLETE | 全28910歷史曝光；重新seed/另存檔/新方法不變fresh |
| 原始採集／window／清理獨立性 | UNKNOWN | 無可證實證據就不填PASS，不要求不存在的硬體作本輪前置條件 |

老師問題1：**類別配置、隨機其他N的既有入口與實驗已完成／本輪主配置已實測；可信fault type仍未達成。** 9 faulty labels主要是同一螺絲鬆動机制的配置，不是9項已確認物理故障原因。老師問題2：**切分依据與用途漏洞處理已完成；來源獨立性與test群組數仍部分完成／無法確認。** 「不完整」不是單一錯誤：用途依賴、本輪缺校準群組、工況分類失敗、test motor數、raw鏈與歷史曝光要分開。

能支持現有三motor的探索性跨motor比較；不能支持廣泛泛化、5%固定FPR保證、獨立盲測、量化老化或RUL。

## 八、工程交付與重現

science runtime Python3.10.19/sklearn1.7.2；compatibility Python3.14.6/sklearn1.9.1。最後完整驗收各**310 passed／0 failed**，pip check PASS、21 CLI help PASS；各runtime自己的synthetic630/630、0失敗，226800保存預測重推論PASS，不跨runtime載入joblib。38項新增工程測試涵蓋表示法、係數／分數公式、unknown與用途、cal-reference防洩漏、來源／score／config tamper、只讀診斷及歷史控制。

工作樹：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`。分支：`research-improvements-20260920`。分階段commit/push紀錄見[execution_log.md](execution_log.md)及result_index；不force push、不stage原90CSV、private資料或282個原有tracked deletions。

原正式105維／linear／Maha-LW、binary detection與PolarMap未改，factory kNN仍正式可切換。新實驗／版本與歷史manifests/models/reports分開，預設沒有被研究最高分自動替換。

8份新版本ZIP位於`D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-10-02\literature_expansion`，whole ZIP SHA、CRC、1935來源members SHA均PASS。保留原檔、不覆寫舊研究ZIP；D槽同機副本不是異地備援。Git保存1.3MB compact summary、3.2MB compact verified與small logs/protocol/lock/index，89MB full verified／50MB readable summary／625個prediction artifacts／models/audits由外部版本包可追溯。

逐項絕對路徑、檔案SHA、seals、失敗格、runtime驗收、archives與verified backup索引：[result_index.json](result_index.json)。執行指令、恢復界線：[reproduction.md](reproduction.md)。報告的最高分是事後描述，不是部署選擇；缺採集證據仍UNKNOWN，不要求重新提供不存在的motor。
