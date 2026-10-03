# 實驗13：模型實際輸入來源重建

2026-10-03。這份補充手冊先於新 verifier 實作；不修改已封存的實驗13方法、參數或權重。主手冊見 [exp13](exp13_metric_classification.md)。

方法：從原 manifest 讀取 known train／calibration，重建 harmonic69 與 hard600 train-only transform；比較模型內實際 k-NN arrays、energy reference、平均／KMeans中心。factory detector 用同一 train/cal重新計算 covariance、neighbor arrays與calibration quantiles，再逐欄核對；校準不能混入 reference。這是數值來源核對，並非新研究runs。

預期：九份 bundle 都可重建；故意把 calibration送入 reference或替換 classifier fit array應失敗。UNKNOWN採集證據與歷史 test曝露不會因重建通過而取得PASS。KMeans與factory的來源沿用主手冊書目；逐陣列核對是本站工程契約。

## 程式碼與輸出

入口 `experiments/fault_type_metric_source_verification.py`，run(...)／main()；讀取 `experiments/fault_type_metric_classification.py`、`core/fault_type_metric_classifiers.py`、`core/openset.py`、FeatureStore。測試 `tests/test_fault_type_metric_source_verification.py`。紀錄 `logs/fault_type_metric_source_verification/`、結果 `output/fault_type_metric_source_verification/`。`experiments/health/`、`web/` 均 N/A。CLI 接收 --protocol、--lock、--data-root，不載入任何test數值。僅新增驗證程式與文件，不改實驗13封存來源。
