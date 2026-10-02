# TODO

專題目標（未知故障辨識、性能指標、視覺化）對照現況後的待辦清單，加上 repo 其他 open issues。2026-10-02 建立，細節見各 issue。
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

## 4. 其他 open issues

兩者都屬於 `research-improvements-20260920` 分支，尚未併入 main。

- [ ] [#9](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/9) 故障配置評估：獨立資料來源與可靠度未解
  - 現況：campaign-group 切分下 N=5 已知準確率 25.744%，unknown AUROC 0.528 / 0.524（Mahalanobis / k-NN），未證明能拒絕未見配置
  - [ ] 核對實體馬達 / session / run 身分與原始訊號區間、stride
  - [ ] 每個評估配置至少兩個獨立測試擷取群組（不拿 calibration 頂替 test，不把 RPM 檔案當獨立馬達）
  - [ ] 稽核跨階段 105 維特徵語意與感測器方向（Stage2 為重建）
  - [ ] 預先登錄新的 train/validation 比較與新的 final test，不回頭調這次的 test
  - [ ] 另外驗證宣告的 Python 3.10 環境（本次以 3.14.6 執行）
- [ ] [#11](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/11) `research-improvements-20260920` 分支文件
  - [ ] 在 `docs/` 新增一份 md 說明這個分支做了什麼
  - [ ] 更新 `README.md`、`docs/README.md`

## 5. Andy：持續研究與分支文件（2026-10-02）

工作分支：`research-improvements-20260920`。依 main 的 AGENT.md（blob `f3b92347582bceff98ede6513f06458cdefdeac5`）先寫實驗手冊，再修改方法。相關來源問題保留在 [#9](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/9)。

- [ ] [#22](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/22) 持續研究：局部距離學習、幅值比值與配對驗證
  - [ ] 完成 [#11](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/11)：分支總覽、README 與 docs 索引；補充同步 raw schema 的實際用途與限制。
  - [ ] 補齊現行 continuous_research 各模組手冊；已有程式的手冊註明補寫日期，後續改動先寫手冊。
  - [ ] 核對已封存 Q01–Q08 配對評估：72 格預定；12 格因訓練最佳化未收斂而 INCOMPLETE，不補零、不換參數填回。
  - [ ] 重推論、重算指標，核對來源 SHA、fit/cal/test IDs 與健康總誤報；保存全部成功與失敗格。
  - [ ] 封存本批結果、雙 Python 測試與 D 槽備份；記錄相對 C02/C17/C24/D01 的配對差異。
  - [ ] 依未收斂／跨馬達失敗證據，先登錄下一批有限改編，再實作與消融；保留 formal105、LW、k-NN factory 與 PolarMap 正式預設。
  - 已有 28,910 筆資料全部有 test 曝露歷史。新比較皆為 exploratory；來源未知與獨立 test groups 不足不改成 PASS。此項不依賴重新採集，也不宣稱可靠模型已完成。
