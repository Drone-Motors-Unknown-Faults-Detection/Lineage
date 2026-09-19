# Local motor research raw-data audit — P1 inventory

## Scope and safety

This phase performed a read-only inventory of the user-provided directory:

```text
D:\schoolshit\fcu\專題\馬達研究
```

No file in that directory was renamed, moved, overwritten, deleted, extracted into, or modified. Archive contents were inspected through read-only ZIP streams. The inventory and helper scripts are stored in this repository; no raw data, cache, virtual environment, or generated feature file is committed.

## P1 inventory result

| Item | Result |
|---|---:|
| Files | 154 |
| Directories | 2 |
| Total size | 4,937,135,027 bytes (4.598 GiB) |
| Outer archives | 3 |
| Archive inventory rows | 796 |
| Unreadable files | 0 |
| Git repository in raw root | No |
| Reparse/symlink evidence | None in the file inventory |

File types:

| Extension | Count | Total bytes |
|---|---:|---:|
| `.zip` | 3 | 4,919,052,686 |
| `.ipynb` | 127 | 17,895,186 |
| `.py` | 24 | 187,155 |

## Archive structure discovered

The three outer archives are `階段1.zip`, `階段2.zip`, and `階段3.zip`. Their nested archive structure is:

```text
階段1.zip
├── csv.zip       -> T1/6000rpm, T1/8000rpm, T1/11000rpm raw CSV archives
├── myfeature.zip -> T1 105-feature CSVs
└── model.zip     -> Keras checkpoints

階段2.zip
└── csv.zip       -> T2/6000rpm, T2/8000rpm, T2/11000rpm raw CSV archives

階段3.zip
├── csv.zip       -> T3/6000rpm, T3/8000rpm, T3/11000rpm raw CSV archives
├── myfeature.zip -> T3 105-feature CSVs
└── model.zip     -> Keras checkpoints
```

Each of the nine condition archives contains 50 raw CSV files: ten screw configurations (`1screws`, `2screws`, `3screws`, `3_14screws`, `4screws`, `4_146screws`, `5screws`, `6screws`, `7screws`, `8screws`) × five channels (`Acceleration_X`, `Acceleration_Y`, `Acceleration_Z`, `Current`, `Delta_T`). This is an archive-level finding; row-level validation is P2.

The Stage 1 and Stage 3 `myfeature.zip` archives contain 30 `*_Group_feature_data_clean.csv` files each, covering all three RPM values and all ten screw configurations for T1 and T3. Stage 2 currently has raw CSV archives but no `myfeature.zip`; this is the main completeness issue to validate before connecting Lineage's 105-feature loader.

The raw directory also contains preprocessing notebooks and Python scripts, including feature-extraction code that documents 10,000-point windows, 10 kHz sampling, FFT features, and IQR filtering. Those scripts are evidence for P2/P3 only; they are not executed in the raw directory.

## Reproducible artifacts

- [file inventory](file_inventory.csv): absolute/relative path, size, timestamps, type, archive flag, reparse/symlink flags, and candidate category.
- [directory summary](directory_summary.csv): directory file counts and sizes.
- [extension summary](extension_summary.csv): extension counts and sizes.
- [archive inventory](archive_inventory.csv): outer, nested, and condition-archive entries with compressed/uncompressed sizes.
- [P1 progress](progress.json): machine-readable counts and safety status.
- [inventory script](inventory_local_raw.ps1): repeatable metadata-only inventory.
- [nested archive inspector](inspect_nested_archives.ps1): repeatable read-only nested ZIP listing.

P1 does not yet claim that all nine conditions are ready for exp6. P2 must parse representative raw and feature files, validate columns/shapes/row counts/labels, and determine how to produce the missing T2 feature layer without modifying the raw source.

## P2 content validation

P2 streamed every raw CSV in the nine condition archives and every clean feature CSV present in `myfeature.zip`:

- 450/450 raw CSV files readable; every condition has 50 files, 10 classes, and 5 channels.
- Every raw CSV has exactly 10,000 data rows and zero malformed rows.
- Raw files have file-specific column widths between 568 and 600; this is the waveform/window representation and is not the Lineage 105-feature schema.
- 60/60 present clean feature CSV files readable; every one has 105 columns and zero non-numeric body fields.
- T1 and T3 have all 30 clean feature files each; T2 has zero clean feature files even though all 150 raw CSV files are present.
- Label semantics come from the screw-configuration directory: `8screws` is healthy known, `1screws`–`4screws` are known faults, and `5screws`, `6screws`, `7screws`, `3_14screws`, `4_146screws` are unknown faults according to the existing project contract.
- No pickle, Keras checkpoint, or other unsafe serialized object was loaded during validation. The Keras archives remain checkpoint candidates only.

The P2 machine-readable reports are [raw_validation.csv](raw_validation.csv), [feature_validation.csv](feature_validation.csv), [condition_summary.csv](condition_summary.csv), [candidate_inventory.csv](candidate_inventory.csv), and [p2_progress.json](p2_progress.json). The raw source remained unchanged.

## P4 materialization

`core/formal_data.py` now connects this nested-archive source to Lineage's
`data/Step-*/myfeature` contract without embedding a developer-specific path.
Stage 1 and Stage 3 clean features are copied byte-for-byte; Stage 2 is
converted from its five-channel matrices using the documented 105-feature
pipeline and the observed feature-level 1.5-IQR clean rule. The converter
requires explicit `--source-root` and `--output-root` arguments and refuses to
write under the source root.

The complete local materialization was validated outside Git tracking:

| Check | Result |
|---|---:|
| Materialized files | 90 (30 per stage) |
| Motor × RPM conditions | 9/9 |
| Configurations per condition | 10/10 |
| Feature columns | 105 in every file |
| Non-finite / non-numeric feature rows | 0 |
| Clean rows per class file | 180–387 |
| `discover_datasets` / `load_pools` | 9 datasets, all with `8screws` |

The materialized files and `formal_materialization_manifest.json` stay under
the ignored `data/` directory; the 4.6 GiB source remains read-only.

P4 implementation and tests were pushed as commit
`2cac19f45056e382f59eaa03bb275d8499389268` on
`feat/knn-openset-comparison`.
