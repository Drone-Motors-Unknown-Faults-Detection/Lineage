# Metrics and uncertainty conventions

Known classification is evaluated on all healthy/known-fault test samples,
whether accepted or rejected: accuracy, balanced accuracy (mean recall over
present true classes), macro-F1, per-class precision/recall/F1, and confusion
matrices. Fault-only results retain a healthy prediction column, so mistakes
are never silently removed from the confusion matrix.

Unknown is the positive class. Scores increase toward unknown. Report AUROC,
average-precision AUPR, precision/recall/F1 at score > 1, known acceptance rate,
healthy false-positive and acceptance rates. FPR@95TPR is interpolated linearly
between adjacent empirical ROC points (all points retained); no unknown
positives means unavailable/null, especially in the N=9 closed-set baseline.

Open-set classification rate = number of known samples correctly classified
AND accepted / number of known samples. It is a single-threshold rate, NOT the
OSCR curve area. We do not report OSCR without a validated curve implementation.
No events/time boundaries means no events-per-hour claim.

Equal-run macro summaries give each configuration/fold equal weight; pooled
summaries give each prediction equal weight and larger splits more influence.
Repeated source samples across class combinations are repeated predictions,
not new independent observations. Mean, sample standard deviation and nominal
Student-t 95% intervals across runs are descriptive. They do not establish
independent motor-population uncertainty with only three campaign codes.

Detector pairing is by identical immutable manifest checksum; sample-ID sets
are also checked when prediction arrays are present. Deltas are k-NN minus
Mahalanobis. A and B cannot be mixed in the aggregator. Reports must separately
stratify protocol, N, detector, completeness status and feature representation;
failed/skipped runs stay in the declared-run index with their reasons.

Per-unknown configuration summaries contain recall, score quantiles and the
closest known reference-class attraction, not only a grand average. A classifier
prediction is not assumed equal to the detector's nearest reference class.
