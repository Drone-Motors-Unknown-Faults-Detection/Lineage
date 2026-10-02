import copy
import unittest
from unittest.mock import patch
from core.fault_type_continuous import stratified_subset
from experiments.fault_type_continuous_study import check_audit
from experiments.fault_type_continuous_registry import ARMS


class ContinuousAuditTests(unittest.TestCase):
    def fixture(self):
        records={part:[{'sample_id':part+str(i),'label':['H','F'][i%2],'rpm':['r1','r2'][i//50], 't_code':motor} for i in range(100)] for part,motor in [('train','T1'),('calibration','T2'),('test','T3')]}
        m={'motor_roles':{'train':'T1','calibration':'T2','test':'T3'},'manifest_checksum':'m'}
        p={'known_labels':['H','F'],'arms':ARMS,'protocol_checksum':'p','dataset_fingerprint':'f'}
        ids=[x['sample_id'] for x in records['train']];ix=stratified_subset([i%2 for i in range(100)],[x['rpm'] for x in records['train']],0);sub=[ids[i] for i in ix]
        a={'definition':ARMS[1],'seed':0,'motor_roles':m['motor_roles'],'protocol_checksum':'p','manifest_checksum':'m','dataset_fingerprint':'f',
           'representation_fit_ids':ids,'scaler_fit_ids':ids,'detector_transform_fit_ids':ids,'reference_fit_ids':ids,'classifier_fit_ids':sub,
           'metric_fit_ids':sub,'calibration_sample_ids':[x['sample_id'] for x in records['calibration']], 'selection_sample_ids':[], 'selection_policy':'none','shared_validation_calibration':False}
        return records,m,p,a
    def call(self,rr,m,p,a):
        with patch('experiments.fault_type_continuous_study.records_for',side_effect=lambda m,part:rr[part]):return check_audit(a,m,p)
    def test_subset_classifier_accepted_but_full_reference(self):
        self.assertTrue(self.call(*self.fixture()))
    def test_cal_in_each_fit_step_rejected(self):
        for k in ['representation_fit_ids','scaler_fit_ids','classifier_fit_ids','reference_fit_ids','metric_fit_ids','detector_transform_fit_ids']:
            rr,m,p,a=self.fixture();a[k]=[*a[k],rr['calibration'][0]['sample_id']]
            with self.assertRaises(ValueError,msg=k):self.call(rr,m,p,a)
    def test_unknown_development_rejected(self):
        for part in ['train','calibration']:
            rr,m,p,a=self.fixture();rr[part][0]['label']='U'
            with self.assertRaises(ValueError):self.call(rr,m,p,a)
    def test_test_id_in_fit_rejected(self):
        rr,m,p,a=self.fixture();a['classifier_fit_ids'][0]=rr['test'][0]['sample_id']
        with self.assertRaises(ValueError):self.call(rr,m,p,a)
    def test_shared_motor_rejected(self):
        rr,m,p,a=self.fixture();m['motor_roles']['calibration']='T1'
        with self.assertRaises(ValueError):self.call(rr,m,p,a)
    def test_selector_and_valcal_rejected(self):
        for key,value in [('selection_sample_ids',['test0']),('selection_policy','global'),('shared_validation_calibration',True)]:
            rr,m,p,a=self.fixture();a[key]=value
            with self.assertRaises(ValueError):self.call(rr,m,p,a)
    def test_sample_overlap_rejected(self):
        rr,m,p,a=self.fixture();rr['test'][0]['sample_id']=rr['train'][0]['sample_id']
        with self.assertRaises(ValueError):self.call(rr,m,p,a)
    def test_config_or_source_alteration_rejected(self):
        for key in ['protocol_checksum','manifest_checksum','dataset_fingerprint']:
            rr,m,p,a=self.fixture();a[key]='changed'
            with self.assertRaises(ValueError):self.call(rr,m,p,a)
