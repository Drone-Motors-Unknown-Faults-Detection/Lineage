"""Bounded paper-inspired train-only mechanisms; no production changes.

Sources/formulas: reports/mechanism_research_v2/adaptation_cards.md.
Inference accepts numeric features and declared RPM ONLY, never true labels.
"""
from __future__ import annotations
import ctypes
import os
import numpy as np
from sklearn.covariance import LedoitWolf


def matrix(X, dimension=None):
    X=np.asarray(X,float)
    if X.ndim!=2 or not len(X) or not np.isfinite(X).all() or (dimension is not None and X.shape[1]!=dimension):
        raise ValueError('finite nonempty matrix/dimension required')
    return X


def training(X,y,K):
    X=matrix(X);y=np.asarray(y)
    if y.shape!=(len(X),) or not np.array_equal(np.unique(y),np.arange(K)) or min(np.bincount(y.astype(int)))<2:
        raise ValueError('all declared known classes need >=2 train samples')
    if not np.array_equal(y,y.astype(int)):raise ValueError('integer class order required')
    return X,y.astype(int)


def precision(cov):
    cov=matrix(cov)
    if cov.shape[0]!=cov.shape[1] or not np.allclose(cov,cov.T):raise ValueError('symmetric covariance required')
    w,v=np.linalg.eigh(cov);floor=max(float(np.trace(cov)/len(cov)),1e-12)*1e-10
    if w.min() < -floor:raise ValueError('negative covariance eigenvalue')
    return (v/np.maximum(w,floor))@v.T


def within(X,y,K):
    means=np.array([X[y==c].mean(0) for c in range(K)])
    residual=X-means[y]
    estimator=LedoitWolf(assume_centered=True).fit(residual)
    return means,estimator.covariance_,float(estimator.shrinkage_)


class RPMPartialPooling:
    def __init__(self,beta,rpms,K):
        if not 0<=beta<=1:raise ValueError('beta outside [0,1]')
        self.beta=float(beta);self.rpms=list(rpms);self.K=K

    def fit(self,X,y,rpms):
        X,y=training(X,y,self.K);rpms=np.asarray(rpms)
        if rpms.shape!=(len(X),) or set(rpms)!=set(self.rpms):raise ValueError('RPM coverage')
        self.dimension=X.shape[1];gm,gc,gs=within(X,y,self.K);self.global_means=gm;self.global_covariance=gc
        self.nodes={};self.shrinkages={'global':gs}
        for rpm in self.rpms:
            z,cy=training(X[rpms==rpm],y[rpms==rpm],self.K)
            lm,lc,ls=within(z,cy,self.K)
            mu=(1-self.beta)*lm+self.beta*gm;cov=(1-self.beta)*lc+self.beta*gc
            self.nodes[rpm]=(mu,cov,precision(cov));self.shrinkages[rpm]=ls
        return self

    def predict(self,X,rpms):
        X=matrix(X,self.dimension);rpms=np.asarray(rpms)
        if rpms.shape!=(len(X),) or not set(rpms)<=set(self.rpms):raise ValueError('undeclared inference RPM')
        result=np.empty(len(X),int)
        for rpm in self.rpms:
            ix=np.flatnonzero(rpms==rpm)
            if not len(ix):continue
            mu,_,P=self.nodes[rpm]
            logits=X[ix]@P@mu.T-.5*np.einsum('ij,jk,ik->i',mu,P,mu)[None,:]
            result[ix]=logits.argmax(1) # uniform priors; deterministic lowest-index tie.
        return result


HARMONIC_BLOCKS=[ [i for i in range(66) if i%22<12],
                  [i for i in range(66) if i%22>=12], [66,67,68] ]


class BlockGeometry:
    def __init__(self,K,blocks=None):self.K=K;self.blocks=HARMONIC_BLOCKS if blocks is None else blocks

    def fit(self,X,y):
        X,y=training(X,y,self.K);self.dimension=X.shape[1]
        flat=[i for b in self.blocks for i in b]
        if sorted(flat)!=list(range(self.dimension)) or any(not b for b in self.blocks):raise ValueError('nonoverlapping full block partition required')
        self.models=[];self.shrinkages=[]
        for indices in self.blocks:
            Z=X[:,indices];mu,cov,s=within(Z,y,self.K)
            bg=LedoitWolf().fit(Z)
            self.models.append((mu,precision(cov),bg.location_,precision(bg.covariance_)))
            self.shrinkages.append({'within':s,'background':float(bg.shrinkage_)})
        return self

    def distances(self,X):
        X=matrix(X,self.dimension);d=np.zeros((len(X),self.K));background=np.zeros(len(X))
        for ix,(mu,P,bm,BP) in zip(self.blocks,self.models):
            z=X[:,ix]
            for c in range(self.K):
                delta=z-mu[c];d[:,c]+=np.einsum('ij,jk,ik->i',delta,P,delta)/len(ix)/len(self.blocks)
            delta=z-bm;background+=np.einsum('ij,jk,ik->i',delta,BP,delta)/len(ix)/len(self.blocks)
        return d,background

    def score(self,X,weight=0.):
        if weight not in [0.,1.]:raise ValueError('fixed background weights only')
        d,bg=self.distances(X);return d.min(1)-weight*bg

    def predict(self,X):return self.distances(X)[0].argmin(1)


def calibrate(scores):
    s=np.asarray(scores,float)
    if s.ndim!=1 or not len(s) or not np.isfinite(s).all():raise ValueError('finite nonempty calibration required')
    return float(np.quantile(s,.95,method='linear'))


def peak_memory_bytes():
    """Process cumulative peak, NOT isolated per-cell incremental memory."""
    if os.name!='nt':
        import resource
        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in
            ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True);psapi=ctypes.WinDLL('psapi',use_last_error=True)
    kernel.GetCurrentProcess.restype=wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    c=Counters();c.cb=ctypes.sizeof(c)
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(c),c.cb):raise OSError(ctypes.get_last_error())
    return int(c.PeakWorkingSetSize)
