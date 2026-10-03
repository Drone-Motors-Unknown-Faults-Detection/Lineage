"""實驗13：公式、來源邊界與固定協定測試。"""
import copy
import unittest
from unittest.mock import patch
import numpy as np
from core.fault_type_metric_classifiers import weight_transform,PrototypeClassifier,MarginEnergyClassifier
from experiments.fault_type_metric_classification import check_audits,expected_audits,ARMS,PARAMS


class MetricClassifierTests(unittest.TestCase):
    def setUp(self):
        self.X=np.array([[0,0],[.1,.2],[.2,.1],[.3,.3],[4,0],[4.1,.2],[4.2,.1],[4.3,.3]],float)
        self.y=np.repeat([0,1],4)

    def test_weight_squared_distance(self):
        w=np.array([2.,0.]);z=weight_transform(self.X,w)
        self.assertAlmostEqual(np.sum((z[0]-z[4])**2),32.)

    def test_invalid_weights(self):
        for w in [[1,-1],[1,float('nan')],[1]]:
            with self.assertRaises(ValueError):weight_transform(self.X,w)

    def test_mean_and_class_order(self):
        model=PrototypeClassifier().fit(self.X,self.y+3)
        np.testing.assert_allclose(model.prototypes_,[[.15,.15],[4.15,.15]])
        np.testing.assert_array_equal(model.predict(self.X),self.y+3)

    def test_prototype_tamper(self):
        model=PrototypeClassifier().fit(self.X,self.y);model.prototypes_[0,0]+=1
        with self.assertRaises(ValueError):model.predict(self.X)

    def test_multicenter_reproducible(self):
        a=PrototypeClassifier(3,42).fit(self.X,self.y);b=PrototypeClassifier(3,42).fit(self.X,self.y)
        self.assertEqual(a.checksum,b.checksum);self.assertEqual(len(a.prototypes_),6)

    def test_energy_three_terms_manual(self):
        w=np.array([.5,2.]);model=MarginEnergyClassifier(batch_size=1).fit(self.X,self.y,w)
        queries=np.array([[2,.2],[4.2,1.]])
        expected=[]
        for x in queries:
            vals=[]
            for c in [0,1]:
                same=np.flatnonzero(self.y==c);other=np.flatnonzero(self.y!=c)
                target=same[np.argsort(np.sum((self.X[same]-x)**2,1),kind='stable')[:3]]
                distance=lambda a,b:float(np.sum((a-b)**2*w))
                pull=sum(distance(x,self.X[j]) for j in target)
                outgoing=sum(max(1+distance(x,self.X[j])-distance(x,self.X[l]),0) for j in target for l in other)
                incoming=sum(max(1+distance(self.X[i],self.X[j])-distance(self.X[i],x),0) for i in other for j in model.targets_[i])
                vals.append(.5*pull+.5*(outgoing+incoming))
            expected.append(vals)
        np.testing.assert_allclose(model.energies(queries),expected,rtol=1e-12)

    def test_energy_batch_invariant(self):
        a=MarginEnergyClassifier(batch_size=1).fit(self.X,self.y,[1,1]);b=MarginEnergyClassifier().fit(self.X,self.y,[1,1])
        np.testing.assert_allclose(a.energies(self.X),b.energies(self.X),rtol=1e-12)

    def test_energy_targets_original_space(self):
        a=MarginEnergyClassifier().fit(self.X,self.y,[1,0]);b=MarginEnergyClassifier().fit(self.X,self.y,[0,1])
        np.testing.assert_array_equal(a.targets_,b.targets_)

    def test_energy_reference_tamper(self):
        a=MarginEnergyClassifier().fit(self.X,self.y,[1,1]);a.y_[0]=7
        with self.assertRaises(ValueError):a.predict(self.X)

    def test_energy_input_unchanged(self):
        x=self.X.copy();a=MarginEnergyClassifier().fit(x,self.y,[1,1]);a.predict(self.X)
        np.testing.assert_array_equal(a.X_,self.X);np.testing.assert_array_equal(x,self.X)

    def test_insufficient_targets(self):
        with self.assertRaises(ValueError):MarginEnergyClassifier().fit(self.X[:6],self.y[:6],[1,1])

    def test_fixed_matrix(self):
        self.assertEqual(len(ARMS)*3*3,108);self.assertEqual(PARAMS['neighbors']['n_neighbors'],5)
        self.assertEqual(ARMS[0]['detector'],'C02/M');self.assertEqual(ARMS[-1]['detector'],'metric/knn')

    def test_audit_prohibits_cal_reference_and_selection(self):
        train=[{'sample_id':'train'+str(i)} for i in range(4)];cal=[{'sample_id':'cal'}]
        p={'arms':ARMS,'protocol_checksum':'p','dataset_fingerprint':'f'}
        m={'manifest_checksum':'m','motor_roles':{'train':'T1','calibration':'T2','test':'T3'}};pa={'sha256':'parent','seed':0}
        with patch('experiments.fault_type_metric_classification.records_for',side_effect=lambda m,r:train if r=='train' else cal):
            a=expected_audits(p,m,pa,[0,2]);check_audits(a,p,m,pa,[0,2])
            for key in ['classifier_fit_ids','metric_fit_ids','reference_fit_ids','representation_fit_ids','scaler_fit_ids','selection_sample_ids']:
                bad=copy.deepcopy(a);bad[1][key].append('cal')
                with self.assertRaises(ValueError):check_audits(bad,p,m,pa,[0,2])

    def test_empty_energy_queries(self):
        a=MarginEnergyClassifier().fit(self.X,self.y,[1,1]);self.assertEqual(a.energies(np.empty((0,2))).shape,(0,2))

if __name__=='__main__':unittest.main()
