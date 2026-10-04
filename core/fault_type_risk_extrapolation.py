"""訓練RPM風險差異；REx公式及本站改編見exp20，無作者程式複製。"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax
from core.fault_type_axis_kernel import array_checksum
from core.fault_type_final_guard import digest

BETAS = (0., 1., 10.)
RIDGE = .001
OPTIMIZER = dict(maxiter=1000, gtol=1e-6, ftol=1e-10, maxls=50, maxcor=10)


def matrix(value, dimensions=None, nonempty=True):
    a = np.asarray(value, dtype=float)
    if (a.ndim != 2 or a.shape[1] < 1 or (dimensions is not None and a.shape[1] != dimensions)
            or not np.isfinite(a).all() or (nonempty and not len(a))):
        raise ValueError('finite risk matrix required')
    return a


def risk_design(X, y, domains):
    X = matrix(X)
    raw_y = np.asarray(y)
    if raw_y.ndim != 1 or len(raw_y) != len(X) or not np.issubdtype(raw_y.dtype, np.integer):
        raise ValueError('integer known class IDs required')
    y = raw_y.astype(np.int64)
    classes = np.unique(y)
    if len(classes) < 2 or not np.array_equal(classes, np.arange(len(classes))):
        raise ValueError('contiguous known class IDs required')
    domains = np.asarray(domains)
    if domains.ndim != 1 or len(domains) != len(X):
        raise ValueError('train environment length')
    if domains.dtype.kind in 'fc' and not np.isfinite(domains).all():
        raise ValueError('finite train environments')
    environments, env = np.unique(domains, return_inverse=True)
    if len(environments) != 3:
        raise ValueError('INCOMPLETE three known train RPM environments required')
    C = len(classes)
    counts = np.zeros((3, C), dtype=int)
    np.add.at(counts, (env, y), 1)
    if not counts.all():
        raise ValueError('INCOMPLETE known class absent in training RPM')
    weights = 1/(C*counts[env, y])
    return X, y, env, weights, counts, environments


def objective(theta, X, y, domains, beta, ridge=RIDGE):
    """等RPM／等class CE＋population variance；回傳解析gradient與三風險。"""
    if beta not in BETAS or not np.isfinite(ridge) or ridge <= 0:
        raise ValueError('fixed beta and positive ridge')
    X, y, env, weights, counts, _ = risk_design(X, y, domains)
    C = counts.shape[1]
    theta = np.asarray(theta, float)
    if theta.shape != ((X.shape[1]+1)*C,) or not np.isfinite(theta).all():
        raise ValueError('finite risk coefficients')
    A = theta.reshape(X.shape[1]+1, C)
    augmented = np.column_stack([X, np.ones(len(X))])
    try:
        with np.errstate(over='raise', invalid='raise'):
            logits = augmented @ A
            ce = logsumexp(logits, axis=1)-logits[np.arange(len(y)), y]
            risks = np.bincount(env, weights=weights*ce, minlength=3)
            mean = risks.mean()
            variance = np.mean((risks-mean)**2)
            loss = mean+beta*variance+ridge/2*np.sum(A[:-1]**2)
            residual = softmax(logits, axis=1)
            residual[np.arange(len(y)), y] -= 1
            coefficients = (1/3+2*beta/3*(risks-mean))[env]*weights
            gradient = augmented.T @ (residual*coefficients[:, None])
            gradient[:-1] += ridge*A[:-1]
    except FloatingPointError as exc:
        raise ValueError('nonfinite risk objective') from exc
    if not np.isfinite(loss) or not np.isfinite(gradient).all() or not np.isfinite(risks).all():
        raise ValueError('nonfinite risk objective')
    return float(loss), gradient.ravel(), risks


class RiskExtrapolationClassifier:
    """只fit known train；beta>0必須由同來源收斂ERM起跑。"""
    def __init__(self, beta=0., seed=42):
        if beta not in BETAS:
            raise ValueError('unregistered risk beta')
        self.beta, self.seed = float(beta), int(seed)

    def fit(self, X, y, domains, warm_start=None):
        X, y, _, _, counts, environments = risk_design(X, y, domains)
        self.n_features_in_, self.classes_ = X.shape[1], np.arange(counts.shape[1])
        self.source_ = dict(features=array_checksum(X), labels=array_checksum(y),
                            environments=digest(np.asarray(domains).tolist()))
        self.counts_, self.environments_ = counts, environments.tolist()
        if self.beta == 0:
            if warm_start is not None:
                raise ValueError('ERM zero initialization required')
            initial = np.zeros((X.shape[1]+1)*len(self.classes_))
            self.warm_start_checksum_ = None
        else:
            if (not isinstance(warm_start, RiskExtrapolationClassifier) or warm_start.beta != 0
                    or warm_start.source_ != self.source_ or warm_start.seed != self.seed):
                raise ValueError('same known source/seed ERM warm start required')
            warm_start.validate()
            initial = np.vstack([warm_start.coef_.T, warm_start.intercept_]).ravel().copy()
            self.warm_start_checksum_ = warm_start.checksum_
        self.initial_checksum_ = array_checksum(initial)
        def loss(theta):
            value, gradient, _ = objective(theta, X, y, domains, self.beta)
            return value, gradient
        result = minimize(loss, initial, jac=True, method='L-BFGS-B', options=OPTIMIZER.copy())
        if not result.success or not np.isfinite(result.x).all():
            raise RuntimeError('INCOMPLETE risk optimizer: '+str(result.message))
        value, gradient, risks = objective(result.x, X, y, domains, self.beta)
        A = result.x.reshape(X.shape[1]+1, len(self.classes_))
        self.coef_, self.intercept_ = A[:-1].T.copy(), A[-1].copy()
        self.optimizer_ = dict(success=True, status=int(result.status), message=str(result.message),
            iterations=int(result.nit), evaluations=int(result.nfev), objective=value,
            gradient_inf=float(np.max(np.abs(gradient))), risks=risks.tolist(),
            risk_mean=float(risks.mean()), risk_population_variance=float(np.var(risks)),
            options=OPTIMIZER.copy(), ridge=RIDGE, initialization='zero' if self.beta == 0 else 'train_only_ERM')
        self.checksum_ = self.signature()
        return self

    def signature(self):
        return digest(dict(beta=self.beta, seed=self.seed, source=self.source_, counts=self.counts_.tolist(),
            environments=self.environments_, dimensions=self.n_features_in_, classes=self.classes_.tolist(),
            coef=self.coef_.tolist(), intercept=self.intercept_.tolist(), optimizer=self.optimizer_,
            initial=self.initial_checksum_, warm_start=self.warm_start_checksum_))

    def validate(self):
        if (self.signature() != self.checksum_ or not self.optimizer_['success']
                or self.optimizer_['options'] != OPTIMIZER or self.optimizer_['ridge'] != RIDGE):
            raise ValueError('risk classifier tampered')

    def decision_function(self, X):
        self.validate()
        X = matrix(X, self.n_features_in_, nonempty=False)
        with np.errstate(over='ignore', invalid='ignore'):
            logits = X @ self.coef_.T+self.intercept_
        if not np.isfinite(logits).all():
            raise ValueError('nonfinite risk logits')
        return logits

    def predict_proba(self, X):
        return softmax(self.decision_function(X), axis=1)

    def predict(self, X):
        return self.classes_[self.decision_function(X).argmax(1)]

    def verify_known_source(self, X, y, domains, warm_start=None):
        """獨立重新fit actual known來源，拒絕重封係數或來源替換。"""
        self.validate()
        rebuilt = RiskExtrapolationClassifier(self.beta, self.seed).fit(X, y, domains, warm_start)
        if rebuilt.signature() != self.signature():
            raise ValueError('actual known risk source mismatch')
        return dict(source=self.source_, counts=self.counts_.tolist(), optimizer=self.optimizer_,
                    classifier_checksum=self.checksum_, test_numeric_reads=0)
