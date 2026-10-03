"""實驗13數值來源重建；不讀 test、不改封存來源。"""
import argparse
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from core.fault_type_metric_classifiers import weight_transform,PrototypeClassifier,MarginEnergyClassifier
from core.fault_type_accuracy_pipeline import records_for
from core.fault_type_features import FeatureStore
from core.fault_type_final_guard import verify_seal,seal,digest
from core.fault_type_provenance import save_json
from core.openset import create_openset_detector
from core.logger import setup_run
from experiments.fault_type_metric_classification import check,read,load_model,weight_cell
from experiments.fault_type_literature_study import load_bundle,artifact
from experiments.fault_type_fixed_calibration import verify_sources


def equal(a,b,description):
    if not np.array_equal(a,b):raise ValueError(description+' differs from actual known source')


def verify_arrays(b,H,C,y,cy,ix,p,seed):
    """逐欄重建模型，來源由外層 records_for/FeatureStore 強制限定。"""
    spaces={'identity':(H,C),'metric':(weight_transform(H,b['weights']),weight_transform(C,b['weights']))}
    for geom,(Z,ZC) in spaces.items():
        for part in ['all','subset']:
            jj=ix if part=='subset' else np.arange(len(Z));model=b['models'][geom+'_'+part]
            equal(model._fit_X,Z[jj],geom+'_'+part+' feature reference');equal(model._y,y[jj],part+' labels')
        for name,centers in [(geom+'_mean',1)]+([('metric_multi',3)] if geom=='metric' else []):
            model=b['models'][name];expected=PrototypeClassifier(centers,seed).fit(Z,y)
            equal(model.prototypes_,expected.prototypes_,name+' centers');equal(model.prototype_labels_,expected.prototype_labels_,name+' labels')
        for method in ['mahalanobis','knn']:
            model=b['detectors'][geom+'/'+method]
            expected=create_openset_detector(method,**p['factory_parameters']).fit(Z,y,ZC,cy)
            if model.confidence!=expected.confidence:raise ValueError('calibration confidence')
            if method=='knn':
                if model.n_neighbors!=expected.n_neighbors:raise ValueError('neighbor configuration')
                for a,c in zip(model.models_,expected.models_):
                    if (a.label,a.threshold,a.n_train,a.n_neighbors)!=(c.label,c.threshold,c.n_train,c.n_neighbors):raise ValueError('kNN reference/calibration metadata')
                    equal(a.neighbors._fit_X,c.neighbors._fit_X,'kNN actual reference')
                if len(model.models_)!=len(expected.models_):raise ValueError('kNN classes')
            else:
                if model.method!=expected.method or model.pca_ is not None:raise ValueError('LW configuration')
                for a,c in zip(model.distributions_,expected.distributions_):
                    if (a.label,a.threshold)!=(c.label,c.threshold):raise ValueError('LW calibration')
                    equal(a.location,c.location,'LW actual train location');equal(a.precision,c.precision,'LW actual train precision')
                if len(model.distributions_)!=len(expected.distributions_):raise ValueError('LW classes')
    energy=b['models']['metric_energy'];expected=MarginEnergyClassifier().fit(H[ix],y[ix],b['weights'])
    if energy.signature()!=expected.signature():raise ValueError('energy actual train reference/target graph')
    return {'train_array_checksum':digest(H.tolist()),'calibration_array_checksum':digest(C.tolist()),
        'classifier_arrays':4,'prototype_models':3,'factory_models':4,'energy_reference':1,'numeric_exact':True}


def run(pools,*,protocol,lock,output):
    p=protocol;_,pp,ms,old,audits=check(p);verify_seal(lock,'locked_checksum')
    if lock['protocol_checksum']!=p['protocol_checksum'] or len(lock['artifacts'])!=9:raise ValueError('source lock coverage')
    before=verify_sources(pools.root,ms[0]);result=[]
    with threadpool_limits(limits=1):
        for a in lock['artifacts']:
            m=next(x for x in ms if x['fold_id']==a['fold_id']);pa=next(x for x in old['artifacts'] if (x['fold_id'],x['seed'])==(a['fold_id'],a['seed']))
            b=load_model(a,p,m,pa);parent=load_bundle(pa,old,pp,ms,audits);_,ix=weight_cell(p,m,pa)
            train=records_for(m,'train');cal=records_for(m,'calibration')
            rep=parent['references']['harmonic69/mixed']['transformer'];H=rep.transform(pools.load(train));C=rep.transform(pools.load(cal))
            y=np.array([p['known_labels'].index(r['label']) for r in train]);cy=np.array([p['known_labels'].index(r['label']) for r in cal])
            r=verify_arrays(b,H,C,y,cy,ix,p,a['seed']);r.update(fold_id=a['fold_id'],seed=a['seed'],model_sha256=a['sha256'],
                train_ids_checksum=digest([x['sample_id'] for x in train]),calibration_ids_checksum=digest([x['sample_id'] for x in cal]))
            result.append(r)
    after=verify_sources(pools.root,ms[0])
    if before!=after:raise ValueError('source changed')
    if len({(x['fold_id'],x['seed']) for x in result})!=9:raise ValueError('duplicate fit cells')
    r=seal({'protocol_checksum':p['protocol_checksum'],'locked_checksum':lock['locked_checksum'],'cells':result,
        'status':'VERIFIED_NUMERIC_KNOWN_SOURCES','source_before':before,'source_after':after,'test_numeric_reads':0,
        'acquisition_independence':'UNKNOWN','fresh_final_test':False,'verifier':artifact(Path(__file__))},'source_verification_checksum')
    save_json(output/'source_verified.json',r);return r


def main():
    q=argparse.ArgumentParser(description=__doc__)
    for key in ['protocol','lock','data-root']:q.add_argument('--'+key,type=Path,required=True)
    a=q.parse_args();log,paths=setup_run('fault_type_metric_source_verification')
    r=run(FeatureStore(a.data_root),protocol=read(a.protocol),lock=read(a.lock),output=paths.output_dir)
    log.info('九份bundle來源核對 {}',r['source_verification_checksum'])
if __name__=='__main__':main()
