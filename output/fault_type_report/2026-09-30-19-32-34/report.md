# Fault-configuration open-set results (exploratory)

All current matrices are INCOMPLETE: only one held-out campaign per class and shared validation/calibration. These are not complete independent physical-motor results.

Known classifier is fixed train-only balanced logistic regression. Detector thresholds use known calibration only. A and B are separate. Intervals are descriptive across correlated combinations/campaign folds, not motor-population confidence.

Rates below are percentages; AUROC is unitless. Healthy FPR is lower-is-better.

| Protocol | N | Detector | Runs | Known acc % | Unknown AUROC | Unknown recall % | Healthy FPR % |
|---|---:|---|---:|---:|---:|---:|---:|
| A | 5 | knn | 378 | 25.744 | 0.524 | 7.943 | 1.268 |
| A | 5 | mahalanobis | 378 | 25.744 | 0.528 | 14.995 | 2.259 |

See results_table.csv for mean, SD, nominal 95% intervals and pooled rates; per-class/paired JSON files contain detailed evidence. N=9 unknown metrics are unavailable, not zero.

## Artifact source directories

- `C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_matrix\2026-09-30-19-05-42`: 756/756 completed; model commit `dd7f679ec498d9836e7f3c2aeb355322776c158b`.
