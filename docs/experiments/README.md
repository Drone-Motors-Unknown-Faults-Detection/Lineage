# 研究分支實驗手冊索引

2026-10-02。這份索引包含本次補寫的 continuous Q 與同步 raw 模組。其他既有研究結果按 [分支總覽](../research_improvements_20260920.md) 的報告索引讀取；不宣稱全 repo 模組的手冊已補齊。main 既有 exp1–6 手冊另見 [main 索引](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/tree/main/docs/experiments)，不拿 main 的程式路徑當本分支実查結果。

依 main AGENT.md 新規定，後續新增實驗或更改方法／切分／指標先寫對應手冊，再改程式；補寫已有實作的手冊明示日期，不假造先後順序。

| 模組 | 手冊 |
|---|---|
| 研究收尾：`experiments/fault_type_research_closeout.py`（本次新增） | [證據盤點與文件交付](research_closeout.md) |
| exp22：`experiments/fault_type_group_dro.py`（預定，尚未實作） | [已知群組穩健損失](exp22_known_group_dro.md) |
| exp21：`experiments/fault_type_self_challenging.py` | [有限表格特徵自挑戰](exp21_feature_self_challenging.md) |
| exp20：`experiments/fault_type_risk_extrapolation.py` | [RPM風險差異與固定softmax](exp20_rpm_risk_extrapolation.md) |
| exp19：`experiments/fault_type_axis_kernel.py` | [三軸排列不變核](exp19_axis_invariant_kernel.md) |
| exp18：`experiments/fault_type_context_rejection.py` | [RPM原型距離與聯合拒絕](exp18_context_rejection.md) |
| exp17：`experiments/fault_type_context_prototypes.py` | [RPM工況相關原型](exp17_context_prototypes.md) |
| exp16：`experiments/fault_type_smooth_l1.py` | [平滑L1原型距離](exp16_smooth_l1_prototypes.md) |
| exp15：`experiments/fault_type_discriminative_prototypes.py` | [判別式原型學習](exp15_discriminative_prototypes.md) |
| exp13：`experiments/fault_type_metric_failure_diagnosis.py` | [封存後失敗診斷](exp13_metric_failure_diagnosis.md) |
| exp14：`experiments/fault_type_local_fisher.py` | [局部 Fisher 與 PCA 配對](exp14_local_fisher.md) |
| exp13：`experiments/fault_type_metric_classification.py` | [收斂距離與分類規則](exp13_metric_classification.md) |
| exp13：`experiments/fault_type_metric_source_verification.py` | [實際輸入來源重建](exp13_metric_source_verification.md) |
| `experiments/fault_type_solver_diagnosis.py`（train-only，無outer評估） | [fault_type_solver_diagnosis](fault_type_solver_diagnosis.md) |
| `experiments/fault_type_solver_report.py`（train-only重算） | [fault_type_solver_report](fault_type_solver_report.md) |
| `experiments/fault_type_continuous_study.py` | [fault_type_continuous_study](fault_type_continuous_study.md) |
| `experiments/synchronized_raw.py` | [synchronized_raw](synchronized_raw.md) |
| `experiments/synchronized_features.py` | [synchronized_features](synchronized_features.md) |
| `experiments/fault_type_continuous_inventory.py` | [fault_type_continuous_inventory](fault_type_continuous_inventory.md) |
| `experiments/fault_type_continuous_registry.py` | [fault_type_continuous_registry](fault_type_continuous_registry.md) |
| `experiments/fault_type_continuous_report.py` | [fault_type_continuous_report](fault_type_continuous_report.md) |
| `experiments/fault_type_continuous_report_v2.py` | [fault_type_continuous_report_v2](fault_type_continuous_report_v2.md) |
| `experiments/fault_type_continuous_smoke.py` | [fault_type_continuous_smoke](fault_type_continuous_smoke.md) |
| `experiments/fault_type_continuous_acceptance.py` | [fault_type_continuous_acceptance](fault_type_continuous_acceptance.md) |

## 各實驗的檔案位置

| 編號 | 入口與共用邏輯 | 測試、紀錄與輸出 | 展示 |
|---|---|---|---|
| exp22（預定） | `experiments/fault_type_group_dro.py`、`core/fault_type_group_dro.py` | `tests/test_fault_type_group_dro.py`、`tests/test_fault_type_group_dro_runner.py`、`logs/fault_type_group_dro_*/`、`output/fault_type_group_dro_*/` | N/A；尚未實作 |
| exp21 | `experiments/fault_type_self_challenging.py`、`core/fault_type_self_challenging.py` | `tests/test_fault_type_self_challenging.py`、`tests/test_fault_type_self_challenging_runner.py`、`logs/fault_type_self_challenging_*/`、`output/fault_type_self_challenging_*/` | N/A |
| exp20 | `experiments/fault_type_risk_extrapolation.py`、`core/fault_type_risk_extrapolation.py` | `tests/test_fault_type_risk_extrapolation.py`、`tests/test_fault_type_risk_runner.py`、`logs/fault_type_risk_extrapolation_*/`、`output/fault_type_risk_extrapolation_*/` | N/A |
| exp19 | `experiments/fault_type_axis_kernel.py`、`core/fault_type_axis_kernel.py` | `tests/test_fault_type_axis_kernel.py`、`logs/fault_type_axis_kernel_*/`、`output/fault_type_axis_kernel_*/` | N/A |
| exp18 | `experiments/fault_type_context_rejection.py`、`core/fault_type_context_rejection.py` | `tests/test_fault_type_context_rejection.py`、`logs/fault_type_context_rejection_*/`、`output/fault_type_context_rejection_*/` | N/A |
| exp17 | `experiments/fault_type_context_prototypes.py`、`core/fault_type_context_prototypes.py` | `tests/test_fault_type_context_prototypes.py`、`logs/fault_type_context_prototypes_*/`、`output/fault_type_context_prototypes_*/` | N/A |
| exp16 | `experiments/fault_type_smooth_l1.py`、`core/fault_type_smooth_l1.py` | `tests/test_fault_type_smooth_l1.py`、`logs/fault_type_smooth_l1_*/`、`output/fault_type_smooth_l1_*/` | N/A |
| exp15 | `experiments/fault_type_discriminative_prototypes.py`、`core/fault_type_discriminative_prototypes.py` | `tests/test_fault_type_discriminative_prototypes.py`、`logs/fault_type_discriminative_prototypes_*/`、`output/fault_type_discriminative_prototypes_*/` | N/A |
| exp13失敗診斷 | `experiments/fault_type_metric_failure_diagnosis.py`、既有預測reader | `tests/test_fault_type_metric_failure_diagnosis.py`、`logs/fault_type_metric_failure_diagnosis/`、`output/fault_type_metric_failure_diagnosis/` | N/A |
| exp14 | `experiments/fault_type_local_fisher.py`、`core/fault_type_local_fisher.py`、既有factory | `tests/test_fault_type_local_fisher.py`、`logs/fault_type_local_fisher_*/`、`output/fault_type_local_fisher_*/` | N/A |
| exp13 | `experiments/fault_type_metric_classification.py`、`core/fault_type_metric_classifiers.py`、既有 `core/openset.py` | `tests/test_fault_type_metric_classifiers.py`、`logs/fault_type_metric_classification_*/`、`output/fault_type_metric_classification_*/` | N/A；不改 `web/` 或 `experiments/health/` |
| exp13來源核對 | `experiments/fault_type_metric_source_verification.py`、既有factory | `tests/test_fault_type_metric_source_verification.py`、`logs/fault_type_metric_source_verification/`、`output/fault_type_metric_source_verification/` | N/A |
