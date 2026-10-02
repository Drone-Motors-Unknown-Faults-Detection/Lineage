"""Synthetic mathematical/role/lock regression, never research performance."""
import copy
import tempfile
import unittest
from pathlib import Path
import numpy as np
from scipy.special import logsumexp
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from core.fault_type_literature import LiteratureRepresentation,BlendedDiscriminant,NoveltyReference
from core.openset import create_openset_detector
from core.fault_type_accuracy import VIBRATION66
from experiments.fault_type_literature_registry import ARMS,SCORES,classifier
from experiments.fault_type_literature_study import audit_roles,make_rows,verify_rows,metrics


def fixture():
    rng=np.random.default_rng(431);X=rng.normal(size=(120,105));y=np.repeat(np.arange(6),20)
    X[:,15:90]+=y[:,None]*.4
    for off in [15,40,65]:
        X[:,off]=np.abs(X[:,off]);X[:,off+3]=np.abs(X[:,off+3]);X[:,off+7]=X[:,off+9]
        X[:,off+12]=X[:,off]**2;X[:,off+13]=X[:,off+3]**2
        X[:,off+15:off+25]=np.abs(X[:,off+15:off+25])
    return X,y


class LiteratureTests(unittest.TestCase):
    def test_all_representations_train_only_and_finite(self):
        X,y=fixture()
        for name,D in [('base75',75),('base66',66),('signed66',66),('harmonic69',69),('harmonic66',66),('pca20',20),('nca10',10)]:
            model=LiteratureRepresentation(name,0).fit(X,y);checksum=model.checksum();Z=model.transform(X*1.3)
            self.assertEqual(Z.shape,(120,D));self.assertTrue(np.isfinite(Z).all());self.assertEqual(checksum,model.checksum())
            self.assertTrue(set(model.metric_subset_indices)<=set(range(len(X))))
    def test_harmonic_zero_and_scale_behavior(self):
        X,y=fixture();model=LiteratureRepresentation('harmonic69',0).fit(X,y);Y=X.copy()
        for off in [15,40,65]:Y[:,off+15:off+25]*=10
        raw,scaled=model._raw(X),model._raw(Y)
        for off in [15,40,65]:
            indices=[VIBRATION66.index(i) for i in range(off+15,off+25)]
            np.testing.assert_allclose(raw[:,indices],scaled[:,indices]);np.testing.assert_allclose(raw[:,indices].sum(1),1)
            Y[:,off+15:off+25]=0
        self.assertTrue(np.isfinite(model.transform(Y)).all());self.assertFalse(np.allclose(raw[:,-3:],scaled[:,-3:]))
    def test_representation_tamper(self):
        X,y=fixture();m=LiteratureRepresentation('pca20',0).fit(X,y);m.embedding.components_[0,0]+=1
        with self.assertRaisesRegex(ValueError,'tampered'):m.transform(X)
    def test_nca_subset_determinism(self):
        X,y=fixture();a=LiteratureRepresentation('nca10',1).fit(X,y);b=LiteratureRepresentation('nca10',1).fit(X,y)
        np.testing.assert_array_equal(a.transform(X),b.transform(X));self.assertEqual(a.metric_subset_indices,b.metric_subset_indices)
    def test_rda_linear_limit(self):
        X,y=fixture();Z=X[:,15:25];m=BlendedDiscriminant(pooling=1.,shrinkage=.1).fit(Z,y)
        np.testing.assert_allclose(m.precisions_[0],m.precisions_[5]);np.testing.assert_allclose(m.predict_proba(Z).sum(1),1)
    def test_rda_predict_decision_agreement(self):
        X,y=fixture();m=BlendedDiscriminant().fit(X[:,15:25],y)
        np.testing.assert_array_equal(m.predict(X[:,15:25]),m.decision_function(X[:,15:25]).argmax(1))
    def test_invalid_blend(self):
        X,y=fixture()
        with self.assertRaises(ValueError):BlendedDiscriminant(shrinkage=0).fit(X,y)
    def test_registry_exact_budget(self):
        self.assertEqual(len(ARMS),24);self.assertEqual(len(SCORES),22);self.assertEqual((24*2+22)*3*3,630)
    def test_all_classifiers_fit_synthetic(self):
        X,y=fixture()
        for a,r,c,v in ARMS:
            clf=classifier({'classifier':c,'parameter':v},0,6);clf.fit(X[:,15:25],y)
            self.assertTrue(set(clf.predict(X[:,15:25]))<=set(y))
    def novelty(self,kind,parameter=1.):
        X,y=fixture();Z=LiteratureRepresentation('base75',0).fit(X,y).transform(X)
        clf=LinearDiscriminantAnalysis(solver='lsqr',shrinkage='auto',priors=[1/6]*6).fit(Z,y)
        factory=create_openset_detector('mahalanobis').fit(Z,y,Z+.1,y)
        return Z,y,clf,factory,NoveltyReference({'kind':kind,'parameter':parameter},0).fit(Z,y,clf,factory)
    def test_relative_formula_and_negative_threshold(self):
        Z,y,clf,factory,m=self.novelty('relative',2.)
        delta=Z-m.background.location_;expected=m.model.raw_scores(Z).min(1)**2-2*np.einsum('ij,jk,ik->i',delta,m.background.precision_,delta)
        np.testing.assert_allclose(m.raw(Z),expected);m.calibrate(Z)
        self.assertEqual(m.threshold,float(np.quantile(expected,.95)));self.assertTrue(np.isfinite(m.raw(Z)).all())
    def test_energy_actual_logits(self):
        Z,y,clf,factory,m=self.novelty('energy');np.testing.assert_allclose(m.raw(Z),-logsumexp(clf.decision_function(Z),axis=1))
    def test_scalar_quantile_frozen(self):
        for kind in ['pooled','oas','diagonal','iforest','lof','ocsvm','gmm','centers','msp','entropy','margin','fusion','vim']:
            Z,y,clf,factory,m=self.novelty(kind,.25);m.calibrate(Z+.1);threshold=m.threshold
            self.assertTrue(np.isfinite(m.raw(Z)).all());m.raw(Z+5);self.assertEqual(m.threshold,threshold)
    def test_predicted_calibration_not_truth_routed(self):
        Z,y,clf,factory,m=self.novelty('predicted');m.calibrate(Z);self.assertEqual(sum(m.predicted_counts),len(Z));self.assertEqual(m.threshold,1.)
    def test_missing_predicted_group_no_fallback(self):
        Z,y,clf,factory,m=self.novelty('predicted')
        with self.assertRaisesRegex(ValueError,'missing predicted'):m.calibrate(np.repeat(Z[:1],20,axis=0))
    def test_factory_knn_variants(self):
        X,y=fixture()
        for k in [1,5,15]:
            d=create_openset_detector('knn',knn_neighbors=k).fit(X[:,15:25],y,X[:,15:25]+.1,y)
            self.assertEqual(d.models_[0].n_neighbors,k);self.assertTrue(np.isfinite(d.score_samples(X[:,15:25])).all())


def role_fixture():
    records=[{'sample_id':s,'t_code':motor,'rpm':'6000rpm','label':label,'source_file':s+'.csv','source_sha256':'a'*64} for s,motor,label in [('a','T1','8screws'),('b','T2','8screws'),('c','T3','unknown')]]
    m={'records':records,'sample_ids':{'train':['a'],'calibration':['b'],'test':['c']},'motor_roles':{'train':'T1','calibration':'T2','test':'T3'},'healthy_label':'8screws','known_fault_labels':[],'manifest_checksum':'m'}
    audit={'manifest_checksum':'m','metric_fit_ids':['a'],'calibration_sample_ids':['b'],'selection_sample_ids':[],'selection_policy':'none','shared_validation_calibration':False}
    for field in ['representation_fit_ids','scaler_fit_ids','classifier_fit_ids','reference_fit_ids']:audit[field]=['a']
    return m,audit


class LiteratureRoleTests(unittest.TestCase):
    def test_valid_no_selection(self):
        m,a=role_fixture();self.assertEqual(audit_roles(a,m,'mixed')['test'],['c'])
    def test_cal_in_every_fit_rejected(self):
        for field in ['representation_fit_ids','scaler_fit_ids','classifier_fit_ids','reference_fit_ids','metric_fit_ids']:
            m,a=role_fixture();a[field]=['b']
            with self.assertRaises(ValueError):audit_roles(a,m,'mixed')
    def test_test_fit_rejected(self):
        m,a=role_fixture();a['reference_fit_ids']=['c']
        with self.assertRaises(ValueError):audit_roles(a,m,'mixed')
    def test_unknown_cal_rejected(self):
        m,a=role_fixture();m['records'][1]['label']='unknown'
        with self.assertRaisesRegex(ValueError,'unknown'):audit_roles(a,m,'mixed')
    def test_motor_overlap_rejected(self):
        m,a=role_fixture();m['motor_roles']['test']='T1'
        with self.assertRaisesRegex(ValueError,'motor'):audit_roles(a,m,'mixed')
    def test_global_selection_rejected(self):
        m,a=role_fixture();a['selection_sample_ids']=['c']
        with self.assertRaisesRegex(ValueError,'selector'):audit_roles(a,m,'mixed')
    def test_shared_cal_rejected(self):
        m,a=role_fixture();a['shared_validation_calibration']=True
        with self.assertRaisesRegex(ValueError,'selector'):audit_roles(a,m,'mixed')
    def test_signed_reject_comparison(self):
        m,a=role_fixture();rows=make_rows(m['records'],np.array([0,0,0]),np.array([-2.,-1.,0.]),-1.,['8screws'],'test','sha','p','l')
        self.assertEqual([r['is_unknown'] for r in rows],[False,False,True]);self.assertTrue(all(r['historical_test_exposed'] for r in rows))


class LiteratureSavedPredictionTests(unittest.TestCase):
    def fixture(self):
        from core.fault_type_final_guard import digest
        m,_=role_fixture();m['sample_ids']['test']=['a','b','c'];m['records'][1]['label']='1screws'
        protocol={'known_labels':['8screws','1screws'],'unknown_labels':['unknown'],'rpms':['6000rpm'],'protocol_checksum':'p'};lock={'locked_checksum':'l'}
        rows=make_rows(m['records'],np.array([0,1,0]),np.array([.2,.3,2.]),1.,protocol['known_labels'],'C01/mahalanobis','sha','p','l')
        run={'arm_id':'C01','score_id':'mahalanobis','test_ids_checksum':digest(m['sample_ids']['test']),'model_artifact':{'sha256':'sha'},'threshold':1.}
        run.update(metrics(rows,protocol['known_labels'],protocol['unknown_labels'],protocol['rpms']))
        return rows,run,m,protocol,lock
    def test_saved_prediction_valid(self):
        self.assertIn('prediction_value_checksum',verify_rows(*self.fixture()))
    def test_saved_id_tamper(self):
        rows,r,m,p,l=self.fixture();rows[0]['sample_id']='copy-alias'
        with self.assertRaises(ValueError):verify_rows(rows,r,m,p,l)
    def test_saved_source_sha_tamper(self):
        rows,r,m,p,l=self.fixture();rows[0]['source_sha256']='b'*64
        with self.assertRaises(ValueError):verify_rows(rows,r,m,p,l)
    def test_saved_model_sha_tamper(self):
        rows,r,m,p,l=self.fixture();rows[0]['model_sha256']='other'
        with self.assertRaises(ValueError):verify_rows(rows,r,m,p,l)
    def test_saved_unknown_classifier_label(self):
        rows,r,m,p,l=self.fixture();rows[0]['predicted_known_class']='unknown'
        with self.assertRaises(ValueError):verify_rows(rows,r,m,p,l)
    def test_saved_exposure_cannot_clear(self):
        rows,r,m,p,l=self.fixture();rows[0]['historical_test_exposed']=False
        with self.assertRaises(ValueError):verify_rows(rows,r,m,p,l)
    def test_saved_score_direction_tamper(self):
        rows,r,m,p,l=self.fixture();rows[0]['is_unknown']=True
        with self.assertRaises(ValueError):verify_rows(rows,r,m,p,l)
    def test_saved_summary_tamper(self):
        rows,r,m,p,l=self.fixture();r['rpm_metrics'][0]['samples']=99
        with self.assertRaises(ValueError):verify_rows(rows,r,m,p,l)


if __name__=='__main__':unittest.main()
