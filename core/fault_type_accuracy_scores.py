"""Explicit new research score IDs. Existing factory formulas are not changed.

Class-conditional conformal uses own-class calibration nonconformity, >= ties,
and fixed alpha .05. Exchangeability across motors/windows is NOT established.
"""
from __future__ import annotations
import numpy as np
from sklearn.covariance import LedoitWolf
from core.mahalanobis import _distances


def matrix(X):
    X=np.asarray(X,float)
    if X.ndim!=2 or not np.isfinite(X).all():raise ValueError('finite2D scores/features required')
    return X


class PooledWithinLW:
    def fit(self,X,y,n_classes):
        X=matrix(X);y=np.asarray(y)
        if len(X)!=len(y) or set(np.unique(y))!=set(range(n_classes)):raise ValueError('all known train classes required')
        self.means=np.array([X[y==c].mean(0) for c in range(n_classes)])
        self.covariance=LedoitWolf(assume_centered=True).fit(X-self.means[y])
        self.train_rows=len(X)
        return self

    def raw_scores(self,X):
        X=matrix(X)
        return np.column_stack([_distances(X,mu,self.covariance.precision_) for mu in self.means])


class ResearchScore:
    def __init__(self,definition,alpha=.05):
        self.definition=definition;self.alpha=alpha

    def calibrate(self,raw,y):
        raw=matrix(raw);y=np.asarray(y)
        if not len(raw) or len(raw)!=len(y) or set(np.unique(y))!=set(range(raw.shape[1])):
            raise ValueError('every calibration class required')
        self.calibration=[np.asarray(raw[y==c,c],float) for c in range(raw.shape[1])]
        self.sorted_calibration=[np.sort(v) for v in self.calibration]
        kind=self.definition['calibration']
        if kind=='global_quantile':self.thresholds=np.array([np.quantile(raw.min(1),.95,method='linear')])
        elif kind=='class_quantile':self.thresholds=np.array([np.quantile(v,.95,method='linear') for v in self.calibration])
        elif kind=='conditional_conformal':self.thresholds=None
        else:raise ValueError('unknown score calibration ID')
        return self

    def details(self,raw):
        raw=matrix(raw)
        if raw.shape[1]!=len(self.calibration):raise ValueError('score class dimension differs')
        kind=self.definition['calibration']
        if kind=='conditional_conformal':
            p=np.column_stack([(1+len(v)-np.searchsorted(v,raw[:,c],side='left'))/(len(v)+1) for c,v in enumerate(self.sorted_calibration)])
            values=1-p.max(1);reject=p.max(1)<=self.alpha
            return {'score':values,'reject':reject,'nearest':p.argmax(1),'p_values':p,
                    'candidate_size':(p>self.alpha).sum(1),'ratios':None,'threshold':1-self.alpha}
        ratios=raw/np.maximum(self.thresholds,np.finfo(float).eps)
        values=ratios.min(1)
        return {'score':values,'reject':values>1,'nearest':ratios.argmin(1),'p_values':None,
                'candidate_size':None,'ratios':ratios,'threshold':1.}

    def summaries(self):
        return {'score_id':self.definition['id'],'reference':self.definition['reference'],
            'calibration':self.definition['calibration'],
            'thresholds':None if self.thresholds is None else self.thresholds.tolist(),
            'class_calibration_counts':[len(v) for v in self.calibration],
            'minimum_p':[1/(len(v)+1) for v in self.calibration],
            'resolution_cannot_reject_at_alpha':[1/(len(v)+1)>self.alpha for v in self.calibration],
            'alpha':self.alpha,'ties':'>=','exchangeability':'UNVERIFIED'}
