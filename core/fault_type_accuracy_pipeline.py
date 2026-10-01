"""Train-only study representations and exact RPM/input contracts."""
from __future__ import annotations
import numpy as np
from sklearn.preprocessing import RobustScaler
from core.fault_type_accuracy import VIBRATION66, VIBRATION75, verify_redundancy
from core.fault_type_final_guard import digest
from core.fault_type_validator import assert_valid_for_formal


class StudyRepresentation:
    def __init__(self, arm, scaler_params):
        self.arm = arm
        self.scaler_params = scaler_params

    def fit(self, X):
        X = self._matrix(X)
        expected = VIBRATION66 if len(self.arm['indices']) == 66 else VIBRATION75
        if self.arm['indices'] != expected:
            raise ValueError('fixed axis/feature mapping differs')
        self.redundancy_check = verify_redundancy(X) if expected == VIBRATION66 else None
        raw = X[:, self.arm['indices']]
        self.signed_scale = np.maximum(np.median(np.abs(raw), axis=0), 1e-12) if self.arm['signed_log'] else None
        values = self._signed(raw)
        params = dict(self.scaler_params)
        params['quantile_range'] = tuple(params['quantile_range'])
        self.scaler = RobustScaler(**params).fit(values)
        self.transform_checksum = self.checksum()
        return self

    def checksum(self):
        return digest({'indices': self.arm['indices'], 'signed_log': self.arm['signed_log'],
            'signed_scale': None if self.signed_scale is None else self.signed_scale.tolist(),
            'center': self.scaler.center_.tolist(), 'scale': self.scaler.scale_.tolist()})

    def _matrix(self, X):
        X = np.asarray(X, float)
        if X.ndim != 2 or X.shape[1] != 105 or not np.isfinite(X).all():
            raise ValueError('finite formal105 input required')
        return X

    def _signed(self, X):
        if self.signed_scale is None: return X
        # logaddexp avoids overflow in abs(x)/s while preserving sign and zero.
        with np.errstate(divide='ignore'):
            return np.sign(X)*np.logaddexp(0., np.log(np.abs(X))-np.log(self.signed_scale))

    def transform(self, X):
        if self.checksum() != self.transform_checksum: raise ValueError('transform tampered')
        values = self.scaler.transform(self._signed(self._matrix(X)[:, self.arm['indices']]))
        if not np.isfinite(values).all(): raise ValueError('nonfinite transformed values')
        return values

    def inverse_signed(self, X):
        if self.signed_scale is None: return np.asarray(X,float)
        return np.sign(X)*np.expm1(np.abs(X))*self.signed_scale


def records_for(manifest, part, rpm=None):
    assert_valid_for_formal(manifest, allow_incomplete=True)
    if rpm is not None and rpm not in manifest['expected_rpms']:
        raise ValueError('unsupported RPM')
    by = {r['sample_id']:r for r in manifest['records']}
    result = [by[s] for s in manifest['sample_ids'][part] if rpm is None or by[s]['rpm'] == rpm]
    if any(r['t_code'] != manifest['motor_roles'][part] for r in result): raise ValueError('motor role mismatch')
    if part != 'test' and any(r['label'] not in [manifest['healthy_label'],*manifest['known_fault_labels']] for r in result):
        raise ValueError('unknown in development data')
    return result


def check_cell(train, cal, known, minimum=5):
    counts = {part:{label:sum(r['label']==label for r in rows) for label in known} for part,rows in [('train',train),('calibration',cal)]}
    if any(counts['train'][c]<minimum or counts['calibration'][c]<1 for c in known):
        raise ValueError('INCOMPLETE missing class/calibration or insufficient k5 reference: '+str(counts))
    return counts


def validate_node_audit(audit, manifest, rpm, arm, registry):
    train = records_for(manifest,'train',rpm)
    cal = records_for(manifest,'calibration',rpm)
    expected = [r['sample_id'] for r in train]
    for field in ['representation_fit_ids','scaler_fit_ids','classifier_fit_ids','reference_fit_ids']:
        if audit.get(field)!=expected: raise ValueError(field+' audit differs from exact train/RPM')
    if audit.get('calibration_sample_ids') != [r['sample_id'] for r in cal]: raise ValueError('calibration audit differs')
    if (audit.get('selection_sample_ids')!=[] or audit.get('selection_policy')!='none' or audit.get('shared_validation_calibration') is not False or
        audit.get('arm_id')!=arm['id'] or audit.get('registry_checksum')!=registry['registry_checksum'] or
        audit.get('manifest_checksum')!=manifest['manifest_checksum']): raise ValueError('audit selection/config mismatch')
    return counts_from_records(train,cal)


def counts_from_records(train,cal):
    return {'train':len(train),'calibration':len(cal)}
