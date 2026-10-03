"""實驗15：Sato／Yamada GLVQ的有限原型改編，正式預設不變。

來源、固定β／anchor／optimizer差異見exp15手冊；不複製外部套件。
"""
import time
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit
from scipy.spatial.distance import cdist
from core.fault_type_final_guard import digest
from core.fault_type_literature import finite
from core.fault_type_metric_classifiers import PrototypeClassifier

OPTIONS={'maxiter':600,'maxfun':2000,'maxls':50,'ftol':1e-9,'gtol':1e-6}
EPSILON=1e-12
BETA=4.


def relative_objective(W,X,y,labels,initial,anchor=0.):
    """平均sigmoid相對距離及解析梯度；true y只出現在train objective。"""
    W=finite(W);X=finite(X);initial=finite(initial)
    y=np.asarray(y);labels=np.asarray(labels)
    if (W.shape!=initial.shape or W.shape[1]!=X.shape[1] or len(y)!=len(X) or
        y.ndim!=1 or labels.ndim!=1 or len(labels)!=len(W) or anchor not in [0.,.01] or
        len(np.unique(labels))<2 or not set(y).issubset(set(labels))):raise ValueError('prototype objective sources')
    distances=cdist(X,W,'sqeuclidean');same=y[:,None]==labels[None,:]
    positive=np.argmin(np.where(same,distances,np.inf),axis=1)
    negative=np.argmin(np.where(~same,distances,np.inf),axis=1)
    dp=distances[np.arange(len(X)),positive];dn=distances[np.arange(len(X)),negative]
    den=dp+dn+EPSILON;mu=(dp-dn)/den;s=expit(BETA*mu)
    gain=BETA*s*(1-s)/len(X)
    grad=np.zeros_like(W)
    np.add.at(grad,positive,(gain*(2*dn+EPSILON)/den**2)[:,None]*2*(W[positive]-X))
    np.add.at(grad,negative,(gain*(-2*dp-EPSILON)/den**2)[:,None]*2*(W[negative]-X))
    value=s.mean()+anchor*np.mean((W-initial)**2)
    grad+=2*anchor*(W-initial)/W.size
    if not np.isfinite(value) or not np.isfinite(grad).all():raise ValueError('nonfinite prototype loss')
    return float(value),grad


class DiscriminativePrototypes:
    """known train初始化／子集loss；未收斂保存狀態但禁止推論。"""
    def __init__(self,centers=1,variant='static',seed=42):
        if centers not in [1,3] or variant not in ['static','glvq','anchored']:raise ValueError('fixed prototype definition')
        self.centers=centers;self.variant=variant;self.seed=seed

    def fit(self,X,y,indices,*,seconds=120,options=None):
        X=finite(X);y=np.asarray(y);ix=np.asarray(indices)
        if (y.ndim!=1 or len(y)!=len(X) or ix.ndim!=1 or not np.issubdtype(ix.dtype,np.integer) or
            not 0<len(ix)<=360 or len(set(ix.tolist()))!=len(ix) or (ix<0).any() or (ix>=len(X)).any() or
            len(np.unique(y))<2 or set(y[ix])!=set(y) or seconds<=0):raise ValueError('known bounded prototype fit')
        initial=PrototypeClassifier(self.centers,self.seed).fit(X,y)
        self.initial_=initial.prototypes_.copy();self.labels_=initial.prototype_labels_.copy();self.classes_=initial.classes_.copy()
        self.train_checksum_=digest([X.tolist(),y.tolist(),ix.tolist()])
        self.options_=dict(OPTIONS if options is None else options)
        anchor=.01 if self.variant=='anchored' else 0.
        xx=X[ix];yy=y[ix];W0=self.initial_;start=time.perf_counter()
        initial_loss,initial_grad=relative_objective(W0,xx,yy,self.labels_,W0,anchor)
        self.prototypes_=W0.copy();last={'W':W0.copy()}
        if self.variant=='static':
            self.optimizer_={'success':True,'message':'STATIC_NO_OPTIMIZATION','iterations':0,'evaluations':0}
        else:
            def objective(flat):
                if time.perf_counter()-start>seconds:raise TimeoutError('prototype optimizer time budget')
                W=flat.reshape(W0.shape);loss,grad=relative_objective(W,xx,yy,self.labels_,W0,anchor)
                last['W']=W.copy();return loss,grad.ravel()
            try:
                result=minimize(objective,W0.ravel(),jac=True,method='L-BFGS-B',options=self.options_)
                self.prototypes_=result.x.reshape(W0.shape)
                self.optimizer_={'success':bool(result.success),'message':str(result.message),'status':int(result.status),
                    'iterations':int(result.nit),'evaluations':int(result.nfev)}
            except TimeoutError as error:
                self.prototypes_=last['W'];self.optimizer_={'success':False,'message':str(error),'status':'TIME_BUDGET'}
        loss,grad=relative_objective(self.prototypes_,xx,yy,self.labels_,W0,anchor)
        self.optimizer_.update(initial_loss=initial_loss,final_loss=loss,gradient_inf_norm=float(np.max(np.abs(grad))),
            seconds=time.perf_counter()-start,budget_seconds=seconds,options=self.options_,anchor=anchor,beta=BETA,epsilon=EPSILON,
            initialization_gradient_inf_norm=float(np.max(np.abs(initial_grad))))
        self.checksum_=self.signature()
        return self

    def signature(self):
        stable={k:v for k,v in self.optimizer_.items() if k!='seconds'}
        return digest([self.centers,self.variant,self.seed,self.train_checksum_,self.initial_.tolist(),
            self.prototypes_.tolist(),self.labels_.tolist(),self.classes_.tolist(),stable])

    def distances(self,X):
        if self.signature()!=self.checksum_:raise ValueError('prototype state tampered')
        if not self.optimizer_['success']:raise ValueError('unconverged prototype cannot infer')
        X=np.asarray(X,float)
        if X.ndim!=2 or X.shape[1]!=self.prototypes_.shape[1] or not np.isfinite(X).all():raise ValueError('finite prototype query dimensions')
        return cdist(X,self.prototypes_,'sqeuclidean')

    def predict(self,X):
        return self.labels_[np.argmin(self.distances(X),axis=1)]

    def ambiguity(self,X):
        distances=self.distances(X);closest=np.argmin(distances,axis=1);pred=self.labels_[closest]
        near=distances[np.arange(len(distances)),closest]
        other=np.min(np.where(self.labels_[None,:]!=pred[:,None],distances,np.inf),axis=1)
        score=1+(near-other)/(near+other+EPSILON)
        if not np.isfinite(score).all():raise ValueError('nonfinite ambiguity score')
        return score


def calibrate_ambiguity(model,C):
    C=finite(C)
    return float(np.quantile(model.ambiguity(C),.95,method='linear'))
