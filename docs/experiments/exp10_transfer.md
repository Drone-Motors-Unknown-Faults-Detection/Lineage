# 實驗十：遷移學習——目標工況少量健康資料的跨工況基準遷移

程式：`experiments/exp10_transfer.py`，函式 `run(data_root, seed, confidence, method, n_values)` 與 `main()`。

問題：exp5 的 9×9 遷移矩陣顯示直接把來源工況的健康基準搬去別的工況，平均 AUROC 0.893、最差 0.10——T1 基準下 T2/T3 健康資料幾乎全被判未知。若目標工況能拿到少量（10/25/50 筆）健康資料，用它做「中心平移」適應來源基準，或乾脆只用這些筆數從零建基準，哪一種比較划算？

## 實驗方法

1. `discover_datasets` 取得 9 組 (motor, rpm) 資料集；對每一組有序配對 `(src, dst)`、`src != dst`（72 組）：
   - **direct**（N=0，零適應基準線）：`OpenSetMonitor({HEALTHY: pools[src][HEALTHY]}, seed, confidence, method).fit_initial()`，直接對 `dst` 的**全部**健康池與故障池評分。
   - 對每個 `N ∈ {10, 25, 50}`：用單一遞進 `default_rng(seed)` 從 `dst` 健康池抽 N 筆當「目標端少量健康樣本」（`support`），其餘健康樣本當評估池 `eval`（避免用來算接受率的資料和用來適應的資料重疊）。
     - **adapted**（中心平移）：`shift = median(support, axis=0) - median(src 訓練集, axis=0)`（`src` 訓練集取自 `monitor.pools[HEALTHY][monitor.splits[HEALTHY].train]`），把 `dst` 的 `eval` 健康池與故障池都減去 `shift` 後，用 `src` 的 monitor `.score()`。
     - **scratch**（目標端從零冷啟動）：`OpenSetMonitor({HEALTHY: support}, seed, confidence, method).fit_initial()`（內部仍是標準 60/20/20 切分；N=10 時等於 6/2/2，holdout 2 筆不使用），對 `dst` 的 `eval` 健康池與故障池評分。
2. 每一列記錄 `{src, dst, n, strategy, healthy_accept, fault_detect, auroc}`。`summary` 把 72 組 pair 依 `(n, strategy)` 取平均，形成「目標樣本數 vs 指標」的曲線資料；`direct`（N=0）只算一次，在圖上畫成參考線。
3. 預設 `--method ledoit_wolf`、`--confidence 0.95`、`--seed 42`、`--n-values 10,25,50`。

```bash
venv/bin/python -m experiments.exp10_transfer
venv/bin/python -m experiments.exp10_transfer --n-values 10,25,50 --method ledoit_wolf
```

**與 exp5 的差異**：exp5 的 9×9 矩阵（a 部分）用 `dst` 的**全部**健康池評估自身以外的目標；exp10 的 `direct` 為了和同一組 `eval` 池公平比較，在 N>0 時扣掉了被抽去當 `support` 的樣本。因此 exp10 的 `direct` 數字和 exp5 矩陣的對應格子不會完全相同（evaluation pool 不同），兩邊不可直接拿來做差值比較，报告时分开引用。

## 理論

「中心平移」是 CORAL（相關對齊）的簡化版：CORAL 原文對齊來源與目標的二階動差（共變異數），這裡只對齊一階動差（中位數），因為目標端只有 10～50 筆、105 維，二階動差的樣本估計在 N < 維度時高度不穩定，先用最簡單、最穩健的中心平移驗證「有沒有用」。「從零冷啟動」沿用 `OpenSetMonitor` 既有的 Ledoit–Wolf 收縮估計，在 N=10（遠小於 105 維）時完全依賴收縮項撐住共變異數估計，這正是 exp1 手冊裡「樣本共變異數容易病態，所以用 Ledoit–Wolf」那段的極端情形。

## 參考論文

- Ledoit–Wolf 收縮估計、60/20/20 切分、分數 `>1` 判未知：出處同 [exp1_cold_start.md](exp1_cold_start.md)。
- B. Sun, J. Feng, and K. Saenko (2016), “Return of Frustratingly Easy Domain Adaptation,” *Proceedings of the AAAI Conference on Artificial Intelligence*, 30(1), 2058–2065。arXiv:[1511.05547](https://arxiv.org/abs/1511.05547)。本實驗的「中心平移」只取 CORAL 精神中最簡單的一階動差對齊，不是完整 CORAL（完整版還要對齊共變異數），這是本專案在小樣本限制下的操作約定。
- exp5 的跨工況評估架構（`_evaluate`、`run_matrix`）：見 [exp5_cross_condition.md](exp5_cross_condition.md)，本實驗沿用同一套資料與切分慣例、但自成一份程式（不互相 import）。

## 預期成果

若遷移有效，`adapted` 在 N=10 時的 AUROC／健康接受率就應該明顯高於 `direct`（N=0）的平均值，且隨 N 增加持續逼近對角線（自身評自身）的水準。若 `scratch` 在同樣 N 下已經接近 `adapted`，代表簡單中心平移沒有額外價值，從零冷啟動一樣划算——因為 exp1 已證明健康-only 冷啟動在單一工況下效果很好，少量健康資料可能已經足夠獨立建基準。若兩者在小 N（10 筆）都明顯劣於中到大 N（50 筆），代表 10 筆在 105 維特徵上还不足以撐起穩定估計，無論用哪種策略都一樣。

## 已記錄的實測

`venv/bin/python -m experiments.exp10_transfer`（9 組資料集、72 組 `(src, dst)` 配對、seed 42、`method=ledoit_wolf`，`output/exp10_transfer/2026-10-09-14-11-31/`）：

| 策略 | N | AUROC | 健康接受率 | 故障偵測率 |
|---|---:|---:|---:|---:|
| direct | 0 | 0.8930 | 0.0% | 100.0% |
| adapted | 10 | 0.9992 | 7.3% | 100.0% |
| adapted | 25 | 0.9992 | 8.8% | 100.0% |
| adapted | 50 | 0.9994 | 9.3% | 100.0% |
| scratch | 10 | 1.0000 | 65.7% | 100.0% |
| scratch | 25 | 1.0000 | 83.6% | 100.0% |
| scratch | 50 | 1.0000 | 87.9% | 100.0% |

`direct` 的 AUROC 0.8930 與 exp5 矩陣的 `offdiag_auroc_mean` 一致（評估池同為「目標全部健康池」）；健康接受率跨 72 組配對平均趨近 0%，呼應 exp5「T1 基準下 T2/T3 健康 100% 判未知」的結論，且把它量化到整個 9×9 矩陣的平均水準，不只是 T1 這一個基準。

結論：中心平移把 AUROC 從 0.893 拉到 0.999 以上，10 筆目標端健康資料就幾乎追平 50 筆的效果——**排序能力**（誰比誰更像故障）很快恢復。但健康接受率在 N=50 時仍只有 9.3%，遠低於 `scratch` 同樣 N 下的 87.9%：中心平移只對齊了一階動差，校準門檻仍然沿用來源端的校準分位數，對目標端大多數健康樣本來說門檻太緊。也就是說，**單純中心平移不足以同時修好排序與校準**；若目標端真的能拿到 10 筆以上健康資料，直接從零冷啟動（`scratch`）在這份資料上全面優於中心平移（AUROC 持平或更好、健康接受率高出 6～9 倍），遷移在本實驗的簡化設計下沒有展現優勢，這印證了「逐工況冷啟動」架構的合理性——與 exp5 的結論一致，但補上了「有少量目標資料時兩種選項的具體落差」。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/exp10_transfer.py` | `run`、`_draw_support`、`_evaluate`、`_figure`、`main` |
| `core/monitor.py` | `OpenSetMonitor.fit_initial`、`score`、`pools`、`splits` |
| `core/data.py` | `discover_datasets`、`load_pools`、`HEALTHY` |

輸出：

- `logs/exp10_transfer/{時間戳}.log`
- `output/exp10_transfer/{時間戳}/summary.json`
- `output/exp10_transfer/{時間戳}/transfer_curve.png`

### 散在其他位置的相關檔案

- 測試：`tests/test_exp10_transfer.py`（strategy 結構、support/eval 不重疊、AUROC 落在 `[0,1]`）。
- 同屬「未知故障辨識與遷移學習」主題：[exp5_cross_condition](exp5_cross_condition.md)（零適應矩陣的原始版本）、[exp9_autoencoder](exp9_autoencoder.md)（獨立方法，不互相依賴）。
- 來源 issue：[#14](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/14)。
