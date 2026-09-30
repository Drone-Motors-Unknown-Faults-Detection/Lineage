# Runtime estimate and pre-test execution decision

Measured on 2026-09-30, before inspecting primary test scores:

- Smoke `--n 5 --pilot --sample-cap-per-source 10`: both methods completed;
  300 test predictions per detector. Output `2026-09-30-19-03-28`.
- Full-size pilot `--n 5 --pilot`: both methods completed; model times .860s
  Mahalanobis and .917s k-NN. Matrix execution (including manifests/prediction
  persistence, excluding initial catalog and final aggregation) 3.983s.
- Full pilot artifact bytes 9,854,684, of which 3,552,194 are its one gzip
  manifest. The CPU/IO estimate is approximately 4–5 seconds per paired fold,
  with aggregation and larger/harder classifiers adding uncertainty.

Primary decision: enumerate all 126 N=5 combinations in Protocol A, with all
three predeclared campaign seeds/folds and both detectors: 756 detector runs,
378 manifests, about 25–35 minutes and approximately 3.7GB artifacts. This is
acceptable on the observed available 20.4GB C-drive space. NO test accuracy or
unknown-rejection score was used in this decision.

Freeze the new registry `class_roles_v1_40cb4312c2e92342.json` before primary
execution. Checksum:
`40cb4312c2e923426407035fc3c0696f8d51cdd7190a2f1ee123c6aae3f1d8d6`.
It has 295 Protocol A roles (N=5 full enumeration, other N retain their declared
all-if-small/balanced30 policy). Full A = 1770 detector runs; remaining N-sweep
after N=5 = 1014 runs, roughly 35 additional minutes (order-of-magnitude estimate).

Secondary Protocol B uses the ORIGINAL balanced30 registry, all four
unknown-validation rotations, three folds and two detectors: 720 runs, roughly
25 minutes and 3.6GB. It is a separate study, not a mixture with A. Unknown
validation remains diagnostic for these fixed known-calibrated methods.

All runs are exploratory INCOMPLETE: shared validation/calibration and only
one held-out campaign per class. Missing physical motor/session/raw-window
metadata prevent a complete independent-test claim. Feature ablation is skipped
with a saved reason (no usable neural embedding). Actual duration, failures and
artifact volume will supersede these estimates in the execution record.
