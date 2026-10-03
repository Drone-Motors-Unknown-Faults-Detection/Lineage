# 實驗18：RPM原型的距離、歧義與聯合拒絕

2026-10-03，Asia/Taipei。先行手冊，exp17 outer剛開始，尚未讀其成績；本批方法預期不回填結果。

## 原始來源及改編

Fischer／Hammer／Wersing（2015），*Efficient Rejection Strategies for Prototype-based Classification*，Neurocomputing169:334–342，DOI[10.1016/j.neucom.2014.10.092](https://doi.org/10.1016/j.neucom.2014.10.092)，[Honda合法作者稿](https://www.honda-ri.de/pubs/pdf/2814.pdf)。25頁全文先前已讀，來源卡見reports/discriminative_prototypes_v1/sources_addendum.md；本次再次核對Eq.7、9、10–11。2014 ESANN會議稿與2015延伸去重，不算兩個新方法。

論文分開處理outlier與分類歧義：RelSim=(d_other−d_near)/(d_other+d_near)，nearest-distance certainty=−d_near；原Comb用decision-boundary certainty和nearest distance的OR，並窮舉threshold。本案不使用其threshold搜尋，也不以接受子集accuracy代替完整分類／未知／健康誤報。

Graeber／Vetter／Saralajew／Unterreiner／Schramm（2021），*AGLVQ - Making Generalized Learning Vector Quantization Aware of Context*，ESANN557–562，DOI[10.14428/esann/2021.ES2021-40](https://doi.org/10.14428/esann/2021.ES2021-40)。本批繼承本站exp17的RPM原型，而非作者完整AGLVQ；所有GLVQ／aux／metric差異見exp17手冊及來源卡，不另fit分類器。

本站改編：以exp17全部12分類器作固定配對，不挑最好I arm。每筆已知或未標記query計算平方距離最小值a=d_near及最近不同類距離d_other；每類一原型，因此第二小距離即不同類。歧義b=1−(d_other−d_near)/(d_other+d_near+1e−12)，高分拒絕。兩距離同時為0時b=1（歧義最高）；一個原型或非有限／負距離拒絕執行。tie採固定原labels順序。

專用cal馬達的healthy＋known faults分別給a、b的固定0.95分位數q_a、q_b，NumPy quantile method=linear，無選參。excess_a=(a−q_a)/max(abs(q_a),1e−12)，excess_b同式。三種score固定為excess_a、excess_b、max(excess_a,excess_b)，統一strict score>0拒絕；最後一項是本站RelSim＋nearest-distance OR改編，不冒稱論文原Comb。零分位數採固定epsilon，等於threshold不拒絕；保存raw scores、quantiles與cal sample IDs。

threshold僅用全部已知cal，不讀unknown；cal不改RPM原型、scaler或metric。三方案均pooled-cal，沒有RPM／class-specific threshold搜尋。OR可能提高未知召回，也可能擴大健康誤報；兩個各95%分位數不能保證聯合5%誤報，跨motor更沒有該保證。

## 可反駁假說與矩陣

H18a：C02/M的跨motor未知排序弱；在相同分類器與工況下，條件原型絕對距離可能揭示不屬已知中心的query。H18b：相對歧義補充距離，OR可提高未知辨識。支持須同時通過原CONTRACT的未知／健康／已知保護；如果T1仍弱、其他motor誤報增加或known coverage崩落，保留FAILED，不掃最佳threshold。

exp17的12分類器×3score×3fold×seeds0/1/2，共36方法／324 detector評估；共享108個已封存分類器，不稱新增324次分類器訓練。全部原型保留，二次static／一次static／GLVQ／aux及identity／hard600幾何按原定義比較。fixed父批I各arm的C02/M為直接matched control，另列C02、C17、C24、D01。不產生global winner。

主N=5、healthy＋5known／4unknown、三fold T1/T2/T3、T2/T3/T1、T3/T1/T2及RPMS完全沿用父協定。所有28,910筆已曝光，adaptive exploratory；非fresh／非部署驗證。fit引用原train，cal只本批quantiles，selection/validation空。raw/window/session證據UNKNOWN，test group數不足仍INCOMPLETE。

source-verify以實際known train/cal重算距離與quantiles，檢查父批原型／state／RPM／IDs／SHA及已完成actual reconstruction鏈。test infer只讀features和文件化RPM；truth mutation結果應一致。paired test IDs、逐筆source、完整final F1／unknown AUROC/AUPR／recall／healthy互斥total alarm／per motor/RPM/class／所有seeds必須保存，不能只報accept accuracy。

## 程式範圍與驗證

| 類別 | 路徑／責任 |
|---|---|
| 新公式 | core/fault_type_context_rejection.py，固定score與已知cal分位數／零分母／SHA |
| 新runner | experiments/fault_type_context_rejection.py，run(...)／main()；lock／calibrate／source-verify／evaluate／verify／report／smoke／backup |
| 新測試 | tests/test_fault_type_context_rejection.py，手算／tie／q0／OR／cal污染／source重封／purpose與truth guard |
| 只讀共用 | exp17、exp15、factory C02/M、formal data與既有source／metric／CONTRACT，不編輯sealed依賴 |
| 文件 | reports/context_rejection_v1/、docs兩索引 |
| 紀錄 | logs/fault_type_context_rejection_*/、output/fault_type_context_rejection_*/ |
| 大型產物 | D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/context_rejection_v1/workspace/output/ |
| 正式預設 | 不改105／linear／Maha-LW／k-NN切換或PolarMap |

每action1800秒，C槽保留1GB。協定在校準前commit/push，actual source重建提交後才outer。未收斂／missing／tamper不借cal或test補fit，保留明確INCOMPLETE／拒絕。雙Python完整測試＋pip check／CLI和合成smoke；合成只作工程測試。大型產物D槽獨立版本包驗證ZIP members SHA／CRC，Git只存compact索引／設定／摘要與logs。不覆寫舊formal／lock／model／prediction。

手冊先行提交後已實作core／runner雙介面，兩環境公式／source-purpose測試及合成smoke完成；28項小測試及完整驗收狀態見execution_log.md。尚未formal lock、calibrate或outer。以下lock必須在runner工程commit推送後執行，再提交協定才calibrate。

```powershell
$env:PYTHONIOENCODING='utf-8'
.venv310/Scripts/python.exe -m experiments.fault_type_context_rejection lock --parent-protocol output/fault_type_context_prototypes_lock/2026-10-03-20-33-01/protocol.json --parent-lock output/fault_type_context_prototypes_fit/2026-10-03-20-34-21/locked_study.json --parent-source output/fault_type_context_prototypes_source_verify/2026-10-03-20-38-00/source_verified.json
```

其餘action與必填參數見`--help`；calibrate／source-verify／evaluate／verify明列`--data-root data/formal_local`。report以原metrics_v2／D01為baseline，並以`--parent-evaluation`指向exp17封存evaluation，重算全部12父classifier及36新score的相同test IDs。calibrate只生rejector與引用父model，不以新增校準數冒充classifier訓練。
