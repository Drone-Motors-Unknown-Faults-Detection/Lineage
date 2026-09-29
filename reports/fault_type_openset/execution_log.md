# Fault-configuration open-set execution log

## 2026-09-29 — Stage 0 baseline

- Repository: `Drone-Motors-Unknown-Faults-Detection/Lineage`.
- Worktree: `_lineage_compare/p1_worktree`; branch/upstream: `research-improvements-20260920` / `origin/research-improvements-20260920`.
- Starting HEAD: `de16708232bafde6b5026ae9922264eff4c3e8cf`; `git fetch origin --prune` found no divergence; worktree was clean.
- The older sibling `Lineage` worktree is on `feat/knn-openset-comparison` and has untracked `core/openset.py`; this task does not stage or edit it.
- Applicable repository guide: `AGENT.md`. Current default detector comes from `core.openset.create_openset_detector`; `core.monitor` and `core.geometry.PolarMap` remain the historical cold-start path.
- Python environment: existing ignored `venv` held packages but lacked `Scripts/python.exe`. Repaired with `C:\Python314\python.exe -m venv --upgrade venv`; `venv\Scripts\python.exe` is Python 3.14.6, NumPy 2.5.3, pandas 3.0.6, scikit-learn 1.9.1.
- Baseline command: `venv\Scripts\python.exe -m unittest discover -s tests -q` → 92 tests passed, exit 0. One test deliberately calls CLI with an invalid detector and prints argparse usage; the test itself passes.
- Formal data: `data/formal_local` is read-only and Git ignored. Stage 1 data audit will record fingerprint, labels, groups and metadata availability.
- Stage 0 status: completed. No research result changed at this stage.

Subsequent entries record commands, seed sets, data/manifest fingerprints, test and run status, commits, remote verification, and retry reasons. A failed or incomplete run stays visible.

## 2026-09-29 — Stage 1 data and label audit

- Read `data/formal_local/formal_materialization_manifest.json`, clean feature CSVs, preprocessing docs, `core.formal_data`, `core.data`, and earlier data-capability reports.
- Data identity: 90 clean CSVs, 28,910 finite 105-D windows; fingerprint `c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d` (sorted source SHA-256 list in compact JSON).
- Validation command: `venv\Scripts\python.exe -c "...load data_audit.json and materialization manifest; recompute fingerprint, row and file counts..."` → `fingerprint_matches True counts_match True files_match True`.
- Physical finding: nine faulty labels are screw-loosening count/position configurations. Physical motor IDs, sessions, raw intervals and events are missing. Campaign holdout has only three T-code groups and will need shared validation/calibration; a single held-out campaign is insufficient for strong physical-independence claims.
- Artifacts: `data_audit.md`, `data_audit.json`. Status: completed audit; strict physical-independence evidence remains incomplete.
- Audit commit/push: `6efdfd259867e624599bbd532182f73eb803ae6f` was pushed to `origin/research-improvements-20260920` and verified by `git ls-remote --heads`.
- Audit follow-up: corrected the newly assigned numeric encoding to match `core.formal_data.CONFIGS` order; strings in source CSV paths remain authoritative.

## 2026-09-29 — Stage 2 class-role splits

- Stage 0 commit `72906cda8cf092c4080de3dcae7f885e24950865` and Stage 1 audit commit `6efdfd259867e624599bbd532182f73eb803ae6f` were verified in the remote branch. Stage 1 encoding follow-up commit `58d8f234b1e937840d679b5be3e6fcaff977ad3a` was also pushed and verified.
- `venv\Scripts\python.exe -m unittest tests.test_fault_type_class_split -v` → 7 passed, 0 failed.
- Registry command: `venv\Scripts\python.exe -m core.fault_type_class_split --dataset-fingerprint c4145d6efcbf02d294e77e5d83fdab5636bba6d9a58b1707752dd34b836f0b2d --output-root reports/fault_type_openset/manifests --class-seed 42 --sample-seed 42 --sample-seed 123 --sample-seed 2026` → 199 Protocol A and 120 Protocol B roles, checksum `6bdff74614f1d7818da90e5d0ac00c69746c9f98fa60e8afc56184f310d4f106`.
- N=5 initially pre-registers 30 balanced combinations; full 126 is supported by a separate immutable registry after a pre-test runtime estimate. No test score was used for this choice.
