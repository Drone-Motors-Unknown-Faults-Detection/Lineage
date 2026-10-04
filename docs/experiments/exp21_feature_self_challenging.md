# 實驗21：有限表格特徵自挑戰與匹配遮蔽對照

2026-10-04，Asia/Taipei。先行手冊；L162已交付8dca5c0，18方法均FAILED。本批程式、正式fit及outer此時均0。方法受既有失敗啟發，全部資料已曝光，屬adaptive exploratory；本次事前固定不等於未接觸歷史test。

## 來源與假說

Zeyi Huang、Haohan Wang、Eric P. Xing、Dong Huang（2020），*Self-Challenging Improves Cross-Domain Generalization*，ECCV2020。[CMU正式出版資料](https://publications.ri.cmu.edu/self-challenging-improves-cross-domain-generalization)、[作者arXiv v1](https://arxiv.org/pdf/2007.02454v1)20頁完整本文／附錄／參考文獻已讀；[ECCV版](https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123470120.pdf)16頁只讀到文字行390，後段取得逾時，不冒稱兩版本均完整。兩版是同一論文，不計兩篇。PDF以文字公式核對，沒有宣稱完整圖像版面檢查。

原RSC Eq.1對true-class logit求feature梯度，Eq.2以signed gradient百分位遮掉主導feature，再反向更新CNN。不能改成gradient絕對值而仍稱原公式。作者碼[固定bf6d280c5d74910f009ea8963c59167252659666](https://github.com/DeLightCMU/RSC/tree/bf6d280c5d74910f009ea8963c59167252659666)之README、BSD-2-Clause LICENSE及Domain_Generalization/models/resnet.py完整已核對，未下載權重、複製程式或安裝PyTorch。新版碼有spatial/channel隨機選擇、true-class softmax下降排序、batch比例curriculum及strict ties，與本文最簡式不同；不照搬作者影像test選出的最佳比例或早停。

H21a：若少數train motor特徵支配配置分類，遮蔽主要貢獻後固定再訓練可能改善跨motor分類。H21b：若收益只來自一般遮蔽正則化，matched random mask會相近；若可用特徵有限或遮掉判別訊號，known train loss可能升高而test仍退步。原理論是二元、條件不變、loss增加與小步假設；本案六known類／三motor未證明這些假設，不宣稱理論泛化保證。

## 本專案的有限改編與固定參數

formal105唯讀；base75／harmonic69 train-only表示法／RobustScaler完全沿用exp20。每表示法重新fit同known train、三RPM等class ERM beta0作固定warm start；與exp20公式相同，只為獨立本批來源可重建。18個warm optimizer fit另計，不將重推當新實驗。之後每表示法四個fixed-horizon分類器：

- unmasked：相同200次full-batch SGD、相同loss／warm／learning rate，不遮蔽。
- random：每個train row用default_rng(seed)抽固定ceil(D/3) feature遮蔽。
- signed_gradient：以true-class logit signed gradient W_y遮固定ceil(D/3) feature；不取絕對值。
- contribution：以Z_ij W_yj排序，改編作者spatial activation×gradient想法到表格欄位。

每step對後三個方法，先建立每row候選mask，計算原／masked true-class softmax差，再依下降量由大到小選固定ceil(n/3) rows使用mask，其他rows維持全feature。exact stable descending rank處理ties，保留所有下降量的正負及非正比例；不clip掉負下降、不用cal/test挑fraction。random也使用同sample挑戰排序，因此是匹配feature遮蔽對照，非一般獨立dropout。signed gradient線性時在同一類不隨sample變化，必須在限制中說明。

改編與原文不同處：固定手工表示法不學CNN backbone；已知train-only ERM warm避免零初始化gradient全tie；exact ceil ties取代百分位可能全遮；固定1/3 feature、1/3 row、200步full batch，不使用作者epoch curriculum／空間channel隨機切換／Adam／test早停。masked輸入的ridge .001只罰W、bias不罰；weights=1/(3×6×n_RPM,class)，保留全部known train，不依test刪點。mask在更新時stop-gradient，只對masked CE求W/b gradient。

固定learning rate僅從known train算：
eta=1/(0.5×sum_i w_i(||Z_i||²+1)+0.001)。
這是多類softmax Hessian spectral bound的保守trace上界；遮feature不增加row norm。mask每step會變，這個上界不保證整個RSC流程收斂或test改善。200步後保存最後迭代，不挑最佳epoch；有限值為FIXED_HORIZON_COMPLETE而不是OPTIMIZER_CONVERGED。非有限／來源不符／缺RPM/class則INCOMPLETE，不改step數／fraction救成績。

inference用完整未遮蔽Z，只收feature array；不輸入query label、RPM、T-code或path。保存每step遮蔽筆數／欄位使用counts、完整mask history digest、true-class概率下降比例、CE／gradient／train RPM風險、learning rate與warm checksum。所有mask、loss、warm、選row僅known train；cal僅設固定detector threshold，unknown只test。

## 矩陣、用途、否證與驗收

2表示法×4training variants×3detectors×3fold×3seed=216評估、72fixed-horizon fit＋18ERM warm fit=90新分類器訓練程序。72個分類器供24方法共用，不把三detector算成三份classifier。seeds0／1／2；random有實際mask變異，其他流程可一致，seed SD不代表獨立motor。

fold0 train/cal/test=T1/T2/T3，fold1=T2/T3/T1，fold2=T3/T1/T2；healthy8screws＋known 1screws／2screws／3_14screws／3screws／4screws、unknown 4_146screws／5screws／6screws／7screws，既有fixed N=5 manifests全部不改。validation／selection空、歷史exposure保留；不重新洗牌使它變fresh。

三detectors固定原C02 base75 Maha-LW／k-NN factory，以及MSP 1−max softmax、known cal pooled linear q95、strict raw>q；零q直接raw比較不除零。Maha／k-NN reference不因classifier改動而改變，以隔離分類器；MSP原文及既有實作見exp20，不加入未知fit、temperature或threshold search。Controls仍C02、C17、C24、D01；同表示法／同detector下每masked variant與unmasked做配對，再以signed_gradient及contribution各對random比較。96外部control pairs＋18unmasked pairs＋12random pairs=126方法pairs，三fold三seed=1134配對；無global winner。

原CONTRACT、完整健康總誤報、最差class recall、unknown保護及coverage都不降低；只有既有N=5一組，通過也需後續已預定的多subset／壓力驗證，不能立即宣稱R2。raw/session/window/cleaning證據仍UNKNOWN，fresh與每類2個獨立test group仍INCOMPLETE。若只增加unknown但healthy誤報爆增或class仍collapse，判FAILED。

測試先覆蓋signed而非abs、貢獻／random及全ties手算、exact count、mask不反向傳遞、解析masked CE gradient、weighted risk、單step可手算、warm來源／config／seed拒絕、random決定論、q0、unknown/cal/test用途、actual重fit與重封篡改、來源alias與舊factory/default回歸。兩native小測試／full acceptance／pip check與CLI smoke先完成；synthetic不能當研究分數。outer前精確protocol／SHA及actual known來源proof逐階段commit/push。

## 路徑與執行

| 範圍 | 路徑 |
|---|---|
| 新公式 | core/fault_type_self_challenging.py |
| 新實驗 | experiments/fault_type_self_challenging.py；run(...)／main()：lock、fit、source-verify、evaluate、verify、report、smoke、backup |
| 新測試 | tests/test_fault_type_self_challenging.py、tests/test_fault_type_self_challenging_runner.py |
| 唯讀共用 | core/fault_type_risk_extrapolation.py beta0、LiteratureRepresentation／NoveltyReference、core.openset、exp20來源／封存機制與最新alias guards |
| 來源／結果 | reports/feature_self_challenging_v1/，先行source card／adaptation、後續實測與SHA索引 |
| 日誌／輸出 | core.logger.setup_run；logs/fault_type_self_challenging_*/、output/fault_type_self_challenging_*/ |
| 大型產物 | D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-04/feature_self_challenging_v1/workspace/output |

先手冊commit/push，再core與公式測試commit/push，runner驗收commit/push，精確protocol commit/push，known fit及來源proof commit/push，216outer／逐筆重推／report／備份／交付。每action1800秒、C槽保留1GB；same config checkpoint可接續，不覆蓋舊sealed模型、ZIP或predictions。282筆無關刪除不stage；formal105／linear／Maha-LW預設、k-NN切換、PolarMap不改。

CLI預定在工程完成後核對：
```powershell
.venv310/Scripts/python.exe -m experiments.fault_type_self_challenging smoke
.venv310/Scripts/python.exe -m experiments.fault_type_self_challenging lock --parent-protocol output/fault_type_discriminative_prototypes_lock/2026-10-03-15-23-33/protocol.json
```
本手冊沒有尚未執行的分數；actual timestamps與完整sealed sources由execution_log接續。
