"""實驗18固定原型拒絕；Fischer等2015改編，精確差異見先行手冊。"""
import numpy as np
from core.fault_type_final_guard import digest

EPSILON = 1e-12
MODES = ('distance', 'ambiguity', 'or')


def components(distances):
    """每known class一原型；僅距離輸入，不需要query真值。"""
    d = np.asarray(distances, float)
    if d.ndim != 2 or d.shape[1] < 2 or not np.isfinite(d).all() or (d < 0).any():
        raise ValueError('finite nonnegative distances to distinct known classes required')
    ordered = np.sort(d, axis=1)
    near, other = ordered[:, 0], ordered[:, 1]
    # 分子為距離差；雙零時相似度0，歧義1，不會判作完全確定。
    with np.errstate(over='ignore'):
        denominator = other+near+EPSILON
    if not np.isfinite(denominator).all():
        raise ValueError('overflow in rejection denominator')
    ambiguity = 1-(other-near)/denominator
    result = np.column_stack([near, ambiguity])
    if not np.isfinite(result).all():
        raise ValueError('nonfinite rejection components')
    return result


class ContextRejection:
    """只校準固定q95，不選模型或門檻；來源用途由runner驗證。"""
    def __init__(self, mode):
        if mode not in MODES:
            raise ValueError('fixed rejection mode required')
        self.mode = mode

    def calibrate(self, distances):
        scores = components(distances)
        if not len(scores):
            raise ValueError('nonempty known calibration required')
        self.quantiles_ = np.quantile(scores, .95, axis=0, method='linear')
        self.calibration_checksum_ = digest(np.asarray(distances, float).tolist())
        self.checksum_ = self.signature()
        return self

    def signature(self):
        return digest([self.mode, self.quantiles_.tolist(), self.calibration_checksum_, .95, 'linear', EPSILON])

    def score_samples(self, distances):
        if self.mode not in MODES or self.signature() != self.checksum_:
            raise ValueError('rejection state tampered')
        raw = components(distances)
        excess = (raw-self.quantiles_)/np.maximum(np.abs(self.quantiles_), EPSILON)
        score = excess[:, 0] if self.mode == 'distance' else excess[:, 1] if self.mode == 'ambiguity' else np.max(excess, axis=1)
        if not np.isfinite(score).all():
            raise ValueError('nonfinite normalized rejection')
        return score
