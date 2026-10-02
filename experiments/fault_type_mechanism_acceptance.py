"""Dual-runtime full test/pip/CLI evidence; no cross-version joblib loads."""
import argparse
import os
import platform
import subprocess
import sys
from core.logger import setup_run
from core.fault_type_provenance import save_json
from experiments.fault_type_literature_acceptance import run as prior


def run(pools,*,output):
    result=prior(pools,output=output)
    for name in ['fault_type_metrics_v2','fault_type_mechanism_diagnosis','fault_type_mechanism_registry','fault_type_mechanism_study','fault_type_mechanism_smoke','fault_type_mechanism_report','fault_type_mechanism_acceptance']:
        command=[sys.executable,'-m','experiments.'+name,'--help'];r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',env=dict(os.environ,PYTHONIOENCODING='utf-8'))
        path=output/(name+'_help.txt');path.write_text(r.stdout+r.stderr,encoding='utf-8')
        result['commands'].append({'command':command,'exit_code':r.returncode,'output':str(path.resolve())})
    result['status']='PASS' if all(x['exit_code']==0 for x in result['commands']) else 'FAILED'
    save_json(output/'environment.json',result)
    if result['status']!='PASS':raise RuntimeError('mechanism acceptance failed')
    return result


def main():
    argparse.ArgumentParser(description=__doc__).parse_args();log,paths=setup_run('fault_type_mechanism_acceptance_py'+platform.python_version().replace('.','_'))
    r=run(None,output=paths.output_dir);log.info('Python {} tests={} {}',r['python'],r['tests_passed'],r['status'])


if __name__=='__main__':main()
