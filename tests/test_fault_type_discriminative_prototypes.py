import unittest
import pickle
import copy
import numpy as np
from scipy.optimize import check_grad
from core.fault_type_discriminative_prototypes import DiscriminativePrototypes,relative_objective,calibrate_ambiguity
from core.fault_type_metrics_v2 import decision
from core.fault_type_final_guard import seal
from experiments.fault_type_discriminative_prototypes import fit_node,verify_node,validate_lock


class DiscriminativePrototypeTests(unittest.TestCase):
    def data(self):
        rng=np.random.default_rng(2)
        X=np.r_[rng.normal(-2,.2,(12,3)),rng.normal(2,.2,(12,3))]
        return X,np.repeat([0,1],12),np.arange(24)

    def test_gradient(self):
        X,y,ix=self.data();W=np.array([[-1.4,-1.7,-2.4],[1.3,2.3,1.8]])
        for anchor in [0.,.01]:
            args=(X,y,np.array([0,1]),W+.2,anchor)
            error=check_grad(lambda w:relative_objective(w.reshape(W.shape),*args)[0],
                lambda w:relative_objective(w.reshape(W.shape),*args)[1].ravel(),W.ravel())
            self.assertLess(error,1e-6)

    def test_zero_distance_and_tie(self):
        W=np.zeros((2,2));X=np.zeros((2,2));y=np.array([0,1])
        value,grad=relative_objective(W,X,y,y,W)
        self.assertEqual(value,.5);np.testing.assert_array_equal(grad,0)
        m=DiscriminativePrototypes().fit(X,y,np.arange(2))
        np.testing.assert_array_equal(m.predict(X),0)
        np.testing.assert_array_equal(m.ambiguity(X),1)

    def test_static_and_replay(self):
        X,y,ix=self.data();m=DiscriminativePrototypes(3,'static',3).fit(X,y,ix)
        n=DiscriminativePrototypes(3,'static',3).fit(X,y,ix)
        self.assertEqual(m.signature(),n.signature())
        self.assertTrue(np.array_equal(m.predict(X),y))
        self.assertTrue(np.array_equal(m.predict(X),pickle.loads(pickle.dumps(m)).predict(X)))

    def test_optimizer_and_anchor(self):
        X,y,ix=self.data()
        for variant in ['glvq','anchored']:
            m=DiscriminativePrototypes(1,variant,0).fit(X,y,ix)
            self.assertTrue(m.optimizer_['success'])
            self.assertLessEqual(m.optimizer_['final_loss'],m.optimizer_['initial_loss']+1e-12)
            self.assertTrue(np.array_equal(m.predict(X),y))

    def test_nonconvergence_preserved(self):
        X,y,ix=self.data();m=DiscriminativePrototypes(1,'glvq').fit(X,y,ix,options={'maxiter':0})
        self.assertFalse(m.optimizer_['success']);self.assertTrue(np.isfinite(m.optimizer_['final_loss']))
        with self.assertRaises(ValueError):m.predict(X)

    def test_ambiguity_and_quantile(self):
        X,y,ix=self.data();m=DiscriminativePrototypes().fit(X,y,ix)
        score=m.ambiguity(X)
        self.assertTrue(((score>=0)&(score<=1)).all())
        self.assertEqual(calibrate_ambiguity(m,X),float(np.quantile(score,.95,method='linear')))
        self.assertEqual(decision('8screws',0,0),'8screws')
        self.assertEqual(decision('8screws',1,0),'unknown')

    def test_mutation_rejected(self):
        X,y,ix=self.data();m=DiscriminativePrototypes().fit(X,y,ix);m.prototypes_[0,0]+=.1
        with self.assertRaises(ValueError):m.predict(X)

    def test_invalid_sources(self):
        X,y,ix=self.data()
        for bad in [np.array([],int),np.array([0,0,15]),np.array([-1,13]),np.array([0.,13.])]:
            with self.assertRaises(ValueError):DiscriminativePrototypes().fit(X,y,bad)
        with self.assertRaises(ValueError):DiscriminativePrototypes().fit(X,np.zeros(len(y)),ix)

    def test_empty_and_nonfinite_query(self):
        X,y,ix=self.data();m=DiscriminativePrototypes().fit(X,y,ix)
        self.assertEqual(len(m.predict(np.empty((0,3)))),0)
        self.assertEqual(len(m.ambiguity(np.empty((0,3)))),0)
        with self.assertRaises(ValueError):m.predict([[np.nan]*3])


class DiscriminativeSourceTests(unittest.TestCase):
    def setUp(self):
        self.X,self.y,self.ix=DiscriminativePrototypeTests().data()
        self.C=self.X+.3
        self.definition={'centers':1,'variant':'static'}
        self.node=fit_node(self.definition,self.X,self.C,self.y,self.ix,0)

    def verify(self):return verify_node(self.node,self.definition,self.X,self.C,self.y,self.ix,0)

    def test_exact_numeric_source(self):self.assertEqual(self.verify()['status'],'completed')

    def test_calibration_cannot_initialize_classifier(self):
        self.node=fit_node(self.definition,self.C,self.C,self.y,self.ix,0)
        with self.assertRaises(ValueError):self.verify()

    def test_calibration_threshold_tamper(self):
        self.node['threshold']+=.1
        with self.assertRaises(ValueError):self.verify()

    def test_train_subset_tamper(self):
        self.node['model']=DiscriminativePrototypes().fit(self.X,self.y,np.r_[0:10,12:22])
        with self.assertRaises(ValueError):self.verify()

    def test_actual_mutation_even_resealed(self):
        self.node['model'].prototypes_[0,0]+=.2
        self.node['model'].checksum_=self.node['model'].signature()
        with self.assertRaises(ValueError):self.verify()

    def test_selector_and_inventory_refused(self):
        p={'protocol_checksum':'p','environment':{},'folds':[{'fold_id':str(i)} for i in range(3)],'seeds':[0,1,2]}
        lock={'protocol_checksum':'p','environment':{},'selection_policy':'none','selection_sample_ids':[],
            'artifacts':[{'fold_id':str(i),'seed':s} for i in range(3) for s in range(3)]}
        validate_lock(p,seal(lock,'locked_checksum'))
        for mutation in ['selection','inventory']:
            bad=copy.deepcopy(lock)
            if mutation=='selection':bad['selection_sample_ids']=['exposed_test']
            else:bad['artifacts'][-1]=bad['artifacts'][0]
            with self.assertRaises(ValueError):validate_lock(p,seal(bad,'locked_checksum'))


if __name__=='__main__':unittest.main()
