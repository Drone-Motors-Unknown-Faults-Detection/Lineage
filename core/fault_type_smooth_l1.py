"""實驗16：Lange等（ESANN2014）平滑L1的有限GLVQ適配。

原式、α來源、非零Q對角與本站改編見exp16手冊。
模型流程依本站exp15改編；不修改封存exp15或正式factory。
"""
import time
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from core.fault_type_final_guard import digest
from core.fault_type_literature import finite
from core.fault_type_metric_classifiers import PrototypeClassifier
from core.fault_type_discriminative_prototypes import OPTIONS, BETA, EPSILON

ALPHA = 20.


def smooth_absolute(z, kind):
    """原式Q／S及對z導數；穩定計算，不改零值常數。"""
    z = np.asarray(z, float)
    if kind not in ['quasi', 'soft'] or not np.isfinite(z).all():
        raise ValueError('finite smooth distance definition')
    t = (ALPHA / 2) * z
    tanh = np.tanh(t)
    if kind == 'quasi':
        a = np.abs(z)
        value = a + 2 / ALPHA * np.log1p(np.exp(-ALPHA * a))
        gradient = tanh
    else:
        value = z * tanh
        gradient = tanh + t * (1 - tanh * tanh)
    if not np.isfinite(value).all() or not np.isfinite(gradient).all():
        raise ValueError('nonfinite smooth distance')
    return value, gradient


def distances_and_gradients(X, W, kind):
    """distance及對每個prototype的導數，允許零筆query。"""
    X = np.asarray(X, float)
    W = finite(W)
    if X.ndim != 2 or X.shape[1] != W.shape[1] or not np.isfinite(X).all():
        raise ValueError('finite query dimensions')
    value, dz = smooth_absolute(X[:, None, :] - W[None, :, :], kind)
    return value.sum(axis=2), -dz


def relative_objective(W, X, y, labels, initial, kind, anchor=0.):
    W = finite(W)
    X = finite(X)
    initial = finite(initial)
    y = np.asarray(y)
    labels = np.asarray(labels)
    if (W.shape != initial.shape or W.shape[1] != X.shape[1] or y.ndim != 1 or
            len(y) != len(X) or labels.ndim != 1 or len(labels) != len(W) or
            anchor not in [0., .01] or len(np.unique(labels)) < 2 or
            not set(y).issubset(set(labels))):
        raise ValueError('prototype objective sources')
    distances, dw = distances_and_gradients(X, W, kind)
    same = y[:, None] == labels[None, :]
    positive = np.argmin(np.where(same, distances, np.inf), axis=1)
    negative = np.argmin(np.where(~same, distances, np.inf), axis=1)
    row = np.arange(len(X))
    dp = distances[row, positive]
    dn = distances[row, negative]
    den = dp + dn + EPSILON
    probability = expit(BETA * (dp - dn) / den)
    gain = BETA * probability * (1 - probability) / len(X)
    grad = np.zeros_like(W)
    np.add.at(grad, positive, (gain * (2 * dn + EPSILON) / den**2)[:, None] * dw[row, positive])
    np.add.at(grad, negative, (gain * (-2 * dp - EPSILON) / den**2)[:, None] * dw[row, negative])
    value = probability.mean() + anchor * np.mean((W - initial)**2)
    grad += 2 * anchor * (W - initial) / W.size
    if not np.isfinite(value) or not np.isfinite(grad).all():
        raise ValueError('nonfinite relative loss')
    return float(value), grad


class SmoothL1Prototypes:
    """全部known train的單平均中心，子集損失；失敗不得推論。"""
    def __init__(self, kind='quasi', variant='static', seed=42):
        if kind not in ['quasi', 'soft'] or variant not in ['static', 'glvq', 'anchored']:
            raise ValueError('fixed smooth prototype definition')
        self.kind = kind
        self.variant = variant
        self.seed = seed

    def fit(self, X, y, indices, *, seconds=120, options=None):
        X = finite(X)
        y = np.asarray(y)
        ix = np.asarray(indices)
        if (y.ndim != 1 or len(y) != len(X) or ix.ndim != 1 or
                not np.issubdtype(ix.dtype, np.integer) or not 0 < len(ix) <= 360 or
                len(set(ix.tolist())) != len(ix) or (ix < 0).any() or (ix >= len(X)).any() or
                len(np.unique(y)) < 2 or set(y[ix]) != set(y) or seconds <= 0):
            raise ValueError('known bounded smooth prototype fit')
        initial = PrototypeClassifier(1, self.seed).fit(X, y)
        self.initial_ = initial.prototypes_.copy()
        self.labels_ = initial.prototype_labels_.copy()
        self.classes_ = initial.classes_.copy()
        self.train_checksum_ = digest([X.tolist(), y.tolist(), ix.tolist()])
        self.options_ = dict(OPTIONS if options is None else options)
        anchor = .01 if self.variant == 'anchored' else 0.
        xx, yy, W0 = X[ix], y[ix], self.initial_
        start = time.perf_counter()
        first_loss, first_grad = relative_objective(W0, xx, yy, self.labels_, W0, self.kind, anchor)
        self.prototypes_ = W0.copy()
        last = {'W': W0.copy()}
        if self.variant == 'static':
            self.optimizer_ = {'success': True, 'message': 'STATIC_NO_OPTIMIZATION', 'iterations': 0, 'evaluations': 0}
        else:
            def objective(flat):
                if time.perf_counter() - start > seconds:
                    raise TimeoutError('smooth prototype optimizer time budget')
                W = flat.reshape(W0.shape)
                loss, gradient = relative_objective(W, xx, yy, self.labels_, W0, self.kind, anchor)
                last['W'] = W.copy()
                return loss, gradient.ravel()
            try:
                result = minimize(objective, W0.ravel(), jac=True, method='L-BFGS-B', options=self.options_)
                self.prototypes_ = result.x.reshape(W0.shape)
                self.optimizer_ = {'success': bool(result.success), 'message': str(result.message), 'status': int(result.status),
                                   'iterations': int(result.nit), 'evaluations': int(result.nfev)}
            except TimeoutError as error:
                self.prototypes_ = last['W']
                self.optimizer_ = {'success': False, 'message': str(error), 'status': 'TIME_BUDGET'}
        loss, grad = relative_objective(self.prototypes_, xx, yy, self.labels_, W0, self.kind, anchor)
        self.optimizer_.update(initial_loss=first_loss, final_loss=loss, gradient_inf_norm=float(np.max(np.abs(grad))),
                               initialization_gradient_inf_norm=float(np.max(np.abs(first_grad))), seconds=time.perf_counter()-start,
                               budget_seconds=seconds, options=self.options_, anchor=anchor, alpha=ALPHA, beta=BETA, epsilon=EPSILON)
        self.checksum_ = self.signature()
        return self

    def signature(self):
        stable = {k: v for k, v in self.optimizer_.items() if k != 'seconds'}
        return digest([self.kind, self.variant, self.seed, self.train_checksum_, self.initial_.tolist(),
                       self.prototypes_.tolist(), self.labels_.tolist(), self.classes_.tolist(), stable])

    def distances(self, X):
        if self.signature() != self.checksum_:
            raise ValueError('smooth prototype state tampered')
        if not self.optimizer_['success']:
            raise ValueError('unconverged smooth prototype cannot infer')
        return distances_and_gradients(X, self.prototypes_, self.kind)[0]

    def predict(self, X):
        return self.labels_[np.argmin(self.distances(X), axis=1)]
