# 實驗十一：與 Ancestor 的 Accuracy / F1 對照實驗

程式：`experiments/exp11_ancestor_comparison.py`，函式 `run(data_root, seeds, confidence, methods)`、可供 exp12 重用的 `build_ancestor_monitor(pools, seed, confidence, method)`，與 `main()`。

問題：專題指標要求相對 Ancestor 提升 Accuracy／F1 5%～10%。`docs/Mahalanobis_Improvement.md`（歷史文件，腳本已移到 Ancestor，現行 repo 不能重跑）記過 Legacy→Ledoit–Wolf 開集 Accuracy +3.55 pp、Balanced Accuracy +6.51 pp，F1 未記錄；`exp6_osr_benchmark` 只比過健康誤報，沒有 Accuracy/F1。本實驗在現行架構下，用 Ancestor 原始協定（已知 8/1/2/3/4screws、未知 5/6/7/3_14/4_146screws）重做 legacy vs Ledoit–Wolf 的多類 Accuracy/F1 對照。

**先寫定，不事後挑指標**：

- 主指標：**Balanced Accuracy** 與 **macro-F1**。Accuracy 照列但不作達標依據——legacy 開集 Accuracy 已經 0.9509，相對 +5% 在數學上不可行（天花板只剩 4.9 pp），且健康-only 協定下類別嚴重不平衡，Accuracy 幾乎只反映多數類（詳見 [#15](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/15) 原文）。
- 達標門檻：Balanced Accuracy 與 macro-F1 相對 legacy **絕對提升 ≥ 5 個百分點（pp）**，不用相對百分比。
- 這兩條在程式與批次執行之前寫定，「已記錄的實測」一律照實填，不論達標與否。

## 實驗方法

1. 對 9 組 (motor, rpm) 資料集，各自定義兩種協定：
   - **Protocol A（Ancestor 協定）**：已知類別 = `{8screws} ∪ ({1screw,1screws} ∩ 該資料集的配置) ∪ {2screws, 3screws, 4screws}`（用交集判斷螺絲配置目錄名陷阱，見 AGENT.md 已知陷阱 5）；未知類別 = `{5screws, 6screws, 7screws, 3_14screws, 4_146screws} ∩ 該資料集配置`。
   - **Protocol B（冷啟動協定，對照組）**：已知類別只有 `8screws`；其餘全部未知。呼應 exp1 的設定，但這裡輸出 Accuracy/Balanced Accuracy/F1 三指標，不只是偵測率。
2. `build_ancestor_monitor(pools, seed, confidence, method)`：`OpenSetMonitor(pools, seed, confidence, method).fit_initial()` 後對 Protocol A 其餘已知類別逐一 `add_class()`，回傳擬合好的 monitor（exp12 直接匯入這個函式重用，不重寫一次）。
3. 評估：已知類別各自的 `monitor.holdout(config)` 丟 `monitor.classify()`；未知池全部丟 `monitor.classify()`。`None`（未知判定）併入一個額外類別字串 `"unknown"`，組成 `y_true`/`y_pred`（Protocol A 是 6 類：5 已知 + unknown；Protocol B 是 2 類：健康 + unknown）。計算 `accuracy_score`、`balanced_accuracy_score`、`f1_score(average="macro")`；另外單獨算 `"unknown"` 類別自己的 binary F1（`y_true=="unknown"` vs `y_pred=="unknown"`）。
4. 對 `methods=("legacy", "ledoit_wolf")`（兩者都走 `OpenSetMonitor(..., method=method)`，`core/mahalanobis.py` 已依鐵則 1 複製並註記 legacy 來源，不需新增偵測器）、`seeds=(42, 123, 2026)`，跑滿 9×3×2 的 Protocol A 與 Protocol B，共 108 列。
5. **配對檢定**：對每個 `(dataset, seed)`，取 legacy 與 ledoit_wolf 的 macro-F1 差（Protocol A）與 F1 差（Protocol B），各 27 對觀測，做 `scipy.stats.wilcoxon`。

```bash
venv/bin/python -m experiments.exp11_ancestor_comparison
venv/bin/python -m experiments.exp11_ancestor_comparison --seeds 42,123,2026
```

## 理論

Ancestor 協定把 8/1/2/3/4screws 當已知、其餘當未知，是論文原始設定的「部分已知」版本；冷啟動協定只認識健康，是本專案主線的起點。兩者都用同一套 `OpenSetMonitor`，差別只在「已知類別有幾種」。Balanced Accuracy 對每一類（含 unknown）的召回率取平均，不會被樣本數最多的類別主導；macro-F1 同理對每一類的 F1 取平均。這兩個指標在已知/未知樣本數差距懸殊（健康-only 時每組約 64 筆健康 vs ~3000 筆故障）時，比原始 Accuracy 更能反映「每一種情況是不是都被顧到」。

## 參考論文

- Ledoit & Wolf 收縮估計、legacy 全域共變異數對照：出處與複製來源同 [exp1_cold_start.md](exp1_cold_start.md)、`core/mahalanobis.py` 檔頭註記。
- F. Wilcoxon (1945), “Individual Comparisons by Ranking Methods,” *Biometrics Bulletin*, 1(6), 80–83。DOI [10.2307/3001968](https://doi.org/10.2307/3001968)。
- 用 Balanced Accuracy／macro-F1 當主指標、Accuracy 天花板分析、5 pp 絕對門檻：本專案操作約定，理由見上方「先寫定」段落與 issue [#15](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/15) 原文。
- `unknown` 類別的 binary F1：本專案操作約定，用來單獨檢視「拒絕未見配置」這件事，不被已知類別的多類指標稀釋。

## 預期成果

若 Ledoit–Wolf 相對 legacy 在 Protocol A 的 Balanced Accuracy／macro-F1 絕對提升 ≥ 5 pp 且 Wilcoxon 顯著（p < 0.05），達標；若提升幅度在 5 pp 以下或不顯著，就是「方法改善確實存在但未達專題門檻」，照實記錄，不調整門檻重跑。Protocol B（冷啟動）應該重現 exp6 已知的健康誤報落差（legacy 83.1% vs ledoit_wolf 7.1%），預期在 Accuracy/F1 上也會有大落差，因為 legacy 的健康誤報會拖垮「健康」這一類的召回率。

## 注意

本實驗的切分是本專案的 60/20/20 隨機切分（`core.data.make_split`），不是 [#9](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/9) 的 campaign-group 切分。#9 在 campaign-group 切分下 N=5 已知準確率只有 25.744%、unknown AUROC ≈ 0.52～0.53；本實驗的數字不能拿來和 #9 的結論相提並論或替代，兩者的切分假設不同。

## 已記錄的實測

`venv/bin/python -m experiments.exp11_ancestor_comparison`（9 組資料集 × seeds `42,123,2026` × `legacy`/`ledoit_wolf`，共 108 列，`output/exp11_ancestor_comparison/2026-10-09-14-17-27/`）：

| Protocol | 方法 | Accuracy | Balanced Accuracy | macro-F1 | unknown F1 |
|---|---|---:|---:|---:|---:|
| A（Ancestor） | legacy | 0.8300 | 0.1667 | 0.1512 | 0.9071 |
| A（Ancestor） | ledoit_wolf | 0.9898 | 0.9505 | 0.9730 | 0.9939 |
| B（冷啟動） | legacy | 0.9784 | 0.5000 | 0.4946 | 0.9891 |
| B（冷啟動） | ledoit_wolf | 0.9988 | 0.9714 | 0.9847 | 0.9994 |

絕對提升：Protocol A 的 Balanced Accuracy +78.38 pp、macro-F1 +82.18 pp；Protocol B 的 Balanced Accuracy +47.14 pp、macro-F1 +49.01 pp。兩個協定、兩個主指標都遠遠超過 **≥5 pp 達標門檻**。Wilcoxon 配對檢定（27 對 `(dataset, seed)`）：Protocol A macro-F1 `W=0.0, p≈0`（27 對全部同方向，p 值小到四捨五入成 0）；Protocol B macro-F1 `W=0.0, p=6e-06`。兩者都達顯著。

這個落差比 exp6 已知的健康誤報差距（83.1% vs 7.1%）更極端，原因不只是校準：`legacy` 用單一全域共變異數（`core/mahalanobis.py` 的 `method="legacy"` 分支忽略 `y_train`，只估一個高斯分布，`ClassDistribution(label=-1, ...)`），`predict_known_class` 找不到 `label=-1` 對應的已知類別名稱，於是**幾乎每一筆已知類別的樣本都被判成 unknown**——Protocol A 的 `unknown_f1` legacy 反而有 0.9071（因為「幾乎都判 unknown」在以 unknown 為正類的二元 F1 上表現不差），但代價是 5 個已知類別的召回率全部趨近 0，Balanced Accuracy 被拖到 1/6 附近（0.1667，剛好對應 6 類裡只有 1 類被正確分辨）。結論：這不是「legacy 校準比較鬆」，而是「legacy 的單一全域分布結構性無法做多類判別」——比主線敘事（健康-only 冷啟動）更嚴重地暴露了逐類 Ledoit–Wolf 共變異數的必要性。Accuracy（非主指標）的差距遠小（Protocol A +15.98 pp、Protocol B +2.04 pp），印證了 issue #15 原文「類別不平衡下 Accuracy 幾乎只反映多數類」的判斷，也驗證了選 Balanced Accuracy/macro-F1 當主指標是對的決定。

## 程式碼與輸出

| 路徑 | 角色 |
|---|---|
| `experiments/exp11_ancestor_comparison.py` | `run`、`build_ancestor_monitor`、`_evaluate_protocol`、`_figure`、`main` |
| `core/monitor.py` | `OpenSetMonitor.fit_initial`、`add_class`、`classify`、`holdout` |
| `core/mahalanobis.py` | `legacy`、`ledoit_wolf` 兩種共變異數估計 |
| `core/data.py` | `discover_datasets`、`load_pools` |

輸出：

- `logs/exp11_ancestor_comparison/{時間戳}.log`
- `output/exp11_ancestor_comparison/{時間戳}/summary.json`
- `output/exp11_ancestor_comparison/{時間戳}/ancestor_comparison.png`

### 散在其他位置的相關檔案

- 測試：`tests/test_exp11_ancestor_comparison.py`（已知類別集合正確、未知配置從未進 `add_class`、回傳指標鍵齊全、Wilcoxon 結構）。
- 被引用：[exp12_confusion_tsne](exp12_confusion_tsne.md) 匯入 `build_ancestor_monitor` 畫開集多類混淆矩陣。
- 歷史對照：[Mahalanobis_Improvement.md](../Mahalanobis_Improvement.md)（舊腳本已移至 Ancestor，不能重跑，僅供數字對照）。
- 來源 issue：[#15](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/15)。
