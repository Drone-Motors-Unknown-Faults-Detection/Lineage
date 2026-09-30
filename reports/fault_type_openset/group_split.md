# Campaign-held-out sample splitting

> 2026-10-01 correction: verified path mappings plus the pinned guide support
> documented leave-one-motor-out interpretation. The original "not proven
> physical motor holdout" wording below concerns missing full provenance,
> not absence of documented motor identity. See provenance_followup.md.

`core.fault_type_sample_split` chooses source groups only after a class-role split has been fixed. The formal CSVs have three acquisition stage/T-code campaigns. Each fold holds out one entire campaign for final test, uses another for known-class training, and uses the third for validation and calibration. The three deterministic rotations are:

| Fold index | Train | Validation and calibration | Final test |
|---:|---|---|---|
| 0 | Stage 1/T1 | Stage 2/T2 | Stage 3/T3 |
| 1 | Stage 2/T2 | Stage 3/T3 | Stage 1/T1 |
| 2 | Stage 3/T3 | Stage 1/T1 | Stage 2/T2 |

The class-role registry binds fold indices 0/1/2 to sample-split seeds 42/123/2026. Each clean CSV remains an indivisible source subgroup. For Protocol A, healthy and known faulty configurations occur in train, validation/calibration and test campaigns; held-out unknown configurations occur only in final test. For Protocol B, the distinct unknown-validation configuration occurs only in validation, never in training, calibration or final test. Samples from the excluded campaigns for those roles are explicitly recorded as excluded.

This is an **exploratory campaign holdout**, not proven physical motor holdout. The feature CSVs provide no verified physical motor or session IDs, and original raw-window intervals are unavailable. There are only three campaigns: validation and calibration must share the same known samples, and final test has one independent campaign per class. The split manifest records `shared_validation_calibration=true`; the validator will return `INCOMPLETE` for the two-independent-test-group requirement even when no known leakage is found. The Stage 2/T2 feature conversion path also differs from the copied Stage 1/3 features, which may influence fold differences.

The source-file subgroups never cross campaign partitions. No scaler, feature selector, classifier, covariance or detector reference may fit outside train; validation can choose preset model parameters, and calibration alone sets thresholds. Test labels and scores are evaluation-only. Those fit/selection contracts are enforced again in the runner and SplitValidator.
