"""實驗14：依 Sugiyama 2007 權重式實作正則化 LFDA；不改正式模型。"""
import numpy as np
from scipy.linalg import eigh
from sklearn.decomposition import PCA
from sklearn.metrics import pairwise_distances
from core.fault_type_final_guard import digest


def finite_matrix(X, width=None, empty=False):
    X = np.asarray(X, float)
    if X.ndim != 2 or not np.isfinite(X).all() or (not empty and not len(X)) or (width is not None and X.shape[1] != width):
        raise ValueError('finite projection matrix')
    return X


def affinity_weights(X, y, k=7):
    """Eq.9–10；自身不計入第k鄰居，零尺度採事前固定數值保護。"""
    X = finite_matrix(X); y = np.asarray(y); n = len(X)
    if y.ndim != 1 or len(y) != n or k != 7 or n > 360 or len(np.unique(y)) < 2:
        raise ValueError('fixed LFDA known training subset')
    distances = pairwise_distances(X, metric='sqeuclidean')
    positive = distances[distances > 0]
    floor = max(float(np.sqrt(np.median(positive))) * 1e-12, 1e-12) if len(positive) else 1e-12
    within = np.zeros((n, n)); between = np.full((n, n), 1/n)
    scales = np.zeros(n)
    for c in np.unique(y):
        ix = np.flatnonzero(y == c); nc = len(ix)
        if nc <= k:
            raise ValueError('insufficient same-class neighbors')
        d = distances[np.ix_(ix, ix)].copy(); np.fill_diagonal(d, np.inf)
        sigma = np.maximum(np.sqrt(np.partition(d, k-1, axis=1)[:, k-1]), floor)
        a = np.exp(-distances[np.ix_(ix, ix)] / np.outer(sigma, sigma))
        np.fill_diagonal(a, 0)
        within[np.ix_(ix, ix)] = a/nc
        between[np.ix_(ix, ix)] = a*(1/n - 1/nc)
        scales[ix] = sigma
    np.fill_diagonal(between, 0)
    return within, between, scales, floor


def scatter(X, weights):
    """0.5Σ W_ij(x_i−x_j)(x_i−x_j)^T，支援 LFDA 的負權重。"""
    X = finite_matrix(X); w = np.asarray(weights, float)
    if w.shape != (len(X), len(X)) or not np.isfinite(w).all() or not np.allclose(w, w.T, rtol=0, atol=1e-14):
        raise ValueError('symmetric affinity weights')
    result = X.T @ (w.sum(1)[:, None]*X - w@X)
    return (result+result.T)/2


class LocalProjection:
    """PCA 與 LFDA 固定秩消融；fit 僅接受已核對的 train 子集。"""
    def __init__(self, kind, dimension):
        if kind not in ['pca', 'lfda'] or dimension not in [10, 20]:
            raise ValueError('fixed projection definition')
        self.kind = kind; self.dimension = dimension

    def fit(self, X, y):
        X = finite_matrix(X); y = np.asarray(y)
        if len(X) > 360 or X.shape[1] < self.dimension or len(X) <= self.dimension or y.shape != (len(X),):
            raise ValueError('bounded projection training shape')
        self.mean_ = X.mean(0); centered = X-self.mean_
        self.input_checksum_ = digest([X.tolist(), y.tolist()])
        if self.kind == 'pca':
            model = PCA(n_components=self.dimension, svd_solver='full', whiten=False).fit(X)
            self.components_ = model.components_.copy(); self.mean_ = model.mean_.copy()
            self.diagnostics_ = {'explained_variance': model.explained_variance_.tolist(), 'ridge': 0., 'uses_labels': False}
        else:
            w, b, scales, floor = affinity_weights(centered, y)
            sw = scatter(centered, w); sb = scatter(centered, b)
            ridge = max(float(np.trace(sw)/X.shape[1]), 1e-12)*1e-6
            regularized = sw + ridge*np.eye(X.shape[1])
            values, vectors = eigh(sb, regularized, check_finite=True)
            order = np.argsort(-values, kind='stable')[:self.dimension]
            values = values[order]; vectors = vectors[:, order]
            if not np.isfinite(values).all() or (values <= 0).any():
                raise ValueError('insufficient positive LFDA directions')
            residual = np.linalg.norm(sb@vectors-(regularized@vectors)*values)/max(np.linalg.norm(sb@vectors), 1e-12)
            if not np.isfinite(residual) or residual > 1e-7:
                raise ValueError('LFDA eigen residual')
            self.components_ = (vectors*np.sqrt(values)).T
            self.diagnostics_ = {'eigenvalues':values.tolist(), 'ridge':ridge, 'relative_eigen_residual':float(residual),
                'scale_floor':floor, 'scales_checksum':digest(scales.tolist()), 'within_checksum':digest(sw.tolist()),
                'between_checksum':digest(sb.tolist()), 'uses_labels':True}
        for row in self.components_:
            if row[np.argmax(np.abs(row))] < 0:
                row *= -1
        self.checksum_ = self.signature()
        return self

    def signature(self):
        return digest([self.kind, self.dimension, self.mean_.tolist(), self.components_.tolist(), self.input_checksum_, self.diagnostics_])

    def transform(self, X):
        if self.signature() != self.checksum_:
            raise ValueError('projection tampered')
        X = finite_matrix(X, len(self.mean_), empty=True)
        return (X-self.mean_) @ self.components_.T
