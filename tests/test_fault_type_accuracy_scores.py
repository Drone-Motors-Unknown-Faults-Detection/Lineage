import unittest
import numpy as np
from sklearn.covariance import LedoitWolf
from sklearn.metrics import roc_auc_score
from core.fault_type_accuracy_scores import PooledWithinLW, ResearchScore
from experiments.fault_type_accuracy_registry import SCORES


class AccuracyScoreTests(unittest.TestCase):
    def test_pooled_within_class_mean_covariance_and_distance_units(self):
        X=np.array([[0,1],[2,3],[100,101],[102,103]],float);y=np.array([0,0,1,1])
        p=PooledWithinLW().fit(X,y,2)
        np.testing.assert_allclose(p.means,[[1,2],[101,102]])
        residual=X-p.means[y]
        np.testing.assert_allclose(p.covariance.covariance_,LedoitWolf(assume_centered=True).fit(residual).covariance_)
        raw=p.raw_scores(np.array([[1,2],[101,102]],float))
        self.assertEqual(raw[0,0],0)
        expected=np.sqrt(np.array([100,100])@p.covariance.precision_@np.array([100,100]))
        self.assertAlmostEqual(raw[0,1],expected)
        with self.assertRaises(ValueError):PooledWithinLW().fit(X,y,3)

    def test_global_calibration_uses_min_raw_not_own_class(self):
        raw=np.array([[100,1],[200,2],[3,300],[4,400]],float);y=np.array([0,0,1,1])
        global_score=ResearchScore(SCORES[0]).calibrate(raw,y)
        class_score=ResearchScore(SCORES[1]).calibrate(raw,y)
        self.assertAlmostEqual(global_score.thresholds[0],3.85)
        np.testing.assert_allclose(class_score.thresholds,[195,395])
        values=global_score.details(raw)
        np.testing.assert_allclose(values['score'],raw.min(1)/3.85)

    def test_conformal_ties_exact_alpha_boundary_and_set_sizes(self):
        raw=np.column_stack([np.arange(19),np.arange(19)]).astype(float)
        y=np.array([0]*19+[1]*19)
        cal=np.vstack([raw,raw]);score=ResearchScore(SCORES[4]).calibrate(cal,y)
        result=score.details(np.array([[18,18],[19,19],[0,19]],float))
        np.testing.assert_allclose(result['p_values'],[[.1,.1],[.05,.05],[1,.05]])
        np.testing.assert_array_equal(result['reject'],[False,True,False])
        np.testing.assert_array_equal(result['candidate_size'],[2,0,1])
        np.testing.assert_allclose(result['score'],1-result['p_values'].max(1))

    def test_conformal_small_sample_resolution_and_missing_cal(self):
        score=ResearchScore(SCORES[5]).calibrate(np.ones((2,2)),np.array([0,1]))
        self.assertEqual(score.summaries()['minimum_p'],[.5,.5])
        self.assertTrue(all(score.summaries()['resolution_cannot_reject_at_alpha']))
        self.assertFalse(score.details(np.full((1,2),100.))['reject'][0])
        with self.assertRaises(ValueError):ResearchScore(SCORES[4]).calibrate(np.ones((2,2)),np.array([0,0]))

    def test_zero_threshold_finite_and_global_monotone_auroc(self):
        zero=ResearchScore(SCORES[0]).calibrate(np.zeros((2,2)),np.array([0,1]))
        self.assertTrue(np.isfinite(zero.details(np.zeros((2,2)))['score']).all())
        self.assertFalse(zero.details(np.zeros((1,2)))['reject'][0])
        score=ResearchScore(SCORES[0]).calibrate(np.array([[1,2],[4,3]],float),np.array([0,1]))
        raw=np.array([[1,2],[4,3],[2,4],[5,6]],float);truth=[0,0,1,1]
        self.assertEqual(roc_auc_score(truth,raw.min(1)),roc_auc_score(truth,score.details(raw)['score']))

    def test_nonfinite_wrong_dimension_and_direction(self):
        with self.assertRaises(ValueError):ResearchScore(SCORES[0]).calibrate(np.full((2,2),np.nan),[0,1])
        score=ResearchScore(SCORES[4]).calibrate(np.ones((2,2)),np.array([0,1]))
        with self.assertRaises(ValueError):score.details(np.ones((2,3)))
        self.assertGreater(score.details(np.full((1,2),100.))['score'][0],score.details(np.zeros((1,2)))['score'][0])


if __name__=='__main__':unittest.main()
