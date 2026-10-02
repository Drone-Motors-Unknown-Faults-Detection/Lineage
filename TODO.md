# TODO

專題目標（未知故障辨識、性能指標、視覺化）對照現況後的待辦清單。2026-10-02 走訪 repo 後建立，細節見各 issue。
依 [AGENT.md](AGENT.md)「實驗手冊」規定，每一項都要先在 `docs/` 寫手冊、在 `docs/README.md` 加一列，再改程式。

## 1. 未知故障辨識與遷移學習

已有：只用健康資料的冷啟動偵測（`exp1_cold_start`）、HDBSCAN 新故障發現（`exp2_scale_growth`）、七種單類偵測器比較（`exp6_osr_benchmark`，含 PCA 重建 `core/detectors.py:127`）。

- [ ] [#13](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/13) 非線性 AutoEncoder 偵測器
  - [ ] 手冊 `docs/exp7_autoencoder.md`
  - [ ] `core/detectors.py` 新增 AE（sklearn `MLPRegressor`，不加依賴），加進 `ALL_DETECTORS`
  - [ ] `exp6_osr_benchmark` 9 工況比較；`tests/` 加 seed 重現檢查
- [ ] [#14](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/14) 遷移學習
  - [ ] 手冊 `docs/exp8_transfer.md`：來源／目標工況、目標端健康樣本數 0 / 10 / 25 / 50
  - [ ] 至少一種遷移方法（CORAL、目標端重新縮放、共變異數混合，或 #13 的 AE 微調）
  - [ ] 對照：直接搬移（exp5 現況，平均 AUROC 0.893、最低 0.10）vs 目標端從零冷啟動

## 2. 性能指標：相對 Ancestor 提升 5%~10%

已有：`docs/Mahalanobis_Improvement.md`（歷史文件，腳本在 Ancestor）開集 Accuracy 0.9509 → 0.9864（+3.55 pp，未達標）、Balanced Accuracy +6.51 pp、F1 未記錄。

- [ ] [#15](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/15) Ancestor 對照實驗
  - [ ] 手冊 `docs/exp9_ancestor_comparison.md`，先寫定主指標與達標門檻（建議 Balanced Accuracy、macro-F1；Accuracy 天花板只剩 4.9 pp）
  - [ ] 從 Ancestor 複製 legacy 邏輯並註記來源（鐵則 1）
  - [ ] Ancestor 協定（已知 8/1/2/3/4screws、未知 5/6/7/3_14/4_146screws）＋冷啟動協定
  - [ ] 9 工況 × 3 seed（42/123/2026），輸出 Accuracy、Balanced Accuracy、macro-F1、unknown F1、Wilcoxon 配對檢定
  - [ ] 寫明切分方式，不和 [#9](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/9) 的 campaign-group 結果混用
  - [ ] 結果寫進 README「原創貢獻總覽」

## 3. 視覺化：混淆矩陣與 t-SNE

已有：PCA 投影（`core/monitor.py:90`、Web）、`polar_map.png`、`detect_rates.png`、`cross_condition.png`、`osr_benchmark.png`。

- [ ] [#16](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/16) 混淆矩陣與 t-SNE
  - [ ] 手冊 `docs/viz_confusion_tsne.md`
  - [ ] 混淆矩陣：健康 vs 故障（exp1）、開集多類（已知各類 + unknown）
  - [ ] t-SNE：105 維 RobustScaler 特徵，顏色 = 螺絲配置、標記 = 系統判定，9 工況
  - [ ] 經 `core.logger.setup_run` / `save_plot()` 輸出；README 或 `docs/Experiments_Guide.md` 引用
  - [ ] #15 完成後加 legacy vs LW 混淆矩陣並排圖
