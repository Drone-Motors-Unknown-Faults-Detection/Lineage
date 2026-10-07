"""只讀實驗入口、書面索引與已封存方法，保存導覽來源。"""
from __future__ import annotations
import ast
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from core.logger import setup_run

MAIN = '64cb71d84663e1745ec54db74abad68def67e8e6'

def git(*args):
    return subprocess.run(['git','-c','core.quotepath=false',*args],check=True,capture_output=True).stdout

def describe(path, raw, ref):
    functions = []
    if path.endswith('.py'):
        functions = [n.name for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    return dict(path=path,ref=ref,sha256=hashlib.sha256(raw).hexdigest(),functions=functions,
                run='run' in functions,main='main' in functions)

def run(pools=None):
    log, paths = setup_run('navigation_inventory')
    head = git('rev-parse','HEAD').decode().strip()
    current = [str(p).replace('\\','/') for p in sorted(Path('experiments').glob('*.py'))]
    modules = [describe(p,Path(p).read_bytes(),head) for p in current]
    main_paths = git('ls-tree','-r','--name-only',MAIN,'experiments').decode().splitlines()
    main_modules = [describe(p,git('show',MAIN+':'+p),MAIN) for p in main_paths if p.endswith('.py')]
    registry = []
    candidates = [*Path('reports').rglob('result_index.json'),Path('reports/continuous_research/global_attempt_ledger.json'),
                  Path('reports/research_closeout_20261005/delivery_index.json')]
    for path in sorted(set(candidates)):
        raw = path.read_bytes()
        registry.append(dict(describe(path.as_posix(),raw,head),saved_index=json.loads(raw)))
    arm_path = Path('output/fault_type_research_closeout/2026-10-05-22-53-29/arm_inventory.json')
    arms = json.loads(arm_path.read_text(encoding='utf-8'))
    index = dict(research_ref=head,main_ref=MAIN,modules=modules,main_modules=main_modules,
                 registries=registry,arm_inventory=describe(arm_path.as_posix(),arm_path.read_bytes(),head),
                 arm_count=len(arms),plans_are_not_completed=True,new_training=0,new_predictions=0,
                 current_deleted_tracked_files=len(git('diff','--name-only','--diff-filter=D').splitlines()))
    (paths.output_dir/'source_index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
    with gzip.open(paths.output_dir/'method_inventory.json.gz','wt',encoding='utf-8') as f:
        json.dump(arms,f,ensure_ascii=False)
    log.info('研究模組{}，main模組{}，結果索引{}，方法／分數條目{}；無新訓練',len(modules),len(main_modules),len(registry),len(arms))
    return dict(output=str(paths.output_dir),modules=len(modules),main_modules=len(main_modules),arms=len(arms))

def main():
    print(json.dumps(run(),ensure_ascii=False))

if __name__ == '__main__': main()
