# Fault-configuration classifier and open-set protocols

The existing binary pipeline and PolarMap are unchanged. A separate executable
`experiments.fault_type_openset` exposes `run(pools, manifest=...)` and `main()`.
Here `pools` is a read-only FeatureStore, not a random sample splitter.

Fixed baseline: train-only RobustScaler, balanced-class-weight multinomial
logistic regression (C=1, lbfgs, tolerance 1e-4, maximum 1000 iterations).
Nonconvergence is a failed run, not silently accepted or fixed after viewing
test scores. There is no PCA, learned embedding, feature selection or early
stopping. No usable Step-3 multiclass classifier exists in the current architecture;
the archived Ancestor pipeline is not imported.

Both detectors use the existing `core.openset.create_openset_detector`, the
same scaler/train/calibration/test matrices and a fixed calibration confidence
of .95. Mahalanobis (Ledoit-Wolf) remains default; k-NN uses k=5. Unknown is
strictly normalized score > 1. The classifier's predicted class is separate
from the detector's nearest reference class, even if the sample is rejected.

- Protocol A: unknown-test classes enter only final evaluation. No unknown
  score participates in model or threshold fitting.
- Protocol B: a separate label can appear in unknown validation. The existing
  fixed-threshold detectors do not need unknown validation; its score/recall
  is diagnostic only, never used for calibration or method selection. Rotation
  is supported by the class registry. A and B must be reported separately.

Every result saves actual probabilities and confidence (not fabricated logits),
test/sample/class IDs, roles, RPM/campaign, rejection scores and decisions,
closest calibrated class, manifest checksum and calibration version. Compressed
fit-audit artifacts list exact scaler/classifier/reference/calibration IDs.
This baseline predicts configurations, not physical fault causes or torque.

Tests spy on the actual scaler and detector fit calls, not just declared audit
metadata; they cover deterministic paired prediction, probability round trips,
invalid-before-load rejection and distinct unknown validation.
