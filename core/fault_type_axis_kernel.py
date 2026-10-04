"""三軸群平均核；Haasdonk／Burkhardt2007及本站改編見exp19手冊。"""
from __future__ import annotations

import hashlib
import itertools
import warnings
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.exceptions import ConvergenceWarning
from sklearn.preprocessing import RobustScaler
from sklearn.svm import SVC
from core.fault_type_accuracy import VIBRATION66, verify_redundancy
from core.fault_type_final_guard import digest

PERMUTATIONS = tuple(itertools.permutations(range(3)))
ALPHAS = (0., .5, 1.)
GAMMA = 1/66
BLOCK_ROWS = 128
NEGATIVE_TOLERANCE = 1e-10
SCALER_PARAMS = dict(with_centering=True, with_scaling=True, quantile_range=(25., 75.),
                     copy=True, unit_variance=False)


def array_checksum(value):
    a = np.ascontiguousarray(value)
    return digest(dict(shape=list(a.shape), dtype=str(a.dtype), sha256=hashlib.sha256(a.tobytes()).hexdigest()))


def matrix(value, dimensions=66, nonempty=False):
    a = np.asarray(value, dtype=float)
    if a.ndim != 2 or a.shape[1] != dimensions or not np.isfinite(a).all() or (nonempty and not len(a)):
        raise ValueError('finite axis matrix with fixed dimensions required')
    return a


class SharedAxisRepresentation:
    """只fit known train；各軸同名特徵共享中心與IQR。"""
    def fit(self, X):
        X = matrix(X, 105, True)
        self.redundancy_check_ = verify_redundancy(X)
        self.scaler_ = RobustScaler(**SCALER_PARAMS).fit(X[:, VIBRATION66].reshape(-1, 22))
        self.fit_input_checksum_ = array_checksum(X)
        self.checksum_ = self.signature()
        return self

    def signature(self):
        return digest(dict(indices=VIBRATION66, params=self.scaler_.get_params(),
            center=self.scaler_.center_.tolist(), scale=self.scaler_.scale_.tolist(),
            source=self.fit_input_checksum_, redundancy=self.redundancy_check_))

    def transform(self, X):
        if self.signature() != self.checksum_:
            raise ValueError('shared axis scaler state changed')
        X = matrix(X, 105)
        if not len(X):
            return np.empty((0, 66))
        Z = self.scaler_.transform(X[:, VIBRATION66].reshape(-1, 22)).reshape(-1, 66)
        return matrix(Z)


def permute_axes(X, permutation):
    X = matrix(X)
    if tuple(sorted(permutation)) != (0, 1, 2):
        raise ValueError('axis permutation required')
    return X.reshape(-1, 3, 22)[:, permutation, :].reshape(-1, 66)


def kernel(X, Y, alpha, block_rows=BLOCK_ROWS):
    """有限群TI核的六項簡化；凸混合及block計算為本站約定。"""
    X, Y = matrix(X), matrix(Y)
    if alpha not in ALPHAS or not isinstance(block_rows, int) or block_rows < 1:
        raise ValueError('fixed alpha and positive block rows required')
    result = np.empty((len(X), len(Y)))
    for start in range(0, len(X), block_rows):
        part = X[start:start+block_rows]
        base = None
        average = np.zeros((len(part), len(Y)))
        for permutation in PERMUTATIONS if alpha else ((0, 1, 2),):
            distances = cdist(part, permute_axes(Y, permutation), metric='sqeuclidean')
            if not np.isfinite(distances).all() or np.any(distances < 0):
                raise ValueError('nonfinite kernel distances')
            values = np.exp(-GAMMA*distances)
            if permutation == (0, 1, 2):
                base = values
            average += values
        result[start:start+len(part)] = base if not alpha else (1-alpha)*base+alpha*average/6
    if not np.isfinite(result).all():
        raise ValueError('nonfinite kernel')
    return result


def kernel_diagonal(X, alpha):
    X = matrix(X)
    if alpha not in ALPHAS:
        raise ValueError('fixed alpha required')
    if not alpha:
        return np.ones(len(X))
    total = np.zeros(len(X))
    for permutation in PERMUTATIONS:
        with np.errstate(over='ignore', invalid='ignore'):
            d = np.sum((X-permute_axes(X, permutation))**2, axis=1)
        if not np.isfinite(d).all():
            raise ValueError('nonfinite kernel diagonal distances')
        total += np.exp(-GAMMA*d)
    return (1-alpha)+alpha*total/6


def classifier_parameters(seed):
    return dict(C=1., kernel='precomputed', degree=3, gamma=GAMMA, coef0=0., shrinking=True,
        probability=False, tol=.001, cache_size=200., class_weight='balanced', verbose=False,
        max_iter=100000, decision_function_shape='ovr', break_ties=False, random_state=seed)


class AxisKernelClassifier:
    def __init__(self, alpha, seed):
        if alpha not in ALPHAS:
            raise ValueError('fixed alpha required')
        self.alpha, self.seed = alpha, seed

    def fit(self, X, y):
        X = matrix(X, nonempty=True)
        y = np.asarray(y)
        if y.ndim != 1 or len(y) != len(X) or y.dtype.kind not in 'iu' or len(np.unique(y)) < 2:
            raise ValueError('known integer class labels required')
        self.reference_ = X.copy()
        self.labels_ = y.copy()
        K = kernel(X, X, self.alpha)
        self.training_kernel_checksum_ = array_checksum(K)
        self.classifier_ = SVC(**classifier_parameters(self.seed))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            self.classifier_.fit(K, y)
        self.warnings_ = [dict(category=w.category.__name__, message=str(w.message)) for w in caught]
        if self.classifier_.fit_status_ != 0 or any(issubclass(w.category, ConvergenceWarning) for w in caught):
            raise RuntimeError('INCOMPLETE SVC convergence; no threshold or iteration change')
        classes = np.unique(y)
        self.centroid_means_ = np.array([K[np.ix_(y == c, y == c)].mean() for c in classes])
        self.checksum_ = self.signature()
        return self

    def signature(self):
        c = self.classifier_
        return digest(dict(alpha=self.alpha, seed=self.seed, params=c.get_params(),
            reference=array_checksum(self.reference_), labels=array_checksum(self.labels_),
            training_kernel=self.training_kernel_checksum_, centroid_means=self.centroid_means_.tolist(),
            classes=c.classes_.tolist(), support=c.support_.tolist(), n_support=c.n_support_.tolist(),
            dual=array_checksum(c.dual_coef_), intercept=c.intercept_.tolist(),
            private_dual=array_checksum(c._dual_coef_), private_intercept=c._intercept_.tolist(),
            shape=list(c.shape_fit_), fit_status=int(c.fit_status_), iterations=c.n_iter_.tolist(), warnings=self.warnings_))

    def validate(self):
        if self.signature() != self.checksum_:
            raise ValueError('axis kernel classifier state changed')

    def infer(self, X):
        self.validate()
        X = matrix(X)
        if not len(X):
            return np.array([], dtype=int), np.empty((0, len(self.classifier_.classes_)))
        labels, distances = [], []
        for start in range(0, len(X), BLOCK_ROWS):
            part = X[start:start+BLOCK_ROWS]
            K = kernel(part, self.reference_, self.alpha)
            labels.append(self.classifier_.predict(K))
            D = np.column_stack([kernel_diagonal(part, self.alpha)-2*K[:, self.labels_ == c].mean(axis=1)+v
                for c, v in zip(self.classifier_.classes_, self.centroid_means_)])
            if not np.isfinite(D).all() or np.any(D < -NEGATIVE_TOLERANCE):
                raise ValueError('invalid RKHS centroid squared distances')
            distances.append(np.maximum(D, 0.))
        return np.concatenate(labels), np.vstack(distances)

    def predict(self, X):
        return self.infer(X)[0]

    def verify_known_source(self, X, y):
        self.validate()
        X = matrix(X, nonempty=True)
        if not np.array_equal(X, self.reference_) or not np.array_equal(y, self.labels_):
            raise ValueError('actual train/reference mismatch')
        K = kernel(X, X, self.alpha)
        expected = np.array([K[np.ix_(self.labels_ == c, self.labels_ == c)].mean()
            for c in self.classifier_.classes_])
        if array_checksum(K) != self.training_kernel_checksum_ or not np.array_equal(expected, self.centroid_means_):
            raise ValueError('actual train kernel/centroid mismatch')
        if np.any(self.classifier_.support_ < 0) or np.any(self.classifier_.support_ >= len(X)):
            raise ValueError('support outside train')
        reconstructed = AxisKernelClassifier(self.alpha, self.seed).fit(X, y)
        if reconstructed.checksum_ != self.checksum_:
            raise ValueError('actual known SVC state reconstruction mismatch')
        return dict(training_kernel_checksum=self.training_kernel_checksum_, state_checksum=self.checksum_,
                    support_count=len(self.classifier_.support_), test_numeric_reads=0)


class KernelCentroidRejection:
    def calibrate(self, distances):
        D = np.asarray(distances, float)
        if D.ndim != 2 or not len(D) or D.shape[1] < 2 or not np.isfinite(D).all() or np.any(D < 0):
            raise ValueError('known calibration squared centroid distances required')
        self.quantile_ = float(np.quantile(D.min(axis=1), .95, method='linear'))
        self.calibration_checksum_ = array_checksum(D)
        self.checksum_ = self.signature()
        return self

    def signature(self):
        return digest(dict(q=self.quantile_, calibration=self.calibration_checksum_, confidence=.95,
            method='linear', score='min squared RKHS class centroid distance', reject='strict >'))

    def score_samples(self, distances):
        if self.signature() != self.checksum_:
            raise ValueError('centroid calibration state changed')
        D = np.asarray(distances, float)
        if D.ndim != 2 or D.shape[1] < 2 or not np.isfinite(D).all() or np.any(D < 0):
            raise ValueError('finite nonnegative query distances required')
        return D.min(axis=1)
