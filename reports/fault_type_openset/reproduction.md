# Executable reproduction guide (Windows)

Run from the Lineage worktree root, on `research-improvements-20260920`.
The read-only feature root must be `data/formal_local` with the fingerprint in
`data_audit.json`. This workflow never runs raw feature extraction or edits data.

1. Run all tests:

   ```powershell
   .\venv\Scripts\python.exe -m unittest discover -s tests -q
   ```

2. Smoke with the first predeclared N=5 combination, first campaign fold, ten
   rows from each source file, both detectors (not a primary accuracy result):

   ```powershell
   .\venv\Scripts\python.exe -m experiments.fault_type_matrix --registry reports/fault_type_openset/manifests/class_roles_v1_6bdff74614f1d781.json --n 5 --pilot --sample-cap-per-source 10
   ```

3. Measure full-size one-role/one-fold cost before choosing full N=5 enumeration;
   inspect timing/bytes only, not accuracy for combination/method selection:

   ```powershell
   .\venv\Scripts\python.exe -m experiments.fault_type_matrix --registry reports/fault_type_openset/manifests/class_roles_v1_6bdff74614f1d781.json --n 5 --pilot
   ```

4. Execute the frozen N=5 study, then the remaining sweep (N=9 separately
   stratified as closed-set; unknown-positive metrics are null). The current
   registry uses thirty balanced N=5 combinations; if timing warrants all126,
   create and commit a NEW immutable registry with `--enumerate-n5` before
   inspecting research results, and replace the registry path below.

   ```powershell
   .\venv\Scripts\python.exe -m experiments.fault_type_matrix --registry reports/fault_type_openset/manifests/class_roles_v1_6bdff74614f1d781.json --n 5
   .\venv\Scripts\python.exe -m experiments.fault_type_matrix --registry reports/fault_type_openset/manifests/class_roles_v1_6bdff74614f1d781.json --n 1 2 3 4 6 7 8 9
   .\venv\Scripts\python.exe -m experiments.fault_type_matrix --registry reports/fault_type_openset/manifests/class_roles_v1_6bdff74614f1d781.json --n 5 --protocol B
   ```

5. Each command prints a `logs/fault_type_matrix/<timestamp>.log` and
   `output/fault_type_matrix/<timestamp>/` directory. Keep the whole output
   directory: immutable run_plan, environment, original manifests, run_status,
   probability-bearing compressed predictions, fit audits, per-run summaries,
   protocol/N/detector aggregates, paired comparison and compact matrix_index.
   Resume using that exact directory; settings and checksums must match:

   ```powershell
   .\venv\Scripts\python.exe -m experiments.fault_type_matrix --resume output/fault_type_matrix/REPLACE_WITH_TIMESTAMP
   ```

   Failed runs are retained. Use `--retry-failed` only after identifying an
   environment/interruption cause, not after choosing a better seed from test.
   Algorithm/protocol changes require a new plan/version. No result is described
   as a complete independent test: current manifests are INCOMPLETE.

6. Commit only compact plans/environment/indices/summary reports and relevant
   logs, not raw data or gigabytes of predictions/manifests. Preserve large
   artifacts at their recorded absolute paths; Git does not contain their bytes.
   Check the exact staged files, commit with the Codex coauthor trailer, push
   the current branch and verify the remote SHA. Never stage unrelated deletions.

7. Once a matrix finishes, create evidence tables/plots (repeat `--matrix` for
   disjoint N/protocol strata only; never pass the same resumed matrix twice):

   ```powershell
   .\venv\Scripts\python.exe -m experiments.fault_type_report --matrix output/fault_type_matrix/REPLACE_WITH_TIMESTAMP
   ```

   The report includes SD/CI and pooled rates, protocol/N-specific paired deltas,
   per-configuration recall/attraction and N=5 RPM/campaign condition analysis.
   It labels all current data INCOMPLETE and refuses pilot matrices.

8. The active worktree lives under Windows Temp and previously had unexplained
   missing historical files. Preserve completed generated artifacts on D: using
   the verified ZIP64 archiver (it does not change/remove sources):

   ```powershell
   .\venv\Scripts\python.exe -m experiments.fault_type_archive --output-root output/fault_type_matrix/REPLACE_WITH_TIMESTAMP --destination 'D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-09-30'
   ```

   It refuses active inventories and existing archives, verifies ZIP CRC and
   archive SHA-256, and embeds a per-file SHA-256 BUNDLE_INDEX.json. Unzip to a
   new directory to recover the timestamped output tree. Internal metadata
   retains original worktree paths; consult the bundle index when reading a
   portable copy. Raw/formal source data and credentials are not archived.
