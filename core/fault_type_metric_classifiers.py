"""實驗13：單／多中心與 LMNN Eq.15 分類；正式預設不變。"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances
from core.fault_type_literature import finite
from core.fault_type_final_guard import digest


def weight_transform(X, weights):
    X = finite(X)
    w = np.asarray(weights, float)
    if w.ndim != 1 or X.shape[1] != len(w) or not np.isfinite(w).all() or (w < 0).any():
        raise ValueError('invalid nonnegative diagonal weights')
    return X * np.sqrt(w)


class PrototypeClassifier:
    """平均中心或每類固定數目的 KMeans 中心，僅由 train 建立。"""
    def __init__(self, centers=1, seed=42):
        if centers not in [1, 3]:
            raise ValueError('fixed one/three centers')
        self.centers = centers
        self.seed = seed

    def fit(self, X, y):
        X = finite(X); y = np.asarray(y)
        if y.ndim != 1 or len(y) != len(X):
            raise ValueError('training labels')
        self.classes_ = np.unique(y)
        self.prototypes_ = []; self.prototype_labels_ = []
        rng = np.random.default_rng(self.seed)
        for c in self.classes_:
            xx = X[y == c]
            if len(xx) < self.centers:
                raise ValueError('insufficient prototype samples')
            if self.centers == 1:
                pts = xx.mean(0)[None, :]
            else:
                pts = KMeans(n_clusters=3, n_init=10, max_iter=300, tol=1e-4,
                    algorithm='lloyd', random_state=int(rng.integers(0, 2**31-1))).fit(xx).cluster_centers_
            self.prototypes_.extend(pts); self.prototype_labels_.extend([c] * len(pts))
        self.prototypes_ = np.asarray(self.prototypes_)
        self.prototype_labels_ = np.asarray(self.prototype_labels_)
        self.checksum = digest([self.prototypes_.tolist(), self.prototype_labels_.tolist()])
        return self

    def predict(self, X):
        if self.checksum != digest([self.prototypes_.tolist(), self.prototype_labels_.tolist()]):
            raise ValueError('prototype tampered')
        X = finite(X)
        return self.prototype_labels_[np.argmin(pairwise_distances(X, self.prototypes_, metric='sqeuclidean'), axis=1)]


class MarginEnergyClassifier:
    """Weinberger & Saul 2009 §3.5 Eq.15，接本站對角 metric。

    三項均保留原式求和。test 僅是假定類別評分，不更新 reference。
    target 由原表示空間選定；平方距離由封存的非負權重計算。
    """
    def __init__(self, k=3, mu=.5, batch_size=128):
        self.k = k; self.mu = mu; self.batch_size = batch_size

    def fit(self, X, y, weights):
        X = finite(X); y = np.asarray(y)
        if y.ndim != 1 or len(y) != len(X) or len(X) > 360 or self.k != 3 or self.mu != .5:
            raise ValueError('fixed bounded energy training')
        self.X_ = X.copy(); self.y_ = y.copy(); self.weights_ = np.asarray(weights, float).copy()
        self.Z_ = weight_transform(X, weights); self.classes_ = np.unique(y)
        distances = pairwise_distances(X, metric='sqeuclidean')
        targets = []
        for i in range(len(y)):
            ix = np.flatnonzero((y == y[i]) & (np.arange(len(y)) != i))
            if len(ix) < self.k: raise ValueError('insufficient same-class target neighbors')
            targets.append(ix[np.argsort(distances[i, ix], kind='stable')[:self.k]])
        self.targets_ = np.asarray(targets)
        metric_dist = pairwise_distances(self.Z_, metric='sqeuclidean')
        self.target_distances_ = metric_dist[np.arange(len(y))[:, None], self.targets_]
        self.checksum = self.signature()
        return self

    def signature(self):
        return digest([self.X_.tolist(), self.y_.tolist(), self.weights_.tolist(),
            self.targets_.tolist(), self.target_distances_.tolist(), self.Z_.tolist(), self.k, self.mu])

    def energies(self, X):
        if self.signature() != self.checksum: raise ValueError('energy reference tampered')
        X = np.asarray(X,float)
        if X.ndim != 2 or X.shape[1] != self.X_.shape[1] or not np.isfinite(X).all():
            raise ValueError('finite energy query dimensions')
        result = []
        for start in range(0, len(X), self.batch_size):
            xx = X[start:start+self.batch_size]
            original = pairwise_distances(xx, self.X_, metric='sqeuclidean')
            d = pairwise_distances(weight_transform(xx, self.weights_), self.Z_, metric='sqeuclidean')
            values = []
            for c in self.classes_:
                same = np.flatnonzero(self.y_ == c); other = np.flatnonzero(self.y_ != c)
                target = same[np.argsort(original[:, same], axis=1, kind='stable')[:, :self.k]]
                pull = np.take_along_axis(d, target, axis=1)
                outgoing = np.maximum(1 + pull[:, :, None] - d[:, None, other], 0).sum((1, 2))
                incoming = np.maximum(1 + self.target_distances_[other][None, :, :] - d[:, other, None], 0).sum((1, 2))
                values.append((1-self.mu)*pull.sum(1) + self.mu*(outgoing+incoming))
            result.append(np.column_stack(values))
        return np.vstack(result) if result else np.empty((0, len(self.classes_)))

    def predict(self, X):
        return self.classes_[np.argmin(self.energies(X), axis=1)]
