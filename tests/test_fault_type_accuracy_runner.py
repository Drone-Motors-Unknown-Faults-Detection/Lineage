"""Synthetic identities/fit spies, never research scores."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import joblib
import numpy as np
from sklearn.preprocessing import RobustScaler
from core.fault_type_fixed_calibration import fixed_manifests
from core.fault_type_final_guard import digest
from core.fault_type_accuracy_pipeline import records_for, validate_node_audit
from experiments.fault_type_fixed_smoke import fixture
from experiments.fault_type_fixed_calibration import build_protocol, load_bound_model
from experiments.fault_type_accuracy_registry import ARMS, SCORES, classifier
from experiments.fault_type_openset import DETECTOR_CONFIG
from experiments.fault_type_accuracy_study import fit_a, fit_b


class AccuracyRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.root=Path(cls.temp.name)
        priors,ledger=fixture(cls.root/'fixture');p=build_protocol(priors,ledger)
        cls.manifests=fixed_manifests(priors,p)
        known=[p['healthy_label'],*sorted(p['known_fault_labels'])]
        cls.registry={'arms':[ARMS[0],ARMS[1],ARMS[5]],'known_labels':known,'seeds':[0],
            'expected_rpms':p['expected_rpms'],'rules':{'minimum_reference_per_class':5,'conformal_alpha':.05},'score_arms':SCORES,
            'registry_checksum':'synthetic','dataset_fingerprint':p['dataset_fingerprint'],
            'scaler_resolved':RobustScaler().get_params(),'detectors':DETECTOR_CONFIG,
            'classifier_resolved':{name:{'0':classifier(name,0,6).get_params()} for name in ['linear','extra_trees']}}
        cls.calls=[]
        class Spy:
            def load(inner, rows):
                if any(r['label'] not in known for r in rows):raise ValueError('unknown unexpectedly loaded')
                if len({r['rpm'] for r in rows})!=1:raise ValueError('RPM mixing')
                cls.calls.append([r['sample_id'] for r in rows])
                X=np.random.default_rng(1).normal(size=(len(rows),105))
                X+=np.array([known.index(r['label']) for r in rows])[:,None]*.15
                return X
        cls.output=cls.root/'models';cls.output.mkdir()
        cls.artifacts,cls.audits,cls.failures,cls.counts=fit_a(Spy(),registry=cls.registry,manifests=cls.manifests,output=cls.output,code_head='synthetic')
        cls.a_calls=len(cls.calls)
        cls.b_artifacts,cls.b_audits,cls.b_failures=fit_b(Spy(),registry=cls.registry,manifests=cls.manifests,a_artifacts=cls.artifacts,output=cls.output,code_head='synthetic')

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def test_routing_exact_ids_and_no_unknown(self):
        self.assertEqual(self.a_calls,36)
        self.assertEqual(len(self.audits),18)
        for a in self.audits:
            m=next(m for m in self.manifests if m['fold_id']==a['fold_id'])
            arm=next(x for x in self.registry['arms'] if x['id']==a['arm_id'])
            validate_node_audit(a,m,a['rpm'],arm,self.registry)
        self.assertFalse(self.failures)
        with self.assertRaisesRegex(ValueError,'unsupported'): records_for(self.manifests[0],'test','7000rpm')

    def test_classifier_shared_reference_no_fake_fits(self):
        self.assertEqual(self.counts['classifier_fits'],18)
        self.assertEqual(self.counts['factory_reference_fits'],18)
        self.assertEqual(self.counts['representation_fits'],9)
        for a in self.artifacts:
            if a['arm_id']!='A5':continue
            model=load_bound_model(a,self.root)
            self.assertIsNotNone(model['reference_artifact'])
            self.assertTrue(all('detectors' not in n and 'transformer' not in n for n in model['nodes'].values()))

    def test_audit_calibration_test_ids_and_selection_tamper(self):
        a=self.audits[0];m=self.manifests[0];arm=ARMS[1]
        for field in ['representation_fit_ids','scaler_fit_ids','classifier_fit_ids','reference_fit_ids']:
            bad=copy.deepcopy(a);bad[field]+=m['sample_ids']['test'][:1]
            with self.assertRaisesRegex(ValueError,'audit'):validate_node_audit(bad,m,a['rpm'],arm,self.registry)
            bad=copy.deepcopy(a);bad[field]+=m['sample_ids']['calibration'][:1]
            with self.assertRaises(ValueError):validate_node_audit(bad,m,a['rpm'],arm,self.registry)
        bad=dict(a,selection_sample_ids=['test'])
        with self.assertRaises(ValueError):validate_node_audit(bad,m,a['rpm'],arm,self.registry)

    def test_bound_model_SHA_tamper(self):
        bad=dict(self.artifacts[0],sha256='0'*64)
        with self.assertRaises(ValueError):load_bound_model(bad,self.root)

    def test_B_only_train_residual_and_exact_calibration_sources(self):
        self.assertEqual(len(self.b_audits),9)
        self.assertFalse(self.b_failures)
        for audit in self.b_audits:
            m=next(m for m in self.manifests if m['fold_id']==audit['fold_id'])
            expected=[r['sample_id'] for r in records_for(m,'train',audit['rpm'])]
            self.assertEqual(audit['pooled_covariance_fit_ids'],expected)
            self.assertEqual(audit['reference_fit_ids'],expected)
            self.assertEqual(audit['calibration_sample_ids'],[r['sample_id'] for r in records_for(m,'calibration',audit['rpm'])])
            self.assertEqual(set(audit['calibration_summaries']),{s['id'] for s in SCORES})
        for artifact in self.b_artifacts:
            model=load_bound_model(artifact,self.root)
            self.assertEqual(len(model['nodes']),3)
            for node in model['nodes'].values():
                self.assertTrue(node['pooled'].covariance.assume_centered)
                self.assertEqual(node['pooled'].train_rows,72)


if __name__=='__main__':unittest.main()
