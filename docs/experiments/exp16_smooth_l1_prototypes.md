# 實驗16：平滑L1原型距離的有限配對

2026-10-03，Asia/Taipei。先寫手冊再改程式；此時實驗15外層評估尚未完成。以下是新批假說與固定設計，沒有回填實測成績。

## 方法、公式與反證

H16a：平方Euclidean對大偏差維度的權重較高，平滑L1可能改善跨motor的配置分類。H16b：原型更新及anchor效果可能依距離形狀改變。競爭解釋是motor訊號與標籤本來重疊；L1也可能消除有效幅值差異。若同條件分類變差、最弱類仍零召回、健康完整誤報過高，依既有契約判失敗，不換分母。

原來源Lange等（2014）Eq.11–13：對z=x−w與α=20，Qα(z)=log(2+exp(−αz)+exp(αz))/α，Sα(z)=z tanh(αz/2)。本站distance=sum(Qα)或sum(Sα)，沒有另學matrix或relevance。Q在z=0為2log(2)/α，保持原印式常數，不默默減掉；它不是零對角metric。穩定Q式為abs(z)+2log1p(exp(−αabs(z)))/α，gradient對z=tanh(αz/2)。S導數=tanh(t)+t(1−tanh(t)²)，t=αz/2；避免直接cosh溢位。

沿用GLVQ平均sigmoid(4μ)、μ=(d+−d−)/(d++d−+1e-12)、最近同／異類原型、固定L-BFGS-B與可選λ=.01 anchor。距離對w導數取負號；相對損失的兩個係數與exp15一致。nonconvex，成功收斂不代表全域最佳。所有核心梯度做有限差分、極端值與tie測試。

固定全部known train每類一平均原型初始化，loss僅用同一合法分層子集最多360筆；identity harmonic69與已封存hard600對角幾何各自配Q／S、static／GLVQ／anchored，共12新分類器。固定C02/M作唯一拒絕支線，12×3fold×3seed=108格。與實驗15相同幾何的單中心Euclidean static／GLVQ／anchor作逐ID配對控制。classifiers改變、detector不變，因此raw known accuracy可比較，C02/M未知召回預期完全相同；不能宣稱此批單獨解決T1未知零召回。

參數與實驗15相同：maxiter600/maxfun2000/maxls50/ftol1e-9/gtol1e-6，每模型120秒；未收斂保留模型／loss／梯度、INCOMPLETE、不得silent fallback。新增依賴0。科學環境Python3.10.19／sklearn1.7.2、相容測試Python3.14.6；不跨版本載joblib。

## 資料與資訊用途

唯讀90份formal105／28,910筆，fingerprint `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。healthy=8screws；known faulty=1screws／2screws／3_14screws／3screws／4screws；unknown=4_146screws／5screws／6screws／7screws。

train/cal/test三fold為T1/T2/T3、T2/T3/T1、T3/T1/T2，seeds0／1／2、RPM6000／8000／11000。同exp13至15實際manifests／source SHA；未知不fit、cal或選參。scaler、harmonic69及hard600仍是該折known train來源。validation／selection空清單，不產生global winner。全部樣本已有歷史test曝露，結果只屬探索。來源session／raw windows仍UNKNOWN，fresh final guard仍INCOMPLETE，不能報R3。

保持既有CONTRACT：fault-only accuracy／conditional macro-F1、每motor／RPM／class／seed最差組、健康完整互斥誤報、unknown保護及全部final decisions的F1分開。新loss不得降低契約。主配置只有一組known subset；R2仍需後續固定多配置、消融及壓力測試。

## 原始來源與本站改編

1. Mandy Lange／Dietlind Zühlke／Olaf Holz／Thomas Villmann（2014），*Applications of lp-Norms and their Smooth Approximations for Gradient Based Learning Vector Quantization*，ESANN:271–276，[會議原文](https://www.esann.org/sites/default/files/proceedings/legacy/es2014-153.pdf)，ISBN978-287419095-7。六頁方法／應用／結論已讀，p274公式圖片核對。原文為GMLVQ、microarray／GC-MS資料；本站固定幾何、只移動原型，不冒稱原GMLVQ重現，不移植其準確率。
2. Atsushi Sato／Keiji Yamada（1995會議／1996卷出版），*Generalized Learning Vector Quantization*，NIPS8:423–429，[原文](https://proceedings.neurips.cc/paper_files/paper/1995/file/9c3b1830513cc3b8fc4b76635d32e692-Paper.pdf)。本站採固定β、批次L-BFGS-B、平均loss、ε與anchor；改編前後及導數見實驗15手冊。不是原作者字元辨識實驗。

α=20取原文數值，未掃本案test；中心數一、固定mean初始化及C02/M是本案匹配控制約定。不能將KMeans的Euclidean初始化冒稱L1最適；本批不使用KMeans。Q零值常數與S的差別列為機制差異，不把同名L1當完全相同距離。

## 程式、命令與預期產物

| 範圍 | 路徑 |
|---|---|
| 新公式／模型 | `core/fault_type_smooth_l1.py` |
| 新API／CLI | `experiments/fault_type_smooth_l1.py`，run(...)／main()；lock/fit/source-verify/evaluate/verify/report/smoke/backup |
| 測試 | `tests/test_fault_type_smooth_l1.py` |
| 只讀共用 | exp13／15的parent、manifests、FeatureStore、factory、metrics／reliability；不改sealed依賴 |
| 紀錄 | `reports/smooth_l1_v1/` |
| 標準產物 | `logs/fault_type_smooth_l1_*/`、`output/fault_type_smooth_l1_*/` |
| 大型產物 | `D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/smooth_l1_v1/workspace/output/`，C標準output保留compact索引 |
| production／web | N/A，formal105／LW／k-NN切換／PolarMap不改 |

先核心公式測試與synthetic smoke；再完成來源／用途驗證與runner。協定lock+commit+push後才fit；實際train/cal重建+commit+push後才outer evaluate；逐筆reinfer／truth mutation／source SHA、完整108格及失敗原因、配對controls和指標重算後才能報成果。每action預算1800秒、C保留1GB，大型產物直接D；不覆寫舊artifact。runner與雙環境工程測試已完成，尚無本批正式研究成績。

```powershell
$env:PYTHONIOENCODING='utf-8'
.venv310/Scripts/python.exe -m experiments.fault_type_smooth_l1 lock --parent-protocol output/fault_type_discriminative_prototypes_lock/2026-10-03-15-23-33/protocol.json --parent-lock output/fault_type_discriminative_prototypes_fit/2026-10-03-15-28-56/locked_study.json --parent-source output/fault_type_discriminative_prototypes_source_verify/2026-10-03-15-31-33/source_verified.json
```

後續命令使用新lock的實際路徑：`fit --protocol ... --data-root data/formal_local`、`source-verify --protocol ... --lock ... --data-root data/formal_local`、`evaluate --protocol ... --lock ... --source-verification ... --data-root data/formal_local`、`verify`加`--evaluation`，最後`report`加`--evaluation --verification --baseline --previous --euclidean`。所有省略位置由execution log記下實際產物；不能引用不存在的時間戳。基線為metrics_v2、D01與exp15封存evaluation，不讀手填分數。
