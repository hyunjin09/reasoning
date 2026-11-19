"""Item bootstrap and outcome contrasts; no detector or trajectory construction."""
import hashlib
import numpy as np
import torch

BOOTSTRAPS = 4000
SEED = 1234


def interval(values, minimum_valid=.95):
    values=np.asarray(values,dtype=float);valid=values[np.isfinite(values)]
    return dict(ci95=np.quantile(valid,[.025,.975]).tolist() if len(valid)>=minimum_valid*len(values) and len(valid) else None,
                valid_resamples=int(len(valid)), requested_resamples=len(values))


def pooled_sd(y, group):
    a,b=[y[(group==g)&np.isfinite(y)] for g in [0,1]]
    if min(len(a),len(b))<2:return np.nan
    return float(np.sqrt(((len(a)-1)*a.var(ddof=1)+(len(b)-1)*b.var(ddof=1))/(len(a)+len(b)-2)))


def joint_intervals(entries):
    """Family-wise max standardized bootstrap deviation, aligned resamples."""
    usable={k:v for k,v in entries.items() if np.isfinite(v['point']) and np.isfinite(v['samples']).mean()>=.95}
    if not usable:return dict(metrics={},status='no estimable metrics')
    names=list(usable);points=np.array([usable[k]['point'] for k in names])
    samples=np.column_stack([usable[k]['samples'] for k in names]);valid=np.isfinite(samples).all(1)
    if valid.mean()<.95:return dict(metrics={},status='insufficient jointly valid resamples',valid_resamples=int(valid.sum()))
    se=samples[valid].std(0,ddof=1);nonzero=se>0
    if not nonzero.any():return dict(metrics={},status='zero bootstrap variation')
    critical=float(np.quantile(np.max(np.abs((samples[valid][:,nonzero]-points[nonzero])/se[nonzero]),axis=1),.95))
    return dict(status='estimated',critical=critical,valid_resamples=int(valid.sum()),
                metrics={name:dict(point=float(points[i]),ci95_simultaneous=[float(points[i]-critical*se[i]),float(points[i]+critical*se[i])]) for i,name in enumerate(names)})


class ItemBootstrap:
    def __init__(self, group, *, device='cpu', resamples=BOOTSTRAPS, seed=SEED):
        self.group=np.asarray(group,dtype=int)
        assert set(self.group)<= {0,1}
        self.device=device;self.resamples=resamples
        rng=np.random.default_rng(seed)
        weights=np.zeros((resamples+1,len(group)),dtype=np.float64);weights[0]=1
        for g in [0,1]:
            ids=np.flatnonzero(self.group==g)
            if len(ids):weights[1:,ids]=rng.multinomial(len(ids),np.full(len(ids),1/len(ids)),size=resamples)
        self.weights=torch.as_tensor(weights,dtype=torch.float64,device=device)
        self.groups=torch.as_tensor(self.group,dtype=torch.float64,device=device)
        self.cache={}

    def raw(self, values):
        y=np.asarray(values,dtype=float);summaries=[];means=[];vars_=[];ns=[]
        for g in [0,1]:
            ids=np.flatnonzero((self.group==g)&np.isfinite(y));ids=ids[np.argsort(y[ids],kind='stable')]
            vals=torch.as_tensor(y[ids],dtype=torch.float64,device=self.device)
            if not len(ids):
                nan=torch.full((self.resamples+1,),torch.nan,dtype=torch.float64,device=self.device)
                means.append(nan);vars_.append(nan);ns.append(torch.zeros_like(nan));summaries.append(dict(n=0,missing=int((self.group==g).sum()),mean=None,median=None,mean_ci=None,median_ci=None));continue
            w=self.weights[:,ids];n=w.sum(1);mean=(w@vals)/n
            variance=(w@vals.square()-n*mean.square()).clamp_min(0)/(n-1)
            cumulative=w.cumsum(1).contiguous()
            low=torch.floor((n-1)/2).clamp_min(0);high=torch.floor(n/2)
            lo=torch.searchsorted(cumulative,low[:,None].contiguous(),right=True).squeeze(1).clamp_max(len(ids)-1)
            hi=torch.searchsorted(cumulative,high[:,None].contiguous(),right=True).squeeze(1).clamp_max(len(ids)-1)
            median=torch.where(n>0,(vals[lo]+vals[hi])/2,torch.nan)
            means.append(mean);vars_.append(variance);ns.append(n)
            summaries.append(dict(n=len(ids),missing=int((self.group==g).sum()-len(ids)),
                mean=float(np.mean(y[ids])),median=float(np.median(y[ids])),
                mean_ci=interval(mean[1:].cpu().numpy()),median_ci=interval(median[1:].cpu().numpy())))
        difference=means[1]-means[0]
        df=ns[0]+ns[1]-2
        sd=torch.sqrt(((ns[0]-1)*vars_[0]+(ns[1]-1)*vars_[1])/df)
        g=(1-3/(4*df-1))*difference/sd
        valid=(ns[0]>=2)&(ns[1]>=2)&(sd>0)
        g=torch.where(valid,g,torch.nan)
        diff=difference.cpu().numpy();gs=g.cpu().numpy()
        return dict(group0=summaries[0],group1=summaries[1],mean_difference=float(diff[0]),
                    difference_ci=interval(diff[1:]),hedges_g=float(gs[0]),hedges_g_ci=interval(gs[1:]),
                    pooled_sd=pooled_sd(y,self.group)),diff[1:]

    def adjusted(self, values, nuisance):
        y=np.asarray(values,dtype=float);d=np.asarray(nuisance,dtype=float)
        assert d.shape[0]==len(y) and np.isfinite(d).all()
        valid=np.isfinite(y);key=(valid.tobytes(),hashlib.sha256(d.tobytes()).hexdigest())
        if key not in self.cache:
            x=torch.as_tensor(d,dtype=torch.float64,device=self.device)
            w=self.weights*torch.as_tensor(valid,dtype=torch.float64,device=self.device)
            gram=torch.einsum('bi,ij,ik->bjk',w,x,x)
            cross=(w*self.groups)@x
            projected=torch.linalg.pinv(gram,hermitian=True,rtol=1e-10)@cross[:,:,None]
            residual=self.groups-(projected.squeeze(-1)@x.T)
            denom=(w*residual*self.groups).sum(1)
            n0=(w*(1-self.groups)).sum(1);n1=(w*self.groups).sum(1)
            estimable=(denom>1e-10*w.sum(1))&(n0>=2)&(n1>=2)
            contrast=torch.where(estimable[:,None],w*residual/denom[:,None],torch.nan)
            self.cache[key]=contrast
        beta=(self.cache[key]@torch.as_tensor(np.nan_to_num(y),dtype=torch.float64,device=self.device)).cpu().numpy()
        sd=pooled_sd(y,self.group);standardized=beta/sd if sd>0 else np.full_like(beta,np.nan)
        return dict(coefficient=float(beta[0]),coefficient_ci=interval(beta[1:]),
            standardized_coefficient=float(standardized[0]),standardized_ci=interval(standardized[1:]),
            pooled_sd=sd,n=int(valid.sum()),n_group0=int((valid&(self.group==0)).sum()),
            n_group1=int((valid&(self.group==1)).sum()),nuisance_rank=int(np.linalg.matrix_rank(d[valid])) if valid.any() else 0,
            nuisance_columns=d.shape[1],estimable=bool(np.isfinite(beta[0]))),beta[1:]


def paired_summary(differences, *, device='cpu', seed=SEED, resamples=BOOTSTRAPS):
    x=np.asarray(differences,dtype=float);x=x[np.isfinite(x)]
    if not len(x):return dict(pairs=0,mean_difference=None,ci95=None)
    weights=np.random.default_rng(seed).multinomial(len(x),np.full(len(x),1/len(x)),size=resamples)
    samples=(torch.as_tensor(weights,dtype=torch.float64,device=device)@torch.as_tensor(x,dtype=torch.float64,device=device)/len(x)).cpu().numpy()
    return dict(pairs=len(x),mean_difference=float(x.mean()),**interval(samples),
                scope='fixed matched-pair bootstrap; conditioning on selected matching')
