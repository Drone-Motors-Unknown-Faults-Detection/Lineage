"""局部 scatter、秩、重複點、封存及來源防護。"""
import unittest
import copy
from dataclasses import replace
import numpy as np
from threadpoolctl import threadpool_limits
from core.openset import create_openset_detector
from core.fault_type_local_fisher import affinity_weights, scatter, LocalProjection
from experiments.fault_type_local_fisher import fit_representation, verify_numeric


class LocalFisherTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        self.X = rng.normal(size=(60, 24)); self.y = np.repeat(np.arange(3), 20)
        self.X[:, 0] += self.y*4

    def test_pairwise_scatter(self):
        w,b,_,_=affinity_weights(self.X,self.y)
        for matrix in [w,b]:
            reference = np.zeros((24,24))
            for i in range(60):
                for j in range(60):
                    delta=self.X[i]-self.X[j]; reference += .5*matrix[i,j]*np.outer(delta,delta)
            np.testing.assert_allclose(scatter(self.X,matrix),reference,rtol=1e-11,atol=1e-11)

    def test_class_renaming(self):
        w,b,_,_=affinity_weights(self.X,self.y)
        ww,bb,_,_=affinity_weights(self.X,np.array(['c','a','b'])[self.y])
        np.testing.assert_array_equal(w,ww);np.testing.assert_array_equal(b,bb)

    def test_affinity_locality(self):
        w,b,s,_=affinity_weights(self.X,self.y)
        self.assertTrue((s>0).all());self.assertTrue((np.diag(w)==0).all())
        self.assertTrue((w[self.y[:,None]!=self.y[None,:]]==0).all())
        self.assertTrue((b[self.y[:,None]!=self.y[None,:]]==1/60).all())

    def test_replay_both_ranks(self):
        for kind in ['pca','lfda']:
            for rank in [10,20]:
                a=LocalProjection(kind,rank).fit(self.X,self.y);b=LocalProjection(kind,rank).fit(self.X,self.y)
                np.testing.assert_array_equal(a.transform(self.X),b.transform(self.X))
                self.assertEqual(a.transform(self.X[:0]).shape,(0,rank))
                if kind=='lfda':self.assertLess(a.diagnostics_['relative_eigen_residual'],1e-7)

    def test_pca_label_invariance(self):
        a=LocalProjection('pca',10).fit(self.X,self.y);b=LocalProjection('pca',10).fit(self.X,self.y[::-1])
        np.testing.assert_array_equal(a.transform(self.X),b.transform(self.X))

    def test_zero_scale(self):
        w,b,s,_=affinity_weights(np.zeros((60,24)),self.y)
        self.assertTrue(np.isfinite(w).all());self.assertTrue(np.isfinite(b).all());self.assertTrue((s>0).all())
        with self.assertRaises(ValueError):LocalProjection('lfda',10).fit(np.zeros((60,24)),self.y)

    def test_insufficient_neighbor(self):
        with self.assertRaises(ValueError):affinity_weights(self.X[:21],np.repeat(np.arange(3),7))

    def test_tampered_projection(self):
        a=LocalProjection('lfda',10).fit(self.X,self.y);a.components_[0,0]+=1
        with self.assertRaises(ValueError):a.transform(self.X)

    def test_nonfinite_and_shape(self):
        for x in [np.full((60,24),np.nan),self.X[:,0]]:
            with self.assertRaises(ValueError):LocalProjection('lfda',10).fit(x,self.y)


class ProjectionSourceTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(42);self.H=rng.normal(size=(60,24));self.C=rng.normal(size=(60,24))+4
        self.y=np.repeat(np.arange(3),20);self.ix=np.arange(60)
        self.p={'known_labels':['a','b','c'],'factory_parameters':{'confidence':.95,'knn_neighbors':5,'mahalanobis_method':'ledoit_wolf'}}
        self.d={'id':'pca10','kind':'pca','dimension':10}
        with threadpool_limits(limits=1):self.node=copy.deepcopy(fit_representation(self.d,self.H,self.C,self.y,self.y,self.ix,self.p))

    def verify(self):
        with threadpool_limits(limits=1):return verify_numeric(self.node,self.d,self.H,self.C,self.y,self.y,self.ix,self.p)

    def test_exact(self):self.assertIn('projection_checksum',self.verify())

    def test_calibration_in_projection(self):
        self.node['projection']=LocalProjection('pca',10).fit(self.C,self.y)
        with self.assertRaises(ValueError):self.verify()

    def test_calibration_in_classifier(self):
        self.node['classifiers']['knn']._fit_X[0]=self.node['projection'].transform(self.C)[0]
        with self.assertRaises(ValueError):self.verify()

    def test_calibration_in_lda(self):
        self.node['classifiers']['lda'].fit(self.node['projection'].transform(self.C),self.y)
        with self.assertRaises(ValueError):self.verify()

    def test_calibration_in_reference(self):
        for method in ['mahalanobis','knn']:
            original=self.node['detectors'][method];z=self.node['projection'].transform(self.C)
            self.node['detectors'][method]=create_openset_detector(method,**self.p['factory_parameters']).fit(z,self.y,z,self.y)
            with self.assertRaises(ValueError):self.verify()
            self.node['detectors'][method]=original

    def test_calibration_quantile(self):
        model=self.node['detectors']['mahalanobis'];model.distributions_[0]=replace(model.distributions_[0],threshold=model.distributions_[0].threshold+1)
        with self.assertRaises(ValueError):self.verify()


if __name__=='__main__':unittest.main()
