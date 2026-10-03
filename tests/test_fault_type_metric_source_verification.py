"""實驗13來源重建的破壞性輸入測試，僅使用合成樣本。"""
import copy
import unittest
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from threadpoolctl import threadpool_limits
from core.fault_type_metric_classifiers import PrototypeClassifier,MarginEnergyClassifier,weight_transform
from core.openset import create_openset_detector
from experiments.fault_type_metric_classification import PARAMS
from experiments.fault_type_metric_source_verification import verify_arrays


class MetricSourceTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(42);self.y=np.repeat([0,1],8);self.cy=np.repeat([0,1],3)
        self.H=rng.normal(size=(16,4))+self.y[:,None]*3;self.C=rng.normal(size=(6,4))+self.cy[:,None]*3
        self.ix=np.arange(16);self.p={'factory_parameters':{'confidence':.95,'knn_neighbors':5,'mahalanobis_method':'ledoit_wolf'}}
        self.b={'weights':[1.,2.,0.,.5],'models':{},'detectors':{}}
        with threadpool_limits(limits=1):
            for geom in ['identity','metric']:
                Z=self.H if geom=='identity' else weight_transform(self.H,self.b['weights']);C=self.C if geom=='identity' else weight_transform(self.C,self.b['weights'])
                for part in ['all','subset']:self.b['models'][geom+'_'+part]=KNeighborsClassifier(**PARAMS['neighbors']).fit(Z,self.y)
                self.b['models'][geom+'_mean']=PrototypeClassifier(1,0).fit(Z,self.y)
                if geom=='metric':self.b['models']['metric_multi']=PrototypeClassifier(3,0).fit(Z,self.y)
                for det in ['mahalanobis','knn']:self.b['detectors'][geom+'/'+det]=create_openset_detector(det,**self.p['factory_parameters']).fit(Z,self.y,C,self.cy)
            self.b['models']['metric_energy']=MarginEnergyClassifier().fit(self.H,self.y,self.b['weights'])
        self.b=copy.deepcopy(self.b)

    def verify(self):
        with threadpool_limits(limits=1):return verify_arrays(self.b,self.H,self.C,self.y,self.cy,self.ix,self.p,0)

    def test_exact_source(self):self.assertTrue(self.verify()['numeric_exact'])
    def test_calibration_in_classifier(self):
        self.b['models']['identity_all']._fit_X[0]=self.C[0]
        with self.assertRaises(ValueError):self.verify()
    def test_calibration_in_knn_reference(self):
        self.b['detectors']['identity/knn'].models_[0].neighbors._fit_X[0]=self.C[0]
        with self.assertRaises(ValueError):self.verify()
    def test_calibration_in_covariance(self):
        self.b['detectors']['identity/mahalanobis']=create_openset_detector('mahalanobis',**self.p['factory_parameters']).fit(np.vstack([self.H,self.C]),np.r_[self.y,self.cy],self.C,self.cy)
        with self.assertRaises(ValueError):self.verify()
    def test_calibration_in_prototype(self):
        self.b['models']['identity_mean'].prototypes_[0]=self.C[0]
        with self.assertRaises(ValueError):self.verify()
    def test_energy_reference_altered(self):
        self.b['models']['metric_energy'].X_[0]=self.C[0]
        with self.assertRaises(ValueError):self.verify()
    def test_calibration_quantile_altered(self):
        self.p['factory_parameters']['confidence']=.9
        with self.assertRaises(ValueError):self.verify()

if __name__=='__main__':unittest.main()
