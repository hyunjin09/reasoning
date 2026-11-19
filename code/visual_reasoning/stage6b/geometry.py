"""Descriptive discovery-only geometry; no semantic or causal labeling."""
from collections import Counter
import numpy as np


def fit_pca(rows,columns):
    if not rows or any(r['split']!='discovery' for r in rows):
        raise ValueError('Only nonempty discovery rows may fit PCA')
    x=np.asarray([[r[c] for c in columns] for r in rows],dtype=float)
    if not np.isfinite(x).all():raise ValueError('PCA requires observed finite components')
    counts=Counter(r['base_id'] for r in rows)
    weight=np.asarray([1./counts[r['base_id']]/len(counts) for r in rows])
    mean=np.sum(x*weight[:,None],axis=0)
    scale=np.sqrt(np.sum((x-mean)**2*weight[:,None],axis=0));scale[scale<1e-12]=1.
    z=(x-mean)/scale;cov=(z*weight[:,None]).T@z
    eigenvalues,components=np.linalg.eigh(cov);order=np.argsort(eigenvalues)[::-1]
    eigenvalues=np.maximum(eigenvalues[order],0.);components=components[:,order].T
    for vector in components:
        if vector[np.argmax(np.abs(vector))]<0:vector*=-1
    ratio=eigenvalues/eigenvalues.sum() if eigenvalues.sum()>0 else np.zeros_like(eigenvalues)
    return {'columns':columns,'mean':mean.tolist(),'scale':scale.tolist(),'components':components[:2].tolist(),
        'explained_variance_ratio':ratio[:2].tolist(),'all_eigenvalues':eigenvalues.tolist(),
        'discovery_bases':len(counts),'discovery_rows':len(rows),'fit_weighting':'Equal total mass per discovery base',
        'semantic_labels_defined_by_pca':False}


def project(rows,model):
    x=np.asarray([[r[c] for c in model['columns']] for r in rows],dtype=float)
    if not np.isfinite(x).all():raise ValueError('Do not impute unobserved components into a PCA coordinate')
    z=(x-np.asarray(model['mean']))/np.asarray(model['scale'])
    return z,z@np.asarray(model['components']).T


def path_metrics(z):
    if len(z)<2:return {'path_length':None,'endpoint_distance':None,'tortuosity':None,'observed_states':len(z)}
    length=float(np.linalg.norm(np.diff(z,axis=0),axis=1).sum());distance=float(np.linalg.norm(z[-1]-z[0]))
    return {'path_length':length,'endpoint_distance':distance,'tortuosity':length/(distance+1e-12),'observed_states':len(z)}
