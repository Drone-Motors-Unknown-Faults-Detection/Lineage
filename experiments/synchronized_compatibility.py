"""Capture exact environment, full regression and new CLI help compatibility."""
import argparse
import importlib.metadata
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from core.fault_type_final_guard import digest
from core.fault_type_provenance import save_json
from core.logger import setup_run


def run(pools, *, output):
    inventory=sorted([{"name":d.metadata["Name"],"version":d.version} for d in importlib.metadata.distributions()],key=lambda d:d["name"].lower())
    env=dict(os.environ,PYTHONIOENCODING="utf-8",MPLCONFIGDIR=str((Path.cwd()/"output/fault_type_mplcache").resolve()))
    commands=[[sys.executable,"-m","pip","check"],[sys.executable,"-m","unittest","discover","-s","tests","-q"]]
    for name in ("synchronized_raw","synchronized_features","fault_type_fresh","synchronized_fixture"):
        commands.append([sys.executable,"-m",f"experiments.{name}","--help"])
    results=[]
    for i,command in enumerate(commands):
        process=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",env=env)
        path=output/f"command_{i}.txt"; path.write_text(process.stdout+process.stderr,encoding="utf-8")
        results.append({"command":command,"exit_code":process.returncode,"output":str(path.resolve())})
    count=re.search(r"Ran (\d+) tests",(output/"command_1.txt").read_text(encoding="utf-8"))
    result={"python":platform.python_version(),"executable":sys.executable,"platform":platform.platform(),"packages":inventory,
        "environment_fingerprint":digest({"python":platform.python_version(),"packages":inventory}),
        "commands":results,"tests_passed":int(count[1]) if count and results[1]["exit_code"]==0 else None,
        "status":"PASS" if all(r["exit_code"]==0 for r in results) else "FAILED",
        "serialization_scope":"new synthetic fixtures fit/load within THIS interpreter; no cross-runtime joblib loading",
        "research_status":"BLOCKED_NO_ELIGIBLE_DATA"}
    save_json(output/"environment.json",result)
    if result["status"]!="PASS": raise RuntimeError("compatibility failed; exact command outputs saved")
    return result


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    log,paths=setup_run("synchronized_compatibility")
    result=run(None,output=paths.output_dir); log.info("Python{} {}tests compatible",result["python"],result["tests_passed"])


if __name__ == "__main__": main()
