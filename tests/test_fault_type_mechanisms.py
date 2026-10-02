import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from threadpoolctl import threadpool_limits
from core.fault_type_mechanisms import RPMPartialPooling,BlockGeometry,calibrate,precision,peak_memory_bytes
from core.fault_type_final_guard import seal,verify_seal
from experiments.fault_type_mechanism_registry import ARMS
from experiments.fault_type_mechanism_smoke import fixture
from experiments.fault_type_mechanism_study import infer,check_audit,load_new,fit
from core.fault_type_provenance import save_json
from experiments.fault_type_fixed_smoke import fixture as metadata_fixture
from experiments.fault_type_fixed_calibration import build_protocol
from core.fault_type_fixed_calibration import fixed_manifests


class MechanismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with threadpool_limits(limits=1):cls.parent,cls.new,cls.p,cls.T,cls.r,cls.X,cls.y=fixture()

    def test_budget_complete_arms(self):
        self.assertEqual(len(ARMS)*3*3,81)
        self.assertEqual(len({d['id'] for d in ARMS}),9)

    def test_pool_endpoints(self):
        p0=self.new['models']['P01'];p1=self.new['models']['P03']
        z=self.parent['references']['base75/mixed']['transformer'].transform(self.X)
        for rpm in self.p['rpms']:
            np.testing.assert_allclose(p0.nodes[rpm][0],[z[(self.r==rpm)&(self.y==c)].mean(0) for c in range(6)])
            np.testing.assert_array_equal(p1.nodes[rpm][0],p1.global_means)
            np.testing.assert_array_equal(p1.nodes[rpm][1],p1.global_covariance)
        p5=self.new['models']['P02']
        for rpm in self.p['rpms']:np.testing.assert_allclose(p5.nodes[rpm][0],.5*(p0.nodes[rpm][0]+p1.global_means))

    def test_pool_global_routing_same_features(self):
        obj=self.new['models']['P03'];z=np.ones((3,75))
        np.testing.assert_array_equal(obj.predict(z,self.p['rpms']),np.repeat(obj.predict(z[:1],[self.p['rpms'][0]]),3))

    def test_pool_missing_class(self):
        with self.assertRaises(ValueError):RPMPartialPooling(0,['a','b'],2).fit([[1],[2],[3],[4]],[0,0,1,1],['a','a','b','b'])

    def test_pool_unknown_rpm(self):
        with self.assertRaises(ValueError):self.new['models']['P01'].predict(np.ones((1,75)),['bad'])

    def test_block_hand_formula_and_signed(self):
        g=BlockGeometry(2,[[0],[1]])
        g.dimension=2;mu=np.array([[0.],[2.]])
        g.models=[(mu,np.eye(1),np.array([1.]),np.eye(1)) for _ in range(2)]
        d,bg=g.distances([[0.,0.],[1.,1.],[2.,2.]])
        np.testing.assert_array_equal(d,[[0,4],[1,1],[4,0]])
        np.testing.assert_array_equal(bg,[1,0,1])
        np.testing.assert_array_equal(g.score([[0,0],[2,2]],1),[-1,-1])
        np.testing.assert_array_equal(g.score([[1,1]],0),d[1:2].min(1))
        self.assertEqual(g.predict([[1,1]])[0],0) # tie is class0, not true class.

    def test_no_amplitude_drop(self):
        self.assertEqual(list(map(len,self.new['geometry'].blocks)),[36,30,3])
        self.assertEqual(sorted(sum(self.new['geometry'].blocks,[])),list(range(69)))

    def test_block_invalid_partition(self):
        with self.assertRaises(ValueError):BlockGeometry(2,[[0],[0]]).fit([[0],[1],[2],[3]],[0,0,1,1])

    def test_small_zero_cov_finite(self):
        g=BlockGeometry(2,[[0]]).fit([[0],[0],[1],[1]],[0,0,1,1])
        self.assertTrue(np.isfinite(g.score([[0],[.5],[1]])).all())
        self.assertTrue(np.isfinite(precision(np.zeros((2,2)))).all())

    def test_negative_cov_refused(self):
        with self.assertRaises(ValueError):precision(np.array([[-1.]]))

    def test_empty_calibration_and_signed_quantile(self):
        for s in [[],[float('nan')]]:
            with self.assertRaises(ValueError):calibrate(s)
        self.assertAlmostEqual(calibrate([-10,-5,-1]),-1.4)

    def test_decoupled_exact_controls(self):
        with threadpool_limits(limits=1):r=infer(self.parent,self.new,self.p,self.T,self.r)
        h=self.parent['references']['harmonic69/mixed']['transformer'].transform(self.T)
        np.testing.assert_array_equal(r['D01'][0],self.parent['models']['C17']['mixed']['classifier'].predict(h))
        np.testing.assert_array_equal(r['D01'][0],r['D02'][0])
        np.testing.assert_array_equal(r['D01'][1],r['D03'][1])

    def test_infer_has_no_truth_argument(self):
        import inspect
        self.assertEqual(list(inspect.signature(infer).parameters),['parent','new','p','X','rpms'])
        records=[{'rpm':rpm,'true_label':'oracle'} for rpm in self.r]
        with threadpool_limits(limits=1):a=infer(self.parent,self.new,self.p,self.T,[r['rpm'] for r in records])
        for r in records:r['true_label']='MUTATED'
        with threadpool_limits(limits=1):b=infer(self.parent,self.new,self.p,self.T,[r['rpm'] for r in records])
        for k in a:
            for j in [0,1]:np.testing.assert_array_equal(a[k][j],b[k][j])

    def test_seal_tamper(self):
        p=seal({'arms':ARMS},'checksum');p['arms']=[]
        with self.assertRaises(ValueError):verify_seal(p,'checksum')

    def test_process_peak(self):self.assertGreater(peak_memory_bytes(),0)

    def test_model_path_and_sha_guard_before_unpickle(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'model.joblib';path.write_bytes(b'not a pickle')
            a={'path':str(path),'sha256':'0'*64}
            with self.assertRaisesRegex(ValueError,'root/SHA'):load_new(a,{}, {}, {},folder)
            with self.assertRaisesRegex(ValueError,'root/SHA'):load_new(a,{}, {}, {},Path(folder)/'wrong')

    def test_checkpoint_resume_rejects_protocol_change(self):
        with tempfile.TemporaryDirectory() as folder:
            m={'fold_id':'f'};cell=Path(folder)/'f_seed0';cell.mkdir()
            save_json(cell/'checkpoint.json',seal({'protocol_checksum':'wrong','status':'completed'},'checkpoint_checksum'))
            with patch('experiments.fault_type_mechanism_study.check',return_value=({},[m],{'artifacts':[{'fold_id':'f','seed':0}]},[])),patch('experiments.fault_type_mechanism_study.verify_sources',return_value='same'):
                class Pools:root=folder
                with self.assertRaisesRegex(ValueError,'resume protocol'):fit(Pools(),p={'protocol_checksum':'right'},output=Path(folder))

    def test_actual_manifest_audit_rejects_cal_fit(self):
        with tempfile.TemporaryDirectory() as folder:
            priors,ledger=metadata_fixture(Path(folder));m=fixed_manifests(priors,build_protocol(priors,ledger))[0]
            ids=m['sample_ids']['train'];a={'manifest_checksum':m['manifest_checksum'],'calibration_sample_ids':m['sample_ids']['calibration'],
                'selection_sample_ids':[],'selection_policy':'none','shared_validation_calibration':False,'metric_fit_ids':ids,
                'definition':ARMS[6],'protocol_checksum':'p','dataset_fingerprint':'d','classifier_rpm_fit_ids':{}}
            for key in ['representation_fit_ids','scaler_fit_ids','classifier_fit_ids','reference_fit_ids','classifier_transform_fit_ids','detector_transform_fit_ids','background_fit_ids','prototype_fit_ids']:a[key]=ids.copy()
            p={'protocol_checksum':'p','dataset_fingerprint':'d','arms':ARMS,'rpms':m['expected_rpms']}
            self.assertTrue(check_audit(a,m,p))
            for field in ['background_fit_ids','prototype_fit_ids','classifier_transform_fit_ids','detector_transform_fit_ids']:
                bad=copy.deepcopy(a);bad[field].append(m['sample_ids']['calibration'][0])
                with self.assertRaises(ValueError):check_audit(bad,m,p)
            bad=copy.deepcopy(a);bad['selection_sample_ids']=m['sample_ids']['test'][:1]
            with self.assertRaises(ValueError):check_audit(bad,m,p)
