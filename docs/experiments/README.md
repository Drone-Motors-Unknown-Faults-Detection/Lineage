# 實驗技術報告

本目錄有13個現行實驗編號（1～12及24）、19份方法與操作手冊。實驗六、八各有基準、矩陣與彙總等輔助入口；實驗九共用實驗六的runner，不另外算一套資料協定。各手冊說明資料、擬合／校準／測試、CLI／API／Web、輸出與限制。[Experiments_Guide.md](../Experiments_Guide.md)提供總覽；逐項參數與資料用途請查對應手冊。實驗八的流程另見 [exp8_health_monitoring_workflow.md](../exp8_health_monitoring_workflow.md)。

預期成果與實測分開說明；完整歷史分數連回固定版本的報告或程式產物，不在手冊另抄一套表。載入筆數以本次資料與輸出為準，手冊不替缺少的採集紀錄填值。

| 編號 | 報告 | 程式 | 在問什麼 |
|---|---|---|---|
| 實驗一 | [exp1_cold_start](exp1_cold_start.md) | `experiments/exp1_cold_start.py` | 只用 `8screws` 建基準，九種故障抓不抓得到 |
| 實驗二 | [exp2_scale_growth](exp2_scale_growth.md) | `experiments/exp2_scale_growth.py` | 未知樣本能否分群、經確認後擴張量尺 |
| 實驗三 | [exp3_trend](exp3_trend.md) | `experiments/exp3_trend.py` | 漸進鬆脫與突發切換能否從分數序列分開 |
| 實驗四 | [exp4_polar_map](exp4_polar_map.md) | `experiments/exp4_polar_map.py` | 故障方向與半徑能不能對上配置 |
| 實驗五 | [exp5_cross_condition](exp5_cross_condition.md) | `experiments/exp5_cross_condition.py` | 某一工況的健康基準能否搬到別的工況 |
| 實驗六 | [exp6_osr_benchmark](exp6_osr_benchmark.md) | `experiments/exp6_osr_benchmark.py` | 八種偵測器的排序與誤報；legacy校準方式須另解讀 |
| 實驗六 | [exp6_formal_benchmark](exp6_formal_benchmark.md) | `experiments/exp6_formal_benchmark.py` | 主線 Mahalanobis 與 k-NN 的單次正式比較 |
| 實驗六 | [exp6_matrix](exp6_matrix.md) | `experiments/exp6_matrix.py` | 上面那次比較的 9×3×2 可續跑矩陣 |
| 實驗六 | [exp6_aggregate](exp6_aggregate.md) | `experiments/aggregate_exp6.py` | 把 exp6 矩陣已完成的 summary 彙總，缺檔就停 |
| 實驗七 | [exp7_compare_openset](exp7_compare_openset.md) | `experiments/compare_openset.py` | 單一工況上、同一 split 的 Mahalanobis 對 k-NN |
| 實驗八 | [exp8_health_index_benchmark](exp8_health_index_benchmark.md) | `experiments/health_index_benchmark.py` | 把 Open Set 分數映成相對健康指數後的分離度 |
| 實驗八 | [exp8_health_index_matrix](exp8_health_index_matrix.md) | `experiments/health_index_matrix.py` | 健康指數的 9×3×2 可續跑矩陣 |
| 實驗八 | [exp8_health_index_aggregate](exp8_health_index_aggregate.md) | `experiments/health_index_aggregate.py` | 唯讀重算 54 列，逐欄核對歷史彙總與來源 SHA |
| 實驗八 | [exp8_health_monitor](exp8_health_monitor.md) | `experiments/health_monitor.py` | 單工況逐窗輸出健康指數、趨勢與告警 |
| 實驗九 | [exp9_autoencoder](exp9_autoencoder.md) | `core/detectors.py`（`MLPAutoencoderDet`） | 非線性 AutoEncoder 重建誤差，能不能比線性 PCA 重建更分得開健康與故障 |
| 實驗十 | [exp10_transfer](exp10_transfer.md) | `experiments/exp10_transfer.py` | 目標工況少量健康資料，中心平移遷移划不划算、還是從零冷啟動就好 |
| 實驗十一 | [exp11_ancestor_comparison](exp11_ancestor_comparison.md) | `experiments/exp11_ancestor_comparison.py` | Ancestor 協定下 legacy vs Ledoit–Wolf 的 Accuracy/Balanced Accuracy/macro-F1 對照 |
| 實驗十二 | [exp12_confusion_tsne](exp12_confusion_tsne.md) | `experiments/exp12_confusion_tsne.py` | 開集混淆矩陣與 t-SNE 視覺化，模型區分正常與故障的效果看不看得出來 |
| 實驗二十四 | [exp24_experiment_navigation](exp24_experiment_navigation.md) | `experiments/navigation_data_contract.py`、`navigation_regression.py` | 獨立導覽與原主線計算是否一致；整理歷史七問，不新增研究成績 |

實驗九～十二依序檢查非線性重建、跨工況平移、Ancestor協定對照及可視化。實驗十的direct與adapted／scratch不完全共用測試健康列；實驗十一的legacy分類label固定為-1，與逐類LW的分差混合了分類API差異，不能直接解讀成共變異數估計帶來的改善。實驗十二的t-SNE使用包含known fit列的完整資料池，只作圖像診斷。各手冊列出實際流程與固定產物；入口存在不等於獨立驗收通過。

## 各實驗的檔案位置

實驗八重算補充：`experiments/health_index_aggregate.py`、`tests/test_health_index_aggregate.py`、`docs/experiments/exp8_health_index_aggregate_contract.json`；紀錄寫入 `logs/exp8_health_index_aggregate/` 與 `output/exp8_health_index_aggregate/`，不經 web 層。

一個實驗的程式常分散在 `experiments/`、`core/`、`experiments/health/`、`web/`、`tests/` 與 `reports/`。2026-10-03 刪除的稽核紀錄不列在表內，清單見 [health_and_reports.md](../health_and_reports.md) 第 2.2 節。下表列出每個實驗用到的全部位置；各報告的「程式碼與輸出」節有逐函式說明。

| 編號 | 入口 | 邏輯 | 測試 | Web | 已提交的紀錄與結果 | 其他文件 |
|---|---|---|---|---|---|---|
| 實驗一 | `experiments/exp1_cold_start.py` | `core/monitor.py`、`core/openset.py`、`core/mahalanobis.py`、`core/data.py` | 無專屬（`tests/test_openset.py` 測共用偵測器） | `web/live.py`、`web/static/index.html` 分數串流圖；`web/experiments.py` 實驗頁 | `logs/`、`output/exp1_cold_start/` | `docs/Experiments_Guide.md` §2 |
| 實驗二 | `experiments/exp2_scale_growth.py` | `ScaleGrowthSession`、`core/monitor.py`、`core/geometry.py` | 無專屬 | `web/live.py`、`web/server.py`、`web/static/index.html` 候選卡；`web/experiments.py` 實驗頁 | `logs/`、`output/exp2_scale_growth/`；`output/web_server/` | `docs/Experiments_Guide.md` §3 |
| 實驗三 | `experiments/exp3_trend.py` | `core/trend.py` | 無專屬 | `web/live.py`、`web/static/index.html` 變化點卡；`web/experiments.py` 實驗頁 | `logs/`、`output/exp3_trend/` | `docs/Experiments_Guide.md` §4 |
| 實驗四 | `experiments/exp4_polar_map.py` | `core/geometry.py`、`core/mahalanobis.py` | `tests/test_geometry.py` | `web/live.py`、`web/static/index.html` 極座標地圖；`web/experiments.py` 實驗頁 | `logs/`、`output/exp4_polar_map/` | `docs/Experiments_Guide.md` §5 |
| 實驗五 | `experiments/exp5_cross_condition.py` | `core/data.py`、`core/monitor.py` | 無專屬 | `web/static/index.html` 資料集下拉；`web/experiments.py` 實驗頁 | `logs/`、`output/exp5_cross_condition/` | `docs/Experiments_Guide.md` §6 |
| 實驗六 | `experiments/exp6_osr_benchmark.py`、`exp6_formal_benchmark.py`、`exp6_matrix.py`、`aggregate_exp6.py` | `core/detectors.py`、`core/openset.py`、`core/formal_data.py` | `tests/test_exp6_benchmark.py`、`test_exp6_matrix.py`、`test_aggregate_exp6.py`、`test_formal_data.py`、`test_openset.py` | `web/experiments.py` 實驗頁 | `logs/`、`output/exp6_osr_benchmark/`；`output/exp6_formal_matrix/` | `docs/Experiments_Guide.md` §7 |
| 實驗七 | `experiments/compare_openset.py` | `core/monitor.py`、`core/openset.py`、`core/mahalanobis.py` | `tests/test_openset.py` | `web/experiments.py` 實驗頁 | 無（輸出目錄名是 `openset_comparison`） | `docs/Experiments_Guide.md` §8 |
| 實驗八 | `experiments/health_index_benchmark.py`、`health_index_matrix.py`、`health_monitor.py` | `experiments/health/` 全部模組、`core/openset.py` | `tests/test_health_*.py`（9 檔） | `web/experiments.py` 實驗頁 | `reports/exp8_health_index_results/` | `docs/exp8_health_monitoring_workflow.md`、`docs/health_and_reports.md`、`docs/Experiments_Guide.md` §9 |
| 實驗九 | 無獨立入口（`core/detectors.py` 新增偵測器，透過 `experiments/exp6_osr_benchmark.py` 執行） | `core/detectors.py`（`MLPAutoencoderDet`） | `tests/test_exp9_autoencoder.py` | 無 | `logs/exp6_osr_benchmark/`、`output/exp6_osr_benchmark/`（與既有 exp6 輸出合併） | 無 |
| 實驗十 | `experiments/exp10_transfer.py` | `core/monitor.py`、`core/data.py` | `tests/test_exp10_transfer.py` | 無 | `logs/exp10_transfer/`、`output/exp10_transfer/` | 無 |
| 實驗十一 | `experiments/exp11_ancestor_comparison.py` | `core/monitor.py`、`core/mahalanobis.py`、`core/data.py` | `tests/test_exp11_ancestor_comparison.py` | 無 | `logs/exp11_ancestor_comparison/`、`output/exp11_ancestor_comparison/` | `docs/Mahalanobis_Improvement.md`（歷史對照） |
| 實驗十二 | `experiments/exp12_confusion_tsne.py` | `experiments/exp11_ancestor_comparison.py`（匯入 `build_ancestor_monitor`）、`core/monitor.py`、`core/data.py` | `tests/test_exp12_confusion_tsne.py` | 無 | `logs/exp12_confusion_tsne/`、`output/exp12_confusion_tsne/` | 無 |
| 實驗二十四 | `experiments/navigation_data_contract.py`、`navigation_regression.py` | 沿用 `core/monitor.py`、`core/openset.py`、`core/geometry.py`、exp2/3 與 `web/live.py` | `tests/test_navigation_guide.py`、`test_integration_navigation.py` | 獨立 `web/guide.py`、`guide.html/js/css` | `logs/navigation_*`、`output/navigation_*`、`logs/web_guide`、`output/web_guide` | `docs/navigation/exp24_*.md`；`docs/integration_20261008` |

Web 頁首可切換即時展示與實驗一～八各頁；實驗頁的目錄與參數在 `web/experiments.py` 的 `CATALOG`，畫面在 `web/static/experiments.js`，每次執行的結果存到 `output/web_server/{ts}/experiments/`。不屬於任何編號實驗的檔案：`web/server.py` 與 `output/web_server/` 是展示本身；`logs/session_analysis/`、`output/session_analysis/`（2026-08-26）是一次 Web session 的事後分析圖，產生它的腳本不在 repo。

共同資料入口：`core.data` 掃描 `data/Step-*/myfeature/{Motor}/{RPM}/{Screws}/*_Group_feature_data_clean.csv`，讀105維特徵；健康類是 `8screws`。一般健康基準由`make_split`洗牌資料列後分train/calibration/holdout約60/20/20，正規化分數`> 1`判未知，seed預設42。多類已知配置、legacy門檻、持續學習確認與實驗四的幾何校準各有不同資料用途，請查對應手冊；不能用這段摘要替它們保證沒有洩漏。T1／T2／T3是不同馬達個體，raw錄製／視窗獨立性與單位仍須來源證據。
