import unittest
import numpy as np
from scipy.optimize import check_grad
from core.fault_type_continuous import margin_problem,margin_loss_grad,DiagonalMargin,GainRepresentation,stratified_subset


class ContinuousTests(unittest.TestCase):
    def data(self):
        rng=np.random.default_rng(0);return rng.normal(size=(12,3)),np.repeat([0,1,2],4)
    def test_analytic_gradient(self):
        X,y=self.data();p=margin_problem(X,y);w=np.array([.4,.8,1.1])
        err=check_grad(lambda z:margin_loss_grad(z,p)[0],lambda z:margin_loss_grad(z,p)[1],w)
        self.assertLess(err,1e-6)
    def test_hand_loss(self):
        X=np.array([[0.],[.5],[2.],[2.5]]);p=margin_problem(X,[0,0,1,1],k=1)
        value,g=margin_loss_grad(np.ones(1),p)
        self.assertAlmostEqual(value,.125);self.assertAlmostEqual(g[0],.125)
    def test_nonnegative_deterministic_and_decreasing(self):
        X,y=self.data();a=DiagonalMargin().fit(X,y);b=DiagonalMargin().fit(X,y)
        self.assertTrue((a.weights>=0).all());self.assertTrue(np.array_equal(a.weights,b.weights))
        self.assertLessEqual(a.optimizer['final_loss'],a.optimizer['initial_loss'])
    def test_metric_requires_class_support(self):
        with self.assertRaises(ValueError):margin_problem(np.ones((4,2)),[0,0,1,1])
    def test_subset_source_and_seed(self):
        y=np.repeat([0,1],80);rpm=np.tile(np.repeat(['a','b'],40),2)
        a=stratified_subset(y,rpm,0);self.assertEqual(len(a),80)
        self.assertTrue(np.array_equal(a,stratified_subset(y,rpm,0)))
        self.assertFalse(np.array_equal(a,stratified_subset(y,rpm,1)))
    def formal(self):
        return np.random.default_rng(1).uniform(.1,4,size=(20,105))
    def test_dimensions_and_gain_invariance(self):
        X=self.formal();Y=X.copy()
        for off,gain in zip([15,40,65],[.2,3,5]):
            for i in [0,1,3,5,10,11,14,*range(15,25)]:Y[:,off+i]*=gain
        for d in [63,66]:
            t=GainRepresentation(d).fit(X);self.assertEqual(t.raw(X).shape,(20,d));np.testing.assert_allclose(t.raw(X),t.raw(Y),atol=1e-12)
        t=GainRepresentation(69).fit(X);self.assertFalse(np.allclose(t.raw(X),t.raw(Y)))
    def test_transform_train_only_no_truth_and_tamper(self):
        X=self.formal();t=GainRepresentation(66).fit(X);before=t.checksum;t.transform(X*1.5)
        self.assertEqual(before,t.signature());t.rms_floor[0]*=2
        with self.assertRaises(ValueError):t.transform(X)
    def test_zero_rms_finite_and_negative_invalid(self):
        X=self.formal();X[:,[15,40,65]]=0;t=GainRepresentation(63).fit(X);self.assertTrue(np.isfinite(t.transform(X)).all())
        X[:,15]=-1
        with self.assertRaises(ValueError):GainRepresentation(63).fit(X)
