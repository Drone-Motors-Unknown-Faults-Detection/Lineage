# 實驗一：冷啟動未知偵測

程式：`experiments/exp1_cold_start.py`，函式 `run(pools, ...)` 與 `main()`。

問題：只拿 `8screws` 擬合健康基準時，其餘螺絲配置會不會被打成未知，健康 holdout 的誤報會落在哪。

## 實驗方法

1. `core.runner.resolve_dataset` 載入一組工況。CLI 預設由 `add_dataset_args` 指定馬達與轉速，文件裡的對照跑法是 T1、8000 rpm。
2. `OpenSetMonitor.fit_initial()` 只用健康池。`make_split` 切 60/20/20。訓練集擬合 `RobustScaler` 與偵測器，校準集的距離分位數把閾值正規化成 1。
3. 預設 `--openset-method mahalanobis`、`--method ledoit_wolf`、`--confidence 0.95`、`--seed 42`。改成 `knn` 時用 `--knn-neighbors`，預設 5。
4. 健康 holdout 算誤報率 `(score > 1)`。每個未知配置用全部樣本算偵測率、分數中位數，以及相對健康 holdout 的 AUROC。未知樣本不進 `fit`。
5. 彙總 `healthy_fp_rate`、`macro_detect_rate`、`macro_auroc`。

```bash
venv/bin/python -m experiments.exp1_cold_start --motor T1 --rpm 8000rpm
```

## 理論

健康樣本在 105 維特徵上估一個位置與散布。新窗口的分數是它離這個健康雲多遠，再除以校準集第 95 百分位。百分位設在 0.95，所以校準集裡約 5% 的健康窗口會被標成超過 1。holdout 誤報不必剛好等於 5%：校準筆數少的時候，分位數本身會晃。

Mahalanobis 距離用類別平均與共變異數。105 維、單類、訓練筆數有限時，樣本共變異數容易病態，所以預設用 Ledoit–Wolf 把樣本共變異數往一個結構目標收縮。k-NN 路徑不估共變異數，改算到該類訓練集 k 個近鄰的平均距離，再各自用校準分位數正規化。

這一步只回答「像不像目前已知的健康」。它不輸出故障名稱，也不估計剩餘壽命。

## 參考論文

- P. C. Mahalanobis (1936), “On the Generalised Distance in Statistics,” *Proceedings of the National Institute of Sciences of India*, 2(1), 49–55。重印 DOI [10.1007/s13171-019-00164-5](https://doi.org/10.1007/s13171-019-00164-5)。
- O. Ledoit and M. Wolf (2004), “A well-conditioned estimator for large-dimensional covariance matrices,” *Journal of Multivariate Analysis*, 88(2), 365–411。DOI [10.1016/S0047-259X(03)00096-4](https://doi.org/10.1016/S0047-259X(03)00096-4)。
- T. Cover and P. Hart (1967), “Nearest Neighbor Pattern Classification,” *IEEE Transactions on Information Theory*, 13(1), 21–27。DOI [10.1109/TIT.1967.1053964](https://doi.org/10.1109/TIT.1967.1053964)。本實驗的 k-NN 用的是類別訓練集上的平均 k 近鄰距離，門檻仍是校準分位數，這段正規化是本專案的操作約定。
- 60/20/20、分數 `> 1` 判未知、`RobustScaler` 只在訓練集擬合：本專案操作約定，寫在 `core/data.py` 與 `core/openset.py`。

## 預期成果

九種未知配置的偵測率要高，AUROC 要明顯高於 0.5。健康 holdout 誤報應靠近校準名義值 5%，允許因為校準樣本少而偏高。若某種故障的偵測率接近健康誤報，或 AUROC 接近 0.5，這組特徵與這個偵測器就沒有把該配置和健康分開。

## 已記錄的實測

[Experiments_Guide.md](../Experiments_Guide.md) 記載 T1/8000 rpm、預設 Mahalanobis：九種故障偵測率 100%，AUROC 1.0，健康誤報 10.9%。該手冊把偏離 5% 歸因於校準集約 62 筆。這是跑完之後的數字，不要把它寫回上面的預期。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/exp1_cold_start.py` | `run`、`iter_run`、`_auroc`、`_make_figure`、`main`；`run` 把 `iter_run` 跑完取最後的 `result`（2026-10-03 起） |
| `core/monitor.py` | `OpenSetMonitor.fit_initial`、`score`、`holdout` |
| `core/data.py` | `HEALTHY`、`make_split`、`load_pools` |
| `core/openset.py` | `create_openset_detector` |
| `core/mahalanobis.py` | Ledoit–Wolf 與 legacy 共變異數 |
| `core/logger.py` | `setup_run("exp1_cold_start")` |
| `core/runner.py` | `add_dataset_args`、`add_openset_args`、`resolve_dataset`、`save_json` |
| `web/live.py` | 展示串流走 `ScaleGrowthSession` 裡的同一個 `OpenSetMonitor`，階段 0 即本實驗的擬合 |

輸出：

- `logs/exp1_cold_start/{時間戳}.log`
- `output/exp1_cold_start/{時間戳}/results.csv`
- `output/exp1_cold_start/{時間戳}/summary.json`
- `output/exp1_cold_start/{時間戳}/detect_rates.png`

### 散在其他位置的相關檔案

- 測試：沒有專屬測試；共用的 `core/openset.py`、`core/mahalanobis.py` 由 `tests/test_openset.py` 涵蓋。
- Web：`web/live.py` 的開集分數串流圖、偵測統計表；`web/static/index.html` 對應畫面。
- 已提交紀錄：`logs/exp1_cold_start/`、`output/exp1_cold_start/`（3 次執行）。
- 其他文件：[Experiments_Guide.md](../Experiments_Guide.md) 第 2 節。
- Web 實驗頁：頁首「實驗一」，`web/experiments.py` 的 `CATALOG` 項目 `exp1` 呼叫本程式的 `run()`，畫面在 `web/static/experiments.js` 的 `RENDER.exp1`；結果存到 `output/web_server/{ts}/experiments/exp1_{時間}.json`。
- 邊跑邊畫：頁面上的「⏵ 邊跑邊畫」改走 `iter_run()`，經 `web/experiments.py` 的 `ExperimentRunner.stream()` 與 `web/server.py` 的 `StreamHandler`（Server-Sent Events，`GET /api/experiments/{id}/stream`）逐步推送，速度 20／80／400 筆/秒可選。`iter_run()` 只多吐出中間事件，計算與 `run()` 相同；`tests/test_iter_run.py` 比對兩者輸出。每筆開集分數依序播放（先健康 holdout、再九種故障），統計列逐配置出現。

2026-10-08 整合：串流來源 PR #36 / `544d4ed8c6516622e2f46c095351f9483a61635c`，本輪只抽取實驗一／三／四，不含 health_monitor（#35 尚未修復）。計算與 main 原 run 配對後才可合入；細節見 [串流整合契約](../../reports/Andy_20261008_分支整合/streaming_contract.md)。
