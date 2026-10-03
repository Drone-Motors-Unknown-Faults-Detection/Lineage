# 實驗15：判別式原型學習與固定中心配對

2026-10-03，Asia/Taipei。先完成手冊，再實作。此時實驗13／14已封存失敗，正式預設不改。

## 假說、改編與反證

H15a：固定平均／KMeans原型不直接最小化分類錯誤；以known train的相對距離損失移動原型，可能改善跨motor配置分類。H15b：固定anchor ridge可能限制原型偏離，減少seed敏感度。H15c（低支持探索）：相對距離模糊分數或許能補充距離拒絕，但遠離所有原型的未知也可能有高信心；不保證OOD分離。若只改善train、跨motor類別仍零召回或healthy完整誤報過高，依原契約判失敗。

Sato／Yamada原GLVQ：對train真值，取最近同類／異類原型平方距離d+、d−；μ=(d+−d−)/(d++d−)，最小化Σf(μ)。原文使用隨時間變窄sigmoid與梯度更新。本站有限改編為平均sigmoid(4μ)、固定β=4、分母加1e-12、批次L-BFGS-B及可選anchor penalty λ mean((W−W0)²)。λ固定0／.01，不搜尋test。沒有沿用官方舊套件隨機梯度擾動；函數與梯度都使用同一平均口徑，以有限差分驗證。

解析導數：D=d++d−+ε，∂μ/∂d+=(2d−+ε)/D²，∂μ/∂d−=(−2d+−ε)/D²；平方距離對原型導數2(W−X)。乘sigmoid導數βs(1−s)、除train子集筆數，再加2λ(W−W0)/W.size。這是分段可微、非凸問題；optimizer success不表示全域最佳。tie採固定原型順序，零距離受ε保護，不借test處理奇異例。

初始化用全部known train：每類1平均或3個KMeans中心（n_init10/max_iter300/tol1e-4/lloyd；default_rng(seed)產生sklearn整數seed）。最佳化只用相同known train分層子集每類RPM20筆、最多360筆。三版本static／GLVQ λ0／GLVQ λ.01，兩種幾何identity harmonic69／已封存hard600對角距離，兩種中心數，共12分類器。對每分類器配兩個detectors：既有C02/M（解耦控制）與原型模糊分數。24方法×3fold×3seed=216格；成本較一般8–20方法略大，但此有限factorial可分離中心數、損失、ridge、metric及拒絕支線，不隱藏detector乘數。

模糊分數不使用test真值：先取最近原型的predicted class，再取最近其他類原型；score=1+(d_nearest−d_other)/(d_nearest+d_other+ε)，通常0–1，越大越模糊。固定known calibration全體95% linear分位數為raw threshold；strict score>threshold拒絕，不除以零／負門檻。它是原文μ拒絕概念的限制性適配，不能把分類歧義等同遠距離未知。C02/M仍走原factory LW、score>1；正式factory k-NN不變，本批不重做已完成的k-NN控制。

optimizer固定maxiter600/maxfun2000/maxls50/ftol1e-9/gtol1e-6、每模型120秒。未收斂者保存原型、loss、gradient、message、時間，標INCOMPLETE且不輸出該模型成績；禁止silent fallback成static。每action預算1800秒、C保留1GB、估計300MB。seeds0/1/2都保存，不挑最好seed。

## 資料、契約與來源

90份正式105維CSV／28,910筆，fingerprint `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。上游harmonic69/scaler及hard600全部只fit該折known train；未知不fit／cal。fold0 train/cal/test=T1/T2/T3、fold1=T2/T3/T1、fold2=T3/T1/T2，沿用同一N=5 manifest、RPM、class IDs。無validation／selector、selection IDs空。calibration只設定已固定分數的分位數，不選模型、loss或λ。

已知healthy=8screws，faulty=1screws/2screws/3_14screws/3screws/4screws；unknown=4_146screws/5screws/6screws/7screws。motor與RPM不作feature；原型label在獨立陣列。沿用不可放寬reliability CONTRACT、完整健康誤報、全分母final F1及最弱組要求。全部樣本已歷史test曝露；只有一組known配置初篩，不是R2，更不是fresh/R3。

1. Atsushi Sato／Keiji Yamada，*Generalized Learning Vector Quantization*，NIPS8:423–429，1995會議／1996卷出版，[原始PDF](https://proceedings.neurips.cc/paper_files/paper/1995/file/9c3b1830513cc3b8fc4b76635d32e692-Paper.pdf)。七頁全文、Eq.4–10及表1已讀；p425公式渲染核對。原實驗為字元辨識，不是motor、open-set或跨機器。日本作者[NEC書目](https://jpn.nec.com/rd/people/atsushi_sato.html)記1996卷出版及1999日文延伸；不把兩個年份當兩個演算法。
2. Graeber／Vetter／Saralajew／Unterreiner／Schramm（2021），*AGLVQ - Making Generalized Learning Vector Quantization Aware of Context*，ESANN:557–562，[原文](https://www.esann.org/sites/default/files/proceedings/2021/ES2021-40.pdf)。已讀method、輔助loss、資料／結果及結論。其context路線與本批固定原型不同；文中有relevance只剩一feature、部分方法未得到同樣增益。本站anchor是自訂W0限制，不冒稱其Eq.4樣本代表性loss。context-adaptive原型留待新協定，不從本輪直接宣稱已實作。
3. [sklearn-lvq官方原始模組](https://sklearn-lvq.readthedocs.io/en/stable/_modules/sklearn_lvq/glvq.html)，1.1.0、revision70012019、BSD3，已核對objective／gradient／L-BFGS及predict；其objective求和、gradient平均並加入隨機擾動，本站不複製這個數值安排。只作核對線索，依論文自行寫解析梯度。沒有安裝該套件。

新增依賴0；NumPy／SciPy／sklearn使用現有3.10.19科學環境、3.14.6相容環境。作者AGLVQ repo README需舊Python/Keras/TF，未執行安裝。公開內容只讀，不上傳private資料。

## 實作與驗收入口

| 項目 | 路徑 |
|---|---|
| 公式 | `core/fault_type_discriminative_prototypes.py` |
| API／CLI | `experiments/fault_type_discriminative_prototypes.py`，run(...)／main()；lock/fit/source-verify/evaluate/verify/report/smoke/backup |
| 測試 | `tests/test_fault_type_discriminative_prototypes.py` |
| 共用 | exp13已封存weight/source、manifest、FeatureStore、factory、metrics/reliability；不修改sealed程式 |
| 標準輸出 | `logs/fault_type_discriminative_prototypes_*/`、`output/fault_type_discriminative_prototypes_*/` |
| 大型輸出 | `D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/discriminative_prototypes_v1/workspace/output/`；C標準output保留compact索引 |
| 研究紀錄 | `reports/discriminative_prototypes_v1/` |
| 健康／網頁 | `experiments/health/`、`web/`：N/A |

先解析梯度／手算／空組／tie／零距離／污染／來源／序列化測試及synthetic smoke，皆只算工程。`python -m experiments.fault_type_discriminative_prototypes lock --parent-protocol output/fault_type_metric_classification_lock/2026-10-03-09-42-02/protocol.json`。protocol commit/push後才fit；fit及source重建提交後才evaluate。source驗證實際原型／loss／train arrays及known calibration分位數，0 test numeric reads。外層verify逐筆重推、label mutation、SHA／IDs、指標重算，report列全部planned/completed/INCOMPLETE與配對消融，不輸出global winner。backup單次接多root，避免同秒索引碰撞，不覆寫舊ZIP。
