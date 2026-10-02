# 實驗四：極座標健康地圖

程式：`experiments/exp4_polar_map.py`。幾何定義在 `core/geometry.py` 的 `PolarMap`。

問題：在健康分布白化之後，故障配置會不會各自沿一條射線離開原點；只認識部分故障時，方向餘弦能否把「均勻鬆動家族」和 `4_146screws` 分開；只給輕、重兩個錨點時，半徑或投影能否排出中間配置的鬆動順序。

## 實驗方法

CLI `--part` 預設 `abc`，可只跑其中幾個字母。資料是單一工況，文件對照是 T1/8000 rpm，`--seed 42`。`PolarMap` 的幾何一律用 Ledoit–Wolf Mahalanobis，不跟 `--openset-method` 走。本檔的 `main()` 沒有接 `add_openset_args`。

**(a) `run_geometry`**  
把除了 `8screws` 以外的配置全部 `add_class`，再算射線兩兩餘弦。彙總中段均勻族（6、5、4、3、2 screws）的族內平均、中段對 `7screws` / `1screws`、均勻族對 `3_14screws` 與 `4_146screws`。

**(b) `run_direction`**  
已知集輪流是 `["7screws"]`、`["1screws"]`、兩者同時、`["5screws"]`、`["3_14screws"]`。對其餘配置算每個樣本對已知射線的最大餘弦。正類是尚未加入的均勻鬆動，負類是 `4_146screws`。`3_14screws` 只報告中位數，不進 AUROC。

**(c) `run_severity`**  
錨點固定 `7screws` 與 `1screws`。對 `UNIFORM` 階梯算三種嚴重度的中位數，再用 Spearman ρ 對配置順位（7 最輕、1 最重）看排序是否一致：

- `radius`：白化空間到原點的距離，除以最重錨點的半徑
- `best_ray`：`PolarMap.analyze` 的沿最佳射線投影
- `bundle`：兩錨點方向的平均單位向量上的投影，用最重錨點在該方向的投影長度正規化

```bash
venv/bin/python -m experiments.exp4_polar_map --motor T1 --rpm 8000rpm
venv/bin/python -m experiments.exp4_polar_map --part a
```

## 理論

白化用健康類 precision 的 Cholesky。已標準化的向量 `x` 映成

`z(x) = W (x − μ_H)`，`W = chol(P_H)^T`

半徑 `r = ‖z‖` 就是到健康中心的馬氏距離。已知故障 c 的射線是類中心白化後的單位向量 `u_c`。樣本方向與射線的餘弦是 `⟨z/‖z‖, u_c⟩`。

`same_ray` 用該類 holdout 餘弦的低百分位當 `τ_c`。沿射線的嚴重度是投影長除以類中心半徑：類中心附近約 1，健康附近約 0，比類中心更遠則大於 1。所有餘弦都低時，程式把這筆留給隔離區，不在本地硬指定新故障名稱。

健康樣本只有一類時沒有故障射線。`tests/test_geometry.py` 鎖住這件事，也鎖住 k-NN 監測器與 Mahalanobis 監測器算出同一套幾何。

## 參考論文

- 馬氏距離與 Ledoit–Wolf 出處同 [exp1_cold_start.md](exp1_cold_start.md)。
- C. Spearman (1904), “The Proof and Measurement of Association between Two Things,” *The American Journal of Psychology*, 15(1), 72–101。DOI [10.2307/1412159](https://doi.org/10.2307/1412159)。
- 射線閾值用 holdout 餘弦的低百分位、三個嚴重度定義、`3_14` 不進 (b) 的 AUROC：本專案操作約定，寫在 `core/geometry.py` 與 `run_direction`。

## 預期成果

(a) 中段均勻鬆動的兩兩餘弦應高於它們對 `4_146screws` 的餘弦。若均勻族內部已經散成多束，星狀圖就只是畫法，不能拿來當家族判據。

(b) 以輕度或中度錨點當已知射線時，家族對 `4_146` 的 AUROC 應高。若最重錨點把 AUROC 打到 0.5 附近或更低，代表從極端鬆動望回去會把家族成員看成新方向。

(c) 至少一種嚴重度的 Spearman ρ 應為正且明顯大於 0。中段若出現順位顛倒，ρ 會低於 1，這仍然可以是物理配置的距離關係，不必改成單調插值。

## 已記錄的實測

[Experiments_Guide.md](../Experiments_Guide.md) 記載 T1/8000 rpm：中段均勻族餘弦約 0.92，對 `4_146` 約 0.49，對 `3_14` 約 0.76。以最輕故障當羅盤時，家族對 `4_146` 的 AUROC 為 0.997；中度錨點 1.000；以最重故障當羅盤時降到 0.146。純距離對鬆動順位的 Spearman ρ 為 0.877，手冊寫中段有 5 顆比 4 顆更遠的倒置。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/exp4_polar_map.py` | `run_geometry`、`run_direction`、`run_severity`、`run`、`main` |
| `core/geometry.py` | `PolarMap`、`Ray`、白化與餘弦 |
| `core/mahalanobis.py` | 幾何用的 Ledoit–Wolf 模型 |
| `core/monitor.py` | `fit_initial`、`add_class` |
| `experiments/exp2_scale_growth.py` | 每次擴張後重建 `PolarMap`，`process` 附帶 `direction` |
| `tests/test_geometry.py` | 健康-only 無射線；開集方法不改幾何 |

`a` 與 `c` 都有結果時才畫圖。

- `logs/exp4_polar_map/{時間戳}.log`
- `output/exp4_polar_map/{時間戳}/summary.json`
- `output/exp4_polar_map/{時間戳}/polar_map.png`

### 散在其他位置的相關檔案

- 測試：`tests/test_geometry.py`。
- Web：`web/live.py` 組 `direction` 訊息；`web/static/index.html` 的「極座標健康地圖（實驗四）」與「方向熟悉度（實驗四）」。
- 已提交紀錄：`logs/exp4_polar_map/`、`output/exp4_polar_map/`（2 次執行）。
- PolarMap 固定建在 Mahalanobis 上的經過：`reports/exp6_ancestor_openset_progress.md` P8。
- 其他文件：[Experiments_Guide.md](../Experiments_Guide.md) 第 5 節。
