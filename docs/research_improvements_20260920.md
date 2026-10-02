# research-improvements-20260920 分支說明

更新：2026-10-02（Asia/Taipei）；文件起點 HEAD `e35abd12c4f257da8173f1a750dedb10d99b0ab7`。對應 [Docs #11](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/11)，後續研究追蹤 [#22](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/22)。本文件描述研究分支，未表示所有功能已合併 main。

## 這個分支做什麼

main 的冷啟動流程只用健康資料建立異常量尺。本分支另外研究「健康＋部分已知螺絲配置」的分類與未知配置識別，並補上來源追溯、用途分離、逐樣本稽核、同步原始訊號與新版特徵入口。健康監測可以提供指標與警報；現有資料不能證明剩餘壽命、損壞百分比或真實退化生命週期。

正式介面仍為 105 維特徵、linear 分類基線與 Mahalanobis–Ledoit–Wolf 預設；k-NN 由 `core.openset` factory 切換，PolarMap 保留。研究表示法與模型獨立封存，較高分數不自動替换正式模型。

## 成果與閱讀順序

| 工作 | 程式入口 | 證據／報告 |
|---|---|---|
| 正式資料盤點、配置 open-set 與老師提出的不同 N | `core/formal_data.py`、`experiments/fault_type_matrix.py` | [fault_type_openset 結案](../reports/fault_type_openset/final_findings.md) |
| 馬達身分、來源與跨階段特徵契約 | `core/fault_type_provenance.py`、`core/fault_type_feature_contract.py` | [來源追蹤](../reports/fault_type_openset/provenance_followup.md) |
| 用途交集、來源副本與 raw alias 防護 | `core/fault_type_leakage.py`、`core/fault_type_final_guard.py` | [20261001 稽核](../reports/data_independence/audit_20261001.md) |
| 取消共同選模型、專用馬達 calibration | `experiments/fault_type_fixed_calibration.py` | [固定方法報告](../reports/fixed_motor_calibration/final_report.md)、[T1 診斷](../reports/fixed_motor_calibration/t1_failure_analysis.md) |
| 有限文獻比較、分類與拒絕分支改編 | `core/fault_type_literature.py`、`core/fault_type_mechanisms.py` | [文獻比較](../reports/literature_expansion/final_findings.md)、[機制比較](../reports/mechanism_research_v2/final_findings.md) |
| 健康完整誤報與持續研究 Q 批 | `core/fault_type_metrics_v2.py`、`core/fault_type_continuous.py` | [持續研究狀態](../reports/continuous_research/research_state.json)、[手冊索引](experiments/README.md) |
| 同步 raw、切窗、新 105 維版本與 fresh qualification | `core/synchronized_raw.py`、`core/synchronized_features.py`、`experiments/fault_type_fresh.py` | [schema 用途](synchronized_raw_schema.md)、[重現與限制](../reports/synchronized_pipeline/reproduction.md) |
| Health Index、嚴重度級別、趨勢與警報 | `health/`、`experiments/health_index_*` | [健康監測流程](health_monitoring_workflow.md) |

文件中的程式路徑屬於本分支。歷史 Step 1–6 快照另見 [docs 索引](README.md)，原始碼在 Ancestor。

## 資料與馬達角色

正式資料為 90 CSV、28,910 筆有限值 105 維；fingerprint：
`c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`。
8screws 為 healthy，其餘九個 labels 是螺絲鬆動數量／位置配置，不能寫成九種已確認的不同物理故障原因。

[固定版本 Experiments_Guide](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/afcfcc419dab3103a86a8f95601d3af85890eb38/docs/Experiments_Guide.md#L218) 支持 T1/T2/T3 為三顆不同馬達，T1 新、T2/T3 老。使用時數、序號、session/run 與原始視窗來源沒有完整證據；保持 UNKNOWN，個體與老化影響無法分離。

目前 no-selection 比較固定：

| fold | train | calibration | test |
|---|---|---|---|
| 0 | T1 | T2 | T3 |
| 1 | T2 | T3 | T1 |
| 2 | T3 | T1 | T2 |

train/calibration 僅包含 healthy 與同組 known；另外兩顆開發馬達的 unknown 不使用。validation/selection IDs 為空，沒有跨折共同 winner。三顆 motor × 三 RPM 為九工況；seed 0/1/2 沒有增加独立馬達數。

## 結果應如何解讀

歷史 N=5 全 126 組、N-sweep 與 Protocol B 共 2,490 runs 已完成。N=5 known accuracy 約 25.74%，Mahalanobis/k-NN unknown AUROC 約 0.5277/0.5245。這些數字屬歷史協定，不能當 no-selection 新跑的數字。

後續 C17 harmonic69/shrinkage LDA 的 healthy＋known accuracy 約 39.29%，fault-only accuracy 約 30.43%；不同協定不能直接歸因為單一算法提升。C17/M unknown recall 約 8.44%，C02/M 約 18.44%；2screws 崩潰、T1 未知漏報及健康被分成已知故障仍是失敗證據。詳細配對結果依各 result index，而非以單項最高分宣布最佳。

Q01–Q08 封存為 72 格；本次檢查 aggregate 實際為 60 格、576,144 筆 prediction records、28,910 unique samples，12 格因訓練 metric 未收斂 INCOMPLETE。獨立 verify 與完整可靠性報告尚待完成，這裡不宣稱 Q 通過。

## 仍未完成的研究驗收

全部 28,910 舊 rows 已有 test 曝露，後续為 adaptive exploratory。新 seed、SHA 或檔名不能成為 fresh test。每類至少兩個獨立 test groups 的要求仍未通過。完全相同檔案／特徵向量重複為零，也不能证明原始 windows 不重疊。

同步 pipeline 與 synthetic fixture 通過工程檢查；沒有合格真實 fresh final test。填寫 metadata、通過 schema、程式能執行，都不能補造原始採集證據。現有資料可以繼續研究與配對實測，不以重採作本輪前置條件。

## 怎麼接續

在研究 checkout 根目錄先確認 branch/HEAD；正式科学環境為 `.venv310/Scripts/python.exe`（3.10.19）。`venv/Scripts/python.exe`（3.14.6）用於相容測試，不跨 sklearn 版本載入同一份 joblib。命令見 [Q study 手冊](experiments/fault_type_continuous_study.md)；每次以 `core.logger.setup_run` 保存 logs/output。大型產物沿 D 槽 archive 策略，compact 索引進 Git，不提交 raw/private data。

main 新 AGENT.md blob `f3b92347582bceff98ede6513f06458cdefdeac5` 已讀取。這一輪補寫已有 continuous 模組手冊；補寫日期不冒稱早於原實作。後續改方法、切分或指標先更新对应手冊，再改程式。請勿因 README 還有歷史冷啟動高分就宣稱跨馬達 fault-type 已可靠。
