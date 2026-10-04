"""exp21核心公式／固定遮蔽測試；合成資料，不作研究成績。"""
import copy
import unittest
import numpy as np
from core.fault_type_self_challenging import (challenge_mask, loss_gradient, learning_rate,
    SelfChallengingClassifier, VARIANTS, STEPS, RIDGE)
from core.fault_type_risk_extrapolation import RiskExtrapolationClassifier, risk_design


class TestChallengeFormula(unittest.TestCase):
    def setUp(self):
        self.X = np.array([[1.,2.,3.,4.,5.,6.]]*6)
        self.y = np.zeros(6,dtype=int)
        self.A = np.zeros((7,2))
        self.A[:-1,0] = [5.,4.,-100.,-99.,-98.,-97.]

    def test_signed_not_absolute_mask(self):
        mask, stat = challenge_mask(self.X,self.y,self.A,'signed_gradient',np.random.default_rng(0))
        self.assertEqual(stat['challenged_rows'],2)
        self.assertEqual(stat['muted_features'],4)
        np.testing.assert_array_equal(mask[:2,:2],0)
        np.testing.assert_array_equal(mask[:,2:],1)

    def test_contribution_is_sample_specific(self):
        X=self.X.copy();X[0,0]=0;X[0,1]=10
        A=self.A.copy();A[:-1,0]=[3.,2.,1.,0.,-1.,-2.]
        mask,stat=challenge_mask(X,self.y,A,'contribution',np.random.default_rng(1))
        self.assertEqual(int(np.sum(mask==0)),4)
        self.assertEqual(sum(stat['column_muted_counts']),4)

    def test_ties_exact_count_not_all_muted(self):
        mask,stat=challenge_mask(self.X,self.y,np.zeros_like(self.A),'signed_gradient',np.random.default_rng(0))
        self.assertEqual(stat['muted_features'],4)
        self.assertEqual(stat['nonpositive_drop_fraction'],1)
        np.testing.assert_array_equal(mask[:2,:2],0)
        np.testing.assert_array_equal(mask[2:],1)

    def test_negative_probability_drop_is_retained(self):
        A=self.A.copy();A[:-1,0]=-1
        mask,stat=challenge_mask(self.X,self.y,A,'signed_gradient',np.random.default_rng(0))
        self.assertEqual(stat['nonpositive_drop_fraction'],1)
        self.assertLess(stat['mean_true_probability_drop'],0)

    def test_random_exact_budget_and_same_seed(self):
        a,s=challenge_mask(self.X,self.y,self.A,'random',np.random.default_rng(7))
        b,t=challenge_mask(self.X,self.y,self.A,'random',np.random.default_rng(7))
        np.testing.assert_array_equal(a,b);self.assertEqual(s,t)
        self.assertEqual(s['muted_features'],4)

    def test_unmasked_control(self):
        mask,stat=challenge_mask(self.X,self.y,self.A,'unmasked',np.random.default_rng(0))
        np.testing.assert_array_equal(mask,1);self.assertEqual(stat['challenged_rows'],0)

    def test_gradient_matches_finite_difference(self):
        X=np.array([[1.,-2.],[0.,3.],[-1.,2.]])
        y=np.array([0,1,0]);weights=np.array([.2,.5,.3])
        A=np.array([[.2,-.1],[.3,-.4],[.5,-.2]])
        _,g=loss_gradient(A,X,y,weights)
        for i in range(3):
            for j in range(2):
                ap,am=A.copy(),A.copy();ap[i,j]+=1e-6;am[i,j]-=1e-6
                numerical=(loss_gradient(ap,X,y,weights)[0]-loss_gradient(am,X,y,weights)[0])/2e-6
                self.assertAlmostEqual(g[i,j],numerical,places=7)

    def test_trace_learning_rate_hand_calculation(self):
        X=np.array([[3.,4.],[0.,0.]])
        weights=np.array([.25,.75])
        self.assertAlmostEqual(learning_rate(X,weights),1/(.5*(.25*26+.75)+RIDGE))
        _,g=loss_gradient(np.zeros((3,2)),X,np.array([0,1]),weights)
        np.testing.assert_allclose(g[-1],[.25,-.25])

    def test_wrong_class_nonfinite_and_weights_rejected(self):
        for change in [dict(y=np.full(6,2)),dict(A=np.full_like(self.A,np.nan))]:
            with self.assertRaises(ValueError):
                challenge_mask(self.X,change.get('y',self.y),change.get('A',self.A),'random',np.random.default_rng(0))
        with self.assertRaises(ValueError):learning_rate(self.X,np.ones(6))
        with self.assertRaises(ValueError):loss_gradient(self.A,self.X,self.y,np.zeros(6))


class TestChallengeTraining(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng=np.random.default_rng(123);cls.X=rng.normal(size=(36,4));cls.y=np.arange(36)%3
        cls.env=np.repeat(['6000rpm','8000rpm','11000rpm'],12)
        cls.warm=RiskExtrapolationClassifier(0,42).fit(cls.X,cls.y,cls.env)
        cls.models={v:SelfChallengingClassifier(v,42).fit(cls.X,cls.y,cls.env,cls.warm) for v in VARIANTS}

    def test_fixed_horizon_and_not_convergence_claim(self):
        for v,m in self.models.items():
            self.assertEqual(len(m.history_),STEPS)
            self.assertEqual(m.optimizer_['status'],'FIXED_HORIZON_COMPLETE')
            self.assertTrue(m.optimizer_['converged_not_claimed'])
            self.assertEqual(m.warm_start_checksum_,self.warm.checksum_)

    def test_all_variants_actual_source_replay(self):
        for m in self.models.values():
            self.assertEqual(m.verify_known_source(self.X,self.y,self.env,self.warm)['test_numeric_reads'],0)

    def test_wrong_known_source_seed_warm_rejected(self):
        with self.assertRaises(ValueError):SelfChallengingClassifier(seed=0).fit(self.X,self.y,self.env,self.warm)
        X=self.X.copy();X[0,0]+=.1
        with self.assertRaises(ValueError):SelfChallengingClassifier(seed=42).fit(X,self.y,self.env,self.warm)
        with self.assertRaises(ValueError):SelfChallengingClassifier(seed=42).fit(self.X,self.y,self.env,None)

    def test_resealed_coefficients_caught_by_replay(self):
        m=copy.deepcopy(self.models['contribution']);m.coef_[0,0]+=.1;m.checksum_=m.signature()
        with self.assertRaisesRegex(ValueError,'actual known'):m.verify_known_source(self.X,self.y,self.env,self.warm)

    def test_history_tamper_caught(self):
        m=copy.deepcopy(self.models['random']);m.history_[0]['muted_features']+=1
        with self.assertRaises(ValueError):m.predict(self.X)

    def test_no_query_rpm_or_truth_and_empty_inference(self):
        m=self.models['random'];X=self.X[:4]
        self.assertEqual(m.predict(X).shape,(4,))
        np.testing.assert_allclose(m.predict_proba(X).sum(1),1)
        self.assertEqual(m.predict(np.zeros((0,4))).shape,(0,))
        with self.assertRaises(ValueError):m.predict(np.zeros((2,5)))

    def test_same_seed_repeat_predictions(self):
        m=SelfChallengingClassifier('random',42).fit(self.X,self.y,self.env,self.warm)
        np.testing.assert_array_equal(m.predict(self.X),self.models['random'].predict(self.X))
        self.assertEqual(m.signature(),self.models['random'].signature())

    def test_missing_class_rpm_is_incomplete(self):
        keep=~((self.env=='6000rpm')&(self.y==0))
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):
            SelfChallengingClassifier(seed=42).fit(self.X[keep],self.y[keep],self.env[keep],self.warm)


if __name__=='__main__':unittest.main()
