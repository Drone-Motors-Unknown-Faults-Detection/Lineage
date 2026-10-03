# 實驗13：收斂距離、分類規則與開集幾何的配對研究

2026-10-03，Asia/Taipei。先寫手冊，再實作與封存協定，提交協定後才跑正式資料。本批接續 hard600 的九份 train-only 權重；尚未取得本批分類成績。

## 實驗方法

90 CSV、28,910 筆 formal105，指紋 `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。已知配置沿用封存 N=5 manifest，不改標籤。fold0 T1/T2/T3、fold1 T2/T3/T1、fold2 T3/T1/T2，順序為 train/calibration/test。seeds 0、1、2 只改 train 子集抽樣與 KMeans 初始化，沒有新增馬達。validation 與 selection IDs 皆空。

沿用 C17 harmonic69 的 train-fit 表示法。E01–E08 共用 C02/M 的已封存參考與校準；E09–E12 使用相同 harmonic69／learned diagonal 空間，透過 `core.openset` factory 建立 LW 或 k-NN，僅以另一顆馬達的已知資料校準。

| ID | 分類器與距離 | detector |
|---|---|---|
| E01 | identity、分層子集、距離加權5NN | C02/M |
| E02 | hard600、同一子集、距離加權5NN | C02/M |
| E03 | identity、全部已知 train、距離加權5NN | C02/M |
| E04 | hard600、全部已知 train、距離加權5NN | C02/M |
| E05 | identity、每類一個平均中心 | C02/M |
| E06 | hard600、每類一個平均中心 | C02/M |
| E07 | hard600、每類三個 KMeans 中心 | C02/M |
| E08 | hard600、子集、energy 分類（Eq.15） | C02/M |
| E09 | E03 分類器 | harmonic69/LW |
| E10 | E04 分類器 | hard600/LW |
| E11 | E03 分類器 | harmonic69/k-NN |
| E12 | E04 分類器 | hard600/k-NN |

12×3×3=108 評估；每組涵蓋三個 RPM。k-NN k=5、distance、brute、p=2、單執行緒。metric 沿用 hard600：每類每 RPM 最多20筆、固定同類 target k=3、非負對角權重、pull/push=.5/.5、identity ridge=.01、600 iterations/2000 function evaluations、ftol=1e-9、gtol=1e-6。單中心與 KMeans 使用全部 known train；KMeans 固定三中心、n_init=10、max_iter=300、tol=1e-4，seed 經 default_rng 轉給套件。factory q=.95、LW、k=5、score>1 拒絕，沿用父協定實值。

Energy 使用論文 Eq.15 的三項：query 到假定類別 target 的距離、query 被異類入侵的 hinge、query 入侵 train target 周界的反向 hinge；target 依原 harmonic69 歐氏距離選定，metric 不重 fit。使用原式求和、mu=.5、margin=1，沒有為 test 改係數。這個分類規則接在專案的正規化對角 objective 後，並非完整 PSD LMNN 重現，也不是 OOD energy logits 方法。

訓練與推論各階段預算1800秒、C槽保留1 GB、產物預估300 MB。超時保存已完成 cell，使用同 protocol 續跑；禁止縮減難類或改 seed。選擇規則為 none，不產生 winner。主驗收沿用 `core/fault_type_reliability.py` 完整 CONTRACT；本批只有一組已知配置，不能宣稱 R2／R3。

## 參考論文與改編

- Weinberger、Saul（2009），*Distance Metric Learning for Large Margin Nearest Neighbor Classification*，JMLR 10:207–244，[原文](https://jmlr.org/papers/volume10/weinberger09a/weinberger09a.pdf)。§3.5 Eq.15 是 E08 的分類規則；本專案將 PSD metric 改成既有非負對角權重、固定分層子集與 identity ridge。作者的原式求解與本站 L-BFGS-B 不同，收斂只表示本站停止條件成立。
- Cover、Hart（1967），*Nearest Neighbor Pattern Classification*，IEEE TIT 13:21–27，[原文](https://isl.stanford.edu/~cover/papers/transIT/0021cove.pdf)。E01–E04 為距離加權5NN變體，不援用 IID 漸近保證。
- Snell、Swersky、Zemel（2017），*Prototypical Networks for Few-shot Learning*，NIPS30，[會議全文](https://papers.nips.cc/paper/2017/file/cb8da6767461f2812ae4290eac7cbc42-Paper.pdf)。Eq.1–2 的平均中心／平方距離提供 E05–E06 的構件；沒有神經 embedding、episode 訓練，不能稱 ProtoNet 重現。
- MacQueen（1967），*Some methods for classification and analysis of multivariate observations*，第五屆 Berkeley Symposium 1:281–297，[機構索引](https://digicoll.lib.berkeley.edu/record/113015?v=pdf)。E07 是每類批次 KMeans 三中心＋metric 最近中心的本站組合；未宣稱原文線上算法。使用 sklearn 1.7.2 已安裝實作，不新增依賴。
- Ledoit、Wolf（2004），*A well-conditioned estimator for large-dimensional covariance matrices*，JMVA 88:365–411，[作者全文](https://www.ledoit.net/Well-conditioned2004.pdf)。E09–E10 沿用正式 factory；縮放後再估 LW 可能改變正則化，不能假設分數不變。

## 預期成果與反證

H13a：hard600 相對 identity 改善配對分類；E02/E01、E04/E03、E06/E05 檢驗。H13b：中心或 energy 規則改善同一 metric 的分類；E06/E04、E07/E06、E08/E02 檢驗。H13c：學習距離同時改善 detector 的排序與拒絕；E10/E09、E12/E11 檢驗。全程報 healthy 完整誤報、unknown recall、每類召回、每 motor/RPM、所有 seeds。只改善平均但 class collapse／安全 gate 未過時，假說僅獲局部支持。尚無數值預測；所有資料已有 test 曝露。

## 程式碼與輸出

| 範圍 | 路徑／用途 |
|---|---|
| 新邏輯 | `core/fault_type_metric_classifiers.py` |
| 實驗入口 | `experiments/fault_type_metric_classification.py`：lock/fit/evaluate/verify/report/smoke；run(...) 與 main() |
| 共用 | `core/fault_type_continuous.py`、`core/fault_type_reliability.py`、`core/openset.py`、既有 metrics_v2、FeatureStore；不改封存來源 |
| 舊權重 | `output/fault_type_solver_fit/2026-10-02-23-51-52/diagnosis.json` 與九份 hard600 checkpoints |
| 舊協定 | `output/fault_type_continuous_registry/2026-10-02-18-40-41/protocol.json` |
| 測試 | `tests/test_fault_type_metric_classifiers.py` |
| 紀錄與結果 | `logs/fault_type_metric_classification_*/`、`output/fault_type_metric_classification_*/`；大型結果依既有 archive 備份 D槽 |
| 健康／網頁 | `experiments/health/`、`web/`：N/A，本批不修改、不新增展示 |

CLI：`.venv310/Scripts/python.exe -m experiments.fault_type_metric_classification --help`。lock 後提交 protocol，再 fit；fit lock 後提交，再 evaluate；verify 從封存模型重推全部已保存逐樣本輸出；report 僅重算與配對，不調參。歷史報告不覆寫，新摘要置於本批 output，研究索引依使用者要求另存獨立版本目錄。
