# 實驗17：RPM工況相關原型的有限改編

2026-10-03，Asia/Taipei。本手冊先於新core／runner；exp16仍在來源重建，尚未看其outer結果。以下預期不回填成績。

## 方法與可反駁假說

H17：同一配置跨RPM的特徵均值改變，固定pooled原型可能混淆配置；用推論時可取得的RPM改變原型，可能改善分類及最弱類召回。反證包括跨motor仍失敗、健康誤報增加、二次模型只記住單motor的均值。RPM從既有manifest取得，只是文件化工況代碼，不證明實際轉速量測或安裝一致。T-code、路徑、true test label不進模型，RPM不當fault label。

原來源：Graeber／Vetter／Saralajew／Unterreiner／Schramm（2021），*AGLVQ - Making Generalized Learning Vector Quantization Aware of Context*，ESANN:557–562，DOI[10.14428/esann/2021.ES2021-40](https://doi.org/10.14428/esann/2021.ES2021-40)，[六頁原文](https://www.esann.org/sites/default/files/proceedings/2021/ES2021-40.pdf)。完整方法／Eq.1–4／數據／負面結果／結論已讀；作者實碼[9f0ee487948803ddf9b4e97fc1d9a8e4d0c64836](https://github.com/graebe/aglvq/tree/9f0ee487948803ddf9b4e97fc1d9a8e4d0c64836)的proto、layers、losses、distance、model、initializer、constraints、setup與MIT授權已唯讀核對，沒有執行或安裝外部程式。

原式w(c)=ws+wa(c)，polynomial path每次冪項加係數向量；aux為true prototype對sample的MSE，先pretrain再margin。作者程式有每冪額外bias、distance取平方和的平方根、模型預設swish(mu)，不是本站exp15的平方距離／sigmoid(4mu)。本文移植context機制，明列改編，不冒稱原AGLVQ完整重現。

本站取c=(RPM−8000)/3000，phi=[1,c]或[1,c,c²]，w_class(c)=theta_class phi。固定6000／8000／11000三RPM，不對未見RPM外插宣稱泛化；缺／不合法RPM拒絕推論。全部known train每類以最小平方初始化theta，取代作者RMSprop的pretrain；二次static在三RPM等價於各RPM該類平均原型，是明確條件化控制。

loss採本站exp15平均sigmoid(4mu)、平方Euclidean、epsilon=1e-12；mu=(d_true−d_other)/(d_true+d_other+epsilon)。aux variant加.01*mean((X−w_true(c))²)，參數.01是本案固定操作約定，不是作者實驗最優值。aux不同於exp15 anchor：它拉向真實train sample，不拉向初始係數。梯度以chain rule把每樣本對w的導數乘phi累加至theta，做有限差分／手算與二次static均值控制。

兩種幾何(identity harmonic69、已封存hard600對角)×degree1／2×static／GLVQ／GLVQ+aux=12分類器，C02/M拒絕固定，12×3fold×3seed=108格。與exp15同幾何單中心Euclidean static／GLVQ作配對；新批不挑global winner。new aux只在degree相同配對；degree1/2差別列capacity與context變化，不能宣稱排除了全部容量效應。

optimizer沿用maxiter600/maxfun2000/maxls50/ftol1e-9/gtol1e-6，單模型120秒，loss用原合法train分層最多360筆（每class/RPM最多20），初始化／harmonic69 scaler fit全部known train；hard600只原合法train subset。未收斂保留INCOMPLETE，不改预算換最好seed。

## 資料、校準與成功判定

唯讀formal105的90CSV、28,910筆，fingerprint `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。healthy=8screws；known=1screws／2screws／3_14screws／3screws／4screws；unknown=4_146screws／5screws／6screws／7screws。

三fold train/cal/test為T1/T2/T3、T2/T3/T1、T3/T1/T2，seed0/1/2及原manifests不改。cal只已知資料閾值，C02/M沿用factory封存來源；未知不fit、cal或選參；validation/selection皆空。所有資料已有test曝光，歷史selection bias仍在。

沿原CONTRACT比較fault-only accuracy／conditional F1、完整final F1、healthy互斥total alarm、unknown／worst-group／coverage與所有seeds。C02/M不變，未知召回應完全相同，單靠本批不能解決T1 unknown floor。主subset初篩後仍須多subset／壓力反證才可能達R2；fresh guard仍INCOMPLETE，session／window／清理／安裝來源UNKNOWN，不能靠RPM語義修正宣稱R3。

## 程式範圍與執行契約

| 類別 | 路徑／責任 |
|---|---|
| 新公式 | `core/fault_type_context_prototypes.py`，train-only context係數／解析梯度／推論RPM驗證 |
| 新API／CLI | `experiments/fault_type_context_prototypes.py`，run(...)／main()，lock／fit／source-verify／evaluate／verify／report／smoke／backup |
| 新測試 | `tests/test_fault_type_context_prototypes.py` |
| 共用唯讀 | exp15 parent、formal Features、split/source guard、factory、metrics、CONTRACT；不修改sealed依賴 |
| 新報告 | `reports/context_prototypes_v1/` |
| 標準紀錄 | `logs/fault_type_context_prototypes_*/`、`output/fault_type_context_prototypes_*/` |
| 大型產物 | `D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/context_prototypes_v1/workspace/output/` |
| 正式default／web | 不改formal105／linear／LW／k-NN切換／PolarMap |

先完成公式、RPM路由、source reconstruction與synthetic smoke、雙環境回歸。協定及code封存提交推送後才fit；actual train/cal重建提交後才outer；逐筆reinfer／truth mutation／相同test IDs／predictions SHA與指標重算後報實測。每action1800秒、C保留1GB；大型產物直接D、索引入Git，舊data/model/prediction/lock不覆寫。

此時尚無新code或formal成績。CLI具體路徑與時間戳由後續execution log補記；原程式需要Python3.6／TF2.1／Keras2.3.1，不在本案科學環境安裝，本站用既有NumPy／SciPy從方程式獨立實作。
