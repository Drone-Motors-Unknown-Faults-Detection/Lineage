"""Save final regression, formal SHA and backup byte-verification evidence."""
import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile
from core.formal_data import _sha256_file
from core.fault_type_provenance import save_json
from core.logger import setup_run


def run(pools, *, archive_index: Path, log, output: Path) -> dict:
    environment = dict(os.environ)
    environment["PYTHONIOENCODING"] = "utf-8"
    environment["MPLCONFIGDIR"] = str((Path.cwd()/"output/fault_type_mplcache").resolve())
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]
    test = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", env=environment)
    (output / "full_suite.txt").write_text(test.stdout+test.stderr, encoding="utf-8")
    match = re.search(r"Ran (\d+) tests", test.stderr)
    if test.returncode or match is None:
        raise RuntimeError("full regression failed; inspect saved full_suite.txt")
    material = json.loads((Path(pools)/"formal_materialization_manifest.json").read_bytes())
    mismatches = [item["output"] for item in material["files"] if _sha256_file(Path(item["output"])) != item["source_sha256"]]
    if mismatches: raise ValueError("formal data changed")
    checks = []
    for item in json.loads(archive_index.read_bytes())["archives"]:
        path = Path(item["path"])
        if _sha256_file(path) != item["sha256"]: raise ValueError("backup SHA mismatch")
        with ZipFile(path) as archive:
            if archive.testzip() is not None: raise ValueError("backup CRC failure")
            bundle_index = json.loads(archive.read("BUNDLE_INDEX.json"))
            for source in bundle_index["files"]:
                content = archive.read(source["path"])
                if len(content) != source["bytes"] or hashlib.sha256(content).hexdigest() != source["sha256"]:
                    raise ValueError("backup per-file SHA mismatch")
        checks.append({**item, "member_sha_status": "PASS"})
    log.info("{} tests;90 formal SHAs unchanged;{} backup SHA/CRC/member checks PASS", match[1], len(checks))
    return {"tests_passed": int(match[1]), "test_command": command, "test_exit_code": test.returncode,
        "actual_python": platform.python_version(), "declared_python": "3.10.19", "declared_python_verified": False,
        "formal_files_checked": len(material["files"]), "formal_sha_mismatches": mismatches,
        "archives": checks, "sources_deleted": False, "fresh_independent_research_validation": "NOT_COMPLETED_NO_ELIGIBLE_DATA"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--archive-index", type=Path, required=True)
    args = parser.parse_args()
    log, paths = setup_run("fault_type_followup_acceptance")
    result = run(args.data_root, archive_index=args.archive_index, log=log, output=paths.output_dir)
    save_json(paths.output_dir/"acceptance.json", result)


if __name__ == "__main__": main()
