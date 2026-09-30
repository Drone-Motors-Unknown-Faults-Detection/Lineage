"""Verify incoming acquisition provenance; final-test eligibility is opt-in."""
import argparse
import gzip
import json
from pathlib import Path
from core.fault_type_final_guard import ingest, guard_final_test, seal
from core.fault_type_provenance import save_json
from core.logger import setup_run


def run(pools, *, manifest, ledger=None, locked=None, claim=None):
    bundle = ingest(Path(pools), manifest)
    qualification = guard_final_test(bundle, ledger, locked, claim=claim) if locked is not None else {
        "status": "INGEST_VERIFIED_NOT_FINAL_TEST", "reason": "no locked model; evaluation forbidden"}
    return {"bundle": bundle, "qualification": qualification}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incoming-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--locked", type=Path)
    parser.add_argument("--claim", choices=("new_session", "new_motor"))
    parser.add_argument("--seal-manifest", action="store_true", help="save checksum-bound copy to output only; not acquisition verification")
    args = parser.parse_args()
    if any([args.locked, args.ledger, args.claim]) and not all([args.locked, args.ledger, args.claim]):
        parser.error("final eligibility requires --locked, --ledger and --claim together")
    log, paths = setup_run("fault_type_ingest")
    if args.seal_manifest:
        if any([args.locked, args.ledger, args.claim]): parser.error("sealing is not final qualification")
        save_json(paths.output_dir / "sealed_manifest.json", seal(json.loads(args.manifest.read_bytes()), "manifest_checksum"))
        log.info("Sealed manifest COPY saved to output; no source edits, no acquisition qualification")
        return
    ledger = json.loads(gzip.decompress(args.ledger.read_bytes())) if args.ledger else None
    locked = json.loads(args.locked.read_bytes()) if args.locked else None
    result = run(args.incoming_root, manifest=json.loads(args.manifest.read_bytes()), ledger=ledger, locked=locked, claim=args.claim)
    save_json(paths.output_dir / "ingest_result.json", result)
    log.info("{}; {} records; hardware claims require attestation review", result["qualification"]["status"], len(result["bundle"]["records"]))


if __name__ == "__main__": main()
