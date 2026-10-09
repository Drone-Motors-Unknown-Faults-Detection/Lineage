# 實驗十二：視覺化——開集混淆矩陣與 t-SNE 特徵分布圖

程式：`experiments/exp12_confusion_tsne.py`，函式 `run(data_root, seed, confidence, perplexity)` 與 `main()`。

問題：專題要求提供混淆矩陣與 t-SNE，展示模型區分正常與故障訊號的效果。repo 既有的圖只有分數折線與 PCA 2D 投影，沒有混淆矩陣，也沒有 t-SNE。

## 實驗方法

1. **二元混淆矩陣**（健康 vs 故障，呼應 exp1）：對 9 工況各自用 `OpenSetMonitor({HEALTHY: 健康池}).fit_initial()`，`score(健康 holdout) <= 1` 記健康、`score(全部故障池) > 1` 記故障；9 工況的判定疊成一組全域 `y_true`/`y_pred`，`sklearn.metrics.confusion_matrix` 輸出 2×2。
2. **開集多類混淆矩陣**：匯入 [exp11_ancestor_comparison.py](exp11_ancestor_comparison.md) 的 `build_ancestor_monitor(pools, seed, confidence, method)` 與已知/未知配置判斷邏輯，重用 Ancestor 協定（已知 8/1/2/3/4screws、未知 5/6/7/3_14/4_146screws），9 工況疊成一組全域 6×6（5 已知 + unknown）混淆矩陣，分別跑 `method="ledoit_wolf"` 與 `method="legacy"` 兩版，並排顯示（exp11 已完成，依 issue 要求補上這組並排圖）。九組資料集裡「1 螺絲」配置的目錄名有 `1screw`／`1screws` 兩種（AGENT.md 已知陷阱 5），跨資料集疊混淆矩陣前先正規化成同一個標籤，否則會多出一個虛假類別。
3. **t-SNE**：對每個工況，在 `monitor.scaler.transform(X)`（與偵測器門檻同一個 `RobustScaler` 縮放空間，不另外重新擬合）上跑 `sklearn.manifold.TSNE(random_state=seed, perplexity=perplexity)`；顏色 = 螺絲配置（依 `core.data.config_sort_key` 排序的類別色），標記形狀 = Ancestor 協定的系統判定（已知且判對／已知但判錯／判為 unknown）。9 工況畫成 3×3 子圖。每個配置最多取 `tsne_max_per_class`（預設 200）筆（`default_rng(seed)` 抽樣），純粹是壓縮 t-SNE 的計算量，不影響混淆矩陣與 Accuracy/F1 的計算（那些用完整樣本）。
4. 預設 `--seed 42`、`--confidence 0.95`、`--perplexity 30`、`--tsne-max-per-class 200`。

```bash
venv/bin/python -m experiments.exp12_confusion_tsne
```

## 理論

混淆矩陣把「健康 vs 故障」「已知 5 類 + unknown」兩層判定攤開看，能同時看出哪一類被誤判成哪一類，不只是整體 Accuracy。t-SNE 用非線性的鄰近關係保留局部結構，比線性 PCA 更可能把高維流形上彎曲分開的群集攤平看出視覺上的群聚；但它的全域距離與座標尺度不具物理意義，不能像 PCA 投影那樣拿來估「嚴重度」或當作量尺的一部分——這正是 exp4 極座標地圖刻意用 PCA 而非 t-SNE 的原因，t-SNE 在本實驗純粹是視覺輔助。

## 參考論文

- L. van der Maaten and G. Hinton (2008), “Visualizing Data using t-SNE,” *Journal of Machine Learning Research*, 9, 2579–2605。<https://jmlr.org/papers/v9/vandermaaten08a.html>。`perplexity=30` 是論文建議的常用預設值。
- 混淆矩陣（`sklearn.metrics.confusion_matrix`/`ConfusionMatrixDisplay`）：標準工具，無特定文獻依據，本專案操作約定。
- Ancestor 協定已知/未知類別定義、Ledoit–Wolf vs legacy：出處同 [exp11_ancestor_comparison.md](exp11_ancestor_comparison.md)。

## 預期成果

二元混淆矩陣應該接近對角矩陣（呼應 exp1 的 100% 偵測率與 10.9% 健康誤報，誤差集中在健康被誤判為故障，不會有故障被誤判為健康）。開集多類混淆矩陣：`ledoit_wolf` 版應接近對角、`legacy` 版若重現 exp11 的結論，大部分已知類別樣本會被錯分到 unknown 或彼此混淆，而不是正確分類。t-SNE 圖若和 PCA 投影講同一個故事，健康與各螺絲配置應形成可辨識但可能重疊的群聚；重疊程度若和 Mahalanobis 分數的判定一致，就支持特徵本身有足夠的判別力，模型的誤判不是來自視覺化工具的誤導。

## 已記錄的實測

`venv/bin/python -m experiments.exp12_confusion_tsne`（9 工況疊成全域矩陣，seed 42，`output/exp12_confusion_tsne/2026-10-09-14-27-55/`）：

**(a) 二元混淆矩陣**（健康 vs 故障）：

|  | 判健康 | 判故障 |
|---|---:|---:|
| 真健康 | 527 | 45 |
| 真故障 | 0 | 26070 |

健康誤報 45/572 = 7.87%，故障偵測 26070/26070 = 100%——沒有任何一筆故障被判成健康，誤差完全集中在健康誤報這一格，和 exp1 的敘事（九種故障偵測率 100%、健康誤報因校準集樣本少而偏高）一致。

**(b) 開集多類混淆矩陣**（Ancestor 協定，5 已知 + unknown）：`ledoit_wolf` 的對角線是 `[525, 562, 559, 561, 529, 14381]`，row sums `[572, 601, 605, 591, 569, 14381]`——**5 個已知類別之間完全沒有互相混淆**（非對角的已知→已知格全是 0），唯一的誤差是已知類別被判成 unknown（8.2%～9.9%）。`legacy` 的對角線是 `[0, 0, 0, 0, 0, 14381]`——**每一個已知類別的樣本 100% 被判成 unknown**，沒有一筆落在正確的已知類別格，也沒有落在錯誤的已知類別格（legacy 的單一全域分布根本沒有「已知類別之間」這個判斷維度）。這張矩陣把 exp11 的數字結果變成可以直接看見的畫面：legacy 不是「比較容易混淆類別」，是「完全沒有能力分辨已知類別」。

**(c) t-SNE**：9 工況的 3×3 網格裡，各螺絲配置形成可辨識但彼此部分重疊的群聚，`known_correct`（圓點）集中在各自配置的群聚中心，`unknown`（三角形）標記多半落在群聚邊緣或介於多個群聚之間，和 PCA 投影呈現的「健康雲 vs 故障雲」故事一致；由於 t-SNE 距離不具量尺意義，這裡只做視覺比對，不用來估計嚴重度排序。

結論：三張圖彼此一致、也和 exp1/exp11 的數字一致，沒有互相矛盾的地方。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/exp12_confusion_tsne.py` | `run`、`_binary_confusion`、`_openset_confusion`、`_tsne_grid`、`main` |
| `experiments/exp11_ancestor_comparison.py` | 匯入 `build_ancestor_monitor`、`_ancestor_known_configs`、`_ANCESTOR_UNKNOWN_CANDIDATES` |
| `core/monitor.py` | `OpenSetMonitor.fit_initial`、`score`、`classify`、`holdout`、`scaler` |
| `core/data.py` | `discover_datasets`、`load_pools`、`config_sort_key` |

輸出：

- `logs/exp12_confusion_tsne/{時間戳}.log`
- `output/exp12_confusion_tsne/{時間戳}/summary.json`（二元與開集混淆矩陣的數字陣列；t-SNE 座標不落地，圖已是產出）
- `output/exp12_confusion_tsne/{時間戳}/confusion_matrices.png`（三格並排：(a) 二元、(b) ledoit_wolf 開集多類、(b) legacy 開集多類）
- `output/exp12_confusion_tsne/{時間戳}/tsne_grid.png`（9 工況 3×3 子圖）

### 散在其他位置的相關檔案

- 測試：`tests/test_exp12_confusion_tsne.py`（二元混淆矩陣形狀 `(2,2)`、開集混淆矩陣形狀 `(6,6)`、列和等於樣本數、t-SNE 座標形狀 `(n,2)` 且無 NaN）。
- 依賴：[exp11_ancestor_comparison](exp11_ancestor_comparison.md)（Ancestor 協定 monitor 建構）、[exp1_cold_start](exp1_cold_start.md)（二元判定邏輯的原型，不互相 import）。
- 來源 issue：[#16](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/16)。
