# 實驗14：局部 Fisher 表示法與固定 PCA 對照

2026-10-03，Asia/Taipei。本手冊先於程式實作與正式擬合。此時實驗13尚未完成 test 評估；本批維度與係數不依其成績決定。

## 方法、範圍與反證

Sugiyama 的 LFDA 保留類內局部鄰域，同時分離已知類別。本批檢驗：類別內存在多群時，局部 scatter 是否比不使用標籤的 PCA 更有助於跨馬達分類。這是可反駁假說，不把多轉速直接當成已證明的群，也不假定 LFDA 能處理未知類別或馬達 domain shift。

沿用已封存 harmonic69、同一 N=5 manifest、同一90 CSV／28,910筆 fingerprint `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。train/calibration/test 依序 fold0=T1/T2/T3、fold1=T2/T3/T1、fold2=T3/T1/T2；seeds=0/1/2。無 validation／selector，unknown 不進入任何擬合或校準。全部現有資料已歷史 test 曝露，本批仍為 exploratory。

四種表示法事先固定：PCA10、PCA20、regularized-LFDA10、regularized-LFDA20。10與20是小型秩消融，不進行維度搜尋、不依最好seed挑選。四者皆使用相同 known train 的每類／RPM最多20筆分層子集（最多360筆）；上游 harmonic69/scaler 只沿用該折全部 known train 的既有擬合。

LFDA 依 JMLR Eq.9–12 自行實作，不複製或安裝 metric-learn。每類 affinity 為 self-tuning Gaussian，尺度是排除自身後第7個同類鄰居。若尺度為0，採 train 子集正距離中位數平方根×1e-12（下限1e-12）作數值保護。類內權重 A/n_class；類間權重：同類 A(1/n−1/n_class)，異類1/n。scatter 用對稱 graph Laplacian 計算；以 train 子集平均中心化以減少消去誤差。

原論文假定 within scatter 可逆。本站新增固定 ridge=`max(trace(Sw)/d,1e-12)×1e-6`，以 SciPy 對稱 generalized eigh 求解，依遞減特徵值取10／20個正值方向、乘 sqrt(eigenvalue)。正方向不足即 INCOMPLETE，不偷偷補方向／改秩。每向量最大絕對值座標固定正號；記錄 eigenvalues、ridge、residual 與來源。這是正則化、有限子集的 LFDA 改編，非原文完整重現。PCA 用 full SVD、whiten=false、同一子集，不使用 labels。

每種表示法配四個固定方法，共16方法×3fold×3seed=144評估：uniform shrinkage LDA＋既有C02/M；距離加權5NN＋C02/M；相同5NN＋該表示法factory LW；相同5NN＋該表示法factory k-NN。LDA=lsqr/shrinkage=auto/uniform priors；5NN=distance/brute/p=2/n_jobs=1。分類器與 reference 使用全部 known train。factory confidence=.95、Ledoit–Wolf、k=5；另一motor known calibration只設定門檻，score>1拒絕。不使用RPM或T-code作模型輸入，也不使用label編碼作特徵。

每階段預算1800秒、C槽保留1GB、預估產物300MB；達限保存已完成cell，不改方法救分數。匹配 PCA/LFDA、10/20、分類與偵測解耦的消融事先固定；全部方法均保存，不輸出 global winner。

實驗13執行期間已遇到C槽保留門檻，因此本批大型fit/evaluate/verify產物直接存於 `D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-03/local_fisher_v1/workspace/output/`，按action與timestamp分目錄。C槽標準logs/output保留執行紀錄、compact lock／gzip摘要與D槽位置索引；既有來源路徑不變。backup入口只接受本批這個明確output根的完成目錄，沿用既有archive／逐成員SHA校驗，不接收raw或任意外部目錄。其餘lock、source-verify、report、smoke仍走標準output。這是儲存位置調整，不變更馬達用途、來源或評分。

## 來源與閱讀範圍

- Masashi Sugiyama（2007），*Dimensionality Reduction of Multimodal Labeled Data by Local Fisher Discriminant Analysis*，JMLR8:1027–1061，[原文](https://www.jmlr.org/papers/volume8/sugiyama07b/sugiyama07b.pdf)。已讀§3.1–3.3、Eq.9–12、演算法圖與§6限制；公式頁已以PDF工具渲染核對。並非聲稱逐頁閱讀35頁。原論文指出 affinity 選擇敏感，本批不事後調k或核寬。
- 官方 [metric-learn LFDA實作](https://contrib.scikit-learn.org/metric-learn/_modules/metric_learn/lfda.html) 用於核對類內尺度與 generalized eigen 邏輯，未複製程式、未安裝套件。本站直接依原文 pairwise 權重重建 scatter，以測試中的逐對求和驗證。
- PCA依既有 sklearn full-SVD 實作；分類器／factory 的書目及改編沿用 [實驗13](exp13_metric_classification.md)。三個seeds不等於三次獨立採集。

## 驗證與輸出

程式先驗證逐對 scatter 與矩陣式一致、類別重新命名不改幾何、重跑固定sign、重複點／零尺度保護、正方向不足拒絕、空輸入處理、來源污染及封存SHA。正式 fit 後從原 train/cal 數值重建 projection、classifier arrays及factory reference／門檻，核對通過並提交fit lock才讀test。

evaluate保存全部逐樣本結果；verify重推並重算指標、truth mutation不影響輸入／推論。report沿用完整 reliability CONTRACT，另報全分母final fault F1、每motor/RPM/class、所有seeds及匹配差異。只有一組known配置，不能稱R2；原始採集獨立性UNKNOWN、final guard仍INCOMPLETE。正式105/LW/PolarMap/k-NN API均不變。

## 程式碼與輸出

| 類型 | 路徑 |
|---|---|
| 邏輯 | `core/fault_type_local_fisher.py` |
| 入口 | `experiments/fault_type_local_fisher.py`，run(...)／main()，lock/fit/source-verify/evaluate/verify/report/smoke/backup |
| 共用 | 原 harmonic69／manifest／FeatureStore／factory／metrics_v2／reliability；不改封存模組 |
| 測試 | `tests/test_fault_type_local_fisher.py` |
| 紀錄／結果 | `logs/fault_type_local_fisher_*/`、`output/fault_type_local_fisher_*/`；大型產物依既有archive到D槽 |
| 研究帳冊 | `reports/local_fisher_v1/`，僅版本化決策與交付索引 |
| 健康／網頁 | `experiments/health/`、`web/`：N/A |

CLI `.venv310/Scripts/python.exe -m experiments.fault_type_local_fisher --help`。protocol封存並commit/push才fit；source-verify與fit lock提交後才evaluate。新路徑保存失敗與限制，不覆寫舊試驗。
