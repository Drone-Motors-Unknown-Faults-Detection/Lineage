# Fault-configuration open-set results (exploratory)

All current matrices are INCOMPLETE: only one held-out campaign per class and shared validation/calibration. These are not complete independent physical-motor results.

Known classifier is fixed train-only balanced logistic regression. Detector thresholds use known calibration only. A and B are separate. Intervals are descriptive across correlated combinations/campaign folds, not motor-population confidence.

Rates below are percentages; AUROC is unitless. Healthy FPR is lower-is-better.

| Protocol | N | Detector | Runs | Known acc % | Unknown AUROC | Unknown recall % | Healthy FPR % |
|---|---:|---|---:|---:|---:|---:|---:|
| A | 1 | knn | 27 | 69.355 | 0.609 | 26.138 | 8.112 |
| A | 1 | mahalanobis | 27 | 69.355 | 0.602 | 39.899 | 16.327 |
| A | 2 | knn | 90 | 47.576 | 0.557 | 18.078 | 5.791 |
| A | 2 | mahalanobis | 90 | 47.576 | 0.555 | 26.227 | 10.996 |
| A | 3 | knn | 90 | 36.716 | 0.536 | 12.208 | 4.306 |
| A | 3 | mahalanobis | 90 | 36.716 | 0.538 | 20.982 | 6.495 |
| A | 4 | knn | 90 | 29.549 | 0.521 | 9.738 | 2.502 |
| A | 4 | mahalanobis | 90 | 29.549 | 0.531 | 17.166 | 3.642 |
| A | 5 | knn | 378 | 25.744 | 0.524 | 7.943 | 1.268 |
| A | 5 | mahalanobis | 378 | 25.744 | 0.528 | 14.995 | 2.259 |
| A | 6 | knn | 90 | 22.329 | 0.521 | 6.334 | 0.688 |
| A | 6 | mahalanobis | 90 | 22.329 | 0.523 | 13.390 | 1.610 |
| A | 7 | knn | 90 | 20.472 | 0.521 | 5.893 | 0.218 |
| A | 7 | mahalanobis | 90 | 20.472 | 0.522 | 11.972 | 0.423 |
| A | 8 | knn | 27 | 18.538 | 0.522 | 4.734 | 0.053 |
| A | 8 | mahalanobis | 27 | 18.538 | 0.519 | 10.807 | 0.011 |
| A | 9 | knn | 3 | 16.445 | unavailable | unavailable | 0.034 |
| A | 9 | mahalanobis | 3 | 16.445 | unavailable | unavailable | 0.000 |
| B | 5 | knn | 360 | 25.262 | 0.522 | 7.383 | 1.027 |
| B | 5 | mahalanobis | 360 | 25.262 | 0.529 | 14.536 | 2.721 |

See results_table.csv for mean, SD, nominal 95% intervals and pooled rates; per-class/paired JSON files contain detailed evidence. N=9 unknown metrics are unavailable, not zero.

## Artifact source directories

- `C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_matrix\2026-09-30-19-05-42`: 756/756 completed; model commit `dd7f679ec498d9836e7f3c2aeb355322776c158b`.
- `C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_matrix\2026-09-30-19-37-27`: 1014/1014 completed; model commit `3d8b9f02269ad1eb030f45c34e3a20612b1d7f77`.
- `C:\Users\andy0\AppData\Local\Temp\codex-d-drive\schoolshit\專題\src\_lineage_compare\p1_worktree\output\fault_type_matrix\2026-09-30-19-37-39`: 720/720 completed; model commit `3d8b9f02269ad1eb030f45c34e3a20612b1d7f77`.
