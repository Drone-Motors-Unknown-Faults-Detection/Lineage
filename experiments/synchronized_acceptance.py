"""Verify unchanged formal/historical bytes and new backed-up derived artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from core.formal_data import _sha256_file
from core.fault_type_provenance import save_json
from core.logger import setup_run


def run(pools, *, historical_archives,archive_index,compatibility,log):
    material=json.loads((Path(pools)/"formal_materialization_manifest.json").read_text(encoding="utf-8"))
    for item in material["files"]:
        if _sha256_file(Path(item["output"]))!=item["source_sha256"]: raise ValueError("formal CSV changed")
    original_files=0; original_bytes=0; matrix_counts=[]
    for path in historical_archives:
        with ZipFile(path) as archive:
            index=json.loads(archive.read("BUNDLE_INDEX.json")); root=Path(index["source_root"])
            for i,item in enumerate(index["files"]):
                target=root/Path(item["path"]).relative_to(root.name)
                if target.stat().st_size!=item["bytes"] or _sha256_file(target)!=item["sha256"]: raise ValueError(f"historical artifact changed: {target}")
                original_files+=1; original_bytes+=item["bytes"]
                if i%1000==0: log.info("{} original artifact bytes checked",original_files)
            state=json.loads((root/"run_status.json").read_text(encoding="utf-8"))
            count=len(state["runs"])
            if count!=state["declared_run_count"] or any(r["status"]!="completed" for r in state["runs"].values()): raise ValueError("historical matrix inventory changed")
            matrix_counts.append(count)
    if sum(matrix_counts)!=2490: raise ValueError("expected preserved2490-run baseline")
    backups=[]
    for item in json.loads(archive_index.read_text(encoding="utf-8"))["archives"]:
        path=Path(item["path"])
        if _sha256_file(path)!=item["sha256"]: raise ValueError("new backup SHA mismatch")
        with ZipFile(path) as archive:
            if archive.testzip() is not None: raise ValueError("new backup CRC mismatch")
            index=json.loads(archive.read("BUNDLE_INDEX.json"))
            for entry in index["files"]:
                data=archive.read(entry["path"])
                if len(data)!=entry["bytes"] or hashlib.sha256(data).hexdigest()!=entry["sha256"]: raise ValueError("new backup member checksum mismatch")
        backups.append({**item,"member_sha_status":"PASS"})
    environments=[json.loads(path.read_text(encoding="utf-8")) for path in compatibility]
    if {e["python"] for e in environments}!={"3.10.19","3.14.6"} or any(e["status"]!="PASS" for e in environments): raise ValueError("two-runtime compatibility incomplete")
    return {"status":"ENGINEERING_ACCEPTANCE_PASS","formal_files_unchanged":len(material["files"]),
        "historical_matrix_counts":matrix_counts,"historical_files_byte_sha_verified":original_files,"historical_bytes_verified":original_bytes,
        "environments":[{"python":e["python"],"tests_passed":e["tests_passed"],"fingerprint":e["environment_fingerprint"]} for e in environments],
        "backups":backups,"research_status":"BLOCKED_NO_ELIGIBLE_DATA","real_hardware_acquisition_performed":False,
        "default_classifier_detector_changed":False,"raw_data_uploaded":False}


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--data-root",type=Path,required=True)
    p.add_argument("--historical-archives",type=Path,nargs=3,required=True); p.add_argument("--archive-index",type=Path,required=True)
    p.add_argument("--compatibility",type=Path,nargs=2,required=True)
    args=p.parse_args(); log,paths=setup_run("synchronized_acceptance")
    result=run(args.data_root,historical_archives=args.historical_archives,archive_index=args.archive_index,compatibility=args.compatibility,log=log)
    save_json(paths.output_dir/"acceptance.json",result); log.info("engineering acceptance PASS; real independent final still NOT completed")


if __name__ == "__main__": main()
