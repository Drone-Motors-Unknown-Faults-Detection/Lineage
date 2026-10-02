# 實驗技術報告

本目錄一檔對應 `experiments/` 裡的一支程式。白話版仍在 [Experiments_Guide.md](../Experiments_Guide.md)。健康指數的資料能力與已跑完的 54 列彙總，另見 [health_monitoring_workflow.md](../health_monitoring_workflow.md)。

每份報告分開寫實驗方法、理論、論文出處、預期成果、程式路徑。預期是設計時要看到的現象。已跑出來的數字放在「已記錄的實測」，出處寫在該節。

| 報告 | 程式 | 在問什麼 |
|---|---|---|
| [exp1_cold_start](exp1_cold_start.md) | `experiments/exp1_cold_start.py` | 只用 `8screws` 建基準，九種故障抓不抓得到 |
| [exp2_scale_growth](exp2_scale_growth.md) | `experiments/exp2_scale_growth.py` | 未知樣本能否分群、經確認後擴張量尺 |
| [exp3_trend](exp3_trend.md) | `experiments/exp3_trend.py` | 漸進鬆脫與突發切換能否從分數序列分開 |
| [exp4_polar_map](exp4_polar_map.md) | `experiments/exp4_polar_map.py` | 故障方向與半徑能不能對上配置 |
| [exp5_cross_condition](exp5_cross_condition.md) | `experiments/exp5_cross_condition.py` | 某一工況的健康基準能否搬到別的工況 |
| [exp6_osr_benchmark](exp6_osr_benchmark.md) | `experiments/exp6_osr_benchmark.py` | 七種單類偵測器在同一校準規則下誰的誤報較低 |
| [exp6_formal_benchmark](exp6_formal_benchmark.md) | `experiments/exp6_formal_benchmark.py` | 主線 Mahalanobis 與 k-NN 的單次正式比較 |
| [exp6_matrix](exp6_matrix.md) | `experiments/exp6_matrix.py` | 上面那次比較的 9×3×2 可續跑矩陣 |
| [aggregate_exp6](aggregate_exp6.md) | `experiments/aggregate_exp6.py` | 把 exp6 矩陣已完成的 summary 彙總，缺檔就停 |
| [compare_openset](compare_openset.md) | `experiments/compare_openset.py` | 單一工況上、同一 split 的 Mahalanobis 對 k-NN |
| [health_index_benchmark](health_index_benchmark.md) | `experiments/health_index_benchmark.py` | 把 Open Set 分數映成相對健康指數後的分離度 |
| [health_index_matrix](health_index_matrix.md) | `experiments/health_index_matrix.py` | 健康指數的 9×3×2 可續跑矩陣 |
| [health_monitor](health_monitor.md) | `experiments/health_monitor.py` | 單工況逐窗輸出健康指數、趨勢與告警 |

共同資料契約：`core.data` 掃描 `data/Step-*/myfeature/{Motor}/{RPM}/{Screws}/*_Group_feature_data_clean.csv`，105 維特徵。健康類是 `8screws`。`make_split` 把健康池切成 train/calibration/holdout = 60/20/20。未知配置不參與擬合與定閾值。正規化分數 `> 1` 判未知。預設 seed 是 42，隨機數走 `numpy.random.default_rng`。
