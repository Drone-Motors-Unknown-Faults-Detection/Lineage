"""Numerical Stage1/2/3 feature-contract verification without writing data."""
import argparse
from pathlib import Path
from core.fault_type_feature_contract import audit_features
from core.fault_type_provenance import save_json
from core.logger import setup_run


def run(pools, *, source_root, extracted_root):
    return audit_features(Path(source_root), Path(extracted_root), Path(pools))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--extracted-root", type=Path, required=True)
    args = parser.parse_args()
    log, paths = setup_run("fault_type_feature_audit")
    result = run(args.data_root, source_root=args.source_root, extracted_root=args.extracted_root)
    save_json(paths.output_dir / "feature_audit.json", result)
    log.info("{} conditions checked; Stage2 {} unique processed mappings; physical equivalence UNVERIFIED",
        len(result["checks"]), result["stage2_unique_processed_mappings"])


if __name__ == "__main__":
    main()
