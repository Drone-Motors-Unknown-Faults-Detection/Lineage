"""指定交付後的唯讀 issue 盤點與固定 main 小型 fixture。"""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import io
import json
import posixpath
import re
from pathlib import Path
import subprocess
import zipfile
import numpy as np
import pandas as pd
from core.logger import setup_run
from experiments.fault_type_citation_audit import github_snapshot, git

MAIN = "64cb71d84663e1745ec54db74abad68def67e8e6"
HISTORY = "80bdf54fdf43d466ea19549fb7c0b4e391394799"
REPO = "Drone-Motors-Unknown-Faults-Detection/Lineage"
FILES = ["core/data.py","core/formal_data.py","core/runner.py","core/openset.py",
         "experiments/exp1_cold_start.py","experiments/exp2_scale_growth.py","experiments/exp3_trend.py",
         "experiments/exp6_formal_benchmark.py","experiments/exp6_osr_benchmark.py","experiments/exp6_matrix.py",
         "experiments/aggregate_exp6.py","web/live.py","web/server.py","docs/README.md","docs/health_and_reports.md",
         "README.md","build_uv.sh","build_uv_mac.sh","run_web.sh","pyproject.toml"]

def api(endpoint):
    value = subprocess.run(["gh","api","--paginate","--slurp",endpoint],capture_output=True,
                           encoding="utf-8",check=True)
    pages = json.loads(value.stdout)
    return pages[0] if len(pages) == 1 and isinstance(pages[0],dict) else [r for page in pages for r in page]

def selected(source, names, namespace):
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    if set(names) != {node.name for node in nodes}: raise ValueError("固定main缺少預期函數")
    exec(compile(ast.Module(body=nodes,type_ignores=[]),"<固定main已讀函數fixture>","exec"),namespace)
    return namespace

def fixtures(sources, root):
    root.mkdir(exist_ok=False)
    expected = dict(method="knn",seed=42,motor="T1",rpm="8000rpm")
    summary = dict(status="completed",method="knn",seed=42,dataset_fingerprint="fixture",
                   rows=[dict(status="completed",**expected)])
    summary_path = root/"summary.json"; summary_path.write_text(json.dumps(summary),encoding="utf-8")
    matrix = selected(sources["experiments/exp6_matrix.py"],["_is_complete"],dict(Path=Path,json=json))
    complete = matrix["_is_complete"](summary_path,expected,"fixture")
    fp = selected(sources["experiments/exp6_formal_benchmark.py"],["dataset_fingerprint"],
                  dict(Path=Path,json=json,hashlib=hashlib))
    data = root/"Step-1/myfeature/T1/8000rpm/8screws"; data.mkdir(parents=True)
    csv_path = data/"T1_Group_feature_data_clean.csv"
    csv_path.write_text("A",encoding="utf-8")
    import os
    timestamp = 1_700_000_000_000_000_000
    os.utime(csv_path,ns=(timestamp,timestamp)); first = fp["dataset_fingerprint"](root)
    csv_path.write_text("B",encoding="utf-8"); os.utime(csv_path,ns=(timestamp,timestamp))
    second = fp["dataset_fingerprint"](root)
    loader = selected(sources["core/data.py"],["config_sort_key","discover_datasets","load_pools"],
                      dict(Path=Path,np=np,pd=pd,CONFIG_ORDER=["8screws"],FEATURE_DIM=105,HEALTHY="8screws"))
    pd.DataFrame([[float(i) for i in range(105)]],columns=[f"任意欄{i}" for i in range(105)]).to_csv(csv_path,index=False)
    pools = loader["load_pools"](data.parent)
    agg_names = ["_read_json","_summary_path","_finite","_mean_std","_round","load_matrix","aggregate"]
    import math
    metrics = ("known_accuracy","open_set_accuracy","auroc","aupr_unknown_positive","fpr_at_tpr95",
               "unknown_precision","unknown_recall","unknown_f1")
    agg = selected(sources["experiments/aggregate_exp6.py"],agg_names,dict(Path=Path,json=json,pd=pd,math=math,METRICS=metrics))
    row = dict(status="completed",dataset="T1/8000",method="knn",seed=42,**{k:0.5 for k in metrics})
    summary_path.write_text(json.dumps(dict(summary,rows=[row])),encoding="utf-8")
    manifest = dict(status="completed",expected_runs=1,completed_runs=1,methods=["knn"],seeds=[42],
                    runs=[dict(run_id="fixture",status="completed",method="knn",seed=42,
                               summary="summary.json",dataset_fingerprint="TAMPERED")])
    manifest_path = root/"matrix_manifest.json"; manifest_path.write_text(json.dumps(manifest),encoding="utf-8")
    aggregate = agg["aggregate"](manifest_path)
    capture = []
    formal = selected(sources["core/formal_data.py"],["_channel_key","_convert_condition"],
        dict(Path=Path,pd=pd,np=np,ZipFile=zipfile.ZipFile,ZipInfo=zipfile.ZipInfo,MaterializedFile=lambda **kw:kw,
             FormalDataError=ValueError,FEATURE_NAMES=[f"f{i}" for i in range(105)],
             _statistical_features=lambda f:np.zeros((f.shape[1],15)),
             _fft_features=lambda f,rpm:np.zeros((f.shape[1],10)),
             _clean_feature_frame=lambda f:(f,len(f)),_write_bytes=lambda path,payload,force:capture.append(str(path.resolve())),
             _sha256_bytes=lambda b:hashlib.sha256(b).hexdigest()))
    memory = io.BytesIO()
    with zipfile.ZipFile(memory,"w") as z:
        for suffix in ["X","Y","Z","Current","Delta_T"]:
            width = 2 if suffix == "Current" else 3
            z.writestr("root/../T2_"+suffix+"_data.csv",pd.DataFrame(np.ones((3,width))).to_csv(index=False))
    memory.seek(0)
    with zipfile.ZipFile(memory) as z:
        converted = formal["_convert_condition"](z,"fixture",root/"materialized","T2","8000rpm",force=False,selected_conditions=None)
    return dict(summary_without_csv_log_accepted=complete,
                same_size_mtime_different_bytes_fingerprint_equal=first == second,
                arbitrary_schema_healthy_only_loaded=list(pools),
                discovered_partial_conditions=len(loader["discover_datasets"](root)),
                tampered_manifest_fingerprint_published=aggregate["dataset_fingerprint"],
                stage2_arbitrary_config_accepted=converted[0]["config"],stage2_unequal_widths_rows=converted[0]["rows_after_clean"],
                stage2_stub_write_targets=capture,stage2_real_feature_math=False,actual_outside_files_written=False,
                formal_data_read=False,models_fit=0)

def run(pools=None, *, network=False):
    logger, paths = setup_run("fault_type_issue_triage")
    target = paths.output_dir
    sources, inventory = {}, []
    for path in FILES:
        raw = git("show",MAIN+":"+path)
        source = raw.decode("utf-8"); sources[path] = source
        functions = []
        if path.endswith(".py"):
            functions = [dict(name=n.name,line=n.lineno,end_line=n.end_lineno) for n in ast.walk(ast.parse(source))
                         if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
        inventory.append(dict(path=path,ref=MAIN,sha256=hashlib.sha256(raw).hexdigest(),functions=functions))
    tests = git("ls-tree","-r","--name-only",MAIN,"tests").decode("utf-8").splitlines()
    tree = set(git("ls-tree","-r","--name-only",MAIN).decode("utf-8").splitlines())
    doc_targets = []
    for match in re.finditer(r"\]\(([^)]+)\)",sources["docs/README.md"]):
        link = match[1].split("#",1)[0]
        if link.startswith(("http:","https:")) or not link: continue
        target_path = posixpath.normpath(posixpath.join("docs",link))
        exists = target_path in tree or any(path.startswith(target_path.rstrip("/")+"/") for path in tree)
        doc_targets.append(dict(link=link,target=target_path,exists=exists))
    result = dict(main_ref=MAIN,history_ref=HISTORY,source_files=inventory,main_test_files=tests,
                  current_docs_index_links=doc_targets,fixture_results=fixtures(sources,target/"fixtures"),
                  programming_changed=False)
    (target/"main_review.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    if network:
        snapshot = github_snapshot(REPO)
        snapshot["merged_prs"] = [api(f"repos/{REPO}/pulls/{n}") for n in [8,32]]
        snapshot["branch_main"] = api(f"repos/{REPO}/branches/main")
        receipts = []
        for n in [22,19,20]:
            issue = api(f"repos/{REPO}/issues/{n}")
            issue["all_comments"] = api(f"repos/{REPO}/issues/{n}/comments")
            receipts.append(issue)
        (target/"github_snapshot.json").write_text(json.dumps(snapshot,ensure_ascii=False,indent=2),encoding="utf-8")
        (target/"issue_receipts.json").write_text(json.dumps(receipts,ensure_ascii=False,indent=2),encoding="utf-8")
    raw = git("show",HISTORY+":reports/project_health_audit/findings.csv").decode("utf-8")
    (target/"historical_findings.json").write_text(json.dumps(list(csv.DictReader(io.StringIO(raw))),
                                                         ensure_ascii=False,indent=2),encoding="utf-8")
    logger.info("完成固定main唯讀查核，未修改程式或正式資料；fixture {}",result["fixture_results"])
    return dict(output=str(target),main_ref=MAIN,network_get_only=network,trained_models=0)

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("--network",action="store_true")
    print(json.dumps(run(**vars(p.parse_args(argv))),ensure_ascii=False))
if __name__ == "__main__": main()
