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
| 實驗八 | [exp8_health_index_aggregate](exp8_health_index_aggregate.md) | `experiments/health_index_aggregate.py`（本輪新增） | 唯讀重算 54 列，逐欄核對歷史彙總與來源 SHA |
| 實驗八 | [exp8_health_monitor](exp8_health_monitor.md) | `experiments/health_monitor.py` | 單工況逐窗輸出健康指數、趨勢與告警 |
| 實驗九 | [exp9_autoencoder](exp9_autoencoder.md) | `core/detectors.py`（`MLPAutoencoderDet`） | 非線性 AutoEncoder 重建誤差，能不能比線性 PCA 重建更分得開健康與故障 |
| 實驗十 | [exp10_transfer](exp10_transfer.md) | `experiments/exp10_transfer.py` | 目標工況少量健康資料，中心平移遷移划不划算、還是從零冷啟動就好 |
| 實驗十一 | [exp11_ancestor_comparison](exp11_ancestor_comparison.md) | `experiments/exp11_ancestor_comparison.py` | Ancestor 協定下 legacy vs Ledoit–Wolf 的 Accuracy/Balanced Accuracy/macro-F1 對照 |
| 實驗十二 | [exp12_confusion_tsne](exp12_confusion_tsne.md) | `experiments/exp12_confusion_tsne.py` | 開集混淆矩陣與 t-SNE 視覺化，模型區分正常與故障的效果看不看得出來 |
| 實驗二十四 | [exp24_experiment_navigation](exp24_experiment_navigation.md) | `experiments/navigation_data_contract.py`、`navigation_regression.py` | 獨立導覽與原主線計算是否一致；整理歷史七問，不新增研究成績 |

實驗七、八在 2026-10-03 補上編號，依程式加入 repo 的時間排：`compare_openset` 是 2026-09-17，健康指數三支是 2026-09-20。程式檔名沒有改，報告檔名與標題帶編號。實驗九～十二（#13～#16）已在本輪完成：AE 偵測器 AUROC 持平、誤報略低；中心平移遷移修好了排序但沒修好校準，不如目標端從零冷啟動；Ancestor 協定下 Ledoit–Wolf 相對 legacy 的 Balanced Accuracy／macro-F1 絕對提升超過 78 pp，遠超 5 pp 門檻；混淆矩陣把這個落差變成可見的畫面。

## 共用模型生命週期

`core.monitor.OpenSetMonitor` 建構後尚未擬合。`score()`、`classify()`、`project()`、`summary()` 都要求完整成功的擬合，否則丟出 `RuntimeError` 並要求成功呼叫 `fit_initial()`。健康基準只用 healthy train 擬合 scaler、detector 與 PCA，known calibration 設門檻；未知資料不參與擬合與校準。

`fit_initial()` 與 `_refit()` 開始即撤銷有效旗標，所有模型及摘要狀態完成後才恢復。重擬合失敗時禁止混用前次模型與新 scaler；操作者須明確重新建立健康基準。`add_class()` 使用已確認配置的完整資料池重新擬合，沒有原子回滾保證；失敗後已改動的 known／splits 不能當作有效模型。無效或重複配置若在註冊前被拒，原模型仍可使用。

`holdout(config)` 只讀既有 splits，不使用推論 guard，未註冊配置保留 `KeyError`。成功擬合後，Mahalanobis-LW／k-NN 均以正規化分數大於 1 拒絕；PolarMap 幾何不受本生命週期說明改動。回歸入口為 `tests/test_monitor_guard.py`、`tests/test_openset.py` 與 `tests/test_geometry.py`。

## Web 串流生命週期

`web.experiments.CATALOG` 的 stream 旗標決定可播放的實驗：exp1、exp3、exp4、exp8_monitor。既有 `run()` 批次與 `iter_run()` 逐步計算共用實驗邏輯；展示編排不自行計算另一套指標。使用 `python -m web.server --bind-address 127.0.0.1 --data-root data --port 8600` 啟動本機展示，再在實驗卡片選批次執行或「邊跑邊畫」。

`GET /api/experiments/{id}/stream` 接受 JSON 物件 params 與有限 rate；速率限制在 1～1000 筆／秒，只控制播放節奏。SSE 事件從 start 開始，再推送 scores／tick／window 等實驗事件，完成才發 done。done 的 payload 已由 runner 存入 `output/web_server/{時間戳}/experiments/`，帶 `streamed: true`；停止或失敗沒有 done 就不得當作完整結果。

批次與 SSE 使用同一執行鎖，另一工作執行中即拒絕。瀏覽器停止或斷線時中止後續播放；已交給 executor 的一次計算可能仍需完成。finally 關閉 generator，即使 close 丟例外也釋放鎖。完成、取消或錯誤後，待伺服器釋放鎖再重試；不能以重新點擊掩蓋中斷。回歸入口為 `tests/test_stream_integration.py`、`tests/test_iter_run.py`、`tests/test_health_monitor.py`。

獨立導覽另用 [UI 操作腳本](../navigation/exp24_UI操作腳本.md) 的 WebSocket session：重連不自動播放，模型失敗須明確重設或重建。兩個入口均為 CSV 重播，不保證實體時間、原始視窗獨立或部署誤報率。現行 server／guide 的部分錯誤會把例外文字傳給 client，可能包含私人路徑；這項限制仍由 [#28](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/28) 追蹤，不能宣稱全部錯誤回應已去敏。

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
| 實驗二十四 | `experiments/navigation_data_contract.py`、`navigation_regression.py` | 沿用 `core/monitor.py`、`core/openset.py`、`core/geometry.py`、exp2/3 與 `web/live.py` | `tests/test_navigation_guide.py`、`test_integration_navigation.py` | 獨立 `web/guide.py`、`guide.html/js/css` | `logs/navigation_*`、`output/navigation_*`、`logs/web_guide`、`output/web_guide` | `docs/navigation/exp24_*.md`；`reports/Andy_20261008_分支整合` |

Web 頁首可切換即時展示與實驗一～八各頁；實驗頁的目錄與參數在 `web/experiments.py` 的 `CATALOG`，畫面在 `web/static/experiments.js`，每次執行的結果存到 `output/web_server/{ts}/experiments/`。不屬於任何編號實驗的檔案：`web/server.py` 與 `output/web_server/` 是展示本身；`logs/session_analysis/`、`output/session_analysis/`（2026-08-26）是一次 Web session 的事後分析圖，產生它的腳本不在 repo。

共同資料契約：`core.data` 掃描 `data/Step-*/myfeature/{Motor}/{RPM}/{Screws}/*_Group_feature_data_clean.csv`，105 維特徵。健康類是 `8screws`。`make_split` 把健康池切成 train/calibration/holdout = 60/20/20。未知配置不參與擬合與定閾值。正規化分數 `> 1` 判未知。預設 seed 是 42，隨機數走 `numpy.random.default_rng`。
