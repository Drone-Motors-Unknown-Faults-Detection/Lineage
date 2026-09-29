# Pre-registered class roles

`core.fault_type_class_split` decides class roles before any sample or feature is read for a split. The fixed universe is `8screws` healthy and nine screw-loosening configuration labels from `core.formal_data.CONFIGS`. Protocol A holds every faulty label outside the known set for final test only. Protocol B rotates one of those held-out labels into unknown validation, leaving distinct unknown-test labels; it is a secondary protocol. N=9 has no unknown positive and is closed-set only.

The initial immutable registry is `manifests/class_roles_v1_6bdff74614f1d781.json`, checksum `6bdff74614f1d7818da90e5d0ac00c69746c9f98fa60e8afc56184f310d4f106`. It uses dataset fingerprint `c4145d6e...`, class-combination seed 42 and separate sample-fold seeds 42, 123 and 2026. Three predeclared folds rotate the T1/T2/T3 campaign roles; the same fold assignment will be paired across detectors.

For N=1 and N=8 (nine combinations) and N=9 (one combination), all possibilities are registered. N=2 through N=7 each have 30 distinct, deterministic balanced choices. Each faulty label occurs as known either equally often or with frequency differing by only one across the selected combinations. Protocol A contains 199 role records in total, including 30 N=5 choices. The secondary Protocol B has 120 records: 30 N=5 combinations × four rotations of unknown-validation label.

`--enumerate-n5` supports all 126 combinations under a new registry checksum. The Stage 8 smoke runtime estimate will determine whether the full enumeration is feasible before any official test scores are inspected. If the mode changes, the existing registry stays immutable and a newly named registry is committed before formal evaluation. No role choice depends on a test result.

Recreate the initial registry:

```powershell
venv\Scripts\python.exe -m core.fault_type_class_split --dataset-fingerprint c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d --output-root reports/fault_type_openset/manifests --class-seed 42 --sample-seed 42 --sample-seed 123 --sample-seed 2026
```
