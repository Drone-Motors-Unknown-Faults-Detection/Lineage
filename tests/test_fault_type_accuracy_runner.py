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
from core.fault_type_final_guard import digest, seal
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
        cls.registry={'arms':[ARMS[0],ARMS[1],ARMS[5]],'known_labels':known,'unknown_labels':p['unknown_test_labels'],'seeds':[0],
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

    def test_registry_JSON_roundtrip_and_tampered_parameters(self):
        from experiments.fault_type_accuracy_registry import build_registry, check_registry
        priors,ledger=fixture(self.root/'roundtrip_fixture');p=build_protocol(priors,ledger)
        path=self.root/'roundtrip_protocol.json';path.write_text(json.dumps(p),encoding='utf-8')
        baseline=seal({'baseline_index':{'paths':{'protocol':str(path)}}},'baseline_checksum')
        bp=self.root/'roundtrip_baseline.json';bp.write_text(json.dumps(baseline),encoding='utf-8')
        registry=build_registry(baseline,bp)
        loaded=json.loads(json.dumps(registry))
        self.assertEqual(check_registry(loaded),baseline)
        loaded['rules']['quantile']=.9;loaded=seal(loaded,'registry_checksum')
        with self.assertRaises(ValueError):check_registry(loaded)

    def _lock(self):
        import gzip, platform, sklearn
        from core.formal_data import _sha256_file
        from experiments.fault_type_accuracy_study import IMPLEMENTATIONS
        path=self.root/'audits.json.gz';path.write_bytes(gzip.compress(json.dumps(self.audits+self.b_audits).encode()))
        return seal({'registry_checksum':self.registry['registry_checksum'],'selection_policy':'none','selection_sample_ids':[],
            'shared_validation_calibration':False,'environment':{'python':platform.python_version(),'sklearn':sklearn.__version__},
            'implementation_artifacts':[{'path':s,'sha256':_sha256_file(Path(s))} for s in IMPLEMENTATIONS],
            'artifacts':self.artifacts+self.b_artifacts,'failures':[],
            'audit_artifact':{'path':str(path),'sha256':_sha256_file(path)}},'locked_checksum')

    def test_lock_runtime_inventory_and_selection_guards(self):
        from experiments.fault_type_accuracy_study import validate_lock
        locked=self._lock();self.assertEqual(len(validate_lock(locked,self.registry,self.manifests)),27)
        for field,value in [('selection_sample_ids',['test']),('shared_validation_calibration',True),('implementation_artifacts',[]),('artifacts',self.artifacts)]:
            bad=seal(dict(locked,**{field:value}),'locked_checksum')
            with self.assertRaises(ValueError):validate_lock(bad,self.registry,self.manifests)

    def test_resolved_shared_model_and_saved_SHA_guards(self):
        from experiments.fault_type_accuracy_study import validate_lock, resolved_model
        locked=self._lock();audits=validate_lock(locked,self.registry,self.manifests)
        for artifact in [self.artifacts[1],self.b_artifacts[0]]:
            model=resolved_model(artifact,locked,self.registry,self.manifests,audits,self.root)
            self.assertIsNotNone(model['resolved_reference_model'])
        bad=dict(self.artifacts[0],sha256='0'*64)
        with self.assertRaises(ValueError):resolved_model(bad,locked,self.registry,self.manifests,audits,self.root)
        changed=copy.deepcopy(audits);key=next(iter(changed));changed[key]['classifier_fit_ids']=['test']
        with self.assertRaises(ValueError):resolved_model(self.artifacts[0],locked,self.registry,self.manifests,changed,self.root)

    def test_prediction_recompute_conformal_truth_and_binding_tamper(self):
        from core.fault_type_accuracy import study_metrics
        from experiments.fault_type_accuracy_study import validate_lock, resolved_model
        from experiments.fault_type_accuracy_report import verify_rows
        locked=self._lock();audits=validate_lock(locked,self.registry,self.manifests)
        artifact=self.b_artifacts[0];model=resolved_model(artifact,locked,self.registry,self.manifests,audits,self.root)
        m=self.manifests[0];known=self.registry['known_labels'];unknown=self.registry['unknown_labels'];rows=[]
        for record in records_for(m,'test'):
            raw=np.ones((1,len(known)));d=model['nodes'][record['rpm']]['scores']['B5'].details(raw)
            reject=bool(d['reject'][0])
            rows.append({'sample_id':record['sample_id'],'true_label':record['label'],'motor_id':record['t_code'],'rpm':record['rpm'],
                'source_file':record['source_file'],'source_sha256':record['source_sha256'],
                'true_role':'unknown_test' if record['label'] in unknown else 'healthy' if record['label']==known[0] else 'known_fault',
                'predicted_known_class':known[0],'arm_id':'B5','score_id':'B5','seed':0,'fold_id':m['fold_id'],
                'registry_checksum':self.registry['registry_checksum'],'locked_checksum':locked['locked_checksum'],
                'manifest_checksum':m['manifest_checksum'],'model_sha256':artifact['sha256'],'historical_test_exposed':True,
                'classifier_model_sha256':model['reference_artifact']['sha256'],'reference_model_sha256':model['reference_artifact']['sha256'],
                'raw_class_scores':dict(zip(known,raw[0].tolist())),'openset_score':float(d['score'][0]),'is_unknown':reject,
                'accepted':not reject,'threshold':d['threshold'],'final_class':'unknown' if reject else known[0],
                'nearest_known_class':known[int(d['nearest'][0])],'class_thresholds':None,'normalized_class_scores':None,
                'class_p_values':dict(zip(known,d['p_values'][0].tolist())),'candidate_set_size':int(d['candidate_size'][0])})
        run={'test_ids_checksum':digest(m['sample_ids']['test']),'arm_id':'B5','score_id':'B5','seed':0,
            'model_artifact':artifact,'metrics':study_metrics(rows,known,unknown),'rpm_metrics':[],'configuration_metrics':[]}
        self.assertIn('prediction_value_checksum',verify_rows(rows,run,m,self.registry,locked,model))
        for field,value in [('source_sha256','0'*64),('true_role','healthy'),('is_unknown',not rows[0]['is_unknown']),
                            ('candidate_set_size',99),('classifier_model_sha256','0'*64),('openset_score',2.)]:
            bad=copy.deepcopy(rows);bad[0][field]=value
            if field=='true_role':bad[-1][field]=value
            with self.assertRaises(ValueError):verify_rows(bad,run,m,self.registry,locked,model)
        bad=copy.deepcopy(rows);bad[0]['class_p_values'][known[0]]=.12345
        with self.assertRaises(ValueError):verify_rows(bad,run,m,self.registry,locked,model)


if __name__=='__main__':unittest.main()
