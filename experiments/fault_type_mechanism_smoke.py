"""Runtime-native synthetic mechanisms/inference smoke; NOT motor results."""
import argparse
import platform
import numpy as np
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from threadpoolctl import threadpool_limits
from core.fault_type_mechanisms import RPMPartialPooling,BlockGeometry,calibrate,peak_memory_bytes
from core.fault_type_literature import LiteratureRepresentation
from core.openset import create_openset_detector
from core.logger import setup_run
from core.fault_type_provenance import save_json
from experiments.fault_type_mechanism_registry import ARMS
from experiments.fault_type_mechanism_study import infer


def fixture():
    rng=np.random.default_rng(20261002);K=6;rpms=['6000rpm','8000rpm','11000rpm'];y=np.tile(np.repeat(np.arange(K),12),3);r=np.repeat(rpms,72)
    def draw():
        X=rng.normal(size=(len(y),105))+y[:,None]*.1
        for off in [15,40,65]:
            X[:,off]=np.abs(X[:,off]);X[:,off+3]=np.abs(X[:,off+3]);X[:,off+7]=X[:,off+9]
            X[:,off+12]=X[:,off]**2;X[:,off+13]=X[:,off+3]**2
        return X
    X=draw();C=draw();T=draw();refs={};models={'C17':{},'C24':{}}
    for name in ['base75','harmonic69']:
        tr=LiteratureRepresentation(name,0).fit(X,y);z=tr.transform(X);cz=tr.transform(C)
        refs[name+'/mixed']={'transformer':tr,'detectors':{m:create_openset_detector(m,confidence=.95,knn_neighbors=5).fit(z,y,cz,y) for m in ['mahalanobis','knn']}}
    for rpm in rpms:
        ix=r==rpm;tr=LiteratureRepresentation('base75',0).fit(X[ix],y[ix]);refs['base75/'+rpm]={'transformer':tr}
        models['C24'][rpm]={'reference_key':'base75/'+rpm,'classifier':LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto',priors=[1/K]*K).fit(tr.transform(X[ix]),y[ix])}
    models['C17']['mixed']={'classifier':LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto',priors=[1/K]*K).fit(refs['harmonic69/mixed']['transformer'].transform(X),y)}
    parent={'references':refs,'models':models};z=refs['base75/mixed']['transformer'].transform(X);h=refs['harmonic69/mixed']['transformer'].transform(X)
    g=BlockGeometry(K).fit(h,y);ch=refs['harmonic69/mixed']['transformer'].transform(C)
    new={'models':{d['id']:RPMPartialPooling(d['beta'],rpms,K).fit(z,y,r) for d in ARMS if d['kind']=='partial_pool'},'geometry':g,'thresholds':{str(w):calibrate(g.score(ch,w)) for w in [0.,1.]}}
    return parent,new,{'arms':ARMS,'rpms':rpms},T,r,X,y


def run(pools,*,output):
    with threadpool_limits(limits=1):
        parent,new,p,T,r,_,_=fixture();a=infer(parent,new,p,T,r);b=infer(parent,new,p,T.copy(),r.copy())
    if len(a)!=9 or any(not np.array_equal(a[k][j],b[k][j]) for k in a for j in [0,1]):raise ValueError('non deterministic smoke')
    result={'scope':'SYNTHETIC_ENGINEERING_ONLY_NOT_RESEARCH','python':platform.python_version(),'status':'PASS','arms':9,
        'rows':len(T),'new_geometry_dimension':new['geometry'].dimension,'deterministic':True,'process_peak_memory_bytes':peak_memory_bytes()}
    save_json(output/'smoke_index.json',result);return result


def main():
    argparse.ArgumentParser(description=__doc__).parse_args();log,paths=setup_run('fault_type_mechanism_smoke_py'+platform.python_version().replace('.','_'))
    r=run(None,output=paths.output_dir);log.info('synthetic {} nine arms; NOT research',r['status'])


if __name__=='__main__':main()
