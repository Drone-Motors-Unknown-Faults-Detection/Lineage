"""Train-only, bounded research adaptations; production formal105 unchanged.

Diagonal margin loss is inspired by Weinberger & Saul, JMLR10 (2009).
Departures/ablations: reports/continuous_research/hypothesis_adaptation_cards.md.
"""
import time
import numpy as np
from scipy.optimize import minimize
from sklearn.preprocessing import RobustScaler
from core.fault_type_literature import finite
from core.fault_type_final_guard import digest


def stratified_subset(y, rpms, seed, per_cell=20):
    y=np.asarray(y); rpms=np.asarray(rpms); rng=np.random.default_rng(seed)
    if len(y)!=len(rpms) or not len(y): raise ValueError('subset input length')
    return np.array(sorted(int(i) for c in np.unique(y) for rpm in sorted(set(rpms))
        for ix in [np.flatnonzero((y==c)&(rpms==rpm))]
        for i in rng.choice(ix,size=min(per_cell,len(ix)),replace=False)),int)


def margin_problem(X,y,k=3):
    X=finite(X); y=np.asarray(y)
    if len(X)!=len(y) or len(np.unique(y))<2: raise ValueError('margin labels')
    delta=(X[:,None,:]-X[None,:,:])**2; dist=delta.sum(2)
    targets=[]
    for i in range(len(X)):
        ix=np.flatnonzero((y==y[i])&(np.arange(len(y))!=i))
        if len(ix)<k: raise ValueError('insufficient same-class targets')
        targets.append(ix[np.argsort(dist[i,ix],kind='stable')[:k]])
    targets=np.asarray(targets); pull=delta[np.arange(len(X))[:,None],targets]
    negative=y[:,None]!=y[None,:]
    return delta,pull,negative


def margin_loss_grad(w,problem,ridge=.01):
    delta,pull,negative=problem
    pd=pull@w; nd=delta@w
    hinge=1+pd[:,:,None]-nd[:,None,:]
    active=(hinge>0)&negative[:,None,:]
    denom=int(negative.sum())*pull.shape[1]
    value=.5*pd.mean()+.5*np.maximum(hinge,0)[np.broadcast_to(negative[:,None,:],hinge.shape)].sum()/denom+ridge*np.mean((w-1)**2)
    grad=.5*pull.mean((0,1))+.5*(np.einsum('ik,ikd->d',active.sum(2),pull)-np.einsum('il,ild->d',active.sum(1),delta))/denom+2*ridge*(w-1)/len(w)
    return float(value),grad


class DiagonalMargin:
    def fit(self,X,y,*,seconds=120):
        X=finite(X)
        if len(X)>360: raise ValueError('bounded metric subset exceeds 360')
        problem=margin_problem(X,y); start=time.perf_counter()
        def objective(w):
            if time.perf_counter()-start>seconds: raise RuntimeError('metric CPU wall budget exhausted')
            return margin_loss_grad(w,problem)
        initial=margin_loss_grad(np.ones(X.shape[1]),problem)[0]
        result=minimize(objective,np.ones(X.shape[1]),jac=True,method='L-BFGS-B',
            bounds=[(0,None)]*X.shape[1],options={'maxiter':150,'maxfun':500,'maxls':50,'ftol':1e-9,'gtol':1e-6})
        self.weights=np.asarray(result.x); self.optimizer={'success':bool(result.success),'status':int(result.status),
            'message':str(result.message),'iterations':int(result.nit),'evaluations':int(result.nfev),
            'initial_loss':initial,'final_loss':float(result.fun),'seconds':time.perf_counter()-start,
            'maxiter':150,'maxfun':500,'maxls':50,'budget_seconds':seconds,'weight_min':float(self.weights.min()),
            'weight_max':float(self.weights.max()),'zero_weights':int(sum(self.weights==0))}
        if not result.success: raise RuntimeError('metric not converged: '+str(result.message))
        self.checksum=digest(self.weights.tolist());return self
    def transform(self,X):
        if digest(self.weights.tolist())!=self.checksum: raise ValueError('metric tampered')
        X=finite(X)
        if X.shape[1]!=len(self.weights):raise ValueError('metric dimension')
        return X*np.sqrt(self.weights)


class GainRepresentation:
    def __init__(self,dimension):
        if dimension not in [63,66,69]:raise ValueError('gain representation dimension')
        self.dimension=dimension
    def raw(self,X):
        X=finite(X)
        if X.shape[1]!=105: raise ValueError('formal105 input required')
        blocks=[];relative=[];absolute=[]
        for axis,off in enumerate([15,40,65]):
            rms=np.maximum(X[:,off],self.rms_floor[axis]);cols=[]
            for i in [1,2,3,4,5,6,7,8,10,11,14]:
                z=X[:,off+i]
                cols.append(z/rms if i in [1,3,5,10,11,14] else z)
            mag=np.abs(X[:,off+15:off+25]);total=mag.sum(1)
            blocks.append(np.column_stack([*cols,mag/np.maximum(total[:,None],self.harmonic_floor[axis])]))
            relative.append(np.log1p(total/rms));absolute.append(np.log1p(rms/self.rms_floor[axis]))
        raw=np.column_stack(blocks)
        if self.dimension>=66:raw=np.column_stack([raw,*relative])
        if self.dimension==69:raw=np.column_stack([raw,*absolute])
        return finite(raw)
    def fit(self,X,y=None):
        X=finite(X)
        if X.shape[1]!=105 or np.any(X[:,[15,40,65]]<0):raise ValueError('invalid formal/RMS')
        self.rms_floor=np.maximum(np.median(X[:,[15,40,65]],0)*1e-6,1e-12)
        self.harmonic_floor=np.array([max(np.median(np.abs(X[:,o+15:o+25]).sum(1))*1e-6,1e-12) for o in [15,40,65]])
        self.scaler=RobustScaler(quantile_range=(25,75)).fit(self.raw(X))
        self.checksum=self.signature();return self
    def signature(self):
        return digest({'dim':self.dimension,'rms_floor':self.rms_floor.tolist(),'harmonic_floor':self.harmonic_floor.tolist(),
            'center':self.scaler.center_.tolist(),'scale':self.scaler.scale_.tolist()})
    def transform(self,X):
        if self.signature()!=self.checksum:raise ValueError('gain transform tampered')
        return finite(self.scaler.transform(self.raw(X)))
