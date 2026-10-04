# 三軸排列核：原始來源與可執行條件

2026-10-03，Asia/Taipei。exp18 outer執行期間研究，尚未依其成績選方法。

## 已讀原始來源

Haasdonk／Burkhardt（2007），*Invariant Kernel Functions for Pattern Analysis and Machine Learning*，Machine Learning68:35–61，[DOI10.1007/s10994-007-5009-7](https://doi.org/10.1007/s10994-007-5009-7)。[Freiburg作者稿](https://lmb.informatik.uni-freiburg.de/papers/download/ha_bu_MachineLearning6807.pdf)32頁全文，已核對方法、實驗、限制與參考文獻；與刊物27頁排版不同，不算不同論文。Eq.2為雙側變換平均，Proposition11為有限群／Haar measure不變性；IDS kernel可能不定的警告保留。本案只採PSD群平均，不用min-distance核或事後投影修補。

本站改編：S3置換三軸22欄特徵block；共享known-train特徵尺度，使置換對齊；6項單側RBF平均等於36項雙側平均。另固定alpha0／0.5／1凸混合；RKHS class-mean距離配known-cal q95。這些馬達特徵配置、權重及拒絕器不是作者原實驗。本案未證明軸方向曾變，也不等同任意旋轉不變。

Cortes／Vapnik（1995），*Support-vector networks*，Machine Learning20:273–297，[出版資訊及摘要](https://link.springer.com/article/10.1007/BF00994018)。此來源本次只重核出版資訊；SVM既有研究已使用，沒有冒稱本次取得其訂閱全文。使用既有scikit-learn native SVC／libsvm，[官方precomputed接口](https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html)，實際版本3.10環境sklearn1.7.2／3.14環境1.9.1，參數在protocol保存全部get_params。

## 作者工具與查詢

論文引用MATLAB KerMet-Tools；HTTP及HTTPS舊作者網址均無法開啟，程式／授權仍UNKNOWN，未下載執行。新增公式獨立實作，不安裝MATLAB或新依賴。

查詢包括英文`Haasdonk Burkhardt invariant kernel functions pattern analysis machine learning 2007 pdf`、德文`invariante Kerne Gruppenintegration Haasdonk Burkhardt 2007`、日文`加速度 軸 入れ替え 不変 特徴 分類 論文`及繁體中文`加速度 軸置換 不變 特徵 故障 診斷 原始論文`。初始中文查詢字形不符繁體要求，已重跑繁體查詢；文件不保留不合規字形。多語查詢沒有當作多篇獨立文獻計數。

## 尚未採用的候選

| 原始來源 | 閱讀深度／本輪限制 |
|---|---|
| Tong等（2018），[DATF arXiv1806.01512](https://arxiv.org/abs/1806.01512) | 只讀摘要；target樣本及pseudolabel refinement的transductive流程不符合本輪test禁止fit，未實作 |
| Li等（2015），[spectrum image／2DPCA arXiv1511.02503](https://arxiv.org/abs/1511.02503) | 只讀摘要；需要raw FFT images，現有105維不能反推，未實作 |
| He等（2015），[periodic group sparse arXiv1511.00067](https://arxiv.org/abs/1511.00067)；Ding等（2015），[STFT arXiv1511.00393](https://arxiv.org/abs/1511.00393) | 只讀摘要；需要raw時域／週期與時間證據，未實作，缺資料不阻擋可用核比較 |
| Kokuyama等（2022），[accelerometer calibration arXiv2204.09212](https://arxiv.org/abs/2204.09212) | 只讀摘要；硬體校正不在現有軟體比較範圍，未實作 |

不把上述abstract-only候選寫成已深入閱讀、已測試或已排除其方法效能；排除的是本輪資料／協定適用性。原formal資料與曝光ledger不修改。
