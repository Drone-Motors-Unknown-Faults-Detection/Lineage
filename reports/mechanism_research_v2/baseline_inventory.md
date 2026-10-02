# 機制研究 v2 起點（2026-10-02，Asia/Taipei）

實際 checkout：`C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree`。
branch `research-improvements-20260920`，起點 HEAD `791ee5bf5fd723b3bd1299feda1885c5d43dd91f`；origin 為 Drone-Motors-Unknown-Faults-Detection/Lineage。完整讀取 AGENT.md；沒有新建 repo、thread 或 PR。

## 已核對證據

- literature_expansion/result_index.json 的 seal PASS，17 個引用 artifact 的實際 SHA 全數一致；9 個正式 joblib SHA、234 組 fit audit、舊 protocol source/runtime 契約 PASS。
- 90 CSV / 28,910 unique 105維有限值 rows；重新 scan 指紋 `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。
- Python 3.10.19 / sklearn1.7.2 / numpy2.2.6 / scipy1.15.3 是 science 環境；3.14.6 / sklearn1.9.1 僅 compatibility，不跨版本載入 joblib。
- 原 dirty status 847 entries，其中282個 tracked deletions，全部保留、不得 stage。C槽可用約2.24GB；D槽约910GB。psutil 未安裝；峰值記憶體使用作業系統標準介面，不安裝新依賴。
- 先前 accuracy study：198 新評估、1,908,060 predictions；literature：630計畫/624完成/6R17 INCOMPLETE、6,013,647 predictions。這些不是新增獨立樣本。
- C02/A0 mixed RPM；C24/A7 full per-RPM pipeline 完整匹配。A1 原本 separate，不重複已撤回的 mixed 解讀。
- C17 fault-only30.4315% vs C02 26.6126%，但 C24/A7 30.9091%；C17/M unknown recall8.4358% vs C02/M18.4367%。C17三motor的2screws recall0；NCA九fits都收斂。
- 舊 healthy_safety.false_positive_rate 只計 healthy→UNKNOWN。C17/T1另有31.5843% healthy→known fault，必須新增完整決策指標。

## 沿用產物與工作範圍

完整絕對路徑、SHA與 seals 沿用 `reports/literature_expansion/result_index.json`；accuracy與fixed-calibration各自index亦已讀取。重新核對 sealed models/manifests，不重推6百萬筆未改模型，不重跑2490次歷史全量研究。本輪用新目錄、新工具、新protocol，不改 sealed source、舊summary或formal data。

| 狀態 | 方法／事項 |
|---|---|
| 已實測 | 24分類pipelines×M/K＋22score，詳舊registry與sources；LR/LDA/RF/ET/HGB/SVM/kNN/GNB/RDA-inspired/PCA/NCA，pooled/RMD/OAS/diagonal/centers/GMM/IF/LOF/OCSVM/MSP/entropy/margin/fusion/Energy/ViM |
| INCOMPLETE | R17 六格 predicted-calibration group 缺樣，不補0、不取消失敗 |
| 文獻候選、未實作 | LMNN、OpenMax、Deep SVDD、SupCon、LogitNorm；不得改名舊NCA或LDA logits冒充 |
| 現資料不可可靠計算 | raw order/time-frequency、每小時誤報、警報延遲、RUL；raw-row mapping/timing等缺證據 |
| 本輪新增 | metric_definition_v2、train/in-sample與曝光test診斷、原始文獻方法卡、有界≤12完整arms、同條件checkpoint實測、完整健康誤報tradeoff |

三fold固定 train/cal/test=T1/T2/T3、T2/T3/T1、T3/T1/T2，selection/validation空。全部樣本历史 test exposure；session/window獨立性UNKNOWN，每類≥2 test groups要求仍INCOMPLETE。此輪不以高分數替換正式105/Maha-LW/PolarMap；kNN factory保持。
