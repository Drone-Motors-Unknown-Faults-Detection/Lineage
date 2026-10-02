"""Native synthetic eight-arm smoke; never counted as motor research."""
import argparse
import platform
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from threadpoolctl import threadpool_limits
from core.fault_type_continuous import GainRepresentation,DiagonalMargin,stratified_subset
from core.openset import create_openset_detector
from core.logger import setup_run
from core.fault_type_provenance import save_json
from experiments.fault_type_mechanism_smoke import fixture
from experiments.fault_type_continuous_registry import ARMS,PARAMS
from experiments.fault_type_continuous_study import infer


def run(pools,*,output):
    with threadpool_limits(limits=1):
        parent,_,_,T,rpms,X,y=fixture();h=parent['references']['harmonic69/mixed']['transformer'].transform(X)
        ix=stratified_subset(y,rpms,0);metric=DiagonalMargin().fit(h[ix],y[ix]);n={'metric':metric,'models':{},'detectors':{},'representations':{},'arm_failures':{}}
        for d in ARMS:
            if d['kind']=='neighbors':
                z=metric.transform(h) if d['metric'] else h;jj=ix if d['subset_classifier'] else np.arange(len(y))
                n['models'][d['id']]=KNeighborsClassifier(**PARAMS['neighbors']).fit(z[jj],y[jj])
            elif str(d['dimension']) not in n['representations']:
                dim=str(d['dimension']);rep=GainRepresentation(d['dimension']).fit(X);z=rep.transform(X);c=rep.transform(T)
                n['representations'][dim]=rep;n['models']['gain'+dim]=LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto',priors=[1/6]*6).fit(z,y)
                n['detectors'][dim]=create_openset_detector().fit(z,y,c,y)
        a=infer(parent,n,{'arms':ARMS},T);b=infer(parent,n,{'arms':ARMS},T.copy())
    if len(a)!=8 or any(not np.array_equal(a[k][j],b[k][j]) for k in a for j in [0,1]):raise ValueError('smoke determinism')
    if not np.array_equal(a['Q06'][0],a['Q08'][0]) or not np.array_equal(a['Q01'][1],a['Q04'][1]):raise ValueError('matched branches')
    result={'scope':'SYNTHETIC_ENGINEERING_ONLY','python':platform.python_version(),'arms':8,'status':'PASS','metric_optimizer':metric.optimizer}
    save_json(output/'smoke_index.json',result);return result
def main():
    argparse.ArgumentParser(description=__doc__).parse_args();log,paths=setup_run('fault_type_continuous_smoke_py'+platform.python_version().replace('.','_'))
    r=run(None,output=paths.output_dir);log.info('synthetic {} eight arms; NOT research',r['status'])
if __name__=='__main__':main()
