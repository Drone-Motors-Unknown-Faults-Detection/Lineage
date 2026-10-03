"""實驗17：AGLVQ工況機制的有限改編；來源與差異見先行手冊。

只以known train學RPM多項式原型，不安裝或複製作者TF程式。
"""
import time
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from core.fault_type_final_guard import digest
from core.fault_type_literature import finite
from core.fault_type_discriminative_prototypes import OPTIONS, BETA, EPSILON

RPMS = (6000, 8000, 11000)
AUXILIARY = .01


def context_basis(rpms, degree):
    """只接受既有三離散RPM；degree0供退化控制，不宣稱外插。"""
    r = np.asarray(rpms, float)
    if (degree not in [0, 1, 2] or r.ndim != 1 or not np.isfinite(r).all() or
            not set(r.tolist()).issubset(RPMS)):
        raise ValueError('documented discrete RPM required')
    c = (r-8000)/3000
    return np.column_stack([c**i for i in range(degree+1)])


def context_distances(X, theta, phi):
    X = np.asarray(X, float)
    theta = np.asarray(theta, float)
    phi = np.asarray(phi, float)
    if (X.ndim != 2 or theta.ndim != 3 or phi.ndim != 2 or len(X) != len(phi) or
            theta.shape[1] != phi.shape[1] or theta.shape[2] != X.shape[1] or
            not all(np.isfinite(v).all() for v in [X, theta, phi])):
        raise ValueError('finite context dimensions')
    W = np.einsum('nq,cqd->ncd', phi, theta)
    distances = np.sum((X[:, None, :]-W)**2, axis=2)
    if not np.isfinite(distances).all():
        raise ValueError('nonfinite context distance')
    return distances, W


def relative_objective(theta, X, y, labels, phi, auxiliary=0.):
    """平方距離GLVQ及true-prototype MSE；解析chain rule梯度。"""
    X = finite(X)
    y, labels = np.asarray(y), np.asarray(labels)
    theta, phi = np.asarray(theta, float), np.asarray(phi, float)
    distances, W = context_distances(X, theta, phi)
    if (y.ndim != 1 or len(y) != len(X) or labels.ndim != 1 or len(labels) != len(theta) or
            len(np.unique(labels)) != len(labels) or len(labels) < 2 or
            not set(y).issubset(set(labels)) or auxiliary not in [0., AUXILIARY]):
        raise ValueError('known context objective sources')
    same = y[:, None] == labels[None, :]
    pos = np.argmin(np.where(same, distances, np.inf), axis=1)
    neg = np.argmin(np.where(~same, distances, np.inf), axis=1)
    row = np.arange(len(X))
    dp, dn = distances[row, pos], distances[row, neg]
    den = dp+dn+EPSILON
    probability = expit(BETA*(dp-dn)/den)
    gain = BETA*probability*(1-probability)/len(X)
    positive_difference = W[row, pos]-X
    gp = (gain*(2*dn+EPSILON)/den**2)[:, None]*2*positive_difference
    gn = (gain*(-2*dp-EPSILON)/den**2)[:, None]*2*(W[row, neg]-X)
    gp += 2*auxiliary*positive_difference/(len(X)*X.shape[1])
    grad = np.zeros_like(theta)
    np.add.at(grad, pos, phi[:, :, None]*gp[:, None, :])
    np.add.at(grad, neg, phi[:, :, None]*gn[:, None, :])
    value = probability.mean()+auxiliary*np.mean(positive_difference**2)
    if not np.isfinite(value) or not np.isfinite(grad).all():
        raise ValueError('nonfinite context objective')
    return float(value), grad


class ContextPrototypes:
    """工況最小平方初始化，固定子集margin；cal/test不能進fit。"""
    def __init__(self, degree=1, variant='static', seed=42):
        if degree not in [0, 1, 2] or variant not in ['static', 'glvq', 'auxiliary']:
            raise ValueError('fixed context definition')
        self.degree, self.variant, self.seed = degree, variant, seed

    def fit(self, X, y, rpms, indices, *, seconds=120, options=None):
        X = finite(X)
        y, ix = np.asarray(y), np.asarray(indices)
        phi = context_basis(rpms, self.degree)
        if (y.ndim != 1 or len(y) != len(X) or len(phi) != len(X) or ix.ndim != 1 or
                not np.issubdtype(ix.dtype, np.integer) or not 0 < len(ix) <= 360 or
                len(set(ix.tolist())) != len(ix) or (ix < 0).any() or (ix >= len(X)).any() or
                len(np.unique(y)) < 2 or set(y[ix]) != set(y) or seconds <= 0):
            raise ValueError('known bounded context train sources')
        r = np.asarray(rpms, float)
        self.labels_ = np.unique(y)
        if any(set(r[y == c].tolist()) != set(RPMS) for c in self.labels_):
            raise ValueError('each known class needs all three RPM for context initialization')
        self.initial_ = np.stack([np.linalg.lstsq(phi[y == c], X[y == c], rcond=None)[0] for c in self.labels_])
        self.coefficients_ = self.initial_.copy()
        self.train_checksum_ = digest([X.tolist(), y.tolist(), r.tolist(), ix.tolist()])
        self.options_ = dict(OPTIONS if options is None else options)
        auxiliary = AUXILIARY if self.variant == 'auxiliary' else 0.
        xx, yy, pp = X[ix], y[ix], phi[ix]
        start = time.perf_counter()
        first, initial_gradient = relative_objective(self.initial_, xx, yy, self.labels_, pp, auxiliary)
        last = {'theta': self.initial_.copy()}
        if self.variant == 'static':
            self.optimizer_ = dict(success=True, message='STATIC_CONTEXT_LEAST_SQUARES', iterations=0, evaluations=0)
        else:
            def objective(flat):
                if time.perf_counter()-start > seconds:
                    raise TimeoutError('context optimizer time budget')
                theta = flat.reshape(self.initial_.shape)
                value, gradient = relative_objective(theta, xx, yy, self.labels_, pp, auxiliary)
                last['theta'] = theta.copy()
                return value, gradient.ravel()
            try:
                result = minimize(objective, self.initial_.ravel(), jac=True, method='L-BFGS-B', options=self.options_)
                self.coefficients_ = result.x.reshape(self.initial_.shape)
                self.optimizer_ = dict(success=bool(result.success), message=str(result.message), status=int(result.status),
                                       iterations=int(result.nit), evaluations=int(result.nfev))
            except TimeoutError as error:
                self.coefficients_ = last['theta']
                self.optimizer_ = dict(success=False, message=str(error), status='TIME_BUDGET')
        loss, gradient = relative_objective(self.coefficients_, xx, yy, self.labels_, pp, auxiliary)
        self.optimizer_.update(initial_loss=first, final_loss=loss, gradient_inf_norm=float(np.max(np.abs(gradient))),
                               initialization_gradient_inf_norm=float(np.max(np.abs(initial_gradient))),
                               seconds=time.perf_counter()-start, budget_seconds=seconds, options=self.options_,
                               auxiliary=auxiliary, beta=BETA, epsilon=EPSILON)
        self.checksum_ = self.signature()
        return self

    def signature(self):
        stable = {k: v for k, v in self.optimizer_.items() if k != 'seconds'}
        return digest([self.degree, self.variant, self.seed, self.train_checksum_, self.initial_.tolist(),
                       self.coefficients_.tolist(), self.labels_.tolist(), stable])

    def distances(self, X, rpms):
        if self.signature() != self.checksum_:
            raise ValueError('context state tampered')
        if not self.optimizer_['success']:
            raise ValueError('unconverged context model cannot infer')
        return context_distances(X, self.coefficients_, context_basis(rpms, self.degree))[0]

    def predict(self, X, rpms):
        return self.labels_[np.argmin(self.distances(X, rpms), axis=1)]
