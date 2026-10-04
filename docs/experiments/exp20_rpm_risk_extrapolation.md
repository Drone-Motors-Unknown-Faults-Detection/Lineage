# 實驗20：訓練 RPM 風險差異與固定 softmax

2026-10-04，Asia/Taipei。先行手冊：K27分類器已fit，actual known來源重建正執行，尚未執行K outer。本批不依K test成績挑表示法、beta或拒絕器。手冊先提交後才能新增實作；這裡的預期不包含未執行的成績。

## 原始來源與可反駁假說

David Krueger、Ethan Caballero、Joern-Henrik Jacobsen、Amy Zhang、Jonathan Binas、Dinghuai Zhang、Remi Le Priol、Aaron Courville（2021），*Out-of-Distribution Generalization via Risk Extrapolation (REx)*，ICML38，PMLR139:5815–5826，[正式來源](https://proceedings.mlr.press/v139/krueger21a.html)。已讀12頁本文及18頁補充；Eq.8以訓練環境風險的差異作懲罰，補充Eq.27–30給出population variance。本文的DomainBed比較沒有穩定優於ERM，異質目標雜訊也可能讓REx失敗；這些反證保留。

[原作者程式](https://github.com/capybaralet/REx_code_release/tree/47dfb3a2f93a195389a9c933a66482eee455c720)之colored_mnist/main.py／README及InvariantRiskMinimization/LICENSE已讀：該子目錄CC BY-NC4.0，兩環境平方風險差、sum loss及Adam／waterfall。本批未複製或執行其程式。[DomainBed固定版本](https://github.com/facebookresearch/DomainBed/tree/b93c22a1cfc3b2428398272c1a116c8de1f4139e)的VREx類別、README及MIT LICENSE已核對：使用mean risk＋population variance。本批依公式以NumPy／SciPy獨立實作，沒有下載影像資料、安裝PyTorch、照搬test選擇或sweep。

Dan Hendrycks／Kevin Gimpel（2017），*A Baseline for Detecting Misclassified and Out-of-Distribution Examples in Neural Networks*，ICLR2017，[作者12頁v3](https://arxiv.org/pdf/1610.02136v3)，全文核對。只採最大softmax分數作對照，沿用本專案已有的1−MSP方向；高softmax不等於可靠信心，沒有複製作者神經網路或auxiliary decoder。

H20a：訓練motor內不同RPM的分類風險差異若源於可減少的特徵依賴，固定REx懲罰可能改善跨motor配置分類。H20b：若差異源於工況本身的不可約雜訊，懲罰會拖累容易工況或造成常數分類。本批會保存各known train RPM風險、類別recall、gradient與收斂狀態。RPM變化是否代表motor／年齡變化仍UNKNOWN，不能宣稱找到因果特徵。

## 資料、方法與本專案改編

formal105唯讀；固定沿用base75與harmonic69兩種LiteratureRepresentation，僅fit該fold known train。harmonic69的harmonic band maxima正規化、幅度floor及RobustScaler不改；它不等於order tracking或原始FFT重建。既有105／linear／Maha-LW正式預設、k-NN切換及PolarMap保留。

每fold只有一顆train motor：healthy8screws＋known 1screws／2screws／3_14screws／3screws／4screws。known train的6000／8000／11000rpm是三個風險環境，不是三次獨立採集；RPM只供fit損失分組，predict輸入只有特徵，不加RPM／T-code／path／label編碼。三motor角色保持fold0 T1/T2/T3、fold1 T2/T3/T1、fold2 T3/T1/T2（train/cal/test）；known cal僅設拒絕門檻，unknown四配置只進test。selection／validation空；historical exposure不清除。

固定六個分類器：2表示法×beta0／1／10。logits=XW+b，六類softmax；每RPM先對六known類別各自平均cross-entropy，再等權平均類別，得到R_e。任一RPM缺known類別標INCOMPLETE，不由cal/test補樣本。

本專案目標明列為 mean_e(R_e)＋beta×mean_e((R_e−mean_e R_e)^2)＋0.001/2×sum(W^2)。bias不加ridge。類別等權、線性softmax、ridge與CPU L-BFGS是本站改編，沒有照搬作者深層影像網路；mean風險取代原Eq.8的sum時，beta數值尺度不同，不把1／10稱為原論文最佳值。三環境時不能拿作者兩環境平方差係數直接代入。

每表示法先用W=b=0，beta0訓練ERM；beta1／10各從同一已收斂ERM狀態起跑。L-BFGS-B固定maxiter1000、gtol1e-6、ftol1e-10、maxls50、maxcor10、解析gradient；不使用cal/test早停或調waterfall。本批沒有annealing選擇，warm start是事前固定的train-only操作。非有限、未收斂或gradient／用途驗證失敗保留INCOMPLETE，不延長iterations或偷換beta。seed0／1／2完整保留；無隨機init時結果應一致，不能將重複預測報成三個獨立motor。ERM共18次optimizer fit、REx共36次，共54分類器／optimizer fit；source replay不計新研究fit。

每分類器配三個固定拒絕器：原C02/base75 factory Maha-LW與k-NN（k5、confidence.95、已封存train reference／known cal）作分類器消融，及沿用既有NoveltyReference的MSP對照。MSP只用該分類器的predict_proba，raw=1−max p；pooled known-cal linear q95，strict raw>q拒絕，threshold為0時不除零，不fit溫度或校準概率。三種拒絕器共用同一分類器，不重複計分類器fit。2表示法×3beta×3拒絕器×3fold×3seed=162評估；保留全部方法，不產生global winner。

## 預期、驗證及否證

原CONTRACT不降低：known faulty F1／accuracy、各motor及RPM healthy total alarm、未知召回與最差類別recall一起核對。REx消融固定同表示法／同拒絕器的beta0；controls仍C02／C17／C24／D01，不選新的有利control。只跑固定N=5一組，不能宣稱R2多subset／stress或126組已完成。所有28,910筆已曝光，研究為adaptive exploratory，fresh guard仍INCOMPLETE。

新增測試須覆蓋：手算risk均值／population variance、解析gradient有限差分、lambda0等於等RPM／等class ERM、重複某格樣本不改該格權重、三環境而非兩環境係數、warm start源於同known train、unknown／cal/test進fit拒絕、缺RPM或類別INCOMPLETE、NaN／overflow／zero-q／tie、不以query RPM或truth推論、source/config/model/coeff/manifest/prediction SHA與重新封checksum篡改、fit/cal分離、重新擬合重現、factory及原default回歸。actual-source需重建表示法、full known RPM/y/features、ERM與REx optimizer、MSP cal及父factory，保存input ID／source SHA／loss／gradient／耗時；來源proof提交後才outer。

保存逐筆test IDs／motor／RPM／truth／pred／score／threshold／reject／model SHA，source前後SHA、全seed結果、各motor/RPM／類別coverage、balanced accuracy／F1／AUROC／AUPR／prevalence／healthy總誤判、完整分母的final fault F1與配對差異。REx若只降低train variance但跨motor退步，記FAILED；不能以train loss較平整宣稱更可靠。

## 影響範圍與執行入口

| 範圍 | 路徑及責任 |
|---|---|
| 新公式 | core/fault_type_risk_extrapolation.py；等RPM／等class風險、softmax、解析gradient與train-only warm start |
| 新實驗 | experiments/fault_type_risk_extrapolation.py；run(...)／main()，lock、fit、source-verify、evaluate、verify、report、smoke、backup |
| 新測試 | tests/test_fault_type_risk_extrapolation.py、tests/test_fault_type_risk_runner.py |
| 只讀共用 | core/fault_type_literature.py的表示法／MSP、core.openset factory、最新用途／來源／alias guards、舊protocol／manifests／controls |
| 文件 | reports/rpm_risk_extrapolation_v1/、docs兩索引 |
| 執行輸出 | core.logger.setup_run；logs/fault_type_risk_extrapolation_*/及output/fault_type_risk_extrapolation_*/ |
| 大型產物 | D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-04/rpm_risk_extrapolation_v1/workspace/output/ |

先行手冊commit/push，實作與synthetic小測試，再兩Python完整acceptance／pip check與CLI。工程commit/push後lock精確參數／source SHA；protocol commit/push後fit，來源重建commit/push後才162評估及逐筆re-infer。每action1800秒、C槽保留1GB，若不足保留同設定checkpoint與INCOMPLETE。大型模型／predictions依已有archive／fixed_delivery逐member SHA／CRC核對，Git只保存compact摘要／索引；不覆蓋舊ZIP，不stage282筆無關刪除或formal資料。

2026-10-04工程接續：CLI help及smoke已在兩native環境通過；以下入口存在，尚不代表formal162評估完成。協定封存前先提交工程驗收證據，精確run timestamp／SHA記execution_log。

```powershell
.venv310/Scripts/python.exe -m experiments.fault_type_risk_extrapolation smoke
.venv310/Scripts/python.exe -m experiments.fault_type_risk_extrapolation lock --parent-protocol output/fault_type_discriminative_prototypes_lock/2026-10-03-15-23-33/protocol.json
# lock、source-verification、evaluation實際路徑以本輪輸出及execution_log為準；不可指向歷史另一批。
```

原論文／作者程式／獨立改編與本輪實測分開記錄。source replay會獨立重跑同known train ERM／REx，成功與失敗的optimizer狀態都要一致；來源重建不計入54次新研究分類器fit。
