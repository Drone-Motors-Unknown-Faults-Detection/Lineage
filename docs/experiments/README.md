# 實驗技術報告

本目錄一檔對應 `experiments/` 裡的一支程式。白話版仍在 [Experiments_Guide.md](../Experiments_Guide.md)。實驗八（健康指數）的資料能力與已跑完的 54 列彙總，另見 [exp8_health_monitoring_workflow.md](../exp8_health_monitoring_workflow.md)。

每份報告分開寫實驗方法、理論、論文出處、預期成果、程式路徑。預期是設計時要看到的現象。已跑出來的數字放在「已記錄的實測」，出處寫在該節。

| 編號 | 報告 | 程式 | 在問什麼 |
|---|---|---|---|
| 實驗一 | [exp1_cold_start](exp1_cold_start.md) | `experiments/exp1_cold_start.py` | 只用 `8screws` 建基準，九種故障抓不抓得到 |
| 實驗二 | [exp2_scale_growth](exp2_scale_growth.md) | `experiments/exp2_scale_growth.py` | 未知樣本能否分群、經確認後擴張量尺 |
| 實驗三 | [exp3_trend](exp3_trend.md) | `experiments/exp3_trend.py` | 漸進鬆脫與突發切換能否從分數序列分開 |
| 實驗四 | [exp4_polar_map](exp4_polar_map.md) | `experiments/exp4_polar_map.py` | 故障方向與半徑能不能對上配置 |
| 實驗五 | [exp5_cross_condition](exp5_cross_condition.md) | `experiments/exp5_cross_condition.py` | 某一工況的健康基準能否搬到別的工況 |
| 實驗六 | [exp6_osr_benchmark](exp6_osr_benchmark.md) | `experiments/exp6_osr_benchmark.py` | 七種單類偵測器在同一校準規則下誰的誤報較低 |
| 實驗六 | [exp6_formal_benchmark](exp6_formal_benchmark.md) | `experiments/exp6_formal_benchmark.py` | 主線 Mahalanobis 與 k-NN 的單次正式比較 |
| 實驗六 | [exp6_matrix](exp6_matrix.md) | `experiments/exp6_matrix.py` | 上面那次比較的 9×3×2 可續跑矩陣 |
| 實驗六 | [exp6_aggregate](exp6_aggregate.md) | `experiments/aggregate_exp6.py` | 把 exp6 矩陣已完成的 summary 彙總，缺檔就停 |
| 實驗七 | [exp7_compare_openset](exp7_compare_openset.md) | `experiments/compare_openset.py` | 單一工況上、同一 split 的 Mahalanobis 對 k-NN |
| 實驗八 | [exp8_health_index_benchmark](exp8_health_index_benchmark.md) | `experiments/health_index_benchmark.py` | 把 Open Set 分數映成相對健康指數後的分離度 |
| 實驗八 | [exp8_health_index_matrix](exp8_health_index_matrix.md) | `experiments/health_index_matrix.py` | 健康指數的 9×3×2 可續跑矩陣 |
| 實驗八 | [exp8_health_monitor](exp8_health_monitor.md) | `experiments/health_monitor.py` | 單工況逐窗輸出健康指數、趨勢與告警 |

實驗七、八在 2026-10-03 補上編號，依程式加入 repo 的時間排：`compare_openset` 是 2026-09-17，健康指數三支是 2026-09-20。程式檔名沒有改，報告檔名與標題帶編號。尚未實作的規劃接著排：實驗九 AutoEncoder（#13）、實驗十遷移學習（#14）、實驗十一 Ancestor 對照（#15）、實驗十二混淆矩陣與 t-SNE（#16），見 [TODO.md](../../TODO.md)。

## 各實驗的檔案位置

一個實驗的程式常分散在 `experiments/`、`core/`、`health/`、`web/`、`tests/` 與 `reports/`。下表列出每個實驗用到的全部位置；各報告的「程式碼與輸出」節有逐函式說明。

| 編號 | 入口 | 邏輯 | 測試 | Web | 已提交的紀錄與結果 | 其他文件 |
|---|---|---|---|---|---|---|
| 實驗一 | `experiments/exp1_cold_start.py` | `core/monitor.py`、`core/openset.py`、`core/mahalanobis.py`、`core/data.py` | 無專屬（`tests/test_openset.py` 測共用偵測器） | `web/live.py`、`web/static/index.html` 分數串流圖；`web/experiments.py` 實驗頁 | `logs/`、`output/exp1_cold_start/` | `docs/Experiments_Guide.md` §2 |
| 實驗二 | `experiments/exp2_scale_growth.py` | `ScaleGrowthSession`、`core/monitor.py`、`core/geometry.py` | 無專屬 | `web/live.py`、`web/server.py`、`web/static/index.html` 候選卡；`web/experiments.py` 實驗頁 | `logs/`、`output/exp2_scale_growth/`；`output/web_server/` | `docs/Experiments_Guide.md` §3 |
| 實驗三 | `experiments/exp3_trend.py` | `core/trend.py` | 無專屬 | `web/live.py`、`web/static/index.html` 變化點卡；`web/experiments.py` 實驗頁 | `logs/`、`output/exp3_trend/` | `docs/Experiments_Guide.md` §4 |
| 實驗四 | `experiments/exp4_polar_map.py` | `core/geometry.py`、`core/mahalanobis.py` | `tests/test_geometry.py` | `web/live.py`、`web/static/index.html` 極座標地圖；`web/experiments.py` 實驗頁 | `logs/`、`output/exp4_polar_map/` | `docs/Experiments_Guide.md` §5；`reports/exp6_ancestor_openset_progress.md` P8 |
| 實驗五 | `experiments/exp5_cross_condition.py` | `core/data.py`、`core/monitor.py` | 無專屬 | `web/static/index.html` 資料集下拉；`web/experiments.py` 實驗頁 | `logs/`、`output/exp5_cross_condition/` | `docs/Experiments_Guide.md` §6 |
| 實驗六 | `experiments/exp6_osr_benchmark.py`、`exp6_formal_benchmark.py`、`exp6_matrix.py`、`aggregate_exp6.py` | `core/detectors.py`、`core/openset.py`、`core/formal_data.py` | `tests/test_exp6_benchmark.py`、`test_exp6_matrix.py`、`test_aggregate_exp6.py`、`test_formal_data.py`、`test_openset.py` | `web/experiments.py` 實驗頁 | `logs/`、`output/exp6_osr_benchmark/`；`output/exp6_formal_matrix/` | `docs/Experiments_Guide.md` §7；`reports/exp6_ancestor_openset_progress.md`、`reports/raw_data_audit/`、`reports/github_data_audit/` |
| 實驗七 | `experiments/compare_openset.py` | `core/monitor.py`、`core/openset.py`、`core/mahalanobis.py` | `tests/test_openset.py` | `web/experiments.py` 實驗頁 | 無（輸出目錄名是 `openset_comparison`） | `docs/Experiments_Guide.md` §8 |
| 實驗八 | `experiments/health_index_benchmark.py`、`health_index_matrix.py`、`health_monitor.py` | `health/` 全部模組、`core/openset.py` | `tests/test_health_*.py`（9 檔） | `web/experiments.py` 實驗頁 | `reports/exp8_health_index_results/` | `docs/exp8_health_monitoring_workflow.md`、`docs/health_and_reports.md`、`reports/exp8_health_monitoring_data_capability.md`、`reports/exp8_fault_type_data_requirements.md`、`docs/Experiments_Guide.md` §9 |

Web 頁首可切換即時展示與實驗一～八各頁；實驗頁的目錄與參數在 `web/experiments.py` 的 `CATALOG`，畫面在 `web/static/experiments.js`，每次執行的結果存到 `output/web_server/{ts}/experiments/`。不屬於任何編號實驗的檔案：`web/server.py` 與 `output/web_server/` 是展示本身；`logs/session_analysis/`、`output/session_analysis/`（2026-08-26）是一次 Web session 的事後分析圖，產生它的腳本不在 repo。

共同資料契約：`core.data` 掃描 `data/Step-*/myfeature/{Motor}/{RPM}/{Screws}/*_Group_feature_data_clean.csv`，105 維特徵。健康類是 `8screws`。`make_split` 把健康池切成 train/calibration/holdout = 60/20/20。未知配置不參與擬合與定閾值。正規化分數 `> 1` 判未知。預設 seed 是 42，隨機數走 `numpy.random.default_rng`。
