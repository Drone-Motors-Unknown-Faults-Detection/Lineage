# Frozen manifests and completeness rules

> 2026-10-01: pinned documentation identifies three physical motor individuals.
> Existing frozen manifests/validator thresholds remain unchanged; see
> provenance_followup.md for the documented LOMO interpretation. Two test
> groups is this study's completeness policy, not a universal LOMO requirement.

`core.fault_type_manifest` freezes roles, sample IDs, provenance, exclusions,
counts, seeds and source fingerprints. Both protocol content and embedded
validation evidence are checksum-bound. Gzip encoding has mtime=0; writing
different bytes over the same artifact is refused. Resume reads and verifies
the exact artifact rather than silently creating a different split.

`core.fault_type_validator` distinguishes:

- PASS: declared classes, sample/group/condition coverage and independence
  checks pass. This is not proof of undocumented physical independence.
- INCOMPLETE: missing classes/coverage, fewer than 30 test windows per class,
  fewer than two test acquisition groups per class, shared validation and
  calibration, insufficient semantic evidence or requested event boundaries.
  These results require explicit exploratory opt-in and cannot support the
  main independent-test claim.
- INVALID: known leakage, threshold inputs outside calibration, unknown-role
  fitting, undeclared exclusions, checksum/provenance failures, test-based
  selection or detector pairing mismatch. Execution must stop before fitting.

The 30-window floor is an operational diagnostic minimum, not a power analysis
or 30 independent observations: adjacent windows may be correlated. The
two-group floor avoids describing a single campaign as replicated testing.
Confidence intervals over overlapping class combinations/folds will be
descriptive, not independent motor-population inference.

All fifteen required error codes have semantic trigger tests; interval overlap
is checked at raw-source level when bounds exist. Missing raw intervals remain
an explicit warning. Whole-campaign holdout is the conservative available
fallback, not verified physical-motor holdout.

Current formal data has only three campaign codes. Three leave-one-campaign-out
rotations keep final test separate but share validation/calibration and have
only one test campaign per class. Thus the expected status is INCOMPLETE, not
PASS. No threshold or model is selected using final-test scores.

Reproduce a frozen three-fold example (from the repository root):

```powershell
.\venv\Scripts\python.exe -m core.fault_type_manifest --data-root data/formal_local --registry reports/fault_type_openset/manifests/class_roles_v1_6bdff74614f1d781.json --git-commit 819c9d06b8cefa13d7b084838ea33b784536195e
```

The CLI uses `setup_run`: complete compressed manifests and a compact validation
index go under `output/fault_type_manifest/<timestamp>/`, with the execution log
under `logs/fault_type_manifest/`. Formal feature data remains read-only.
