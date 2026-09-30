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

## 2026-09-30 — N-sweep complete; review-service interruption resolved

- Protocol B committed locally as `9532e6d76911af9eb6bba8ecfb60dde01671cd9d`. Its first push was NOT executed: automatic approval review failed due account usage limit and advised trying after 11:37 PM. This was a review-service failure, not a Git credential failure or safety rejection. No bypass was attempted.
- On the later user continuation after that indicated reset time, the SAME escalated review flow succeeded; push and ls-remote verified `9532e6d76911af9eb6bba8ecfb60dde01671cd9d` remotely.
- N-sweep finished at 20:12:22, exit 0: 1014 completed, 0 failed/pending; 507 matched pairs, unmatched=0, ignored=0. All strata remain INCOMPLETE. Combined with N=5, A has 1770 detector runs/885 pairs; B remains separate at 720/360. Total 2490 completed, zero failures.
- Combined report command: `python -m experiments.fault_type_report --matrix output/fault_type_matrix/2026-09-30-19-05-42 --matrix output/fault_type_matrix/2026-09-30-19-37-27 --matrix output/fault_type_matrix/2026-09-30-19-37-39` → exit 0 at 23:51:08; output `output/fault_type_report/2026-09-30-23-49-34`. Plot visually checked; A/B and N=9 unavailable values remain separate.
- Sweep archive command: `python -m experiments.fault_type_archive --output-root output/fault_type_matrix/2026-09-30-19-37-27 --destination D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-09-30` → exit 0 at 23:50:50. Index `output/fault_type_archive/2026-09-30-23-49-43/archive_index.json`: 4,691,045,317 bytes, 3570 files, CRC PASS, SHA `64ad06dac8625e838a6df251b247d7bc295837f602a3a7f9c2d98ceeea36377b`.
- `n_sweep_results.md` records the actual trend and why varying class counts/configurations/fit distributions prevents a simple causal interpretation. No settings/thresholds/default detector were changed from these results.

## 2026-09-30 — Final evidence and teacher-recommendation audit

- N-sweep results commit `686cb38a1392e3da536a6e45e5e2d291014cd516` pushed and remote SHA verified.
- Full suite rerun after all matrices/reports: 137 passed, exit 0 at 23:54:18; original binary/PolarMap checks pass. No formal run failed and no post-test model adaptation was made.
- Combined report archived using `python -m experiments.fault_type_archive --output-root output/fault_type_report/2026-09-30-23-49-34 --destination D:\schoolshit\專題\src\lineage_fault_type_artifacts\2026-09-30`: exit 0, 2,176,346 bytes, 10 files, CRC PASS, SHA `414532b03e8dbc3a7e13b22daef2934c5771bdfbddcdcfb35f4cae80108df047`. Index `output/fault_type_archive/2026-09-30-23-53-04/archive_index.json`.
- Final teacher audit distinguishes completed engineering/2490-run evaluation from unresolved reliable classification/rejection and external independent-data provenance. Full 13-section report, artifact full paths, reproduction commands and explicit limitations are saved. Existing 282 historical tracked deletions remain untouched and unstaged.
- Tracking issue search returned no existing open matching issue; its evidence body is saved for creation after the final report is pushed, as required by AGENT.md.

## 2026-10-01 — Final push and research tracking handoff

- Final report/tables/paths commit `79ff29200551627fb3a312c8deddb7f7a050b7b9` pushed to the existing research branch and exact remote SHA verified by ls-remote. No main merge or history rewrite.
- Created https://github.com/Drone-Motors-Unknown-Faults-Detection/Lineage/issues/9 using the saved evidence body, satisfying AGENT.md's issue/PR requirement. It tracks unresolved independent-data provenance, cross-stage feature semantics, efficacy and untested Python3.10 compatibility, not a claim that those items are fixed.
- Final local status review: no modified tracked implementation files; existing 282 historical deletions remain unstaged. Untracked per-run prediction/manifests are intentionally not in Git and are retained in verified D-drive archives. Raw source files were not modified or uploaded.
- Teacher recommendations are implemented and evaluated; trustworthy fault-type/generalization conclusions remain unsupported by the observed weak baseline and INCOMPLETE datasets. No additional threshold/model tuning is authorized or implied by reporting these limitations.

## 2026-10-01 — Provenance follow-up, Stage 1

- User explicitly authorized provenance/feature/known-validation work and staged commit+push, without rerunning2490 experiments.
- Baseline full suite 137 passed at00:57; new evidence tests3 passed. Read pinned Git object afcfcc4 (lines218,230–231), verified90CSV path mappings/28910 rows using existing catalog.
- Added non-mutating motor evidence overlay output/fault_type_provenance/2026-10-01-00-59-11/motor_evidence.json. Missing serials/hours remain null; frozen manifests/results unchanged.
- Stage1 commit0dcd67b03d3d57016ed8038eda31fd7b8aa46e54 pushed; ls-remote returned exact SHA. Branch unchanged;282 deletions not staged.

## 2026-10-01 — Source reconstruction, Stage 2

- Three semantic row-mapping tests passed. Read-only CLI source audit started01:02:35, completed01:07:56, exit0; output/fault_type_source_audit/2026-10-01-01-02-35/source_audit.json.
- Recovered19053 unique clean-to-unclean processed-feature row mappings for all60 Stage1/3 CSVs. These are processed-window ordinals, NOT original contiguous DAQ intervals.
- Source/archive inventory and AST code evidence saved; scripts NEVER executed. Original acquisition boundaries and deletion masks remain unknown. Source/data bytes not changed.

- Stage2 commit a82b833fa0692e583e3dd57a708e9131ec756c85 pushed; exact remote SHA verified. Two roots' three archive SHAs identical;450 channel CSV members/root are copies, not900 recordings. Original DAQ candidates0 under bounded extension/header inventory, not proof files do not exist elsewhere.

## 2026-10-01 — Cross-stage computational contract, Stage 3

-3 feature-contract tests passed (signed statistical quirks, FFT amplitude/axis, nominal-vs-measured constants).
- CLI feature audit01:04:50–01:14:09 exit0; output/fault_type_feature_audit/2026-10-01-01-04-50/feature_audit.json. Checks all30 Stage2 conditions and predeclared6 healthy Stage1/3 RPM probes using existing extracted files, independent numerical reference, fileSHAs.
- Stage2's9857 clean rows uniquely matched recomputed105-D processed windows. Together with Stage1/3 mappings this recovers all28910 processed ordinals, zero original DAQ intervals. This is not900 independent recordings or a raw-time metadata recovery.
- Historical statistics/FFT kept fixed: redundant clearance/impulse, signed max crest, RMS/MSA and std/variance redundancy, integer133/183Hz bases, nominal10kHz, Y/Z historical FFTnX text labels. Physical axes/units/calibration/load remain unknown.

- Stage3 commit27927a28ed80c06e65aac272519985e19b000bb3 pushed and exact remote SHA verified. All36 probes' clean rows match recomputed105D; all30 Stage2 adapter clean reproductions true. Nine scripts have one statistical-function AST and one FFT-function AST. Actual unequal channel counts occur T1/11000 healthy596vs600, T1/6000 healthy595vs600, T2/6000/7screws599vs600; matching feature values does NOT prove synchronized physical windows.

## 2026-10-01 — Exposure ledger and final-test guard, Stage 4

- Checked three saved matrix plan checksums/completed status (756+1014+720); recomputed metrics from one actual saved prediction run per matrix, allPASS. No retraining of baseline2490 runs.
- Three completed N9 frozen test manifests cover all28910 unique catalog IDs. Saved ledger output/fault_type_exposure/2026-10-01-01-10-40/exposure_ledger.json.gz checksum4cb30f0a8220891b169ea32fce1fbdc24650d27f64ed8730755ee3dc95d38bdc.
- Added read-only ingest/data-version verification and final eligibility gate: exposed bytes/numeric-row copies, same acquisition, overlapping windows, new-session-vs-new-motor claims, unlocked configs, coverage, and sealed histories.12 new semantic tests passed. No fresh independent final test found in the inspected sources.
- acquisition_contract.md gives minimum real acquisition facts and executable CLI. No hardware collection performed or external messages sent. Eligibility is conditional on attested physical provenance, not automatic reliabilityPASS.

- Stage4 commit616aa9b441818626f38fa0e9fa3ead5ab1e4158c pushed, exact remote SHA verified. Ledger gzip ignored by existing*.gz rule, retained locally and will be included in verified D-drive follow-up backup; Git index binds its byteSHA.

## 2026-10-01 — Known-validation preregistration, Stage 5a

- Prepared exactly3 candidates: unchanged balanced logistic C1, RBF SVM C1/gamma scale/balanced, ExtraTrees200/depth12/minleaf5/sqrt/balanced. Train-only RobustScaler; no PCA/feature selection/unknown selection.
- Original first126 registry N5 class combination, all3 original folds chosen by prior order, NOT performance. Scores use equal-fold known-validation macro-F1, balanced accuracy secondary, simpler-model ties. Historical exposure/sharedval-cal limitations explicit.
- Initial prepare-only01:17:10 failed KeyError class_split_id: role registry field is split_id, while manifest field is class_split_id. Fixed adapter field reference, no model ran and no data/results altered. Successful prepare-only01:18:13 exit0 produced candidate_registry.json before actual training.
-4 new selection tests passed: pool spy forbids test loading, unknown validation rejected beforefit, deterministic scores, tie rule, modified candidate set rejected. Training artifacts use joblib generated locally; do not load arbitrary untrusted pickle/joblib files.

- Stage5a d0daccdf3a31d44f3313719a998172c74abd470b pushed and remote verified BEFORE actual model training.
- Training CLI01:19:31–01:19:37 exit0: all9 candidate-fold fits completed. SelectedExtraTrees by known-validation macro-F1 .236452 vs linear .188776 / SVM .156778; balanced accuracy .319710 vs .225878/.219895. No test/unknown features loaded during selection.
- Locked config checksumc39437ab92b74ea31c94a220bfd2e3cbc83a91f3670c1a7246b45dc81493b5c5; output/fault_type_model_selection/2026-10-01-01-19-31 contains reports/lock/3training joblibs/known-only calibration and fit-ID audit. All source data read-only; historical test exposure/sharedvalcal limitations persist. Selectedmodel is research-only, not deployed as new default.

- Stage5b ba7e7283799201ea3d5c38a0d0e8c2dc3709485d pushed and exact remote SHA verified BEFORE oldtest reanalysis.

## 2026-10-01 — Controlled exposed-test evaluation, Stage 6

- CLI fault_type_controlled_eval01:23:25–01:23:36 exit0:12/12 completed,0failed, baseline/ExtraTrees x3originalfolds x2factory detectors. All115640 predictions are repeated use of28910 original test samples, not new independent observations. Explicit --exploratory required; lock/artifact SHA checked before loading.
- First fixed N5 combination ONLY: known accuracy .296306linear→.307605ExtraTrees (+1.1299pp), BA .297372→.311033 (+1.3661pp), macro-F1 .262007→.252613 (-.009394). Twofolds worsen, one improves; no production model/default update. Do not compare this one combination to old126-combination25.744% average.
- Unchanged detector spaces: both classifiers have same unknown metrics. Maha/kNN AUROC .531118/.504657, recall .150702/.044939; scores not improved by classifier replacement. Per-class confusion/unknown attraction and motor/RPM/config strata retained; paired differences verified.
- Initial followup report01:25:55 failed native metric-key adapter (auroc vs auroc_unknown_positive); fixed without rerunning fits/evaluation or changing data.2 adapter/pair tests added. Successful01:26:39–01:26:42 verifies all12 saved predictionSHA/count/IDs/actualmetrics; output/fault_type_followup_report/2026-10-01-01-26-39.
- Hardened final guard: same raw recording cannot be relabeled as multiple independent session/motor/run owners; new tests added. Future freshAPI requires durable exposure receipt BEFORE prediction, failure still exposed. Seal-manifest CLI creates outputcopy only. Full previous frozen artifacts untouched; new split descriptions now distinguish documented identity from unverified raw provenance.
- Final full suite01:34:31 first encountered stale assertion demanding the withdrawn "not verified physical motor" wording. Updated semantic assertion to documented motor IDs plus unverified raw provenance, retaining INCOMPLETE/group-count/calibration checks. No validation threshold weakened.170 tests passed on01:35:02–01:35:07 rerun.
- Final formalSHA check90/90 matches.8 backups at D:/schoolshit/專題/src/lineage_fault_type_artifacts/2026-10-01 verified wholeSHA/CRC AND all internal member bytes/SHA. Original files kept, rawdata not uploaded. Acceptance evidence saved; final commit bookkeeping follows.
