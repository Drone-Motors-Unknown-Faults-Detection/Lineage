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

## 2026-09-30 — Stage 7 end-to-end matrix verification

- Stage 6 commit `3bb4a7ccef254a120edd00d92132108a669a9fd9` pushed and verified.
- Added immutable run plans, per-run attempt/status/reason records, exact-artifact resume verification, original complete manifests, paired test-ID digests and protocol/N/detector-stratified aggregation. Smoke can cap each source before fitting; normal research matrices cannot silently cap data.
- Matrix synthetic tests: 4 passed; both detectors execute end to end. Resume does not refit completed runs, corrupted prediction artifacts fail fast, and intentional failed runs remain in the status/index.
- Feature ablation is explicitly skipped because current Lineage has only the formal 105-D representation, not a usable neural embedding.

## 2026-09-30 — Stage 8 smoke, runtime and primary registration

- Stage 7 commit `f2f09b44cbe8825676fca2383046b5d85ae1b71b` pushed and remote SHA verified. Full suite: 133 passed.
- Real-data smoke: `python -m experiments.fault_type_matrix --registry reports/fault_type_openset/manifests/class_roles_v1_6bdff74614f1d781.json --n 5 --pilot --sample-cap-per-source 10` → 2 completed, 0 failed, 300 test samples per method; output `output/fault_type_matrix/2026-09-30-19-03-28`.
- Full-data pilot: same command without the sample cap → 2 completed, 0 failed; output `output/fault_type_matrix/2026-09-30-19-03-39`. Timing/bytes only were inspected for planning; no score-based method/combination selection. 3.983s matrix execution, 9,854,684 artifact bytes.
- Generated and pre-registered full126 Protocol A N=5 registry `40cb4312c2e923426407035fc3c0696f8d51cdd7190a2f1ee123c6aae3f1d8d6` before primary evaluation. Runtime decision and separate balanced30 Protocol B budget in `runtime_plan.md`.
- Preregistration commit `dd7f679ec498d9836e7f3c2aeb355322776c158b` pushed and verified. Full N=5 launched with `python -m experiments.fault_type_matrix --registry reports/fault_type_openset/manifests/class_roles_v1_40cb4312c2e92342.json --n 5`; model/manifest commit is dd7f679. Output `output/fault_type_matrix/2026-09-30-19-05-42`. Results remain INCOMPLETE exploratory; no early score-based selection.

## 2026-09-30 — Reporting and artifact preservation support

- Added protocol/N/detector tables and paired analyses, descriptive-interval sweep plot, hardest-configuration summaries and checksum-verified primary condition analysis. Added verified ZIP64 preservation for completed outputs because the active worktree is temporary. No source files are removed or restored.
- Resume verification now recomputes metrics from actual predictions and checks ground-truth groups and rejection decisions; no fitting/threshold logic changed. The already running N=5 process retains its original dd7f679 code and plan; later matrices record their actual new code commit.
- `method_sources.md` cites Ledoit/Wolf (2004, J. Multivariate Analysis), Sun/Ming/Zhu/Li (2022, ICML/PMLR) and the actual scikit-learn classifier implementation. Our engineered-feature class-wise k-NN variant is not claimed to reproduce deep-kNN paper results.
- Reporting fixture validates table/pair/plot creation and rejects duplicated strata; archive fixture validates exact content hashes, source preservation and no-overwrite behavior.
- `venv\Scripts\python.exe -m unittest discover -s tests -q` → 135 passed, exit 0. Matplotlib cache was explicitly routed to writable `output/fault_type_mplcache`; single-class confusion warnings in synthetic fixtures are non-failing. N=5 still running at this support commit, without score-based adaptation.
- Reporting/archive support commit `084e209aecb9a6e4002d793f502c9d69d69ae380` pushed and verified.

## 2026-09-30 — Pooled task-count metadata guard

- Code review while primary aggregates were being built found that pooling different known-class combinations can have a nine-label union even when every task has N=5. The old pooled descriptor inferred N from that union. Numerical metrics are unaffected.
- Added explicit per-run task N versus union size, a regression test and a metadata-only migration command that asserts all numerical fields are unchanged and records before/after hashes. Original predictions, training settings, class combinations and immutable manifests are not changed.
- Archiver now also requires a finished matrix aggregation index, rather than relying solely on completed per-run statuses.
- Targeted metric tests: 8 passed. Primary 756 detector runs finished without failures; both-method aggregation is still in progress at this guard commit.
- Full suite after this guard: 136 passed. Migration is also covered in the matrix resume fixture and preserves known-class numerical metrics.

## 2026-09-30 — Stage 8 primary N=5 completed

- Guard commit `1cfdcb63e513a129f86f1a4054fd49108c53a775` pushed and verified.
- Primary matrix finished 19:31:50: 756/756 completed, 0 failed; 126 combinations × 3 folds × 2 methods. Both methods have 3,642,660 predictions and 378 verified same-manifest pairs. Formal data fingerprint unchanged. All manifests are INCOMPLETE.
- Descriptive label-union metadata migrated with `python -m experiments.fault_type_matrix --resume output/fault_type_matrix/2026-09-30-19-05-42 --annotate-pooled-task-count-only`; no numerical metric, prediction or immutable manifest changed. Before/after aggregate hashes saved.
- `python -m experiments.fault_type_report --matrix output/fault_type_matrix/2026-09-30-19-05-42` completed; output `output/fault_type_report/2026-09-30-19-32-34`.
- `python -m experiments.fault_type_archive --output-root output/fault_type_matrix/2026-09-30-19-05-42 --destination D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-09-30` completed. D-drive ZIP64: 3,712,231,384 bytes / 2654 files, CRC PASS, SHA-256 `25fc12c6982143f72fdf8c5534837dcd4767ba98ab106af39bdbb10eacb3d540`.
- Actual findings: known accuracy .257437 both; unknown AUROC .527746 Mahalanobis / .524480 k-NN; unknown recall .149949 / .079434; healthy FPR .022593 / .012681. No reliable unseen-configuration rejection claim. Details/limitations in `primary_results.md`; no post-test threshold/model/seed changes.

## 2026-09-30 — Remaining predeclared matrices and checkpoint hardening

- Primary results commit `3d8b9f02269ad1eb030f45c34e3a20612b1d7f77` pushed and verified.
- N-sweep launched: `python -m experiments.fault_type_matrix --registry reports/fault_type_openset/manifests/class_roles_v1_40cb4312c2e92342.json --n 1 2 3 4 6 7 8 9`; output `output/fault_type_matrix/2026-09-30-19-37-27`; declared 1014 runs.
- Separate Protocol B launched: `python -m experiments.fault_type_matrix --registry reports/fault_type_openset/manifests/class_roles_v1_6bdff74614f1d781.json --n 5 --protocol B`; output `output/fault_type_matrix/2026-09-30-19-37-39`; declared 720 runs (30 combinations ×4 distinct unknown-validation rotations ×3 folds ×2 methods).
- Independent output directories allow the two remaining studies to execute concurrently. Both execute the fixed 3d8b9f0 code/config; no adaptation to primary scores.
- Hardened future checkpoint writes using flush/fsync and atomic replacement. A simulated interrupted write preserves the previous valid JSON checkpoint. This does not hot-patch the already-running processes or change fitting, prediction or thresholds.
- Targeted matrix tests after checkpoint hardening: 5 passed. N=1 fault-only one-label confusion-matrix warnings are expected/non-failing; full matrices retain all declared label axes and errors.
- Checkpoint hardening commit `a495c18d36eefa5c8aacd4d03c1bcc1c31a25992` pushed and remote SHA verified.
- Full suite rerun at 19:48:20 with `MPLCONFIGDIR=output/fault_type_mplcache`: 137 passed, exit 0. Existing binary and PolarMap tests pass; no model/test-based changes were made.
- Reproduction guide now explicitly uses the pre-registered full126 registry for Protocol A, balanced30/four-rotation registry for Protocol B, and a writable Matplotlib cache. README separates this campaign-held-out study from historical cold-start random-split numbers and documents the observed weak baseline rather than claiming an improvement.

## 2026-09-30 — Protocol B complete and preserved

- Documentation clarification commit `2104fec172e1b71d4047ee201cd080b5164e450d` pushed and remote SHA verified.
- Protocol B matrix `2026-09-30-19-37-39` finished at 20:03:50, exit 0: 720 completed, 0 failed/pending, 360 matched detector pairs, unmatched=0. Every manifest is INCOMPLETE; no score-based tuning or retries.
- Each method has 3,121,529 repeated-source predictions. Known accuracy .252623; unknown AUROC .528838 Mahalanobis / .522188 k-NN; unknown recall .145357 / .073827; healthy FPR .027208 / .010274. Separate report `protocol_b_results.md` explains why A/B means are not a tuning improvement.
- Actual archive command: `python -m experiments.fault_type_archive --output-root output/fault_type_matrix/2026-09-30-19-37-39 --destination D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-09-30` → exit 0 at 20:05:49. Index `output/fault_type_archive/2026-09-30-20-05-02/archive_index.json` records 3,375,246,908 bytes, 2527 files, CRC PASS and SHA `24ec1e80346dcbc2d8244dfaa9c0cc2188788ae8eed0530d2fde3671b1e38f8f`.
- Read-only SHA-256 recheck of all 90 formal CSVs against formal_materialization_manifest: 90 checked, zero mismatches. No source data changed. Latest full test evidence remains 137 passed; B counts/strata/pairing were additionally checked before this results commit.
