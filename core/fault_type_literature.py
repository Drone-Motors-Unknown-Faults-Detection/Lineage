"""Versioned research adaptations; never changes production detectors/defaults.

Source graph and precise departures are in reports/literature_expansion/sources.md.
Train-only representations, RDA-inspired covariance blending, and calibrated
novelty models operate on existing formal105 rows, NOT reconstructed time series.
"""
from __future__ import annotations
import numpy as np
from scipy.special import softmax, logsumexp
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import RobustScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import NeighborhoodComponentsAnalysis, LocalOutlierFactor
from sklearn.covariance import LedoitWolf, OAS
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from core.fault_type_accuracy import VIBRATION75, VIBRATION66, verify_redundancy
from core.fault_type_final_guard import digest
from core.fault_type_accuracy_scores import PooledWithinLW


def finite(X):
    X=np.asarray(X,float)
    if X.ndim!=2 or not len(X) or not np.isfinite(X).all():raise ValueError('finite nonempty matrix required')
    return X


class LiteratureRepresentation:
    def __init__(self, name, seed): self.name=name;self.seed=seed

    def _raw(self,X):
        X=finite(X)
        if X.shape[1]!=105:raise ValueError('formal105 required')
        raw=X[:,VIBRATION75 if self.name in ['base75','pca20','nca10'] else VIBRATION66].copy()
        if self.name=='signed66':
            with np.errstate(divide='ignore'):
                raw=np.sign(raw)*np.logaddexp(0.,np.log(np.abs(raw))-np.log(self.signed_scale))
        if self.name in ['harmonic69','harmonic66']:
            amps=[]
            for axis,off in enumerate([15,40,65]):
                indices=[VIBRATION66.index(i) for i in range(off+15,off+25)]
                # Historical harmonic BAND MAXIMA, not energy or order tracking.
                magnitude=np.abs(raw[:,indices]);total=magnitude.sum(1)
                raw[:,indices]=magnitude/np.maximum(total[:,None],self.harmonic_floor[axis])
                amps.append(np.log1p(total/self.harmonic_floor[axis]))
            if self.name=='harmonic69':raw=np.column_stack([raw,*amps])
        return finite(raw)

    def fit(self,X,y):
        X=finite(X);self.metric_subset_indices=[];self.optimizer={}
        if self.name not in ['base75','base66','signed66','harmonic69','harmonic66','pca20','nca10']:raise ValueError('unregistered representation')
        if self.name not in ['base75','pca20','nca10']:verify_redundancy(X)
        self.signed_scale=np.maximum(np.median(np.abs(X[:,VIBRATION66]),0),1e-12)
        self.harmonic_floor=np.array([max(np.median(np.abs(X[:,off+15:off+25]).sum(1))*1e-6,1e-12) for off in [15,40,65]])
        self.scaler=RobustScaler(quantile_range=(25.,75.)).fit(self._raw(X))
        Z=self.scaler.transform(self._raw(X));self.embedding=None
        if self.name=='pca20':
            self.embedding=PCA(n_components=20,svd_solver='full',whiten=False,random_state=self.seed).fit(Z)
        if self.name=='nca10':
            rng=np.random.default_rng(self.seed)
            indices=sorted(int(i) for c in sorted(np.unique(y)) for i in rng.choice(np.flatnonzero(y==c),size=min(60,int(sum(y==c))),replace=False))
            self.metric_subset_indices=indices
            self.embedding=NeighborhoodComponentsAnalysis(n_components=10,init='pca',max_iter=50,tol=1e-5,random_state=self.seed).fit(Z[indices],np.asarray(y)[indices])
            self.optimizer={'iterations':int(self.embedding.n_iter_),'budget_max_iter':50,'budget_reached':bool(self.embedding.n_iter_>=50)}
        self.transform_checksum=self.checksum();return self

    def checksum(self):
        return digest({'name':self.name,'seed':self.seed,'signed_scale':self.signed_scale.tolist(),'harmonic_floor':self.harmonic_floor.tolist(),
            'center':self.scaler.center_.tolist(),'scale':self.scaler.scale_.tolist(),'metric_subset':self.metric_subset_indices,
            'components':None if self.embedding is None else self.embedding.components_.tolist(),
            'pca_mean':self.embedding.mean_.tolist() if isinstance(self.embedding,PCA) else None})

    def transform(self,X):
        if self.checksum()!=self.transform_checksum:raise ValueError('representation tampered')
        Z=self.scaler.transform(self._raw(X))
        return finite(Z if self.embedding is None else self.embedding.transform(Z))


class BlendedDiscriminant(ClassifierMixin,BaseEstimator):
    """RDA-inspired equal-prior Gaussian classifier, not exact Friedman weighting.

    cov_c=(1-gamma)*((1-lambda)*cov_c+lambda*pooled)+gamma*trace(blend)/D*I.
    Pooled covariance weights class observations, not an equal-class average.
    """
    def __init__(self,pooling=.5,shrinkage=.1):self.pooling=pooling;self.shrinkage=shrinkage
    def fit(self,X,y):
        X=finite(X);y=np.asarray(y)
        if not 0<=self.pooling<=1 or not 0<self.shrinkage<=1:raise ValueError('invalid covariance blend')
        self.classes_=np.unique(y);self.means_=np.array([X[y==c].mean(0) for c in self.classes_])
        residual=X-np.array([self.means_[list(self.classes_).index(c)] for c in y])
        pooled=residual.T@residual/len(X);D=X.shape[1];self.precisions_=[];self.logdets_=[]
        for c,mu in zip(self.classes_,self.means_):
            centered=X[y==c]-mu;cov=centered.T@centered/len(centered)
            blend=(1-self.pooling)*cov+self.pooling*pooled
            cov=(1-self.shrinkage)*blend+self.shrinkage*max(np.trace(blend)/D,1e-12)*np.eye(D)
            sign,ld=np.linalg.slogdet(cov)
            if sign<=0:raise ValueError('non-positive covariance')
            self.precisions_.append(np.linalg.inv(cov));self.logdets_.append(ld)
        self.n_features_in_=D;return self
    def decision_function(self,X):
        X=finite(X)
        return np.column_stack([-.5*(np.einsum('ij,jk,ik->i',X-mu,P,X-mu)+ld) for mu,P,ld in zip(self.means_,self.precisions_,self.logdets_)])
    def predict(self,X):return self.classes_[self.decision_function(X).argmax(1)]
    def predict_proba(self,X):return softmax(self.decision_function(X),axis=1)


class NoveltyReference:
    """Train-only reference; cal sets q95 of scalar scores without search.

    Signed RMD/energy/density scores use score > threshold, never division by a
    negative threshold. Unknown labels are NOT an argument to score_samples.
    """
    def __init__(self,definition,seed):self.definition=definition;self.seed=seed
    def fit(self,X,y,classifier,factory):
        X=finite(X);self.classifier=classifier;self.factory=factory
        self.kind=self.definition['kind'];self.parameter=self.definition.get('parameter',1.)
        self.model=None
        if self.kind in ['pooled','relative','diagonal','centers']:
            self.model=PooledWithinLW().fit(X,y,len(np.unique(y)))
            if self.kind=='relative':self.background=LedoitWolf().fit(X)
            if self.kind=='diagonal':self.diag=np.maximum(np.diag(self.model.covariance.covariance_),1e-12)
            if self.kind=='centers':self.centers=np.vstack([KMeans(n_clusters=2,n_init=10,random_state=self.seed).fit(X[y==c]).cluster_centers_ for c in np.unique(y)])
        elif self.kind=='oas':
            self.means=np.array([X[y==c].mean(0) for c in np.unique(y)])
            self.model=OAS(assume_centered=True).fit(X-self.means[y])
        elif self.kind=='iforest':self.model=IsolationForest(n_estimators=200,max_samples=256,contamination='auto',random_state=self.seed,n_jobs=1).fit(X)
        elif self.kind=='lof':self.model=LocalOutlierFactor(n_neighbors=20,novelty=True,n_jobs=1).fit(X)
        elif self.kind=='ocsvm':self.model=OneClassSVM(nu=.05,gamma='scale',kernel='rbf').fit(X)
        elif self.kind=='gmm':
            self.model=[GaussianMixture(n_components=2,covariance_type='diag',reg_covar=1e-4,n_init=1,max_iter=200,random_state=self.seed).fit(X[y==c]) for c in np.unique(y)]
            if not all(m.converged_ for m in self.model):raise ValueError('GMM did not converge')
        elif self.kind=='vim':
            # Tabular/LDA adaptation of ViM; not a deep-network reproduction.
            W=classifier.coef_;b=classifier.intercept_;self.origin=-np.linalg.pinv(W)@b
            centered=X-self.origin;_,vectors=np.linalg.eigh(centered.T@centered/len(X))
            self.nullspace=vectors[:,:max(1,X.shape[1]-20)]
            residual=np.linalg.norm(centered@self.nullspace,axis=1)
            self.alpha=float(np.mean(classifier.decision_function(X).max(1))/max(residual.mean(),1e-12))
            if self.alpha<=0:raise ValueError('ViM alpha non-positive; no silent sign fix')
        elif self.kind not in ['msp','entropy','margin','energy','predicted','fusion']:raise ValueError('unregistered novelty method')
        return self

    def raw(self,X):
        X=finite(X);kind=self.kind
        if kind in ['pooled','relative']:score=self.model.raw_scores(X).min(1)**2
        if kind=='relative':
            centered=X-self.background.location_
            score-=self.parameter*np.einsum('ij,jk,ik->i',centered,self.background.precision_,centered)
        elif kind=='diagonal':score=np.min([np.sum((X-mu)**2/self.diag,axis=1) for mu in self.model.means],axis=0)
        elif kind=='oas':score=np.min([np.einsum('ij,jk,ik->i',X-mu,self.model.precision_,X-mu) for mu in self.means],axis=0)
        elif kind=='centers':score=np.min([np.einsum('ij,jk,ik->i',X-mu,self.model.covariance.precision_,X-mu) for mu in self.centers],axis=0)
        elif kind in ['iforest','lof','ocsvm']:score=-self.model.score_samples(X)
        elif kind=='gmm':score=-np.column_stack([m.score_samples(X) for m in self.model]).max(1)
        elif kind in ['msp','entropy','margin','fusion']:
            p=self.classifier.predict_proba(X)
            if kind=='msp':score=1-p.max(1)
            elif kind=='entropy':score=-np.sum(p*np.log(np.maximum(p,1e-300)),axis=1)/np.log(p.shape[1])
            elif kind=='margin':
                ordered=np.sort(p,axis=1);score=1-(ordered[:,-1]-ordered[:,-2])
            else:
                parts=np.column_stack([self.factory.score_samples(X),1-p.max(1)])
                normalized=(parts-self.fusion_center)/self.fusion_scale
                score=self.parameter*normalized[:,0]+(1-self.parameter)*normalized[:,1]
        elif kind=='energy':score=-logsumexp(self.classifier.decision_function(X),axis=1)
        elif kind=='vim':score=self.alpha*np.linalg.norm((X-self.origin)@self.nullspace,axis=1)-logsumexp(self.classifier.decision_function(X),axis=1)
        elif kind=='predicted':
            from experiments.fault_type_fixed_calibration import raw_class_scores
            raw,_,_,_=raw_class_scores(self.factory,X);pred=self.classifier.predict(X)
            score=raw[np.arange(len(X)),pred]/np.maximum(self.predicted_thresholds[pred],np.finfo(float).eps)
        score=np.asarray(score,float)
        if score.shape!=(len(X),) or not np.isfinite(score).all():raise ValueError('nonfinite novelty scores')
        return score

    def calibrate(self,C):
        C=finite(C)
        if self.kind=='predicted':
            from experiments.fault_type_fixed_calibration import raw_class_scores
            raw,_,_,_=raw_class_scores(self.factory,C);pred=self.classifier.predict(C)
            self.predicted_counts=[int(sum(pred==c)) for c in range(raw.shape[1])]
            if not all(self.predicted_counts):raise ValueError('INCOMPLETE missing predicted calibration class; no fallback')
            self.predicted_thresholds=np.array([np.quantile(raw[pred==c,c],.95) for c in range(raw.shape[1])]);self.threshold=1.
        else:
            if self.kind=='fusion':
                parts=np.column_stack([self.factory.score_samples(C),1-self.classifier.predict_proba(C).max(1)])
                self.fusion_center=np.median(parts,0);self.fusion_scale=np.maximum(np.subtract(*np.percentile(parts,[75,25],axis=0)),1e-12)
            self.threshold=float(np.quantile(self.raw(C),.95,method='linear'))
        self.calibration_count=len(C);return self
