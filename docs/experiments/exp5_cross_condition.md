# 實驗五：跨工況冷啟動

程式：`experiments/exp5_cross_condition.py`。一次載入 `discover_datasets` 掃到的全部工況，目前契約是 9 組：T1/T2/T3 × 6000/8000/11000 rpm。

問題：在工況 A 只用健康資料建的基準，直接拿去給工況 B 打分時，健康接受率與故障偵測率還在不在；把多個工況的健康樣本混在一起建一個基準，會不會比逐工況各建一個更好。

## 實驗方法

`--part` 預設 `abc`。`--method` 預設 `ledoit_wolf`，`--confidence 0.95`，`--seed 42`。本檔沒有 k-NN 開關。

**(a) `run_matrix`**  
每個來源工況各自 `fit_initial()`。對每個目標工況算健康接受率 `(score ≤ 1)`、故障偵測率 `(score > 1)`、AUROC。來源等於目標時，健康分數只用該監測器自己的 holdout，避免訓練樣本回測。跨工況時，目標的健康池整池拿來評，因為那些樣本沒有參與來源的擬合。彙總對角線 AUROC、非對角線 AUROC、同轉速跨馬達、同馬達跨轉速。

**(b) `run_strategy`**  
先對每個工況的健康池用 `seed + 7` 做一次 `make_split`，留 20% holdout 給三種策略共用，混合基準只能看 train+calibration。

- `per_condition`：各工況自己的監測器，再在自己的 holdout 上評
- `global_mixed`：九組健康的 train+calibration 疊成一個健康池
- `per_rpm_mixed`：同一轉速的三個馬達疊成一個健康池

指標是健康接受率與故障偵測率的九組平均。

**(c) `run_drift`**  
每個轉速用 T1 的健康基準，去看 T1 holdout、以及 T2、T3 的全部 `8screws`。記錄分數中位數、第 90 百分位、被標未知的比例。T1/T2/T3 是三顆馬達，分數位移同時含個體差與檔名上的壽命期，這份資料拆不開。

```bash
venv/bin/python -m experiments.exp5_cross_condition
venv/bin/python -m experiments.exp5_cross_condition --part a
```

## 理論

監測器估的是「這一組健康窗口的位置與散布」。轉速或馬達一換，健康雲的中心可以離開原來的校準橢球，於是另一台機器的健康窗口也會得到大於 1 的分數。故障偵測率在這種時候仍可能很高，因為故障離新云更遠；健康接受率會先壞。

混合基準把多團健康雲塞進同一個共變異數。若三團中心彼此離得遠，橢球被拉大，閾值跟著變寬，故障可能掉回橢球裡面。逐工況基準避免這次混合，代價是每台機器、每個轉速都要自己的 `8screws` 訓練與校準。

## 參考論文

- 馬氏距離與 Ledoit–Wolf 出處同 [exp1_cold_start.md](exp1_cold_start.md)。
- 跨工況時整池評健康、同工況只用 holdout、混合策略用 `seed + 7`：本專案操作約定，寫在 `_evaluate` 與 `run_strategy`。
- 不把 T1→T3 的分數上升單獨解釋成老化：本專案的資料限制，見本檔 `run_drift` 與 [Experiments_Guide.md](../Experiments_Guide.md) 第 6 節。

## 預期成果

(a) 對角線 AUROC 應高於非對角線，同轉速或同馬達的格子可以比任意交叉好，也可以不好，要看分數而不是先假設。最差的非對角線若掉到 0.5 附近，那一對工況不能共用基準。

(b) 若 `per_condition` 的健康接受率與故障偵測率同時高於兩種混合，部署就該逐工況冷啟動。若混合在故障偵測上更高、健康接受率卻掉很多，那是閾值變寬，不是泛化變好。

(c) T1 看自己的 holdout，未知比例應靠近實驗一的誤報。T1 基準看 T2/T3 的 `8screws` 若大量超過 1，就不能把 T1 的閾值套到另外兩顆馬達。

## 已記錄的實測

[Experiments_Guide.md](../Experiments_Guide.md) 記載：自身 AUROC 為 1.0；跨工況平均 0.893，最差一格 0.10。逐工況策略的健康接受率 97.4%、故障偵測率 100%，兩種混合都較低。T1 基準看 T2/T3 的健康資料，100% 被標未知，分數中位約 14 到 86。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/exp5_cross_condition.py` | `run_matrix`、`run_strategy`、`run_drift`、`run`、`main` |
| `core/data.py` | `discover_datasets`、`load_pools`、`make_split` |
| `core/monitor.py` | 每個來源工況一個 `OpenSetMonitor` |

`a` 與 `c` 都有結果時才畫 `cross_condition.png`。

- `logs/exp5_cross_condition/{時間戳}.log`
- `output/exp5_cross_condition/{時間戳}/summary.json`
- `output/exp5_cross_condition/{時間戳}/cross_condition.png`

### 散在其他位置的相關檔案

- 測試：沒有專屬測試。
- Web：`web/static/index.html` 的資料集下拉選單（9 組工況各自冷啟動）。
- 已提交紀錄：`logs/exp5_cross_condition/`、`output/exp5_cross_condition/`（1 次執行）。
- 其他文件：[Experiments_Guide.md](../Experiments_Guide.md) 第 6 節。
- Web 實驗頁：頁首「實驗五」，`web/experiments.py` 的 `CATALOG` 項目 `exp5` 呼叫本程式的 `run()`，畫面在 `web/static/experiments.js` 的 `RENDER.exp5`；結果存到 `output/web_server/{ts}/experiments/exp5_{時間}.json`。
