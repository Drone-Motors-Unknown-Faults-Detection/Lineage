"""Full regression and fixed-method CLI compatibility, per interpreter."""
import argparse
import os
import subprocess
import sys
from pathlib import Path
from core.logger import setup_run
from core.fault_type_provenance import save_json
from experiments.synchronized_compatibility import run as compatible


def run(pools, *, output):
    result=compatible(pools,output=output)
    for module in ['fault_type_fixed_calibration','fault_type_fixed_smoke']:
        command=[sys.executable,'-m','experiments.'+module,'--help']
        process=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',
            env=dict(os.environ,PYTHONIOENCODING='utf-8'))
        path=output/(module+'_help.txt'); path.write_text(process.stdout+process.stderr,encoding='utf-8')
        result['commands'].append({'command':command,'exit_code':process.returncode,'output':str(path.resolve())})
    result['status']='PASS' if all(r['exit_code']==0 for r in result['commands']) else 'FAILED'
    result['research_status']='ENGINEERING_ONLY; existing exposed research comparisons permitted, not fresh validation'
    save_json(output/'environment.json',result)
    if result['status']!='PASS': raise RuntimeError('fixed-method acceptance failed')
    return result


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    log,paths=setup_run('fault_type_fixed_acceptance')
    r=run(None,output=paths.output_dir)
    log.info('Python{} {} tests {}',r['python'],r['tests_passed'],r['status'])


if __name__=='__main__': main()
