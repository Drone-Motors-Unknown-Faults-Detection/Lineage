# exp6 formal matrix aggregate

- expected runs: 54
- completed runs: 54
- methods: mahalanobis, knn
- seeds: 42, 123, 2026

## Macro summary

| method | AUROC mean ± std | open-set accuracy mean ± std | unknown F1 mean ± std |
|---|---:|---:|---:|
| mahalanobis | 1.000000 ± 0.000000 | 0.998849 ± 0.000887 | 0.999412 ± 0.000453 |
| knn | 1.000000 ± 0.000000 | 0.998842 ± 0.000937 | 0.999409 ± 0.000478 |

## Paired differences

Positive values mean kNN is higher than Mahalanobis for that metric.

| metric | mean difference | std difference | pairs |
|---|---:|---:|---:|
| known_accuracy | -0.000531 | 0.042887 | 27 |
| open_set_accuracy | -0.000007 | 0.000954 | 27 |
| auroc | 0.000000 | 0.000000 | 27 |
| aupr_unknown_positive | 0.000000 | 0.000000 | 27 |
| fpr_at_tpr95 | 0.000000 | 0.000000 | 27 |
| unknown_precision | -0.000007 | 0.000972 | 27 |
| unknown_recall | 0.000000 | 0.000000 | 27 |
| unknown_f1 | -0.000003 | 0.000487 | 27 |
