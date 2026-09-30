"""Read-only motor identity evidence verification CLI."""
from __future__ import annotations
import argparse
from pathlib import Path
from core.fault_type_provenance import motor_overlay, save_json
from core.logger import setup_run


def run(pools, *, repo: Path | str = ".") -> dict:
    return motor_overlay(pools, repo)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    args = parser.parse_args()
    log, paths = setup_run("fault_type_provenance")
    result = run(args.data_root)
    save_json(paths.output_dir / "motor_evidence.json", result)
    log.info("Verified {} files / {} rows; path mapping={}, physical chain=INCOMPLETE", result["file_count"], result["sample_count"], result["mapping_check"]["status"])


if __name__ == "__main__":
    main()
