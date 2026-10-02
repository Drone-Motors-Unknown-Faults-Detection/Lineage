"""Full tests, pip check, legacy16/new5 CLI checks in each runtime separately."""
import argparse
import os
import platform
import subprocess
import sys
from core.logger import setup_run
from core.fault_type_provenance import save_json
from experiments.fault_type_accuracy_acceptance import run as prior_acceptance


def run(pools,*,output):
    result=prior_acceptance(pools,output=output)
    for module in ['fault_type_literature_registry','fault_type_literature_study','fault_type_literature_report','fault_type_literature_smoke','fault_type_literature_diagnosis']:
        command=[sys.executable,'-m','experiments.'+module,'--help']
        r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',env=dict(os.environ,PYTHONIOENCODING='utf-8'))
        path=output/(module+'_help.txt');path.write_text(r.stdout+r.stderr,encoding='utf-8')
        result['commands'].append({'command':command,'exit_code':r.returncode,'output':str(path.resolve())})
    result['status']='PASS' if all(r['exit_code']==0 for r in result['commands']) else 'FAILED'
    save_json(output/'environment.json',result)
    if result['status']!='PASS':raise RuntimeError('literature acceptance failed')
    return result


def main():
    argparse.ArgumentParser(description=__doc__).parse_args();log,paths=setup_run('fault_type_literature_acceptance_py'+platform.python_version().replace('.','_'))
    r=run(None,output=paths.output_dir);log.info('Python{} tests={} status={}',r['python'],r['tests_passed'],r['status'])


if __name__=='__main__':main()
