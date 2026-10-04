"""表格特徵自挑戰有限改編；Huang等ECCV2020與差異見exp21，未複製作者碼。"""
from __future__ import annotations

import numpy as np
from scipy.special import softmax, logsumexp
from core.fault_type_risk_extrapolation import matrix, risk_design, RiskExtrapolationClassifier, RIDGE
from core.fault_type_axis_kernel import array_checksum
from core.fault_type_final_guard import digest

VARIANTS = ('unmasked', 'random', 'signed_gradient', 'contribution')
STEPS = 200
FRACTION = 1/3
TRAINING = dict(steps=STEPS, feature_fraction=FRACTION, row_fraction=FRACTION, ridge=RIDGE,
    optimizer='fixed_full_batch_SGD', ties='stable_descending_exact_ceil', mask_gradient='stop',
    initialization='same_known_source_ERM', selection='last_iterate',
    learning_rate='1/(0.5*weighted_augmented_train_trace+ridge)')


def coefficients(A, X, y):
    A = np.asarray(A, float)
    raw_y = np.asarray(y)
    if (A.ndim != 2 or A.shape[0] != X.shape[1]+1 or A.shape[1] < 2
            or not np.isfinite(A).all() or raw_y.shape != (len(X),)
            or not np.issubdtype(raw_y.dtype, np.integer)
            or np.any(raw_y < 0) or np.any(raw_y >= A.shape[1])):
        raise ValueError('finite known coefficients/classes required')
    return A, raw_y.astype(np.int64)


def loss_gradient(A, X, y, weights):
    """固定masked矩陣的weighted CE；不對mask求導，bias不罰ridge。"""
    X = matrix(X)
    A, y = coefficients(A, X, y)
    weights = np.asarray(weights, float)
    if (weights.shape != (len(X),) or not np.isfinite(weights).all()
            or np.any(weights <= 0) or not np.isclose(weights.sum(), 1, rtol=0, atol=1e-12)):
        raise ValueError('positive normalized train weights required')
    with np.errstate(over='raise', invalid='raise'):
        aug = np.column_stack([X, np.ones(len(X))])
        logits = aug @ A
        ce = logsumexp(logits, axis=1)-logits[np.arange(len(X)), y]
        p = softmax(logits, axis=1)
        p[np.arange(len(X)), y] -= 1
        gradient = aug.T @ (weights[:, None]*p)
        gradient[:-1] += RIDGE*A[:-1]
        loss = weights @ ce + RIDGE/2*np.sum(A[:-1]**2)
    if not np.isfinite(loss) or not np.isfinite(gradient).all():
        raise ValueError('nonfinite masked loss/gradient')
    return float(loss), gradient


def learning_rate(X, weights):
    X = matrix(X)
    weights = np.asarray(weights, float)
    if (weights.shape != (len(X),) or not np.isfinite(weights).all()
            or np.any(weights <= 0) or not np.isclose(weights.sum(), 1, rtol=0, atol=1e-12)):
        raise ValueError('normalized trace weights required')
    with np.errstate(over='raise', invalid='raise'):
        bound = .5*np.dot(weights, np.sum(X**2, axis=1)+1)+RIDGE
    if not np.isfinite(bound) or bound <= 0:
        raise ValueError('finite trace bound required')
    return float(1/bound)


def challenge_mask(X, y, A, variant, rng):
    """true-class signed梯度／貢獻／matched random；只在known train使用truth。"""
    X = matrix(X)
    A, y = coefficients(A, X, y)
    if variant not in VARIANTS:
        raise ValueError('unregistered challenge variant')
    n, D = X.shape
    mask = np.ones_like(X)
    if variant == 'unmasked':
        return mask, dict(challenged_rows=0, muted_features=0, nonpositive_drop_fraction=None,
                          mean_true_probability_drop=0., column_muted_counts=[0]*D,
                          mask_checksum=array_checksum(mask))
    if not isinstance(rng, np.random.Generator):
        raise ValueError('default_rng generator required')
    with np.errstate(over='raise', invalid='raise'):
        salience = (rng.random(X.shape) if variant == 'random' else
                    A[:-1, y].T if variant == 'signed_gradient' else X*A[:-1, y].T)
        k, b = int(np.ceil(D*FRACTION)), int(np.ceil(n*FRACTION))
        order = np.argsort(-salience, axis=1, kind='stable')[:, :k]
        candidate = np.ones_like(X)
        candidate[np.arange(n)[:, None], order] = 0
        before = softmax(X @ A[:-1]+A[-1], axis=1)[np.arange(n), y]
        after = softmax((X*candidate) @ A[:-1]+A[-1], axis=1)[np.arange(n), y]
        drop = before-after
    if not np.isfinite(salience).all() or not np.isfinite(drop).all():
        raise ValueError('nonfinite challenge salience/probability')
    rows = np.argsort(-drop, kind='stable')[:b]
    mask[rows] = candidate[rows]
    stats = dict(challenged_rows=b, muted_features=b*k,
        nonpositive_drop_fraction=float(np.mean(drop[rows] <= 0)),
        mean_true_probability_drop=float(drop[rows].mean()),
        column_muted_counts=np.sum(mask == 0, axis=0).tolist(), mask_checksum=array_checksum(mask))
    return mask, stats


class SelfChallengingClassifier:
    """200固定步數最後iterate；不宣稱最佳化收斂或RSC理論保證。"""
    def __init__(self, variant='signed_gradient', seed=42):
        if variant not in VARIANTS:
            raise ValueError('unregistered challenge variant')
        self.variant, self.seed = variant, int(seed)

    def fit(self, X, y, domains, warm_start):
        X, y, env, ew, counts, environments = risk_design(X, y, domains)
        self.source_ = dict(features=array_checksum(X), labels=array_checksum(y),
                            environments=digest(np.asarray(domains).tolist()))
        if (not isinstance(warm_start, RiskExtrapolationClassifier) or warm_start.beta != 0
                or warm_start.seed != self.seed or warm_start.source_ != self.source_):
            raise ValueError('same known source/seed ERM warm start required')
        warm_start.validate()
        self.classes_, self.n_features_in_ = np.arange(counts.shape[1]), X.shape[1]
        self.counts_, self.environments_ = counts, environments.tolist()
        A = np.vstack([warm_start.coef_.T, warm_start.intercept_]).copy()
        self.initial_checksum_, self.warm_start_checksum_ = array_checksum(A), warm_start.checksum_
        weights = ew/3
        eta = learning_rate(X, weights)
        rng = np.random.default_rng(self.seed)
        self.history_ = []
        try:
            for step in range(STEPS):
                mask, stat = challenge_mask(X, y, A, self.variant, rng)
                value, gradient = loss_gradient(A, X*mask, y, weights)
                with np.errstate(over='raise', invalid='raise'):
                    A -= eta*gradient
                if not np.isfinite(A).all():
                    raise ValueError('nonfinite fixed-horizon coefficients')
                self.history_.append(dict(step=step+1, masked_objective=value,
                    gradient_inf=float(np.max(np.abs(gradient))), **stat))
            full_value, gradient = loss_gradient(A, X, y, weights)
            logits = X @ A[:-1]+A[-1]
            ce = logsumexp(logits, axis=1)-logits[np.arange(len(y)), y]
            risks = np.bincount(env, weights=ew*ce, minlength=3)
        except (ValueError, FloatingPointError) as exc:
            raise RuntimeError('INCOMPLETE challenge training: '+str(exc)) from exc
        self.coef_, self.intercept_ = A[:-1].T.copy(), A[-1].copy()
        self.optimizer_ = dict(success=True, status='FIXED_HORIZON_COMPLETE', converged_not_claimed=True,
            steps=STEPS, objective=full_value, gradient_inf=float(np.max(np.abs(gradient))),
            learning_rate=eta, risks=risks.tolist(), risk_mean=float(risks.mean()),
            risk_population_variance=float(np.var(risks)), training=TRAINING.copy(),
            history_checksum=digest(self.history_))
        self.checksum_ = self.signature()
        return self

    def signature(self):
        return digest(dict(variant=self.variant, seed=self.seed, source=self.source_,
            dimensions=self.n_features_in_, classes=self.classes_.tolist(), counts=self.counts_.tolist(),
            environments=self.environments_, coef=self.coef_.tolist(), intercept=self.intercept_.tolist(),
            optimizer=self.optimizer_, history=self.history_, initial=self.initial_checksum_,
            warm_start=self.warm_start_checksum_))

    def validate(self):
        if (self.signature() != self.checksum_ or self.optimizer_['training'] != TRAINING
                or self.optimizer_['status'] != 'FIXED_HORIZON_COMPLETE'
                or len(self.history_) != STEPS or self.variant not in VARIANTS):
            raise ValueError('challenge classifier tampered')

    def decision_function(self, X):
        self.validate()
        X = matrix(X, self.n_features_in_, nonempty=False)
        with np.errstate(over='ignore', invalid='ignore'):
            logits = X @ self.coef_.T+self.intercept_
        if not np.isfinite(logits).all():
            raise ValueError('nonfinite challenge inference')
        return logits

    def predict_proba(self, X):
        return softmax(self.decision_function(X), axis=1)

    def predict(self, X):
        return self.classes_[self.decision_function(X).argmax(1)]

    def verify_known_source(self, X, y, domains, warm_start):
        self.validate()
        rebuilt = SelfChallengingClassifier(self.variant, self.seed).fit(X, y, domains, warm_start)
        if rebuilt.signature() != self.signature():
            raise ValueError('actual known challenge source mismatch')
        return dict(classifier_checksum=self.checksum_, source=self.source_,
                    optimizer=self.optimizer_, test_numeric_reads=0)
