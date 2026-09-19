# P3 — Formal raw source mapped to the Lineage contract

## Source identity

The confirmed local source is the user-provided directory:

```text
D:\schoolshit\fcu\專題\馬達研究
```

The source contains three outer ZIP archives. Their SHA-256 fingerprints are recorded in [outer_archive_fingerprint.csv](outer_archive_fingerprint.csv) and the complete source manifest is [formal_source_manifest.json](formal_source_manifest.json). The raw directory was not modified.

## Contract comparison

| Lineage requirement | Evidence in local source | Status | Required conversion or guard |
|---|---|---|---|
| Data root | `階段1.zip`, `階段2.zip`, `階段3.zip` under the user root | confirmed | Add a configurable local source/archive root; never hard-code this personal path in Python |
| Nine conditions | `csv/T1`, `csv/T2`, `csv/T3` × `6000rpm`, `8000rpm`, `11000rpm` | complete | Manifest-driven condition discovery |
| Raw files | 50 CSV files per condition = 10 configurations × 5 channels | complete | Read-only nested ZIP stream or extract to configured processed cache |
| Raw rows | Every one of 450 raw CSVs has 10,000 data rows | complete | Treat each row as a 10,000-point window; validate before conversion |
| Sampling rate | preprocessing scripts state `Fs = 10000` | documented | Store 10 kHz in manifest; do not infer from filename |
| Raw channels | `Acceleration_X`, `Acceleration_Y`, `Acceleration_Z`, `Current`, `Delta_T` (T2/T3 use `X/Y/Z` filename aliases) | complete | Normalize filename aliases to the five canonical channels |
| Labels | Directory names: `8screws`, `1screws`–`8screws`, `3_14screws`, `4_146screws` | complete | Label comes from path, not test data or a hidden CSV column |
| Known/unknown | `8screws` healthy known; `1screws`–`4screws` known faults; `5screws`, `6screws`, `7screws`, `3_14screws`, `4_146screws` unknown faults | confirmed from existing contract/docs | Save mapping with every run |
| Lineage input format | `data/Step-*/myfeature/{Motor}/{RPM}/{Screws}/*_Group_feature_data_clean.csv`, 105 numeric columns | partial | T1/T3 clean features present; T2 conversion required |
| Existing clean features | 60 files: T1/T3, 3 RPM × 10 classes each; all 105 columns and numeric | confirmed | Use only after fingerprinted extraction to processed root |
| T2 clean features | No `myfeature.zip`; all 150 raw CSVs present | missing | Reproduce the documented 105-feature extraction into ignored processed cache |
| Split | Lineage `make_split`: train/calibration/holdout = 60/20/20 per configuration | code confirmed | Persist indices/seed; holdout never enters fitting or calibration |
| Normalization | Lineage `RobustScaler` fit on known training rows | code confirmed | Fit only on train; transform calibration/holdout/test |
| Threshold | Detector calibration quantile from known calibration only; score > 1 = unknown | code confirmed | Never use unknown/test labels for threshold |
| Checkpoint | `.keras` model archives are present but not required by the current feature loader | candidate only | Do not load or submit checkpoints as data |

## Formal-source decision

The local directory is the **formal raw source candidate** because all nine conditions have the expected raw channel coverage, row count, and class directory structure. It is not directly loadable by the current Lineage loader because the source is nested ZIP/raw-waveform format. The source is therefore classified as:

- `A_FORMAL_RAW`: 450 raw CSV files, confidence High.
- `B_FORMAL_PROCESSED`: 60 existing 105-dimensional clean feature CSV files for T1/T3, confidence High.
- T2 105-dimensional features: missing, not filled with synthetic or debug data.

The raw and processed inventories contain no duplicate condition, no missing raw class/channel in the nine-condition matrix, and no malformed raw rows. A leakage audit cannot be declared complete until the T2 conversion and Lineage manifest/split implementation are in place; row indices must remain disjoint across train, calibration, and holdout.

## P4 implementation boundary

The next implementation phase will:

1. Add a manifest-driven, configurable data-root/source adapter to Lineage.
2. Add a safe conversion script that reads raw nested archives and writes only to a configured ignored processed root.
3. Reproduce the documented feature extraction (10 kHz, 10,000-point windows, 15 statistical features per channel plus 10 FFT features for each vibration axis) for T2, then validate its 30 clean files against the 105-column contract.
4. Record source archive SHA-256, conversion configuration, and generated feature fingerprints in run metadata.
5. Refuse to fall back to synthetic data when the source or manifest is missing.

No Open Set algorithm or exp6 code is changed in this P3 mapping phase.
