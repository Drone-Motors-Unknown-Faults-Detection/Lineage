# 實驗九：非線性 AutoEncoder 偵測器（exp6 第八種方法）

程式：`experiments/exp6_osr_benchmark.py`（不需改），新增的偵測器類別在 `core/detectors.py` 的 `ALL_DETECTORS`。

問題：專題目標要求「探索非監督式學習（如 AutoEncoder）」。`core/detectors.py` 已有 `PCAReconDet`（線性 autoencoder 的等價物），但沒有非線性版本；本實驗補上一個用 `MLPRegressor` 做瓶頸重建的非線性 AE，沿 exp6 既有的七方法比較框架再加一種，看非線性重建是否比線性 PCA 重建更能分開健康與故障。

## 實驗方法

1. `core/detectors.py` 新增 `MLPAutoencoderDet(_Base)`：`_fit_raw(X)` 用 `sklearn.neural_network.MLPRegressor(hidden_layer_sizes=(64, 16, 64), activation="relu", random_state=self.seed, max_iter=2000, early_stopping=True)` 對 `X -> X` 做瓶頸重建（105 維進、16 維瓶頸、105 維出）；`_raw_score(X)` 回傳 `np.linalg.norm(X - predict(X), axis=1)`，與 `PCAReconDet` 同構。
2. 繼承 `_Base.fit`：`RobustScaler` 只在健康訓練集擬合，原始重建誤差除以校準集第 95 百分位，沿用 exp6 既有的校準哲學（見 [exp6_osr_benchmark.md](exp6_osr_benchmark.md)）。
3. 加進 `ALL_DETECTORS`（`core/detectors.py:142` 附近）。`experiments/exp6_osr_benchmark.py` 的 `run()` 迴圈 `ALL_DETECTORS`，不需要改這支程式——新偵測器自動被納入九工況比較。
4. seed、切分、資料來源與 exp6 完全相同：`discover_datasets` 掃 `--data-root`，單一 `default_rng(seed)`（預設 42）依序往下切 9 組資料集。

```bash
venv/bin/python -m experiments.exp6_osr_benchmark
```

## 理論

`PCAReconDet` 只能捕捉特徵間的線性相關；若 105 維特徵裡健康與故障的差異主要是非線性的（例如某些特徵組合的交互作用），線性重建會把這部分誤差也算進「正常」範圍，非線性 AE 的瓶頸層理論上能學到更貼近健康流形的非線性結構，重建誤差對故障更敏感。代價是訓練樣本少、瓶頸夠窄時容易過擬合或訓練不穩定，這也是用 `early_stopping=True` 與固定 seed 控制的原因。

## 參考論文

- M. Sakurada and T. Yairi (2014), “Anomaly Detection Using Autoencoders with Nonlinear Dimensionality Reduction,” *Proceedings of the MLSDA 2014 2nd Workshop on Machine Learning for Sensory Data Analysis*, ACM, 4–11。DOI [10.1145/2689746.2689747](https://doi.org/10.1145/2689746.2689747)。
- 隱藏層大小 `(64, 16, 64)`、`activation="relu"`、`max_iter=2000`：本專案操作約定，沒有照搬論文的網路規模（論文用於不同資料集維度）。校準哲學（`RobustScaler` 只用訓練集、分數除以校準集第 95 百分位）同 [exp6_osr_benchmark.md](exp6_osr_benchmark.md)。

## 預期成果

若 105 維特徵裡健康與故障的差異主要是線性可分的，非線性 AE 的 AUROC 會和 `pca_recon` 接近，不會有明顯優勢。若存在線性 PCA 抓不到的非線性結構，AE 的 AUROC 或健康誤報應優於 `pca_recon`。若 AE 的健康誤報明顯高於其餘方法，代表瓶頸重建在小樣本（訓練集僅健康池的 60%）下過擬合，不適合當冷啟動基準。

## 已記錄的實測

`venv/bin/python -m experiments.exp6_osr_benchmark`（九組資料集、seed 42，`output/exp6_osr_benchmark/2026-10-09-14-07-53/`）：八種方法 AUROC 全部 1.0000±0.0000、故障偵測率全部 100%，差異只在健康誤報率——`mlp_autoencoder` 5.8%，是八種方法裡最低的（`knn_dist` 6.0%、`lof` 6.7%、`pca_recon` 6.4%、`maha_ledoit_wolf` 7.1%、`ocsvm` 7.4%、`iforest` 8.4%、`maha_legacy` 83.1%）。結論：在這份 105 維特徵上，健康與故障本來就被線性方法清楚分開（AUROC 全頂滿 1.0），非線性 AE 沒有展現出線性 PCA 抓不到的額外判別力，但重建誤差的校準穩定度（健康誤報）比線性版本略好；這與「預期成果」裡「若線性已經足夠，AE 不會有優勢」的條件句一致，AE 在誤報率上的些微領先不足以改變主線仍用 Ledoit–Wolf 馬氏距離的決定（它保留逐類共變異數，供後續極座標與量尺擴張使用）。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `core/detectors.py` | 新增 `MLPAutoencoderDet`，加入 `ALL_DETECTORS` |
| `experiments/exp6_osr_benchmark.py` | `run`、`_figure`、`main`（不需修改，自動納入新偵測器） |
| `core/data.py` | `discover_datasets`、`load_pools`、`make_split` |

輸出（與 exp6 既有輸出合併在同一次執行裡，不另開目錄）：

- `logs/exp6_osr_benchmark/{時間戳}.log`
- `output/exp6_osr_benchmark/{時間戳}/results.csv`（新增 `mlp_autoencoder` 列）
- `output/exp6_osr_benchmark/{時間戳}/summary.json`
- `output/exp6_osr_benchmark/{時間戳}/osr_benchmark.png`（長條圖新增一根）

### 散在其他位置的相關檔案

- 測試：`tests/test_exp9_autoencoder.py`（seed 重現性、`ALL_DETECTORS` 成員、校準邊界）。
- 同屬「未知故障辨識」主題：[exp10_transfer](exp10_transfer.md)（遷移學習，獨立方法）。
- 來源 issue：[#13](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/13)。
