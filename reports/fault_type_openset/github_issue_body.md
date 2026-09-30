## Completed evaluation, not a reliable physical fault-type claim

Branch: `research-improvements-20260920` (no main merge).

Implemented auditable class-role/campaign-group splits, immutable checksum-bound
manifests, PASS/INCOMPLETE/INVALID validator, train-only balanced multiclass
logistic baseline, existing factory Mahalanobis/Ledoit–Wolf and class-wise k-NN,
paired sample-ID verification, resumable matrices, complete metrics and archives.

- Protocol A N=5: all126 combinations ×3folds ×2methods =756 completed.
- Remaining N=1…8 sweep and N=9 closed-set:1014 completed.
- Separate B:30 combinations ×4 unknown-validation rotations ×3folds ×2methods =720.
- Total:2490 completed,0 failed,1245 matched detector pairs,137 tests passed.
- N=5 known accuracy25.744%; unknown AUROC .52775/.52448, recall14.995%/7.943%
  (Mahalanobis/k-NN). No reliable unseen-configuration rejection has been shown.

All current manifests are **INCOMPLETE**: one held-out campaign per class,
shared validation/calibration, no verified physical motor/session/run or raw-window
interval provenance. Nine faulty labels are screw count/position configurations
of one loosening mechanism, not nine verified physical fault causes.
No test-based tuning; Mahalanobis remains default, binary/PolarMap regressions pass.

## Evidence

- [Final 13-section report](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/research-improvements-20260920/reports/fault_type_openset/final_findings.md)
- [N-sweep results](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/research-improvements-20260920/reports/fault_type_openset/n_sweep_results.md)
- [Split completeness](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/research-improvements-20260920/reports/fault_type_openset/split_validation.md)
- [Artifact locations and SHA-256](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/research-improvements-20260920/reports/fault_type_openset/artifact_paths.md)
- [Commands and execution history](https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/blob/research-improvements-20260920/reports/fault_type_openset/execution_log.md)

Large predictions/original manifests/fit audits are retained in verified D-drive
ZIP64 bundles; raw/formal source data is not uploaded. Current execution used
Python3.14.6, not the declared3.10.19; unverified compatibility remains explicit.

## Remaining research acceptance criteria

- [ ] Verify physical motor/session/run identities and raw-source intervals/stride.
- [ ] Add independent test acquisition groups (at least two per evaluated configuration),
  without replacing test with calibration or counting RPM files as independent motors.
- [ ] Audit cross-stage 105-D feature semantics/sensor orientation (Stage2 was reconstructed).
- [ ] Pre-register a new train/validation-only model/feature comparison with a new final test;
  do not retrospectively tune this study's test to manufacture an improvement.
- [ ] Validate the declared Python3.10 environment separately.

Engineering/evaluation is complete; these external-data and efficacy limitations
remain open. This issue tracks them rather than asserting successful fault diagnosis.
