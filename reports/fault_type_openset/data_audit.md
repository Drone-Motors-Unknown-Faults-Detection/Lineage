# Fault-configuration data audit (2026-09-29)

## Actual input and physical meaning

The experiment loader consumes the ignored local `data/formal_local/Step-*/myfeature/*/*/*/*_Group_feature_data_clean.csv`, materialized from three user-provided stage ZIP archives. The materialization manifest records 90 clean feature CSVs, 28,910 rows and 105 numeric features per row. Stage 1/T1 and Stage 3/T3 files were copied from clean-feature archives; Stage 2/T2 features were reconstructed from five 10 kHz channels. All 90 files were readable and their numeric rows finite. A numeric-position exact-duplicate check across all 28,910 rows found zero exact duplicates; this does not establish independence of nearby or overlapping raw windows.

The directory names encode one **screw-loosening mechanism** in nine configurations, not nine independently verified physical fault causes. `8screws` is the healthy mounting. The `7screws` through `1screws` labels vary the number of tight screws and may proxy severity; `3_14screws` and `4_146screws` additionally encode nonuniform positions. No measured torque, physical damage severity, bearing defect, or causal failure label is available. All results in this task are therefore fault-**configuration** classification and rejection.

| Path label | Role/meaning | Clean CSVs | Source-file groups | 105-D windows |
|---|---|---:|---:|---:|
| 8screws | healthy mounting | 9 | 9 | 2,822 |
| 7screws | one screw loosened | 9 | 9 | 2,637 |
| 6screws | two screws loosened | 9 | 9 | 2,876 |
| 5screws | three screws loosened | 9 | 9 | 2,890 |
| 4screws | four screws loosened | 9 | 9 | 2,803 |
| 3screws | five screws loosened | 9 | 9 | 2,929 |
| 2screws | six screws loosened | 9 | 9 | 2,985 |
| 1screws | seven screws loosened | 9 | 9 | 2,986 |
| 3_14screws | three-screw positional configuration | 9 | 9 | 3,021 |
| 4_146screws | four-screw positional configuration | 9 | 9 | 2,961 |

Each label occurs in three stage/T-code campaigns and three RPM values (6000, 8000, 11000) per campaign, yielding nine feature files. Stage totals: T1 9,759, T2 9,857, T3 9,294 rows. The largest/smallest class ratio is about 1.15, so sample count imbalance is modest; campaign and processing differences matter more.

The existing `core.data.load_pools` keys classes by directory-name strings. `data_audit.json` assigns stable numeric IDs 0–9 in table order for this new experiment only; these IDs are not claimed to be pre-existing source labels.

## Acquisition units and missing metadata

The feature CSV body has only 105 numeric feature columns. The path gives `stage`, T-code, RPM and configuration. It does **not** give a trustworthy physical motor serial, acquisition date, session, run, load, ambient or motor temperature, event boundary, operator, raw-window start/end sample, or original 10 kHz source interval. The preprocessing description documents nominal 10,000-point/1 s windows, but does not preserve stride or raw-window IDs in the clean CSV. Event counts and overlap counts are therefore unknown, not zero.

Repository documents conflict about T1/T2/T3: README describes three lifetime phases, while `reports/health_monitoring_data_capability.md` says the T-codes are paths/stages without verified motor IDs. They are treated as **acquisition campaigns**, never as proven distinct physical motors. Motor-level holdout cannot be certified. `stage/T-code` is the coarsest available grouping, with three groups per class; source CSV is an indivisible lower-level group for traceability. Any four-way split using only these campaigns must share validation and calibration or use nested folds. One campaign held out for test gives only one independent coarse test group per class, below the preferred two-group minimum; the validator must mark that limitation `INCOMPLETE`.

## Leakage and compatibility checks

- Labels come from directory names, not a CSV label column. Filenames and paths expose the class and must never be features.
- Stage 2 has 23 text-header differences from the copied Stage 1/3 files (capitalization and historical Y/Z FFT suffix names). The 105 positions are aligned by the documented extraction contract; matrix loading must use position and verify dimension/order rather than concatenate by text header.
- The previous `core.continual_protocol` used 45 of 90 files (14,070 rows), including Stage 3 files in both update and test roles. Its fingerprint is valid for that earlier replay, not for rotating known/unknown labels or campaign holdout here.
- No exact duplicate numeric 105-D rows were found, but the missing raw interval and acquisition IDs prevent proving absence of overlapping windows or short-term autocorrelation across different files/campaigns.
- Source-file checksums and per-row IDs must be preserved. New class-role decisions precede sample splits; unknown-test labels may occur only in final test.

## Dataset identity and decision

The dataset fingerprint is `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d`, SHA-256 of compact JSON containing the sorted 90 `source_sha256` strings from `data/formal_local/formal_materialization_manifest.json`. The source archives remain read-only. This audit uses no test labels or scores to choose class combinations, split folds, models or thresholds.

The primary study can run as a predeclared **exploratory campaign-holdout** comparison. It cannot earn `PASS` for a claim of fully independent physical-motor testing until new verified motor/session and raw-window provenance, plus at least two independent test acquisition groups per configuration, are available.
