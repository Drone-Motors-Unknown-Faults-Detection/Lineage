# 實驗二：量尺擴張

程式：`experiments/exp2_scale_growth.py`。批次入口是 `run()`；即時展示驅動的是 `ScaleGrowthSession`。

問題：故障一種一種出現時，系統能否在不看標籤的情況下把未知窗口堆進隔離區、用 HDBSCAN 提出候選叢，再在確認當下才用標籤決定收進量尺或退回。

## 實驗方法

1. `ScaleGrowthSession` 先做實驗一的 `fit_initial()`，已知類只有 `8screws`。
2. `process(x, truth)` 對每一筆打分。`truth` 只存進隔離區，分群時不讀它。分數 `> 1` 且 `classify` 回傳 `None` 才算未知。分數還要 `> quarantine_margin`（預設 2.0）才進隔離區。邊界上 1.0 到 2.0 的點只警報。
3. 隔離區長度達到 `min_cluster_size`（25），而且距離上次嘗試已滿 `recluster_every`（10）筆，才呼叫 `_try_cluster()`。
4. HDBSCAN 跑在 scaler 之後的特徵上。參數階梯寫在 `_cluster_params`：先 `(25, 3)`；隔離區 ≥ 75 再試 `(15, 3)`；≥ 100 再試 `(10, 2)`。候選叢仍須至少 25 筆。噪點標籤 `-1` 不算叢。
5. `confirm()` 才讀叢內多數 `truth`。多數類還沒學過則 `add_class` 後整組重擬合，動作 `learned`。多數類已在量尺裡則清掉該叢，動作 `rejected_known`，量尺不變。
6. 批次 `run()` 依 `config_sort_key` 由輕到重注入未知配置。每段最多 600 筆。找到第一個 `learned` 就停，記錄發現筆數、叢大小、純度、該類 holdout 準確率、健康 holdout 準確率。

```bash
venv/bin/python -m experiments.exp2_scale_growth --motor T1 --rpm 8000rpm
venv/bin/python -m experiments.exp2_scale_growth --sequence 5screws 3_14screws
```

## 理論

開放集拒絕只說「不屬於已知類」。要把新類收進量尺，還得先看到一群彼此靠近、又離已知類夠遠的點。HDBSCAN 在互達距離上建階層，再用 `min_cluster_size` 切穩定叢，其餘標成噪點。密度階梯放寬的是搜尋時的密度門檻；25 筆的候選下限沒有放寬。

兩段閾值是本專案的操作約定。偵測線 1.0 沿用校準分位數。隔離線 2.0 放在「校準誤報只略高於 1」和「故障分數遠高於 1」之間，避免誤報自己聚成假叢。確認步驟模擬操作員：分群期間標籤不參與擬合，這是實驗效度的條件。

`PolarMap` 在每次 `__init__` 與成功 `add_class` 後重建。方向分數不改已知/未知判定，幾何說明見 [exp4_polar_map.md](exp4_polar_map.md)。

## 參考論文

- R. J. G. B. Campello, D. Moulavi, and J. Sander (2013), “Density-Based Clustering Based on Hierarchical Density Estimates,” *PAKDD*, Lecture Notes in Computer Science 7819, 160–172。DOI [10.1007/978-3-642-37456-2_14](https://doi.org/10.1007/978-3-642-37456-2_14)。實作套件是 `hdbscan`。
- 馬氏距離與 Ledoit–Wolf 出處同 [exp1_cold_start.md](exp1_cold_start.md)。
- `quarantine_margin=2.0`、重分群每 10 筆、密度階梯 `(25,3)/(15,3)/(10,2)`：本專案操作約定，寫在 `ScaleGrowthSession.__init__` 與 `_cluster_params`。

## 預期成果

每種注入配置都應在 600 筆內出現 `learned`，叢純度要高。已知類變多之後，自類 holdout 準確率可以下降，健康 holdout 不應崩掉。若 600 筆內 `discovered=false`，或純度長期明顯低於 1，代表該配置在特徵空間散到目前的密度階梯還聚不起穩定叢，或隔離區混進了別的配置。

`learned` 欄可能不同於該段注入的配置：候選來自整個隔離區，多數決可能是前一段殘餘。判讀以 CSV 的 `learned` 為準。

## 已記錄的實測

[Experiments_Guide.md](../Experiments_Guide.md) 記載 T1/8000 rpm：十種配置都發現，純度 100%，發現延遲 65 到 265 筆，自類準確率從 100% 降到約 85%，健康保持率始終 ≥ 90%。`AGENT.md` 另記 2screws 在固定 `(25,3)` 下要 225 筆，自適應階梯把這類延遲壓到 65–265 筆。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/exp2_scale_growth.py` | `ScaleGrowthSession`、`run`、`main` |
| `core/monitor.py` | 打分、`classify`、`add_class` |
| `core/data.py` | `CycleSampler`、`CONFIG_ORDER`、`config_sort_key` |
| `core/geometry.py` | 擴張後重建 `PolarMap` |
| `web/live.py` | 直接建構 `ScaleGrowthSession`，`confirm` 由 WebSocket 指令觸發 |
| `web/server.py` | 把 `confirm` 放到執行緒池 |

輸出：

- `logs/exp2_scale_growth/{時間戳}.log`
- `output/exp2_scale_growth/{時間戳}/stages.csv`
- `output/exp2_scale_growth/{時間戳}/summary.json`
