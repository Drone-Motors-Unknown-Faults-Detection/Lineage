"""Inventory existing ZIPs and reconstruct processed-feature row lineage."""
import argparse
from pathlib import Path
from core.fault_type_source_audit import source_inventory
from core.fault_type_provenance import save_json
from core.logger import setup_run


def run(pools, *, source_roots) -> dict:
    return source_inventory([Path(root) for root in source_roots], Path(pools))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, action="append", required=True)
    args = parser.parse_args()
    log, paths = setup_run("fault_type_source_audit")
    result = run(args.data_root, source_roots=args.source_root)
    save_json(paths.output_dir / "source_audit.json", result)
    log.info("Recovered {} processed row mappings; original DAQ intervals unknown", result["recovered_processed_rows"])


if __name__ == "__main__":
    main()
