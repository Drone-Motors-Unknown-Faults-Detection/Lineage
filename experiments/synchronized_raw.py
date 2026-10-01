"""Preview one configured recording. Never declares unknown alignment verified."""
import argparse
import json
from pathlib import Path
from core.synchronized_raw import read_recording, audit_timebase, quality_mask, make_windows
from core.fault_type_provenance import save_json
from core.logger import setup_run


def run(pools, *, config):
    recording = read_recording(pools, config)
    audit = audit_timebase(recording)
    quality = quality_mask(recording, config["quality"])
    windows, rejected = make_windows(recording, audit, quality, config["windows"])
    return {"audit": audit.summary, "quality": {"checksum": quality.config_checksum, "bad_points": quality.reasons},
            "accepted_windows": [w.metadata for w in windows], "rejected_windows": rejected,
            "research_status": "BLOCKED_NO_ELIGIBLE_DATA" if config.get("synthetic") or not audit.summary["physical_time_alignment_verified"] else "MEASUREMENT_ATTESTED_NOT_MODEL_VALIDATED"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-file", type=Path, required=True); p.add_argument("--config", type=Path, required=True)
    args = p.parse_args(); log, paths = setup_run("synchronized_raw")
    result = run(args.raw_file, config=json.loads(args.config.read_text(encoding="utf-8")))
    save_json(paths.output_dir / "raw_audit.json", result)
    log.info("accepted={} rejected={} alignment={}", len(result["accepted_windows"]), len(result["rejected_windows"]), result["audit"]["status"])


if __name__ == "__main__": main()
