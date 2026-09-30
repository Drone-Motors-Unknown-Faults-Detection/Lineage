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

## 2026-09-30 — Stage 3 grouped sample splitting

- Stage 2 commit `e0a3eab983568c7e0de37318cea86048d01c9584` was pushed and verified remotely.
- Added three whole-campaign folds, explicit exclusions, read-only catalog indexing and checksum-checked positional feature loading.
- Initial fixture test failed because different fixture labels contained byte-identical CSVs; the duplicate fingerprint guard correctly rejected them. Fixed the fixture to contain distinct source values. Retry reason: invalid fixture, not relaxed validation.
- `venv\Scripts\python.exe -m unittest tests.test_fault_type_sample_split tests.test_fault_type_features -q` → 9 passed.
- Ran the sample-split CLI on all 90 formal files with known labels `1screws 2screws 3screws 3_14screws 4screws` and remaining four faulty labels unknown; `manifests/campaign_example/campaign_split_summary.json` records all three folds and counts. Dataset fingerprint matched the audit.

## 2026-09-30 — Stage 4 manifests and validator

- Stage 3 commit `819c9d06b8cefa13d7b084838ea33b784536195e` was pushed and verified.
- On resume, 282 tracked files were absent (historical logs/output/docs/scripts/package initializers); unrelated deletions are not staged or restored. Their cause is not established. The D-drive counterpart worktree was not present.
- The ignored venv also lacked Python sources and pip RECORD metadata. Initial tests failed on SciPy imports, not algorithm assertions. Same-version cached wheel reinstall first failed on missing six RECORD, then succeeded with `pip --ignore-installed --no-deps`; cloudpickle/colorama/narwhals were repaired in a follow-up. No raw data changed.
- `venv\Scripts\python.exe -m unittest tests.test_fault_type_validator tests.test_fault_type_manifest tests.test_fault_type_sample_split tests.test_fault_type_features -q`: stage-specific checks pass (19 tests; metrics are a later stage).
- Actual CLI: `venv\Scripts\python.exe -m core.fault_type_manifest --data-root data/formal_local --registry reports/fault_type_openset/manifests/class_roles_v1_6bdff74614f1d781.json --git-commit 819c9d06b8cefa13d7b084838ea33b784536195e`.
- Three gzip manifests were read back and checksum verified. Compact report: `output/fault_type_manifest/2026-09-30-18-43-30/validation_index.json`; all three are INCOMPLETE (`TEST_INSUFFICIENT_GROUPS`), not INVALID. Complete manifests remain local large artifacts; index and log are committed.
- Additional metrics check found an incorrect synthetic FPR95 expectation (two negatives precede the fourth positive, so FPR95=1.0); correction belongs to stage 6. No measured formal score has yet been used to select combinations or methods.

## 2026-09-30 — Stage 5 factory-based protocols

- Stage 4 commit `7a8507bd07097b24528316c6d0cf437f39b384f4` pushed and remote SHA verified.
- Added fixed train-only balanced logistic classifier, exact fit-input audit, both factory detectors, probability-bearing per-sample artifacts and A/B separation. Unknown validation is diagnostic, not threshold fitting. Mahalanobis default and binary/PolarMap remain unchanged.
- `venv\Scripts\python.exe -m unittest tests.test_fault_type_runner tests.test_openset -q` → 16 passed. Actual scaler and detector fit calls were checked against train/calibration-only matrices.
- Broader test before stage-6 fixture correction: 127 tests, one failure (the documented FPR95 expected-value error); no other regressions. Invalid CLI usage is intentionally tested and prints argparse error while passing.

## 2026-09-30 — Stage 6 metrics and aggregation

- Stage 5 commit `3f49a40a40e9ceef7d1f9a553a9465f2c52f5f66` pushed and SHA verified.
- Metrics include known and fault-only classification, unknown-positive ranking/rejection, healthy safety, per-unknown attraction, equal-run versus pooled summaries and same-manifest paired deltas. Intervals explicitly describe correlated configuration/campaign runs, not motor-population inference. N=9 unavailable unknown metrics and protocol mixing are checked.
- Corrected FPR95 fixture expectation from .5 to 1.0 by direct ROC ordering; no algorithm or threshold was changed. Fixed a real reporting issue: faulty samples predicted healthy must remain in the fault-only confusion matrix.
- `venv\Scripts\python.exe -m unittest tests.test_fault_type_metrics -q` → 7 passed.
- `venv\Scripts\python.exe -m unittest discover -s tests -q` → 129 passed, exit 0 (including original binary and PolarMap tests). No formal experiment score has yet been inspected.
