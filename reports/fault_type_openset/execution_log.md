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
