# 實驗19：三軸排列不變核與固定 SVM

2026-10-03，Asia/Taipei。先行手冊：exp18正在執行outer，尚未讀其成績。本批沿用全部固定controls，不依J結果挑分類器或threshold。

## 來源與可反駁假說

Bernard Haasdonk／Hans Burkhardt（2007），*Invariant Kernel Functions for Pattern Analysis and Machine Learning*，Machine Learning 68:35–61，DOI[10.1007/s10994-007-5009-7](https://doi.org/10.1007/s10994-007-5009-7)，[作者32頁稿](https://lmb.informatik.uni-freiburg.de/papers/download/ha_bu_MachineLearning6807.pdf)。全文已核對；Eq.2及Proposition11給出transformation integration kernel，均勻有限群的雙平均保留base kernel的正定性及排列不變性。論文另列IDS kernel；最小變換距離代入可能產生不定核，本批不採IDS或事後eigenvalue clipping。

Corinna Cortes／Vladimir Vapnik（1995），*Support-vector networks*，Machine Learning20:273–297，[DOI10.1007/BF00994018](https://doi.org/10.1007/BF00994018)。使用既有scikit-learn SVC／libsvm的precomputed接口，未複製作者程式。Haasdonk的MATLAB KerMet-Tools舊作者網址本次無法開啟，程式／授權UNKNOWN；不安裝或執行該工具。核函數以既有NumPy／SciPy獨立實作，SVC參數逐項封存。

歷史G／H／I顯示，多種距離與RPM條件原型仍有跨motor配置混淆及healthy錯判。H19a：把三個軸的排列當作有限nuisance，可減少同類跨motor特徵排列差異。H19b：完整排列不變也可能抹掉螺絲位置資訊，故保留無不變及半權重配對。實際感測器方向／安裝仍UNKNOWN，不能用本批分數證明曾換方向。本批不聲稱任意三維旋轉不變；105維統計量不足以重建旋轉後訊號。

## 方法、資料與固定參數

原formal105唯讀，研究表示法取既有VIBRATION66：每軸25欄去除三個已確認冗餘項，保留每軸22欄；冗餘關係只在known train檢查。將known train三軸堆成(N×3,22)，對同一物理特徵共用RobustScaler（with_centering=true、with_scaling=true、quantile_range=[25,75]、unit_variance=false），再還原66維。此共用尺度與軸置換交換；禁止先各軸獨立標準化後宣稱相同物理置換。

base kernel為exp(−gamma×平方Euclidean距離)，gamma=1/66，無資料選參。S3六種axis-block排列均勻平均：K_TI(x,y)=sum_g K_base(x,g(y))/6；因base RBF對共同排列為isometry，等於36項雙平均（測試比對兩式）。K_alpha=(1−alpha)K_base+alpha K_TI，alpha固定0／0.5／1。凸混合是本專案改編，非論文原調T大小策略；alpha=1才具有完整排列不變。不得將核對角強制改成1；TI核的自相似可能小於1。

三個固定分類器均SVC：C=1、kernel=precomputed、degree=3、gamma=1/66（precomputed接口不消費gamma）、coef0=0、shrinking=true、probability=false、tol=0.001、cache_size=200MB、class_weight=balanced、verbose=false、max_iter=100000、decision_function_shape=ovr、break_ties=false、random_state=seed。訓練使用全部known train；核矩陣及支持向量只參照train。fit_status非0或ConvergenceWarning記INCOMPLETE，不用cal/test補fit或放寬max_iter。概率未啟用，不做內部probability交叉驗證。

每分類器配三種固定拒絕器：

- 原factory Mahalanobis-LW與k-NN(k=5、confidence=.95)，讀原C02 base75已封存train reference／known cal狀態，隔離分類器改動；不重寫factory行為。
- 本專案RKHS class-centroid改編：d_c²(x)=K(x,x)−2 mean_train_c K(x,z)+mean_train_c,c K(z,z')。只用train建六個中心；分數為min_c d_c²，pooled known-cal linear .95分位數q；strict raw score>q拒絕。不由true query label或predicted query label挑中心／threshold。平方距離只容許浮點誤差−1e−10至0歸零，更負或非有限拒絕，不能修補不定核。保存raw score與q，零q不除零。

共3alpha×3detectors×3motor folds×seeds0/1/2=81 detector評估，27分類器fit。工況／N=5已知五配置、unknown四配置、known healthy、來源fingerprint／exposure與歷史manifests不變。角色fold0 T1/T2/T3、fold1 T2/T3/T1、fold2 T3/T1/T2（train/cal/test）；selection/validation空，不產生global winner。全部28,910筆已曝光，本批為adaptive exploratory；不稱fresh或R2完成。

核矩陣以128列block計算，避免建立(N,6,N,66)巨型tensor；只在已知訓練建立完整Gram，query分block infer。每action1800秒、C槽保留1GB，D槽保存模型與逐筆產物。若超時／資源不足保留checkpoint與INCOMPLETE，不暗改candidate／sample cap。所有seeds完整保存；確定性結果相同照實報告。

## 預期與驗證

支持須通過原CONTRACT：known faulty分類F1／accuracy配對提升、逐motor/RPM healthy total alarm保護、未知召回非劣性及最差類別召回，不以較高accepted accuracy或單motor成績取代。alpha0/0.5/1為固定消融；若full invariance使位置配置混淆更大，記FAILED並保存反證。

測試共用尺度置換交換、六項／36項核相等、對稱與小型Gram PSD、alpha0退回RBF、alpha1獨立置換不變、核自相似不強制1、centroid手算、q0／empty／NaN／overflow、fit樣本與cal分離、unknown用途拒絕、來源／manifest／config／model／prediction SHA tamper及逐筆truth mutation。source-verify重建actual known train/cal核、scaler、支持向量來源與centroid／quantile，再提交證據後outer。完整兩Python回歸與pip check／CLI，synthetic smoke不作研究分數。

## 影響範圍與入口

| 範圍 | 路徑／責任 |
|---|---|
| 新共用公式 | core/fault_type_axis_kernel.py，共用軸尺度／PSD群平均／固定SVC／centroid |
| 新實驗 | experiments/fault_type_axis_kernel.py，run(...)及main()；lock／fit／source-verify／evaluate／verify／report／smoke／backup |
| 新測試 | tests/test_fault_type_axis_kernel.py |
| 只讀來源 | 原literature native模型、已封存protocol／manifests／C02 factory與最新用途／別名guard |
| 文件與紀錄 | reports/axis_invariant_kernel_v1/、docs兩索引、logs/fault_type_axis_kernel_*/及output/fault_type_axis_kernel_*/ |
| 大型產物 | D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/axis_invariant_kernel_v1/workspace/output/ |
| 保持不變 | 正式105／linear／Maha-LW／k-NN切換、PolarMap、formal CSV、舊模型／報告／manifest |

先提交手冊，再實作與雙環境smoke／測試；runner工程提交後lock，協定push後fit；actual來源重建push後才能outer。執行命令由新CLI `--help`列出精確必填protocol／lock／source／data-root，版本化產物不覆寫。ZIP備份逐member SHA／CRC核對，Git保存compact設定／摘要／索引；D槽同機備份不稱異地備份。

2026-10-04工程接續：runner／33小測試與兩native smoke／help完成，完整acceptance另記execution_log。paired report除C02／C17／C24／D01外，固定同detector的alpha0消融，共42方法配對、每配對9fold/seed格；沒有使用G的prototype變體欄位。JSON或既有.gz摘要皆可由新CLI讀取，不改任何父批reader。下列lock在工程commit/push及完整回歸通過後執行；此時尚無正式K模型或成績。

```powershell
$env:PYTHONIOENCODING='utf-8'
.venv310/Scripts/python.exe -m experiments.fault_type_axis_kernel lock --parent-protocol output/fault_type_discriminative_prototypes_lock/2026-10-03-15-23-33/protocol.json
```

對新protocol執行fit／source-verify／evaluate／verify時，明列`--data-root data/formal_local`；fit後傳新`--lock`，outer前傳已提交的`--source-verification`。report沿用metrics_v2及D01檔，另傳本批evaluation／verification；不拿J後續成績挑K候選。完整命令與產物時間戳由execution_log及result_index保存。
