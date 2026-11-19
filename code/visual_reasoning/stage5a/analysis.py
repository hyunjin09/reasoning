"""Frozen matching and base-level inference, without optional ML dependencies."""
import math
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit,logsumexp
from scipy.stats import rankdata,wilcoxon


SIZE=[1,2,4,8,16,32,1000000]
LENGTH=[256,512,1024,2048,4096,8192,16384,65536]


def bucket(value,edges):return int(np.searchsorted(edges,value,side='left'))


def matched_reference(row,references):
    eligible=[r for r in references if r['source_class']==row['source_class'] and bucket(r['token_count'],SIZE)==bucket(row['token_count'],SIZE)]
    progress=bucket(row['reasoning_progress'],[.25,.5,.75]);length=bucket(row['sequence_length'],LENGTH)
    distance=lambda r:abs(bucket(r['reasoning_progress'],[.25,.5,.75])-progress)+abs(bucket(r['sequence_length'],LENGTH)-length)
    for radius in sorted(set(distance(r) for r in eligible)):
        chosen=[r for r in eligible if distance(r)<=radius]
        if len(chosen)>=8:return chosen,radius
    return [],None


def normalize_roi(row,references):
    ref,radius=matched_reference(row,references)
    result={'reference_rois':len(ref),'reference_bases':len({r['base_problem_id'] for r in ref}),'merge_radius':radius,
            'reference_ids':[r['reference_id'] for r in ref],'resolved':bool(ref)}
    for metric in ('mass','density'):
        x=row[metric];values=np.array([r[metric] for r in ref])
        sd=float(values.std(ddof=1)) if len(values)>1 else 0.
        result[metric+'_z']=(x-float(values.mean()))/sd if sd>0 else None
        result[metric+'_percentile']=float(np.mean(values<=x)) if len(values) else None
    return result


def holm(pvalues):
    order=sorted(range(len(pvalues)),key=lambda i:pvalues[i]);out=[1.]*len(pvalues);previous=0.
    for rank,i in enumerate(order):
        previous=max(previous,min(1.,(len(pvalues)-rank)*float(pvalues[i])));out[i]=previous
    return out


def paired_inference(values,minimum=12):
    x=np.array([v for v in values if v is not None and math.isfinite(v)],dtype=float)
    result={'N_paired_bases':len(x),'median':float(np.median(x)) if len(x) else None,'mean':float(x.mean()) if len(x) else None,
            'positive_bases':int((x>0).sum()),'p_raw':1.,'CI95':None,'status':'insufficient' if len(x)<minimum else 'tested'}
    if len(x)>=minimum:
        rng=np.random.default_rng(12348);boot=np.median(x[rng.integers(len(x),size=(10000,len(x)))],axis=1)
        result['CI95']=np.quantile(boot,[.025,.975]).tolist()
        result['p_raw']=float(wilcoxon(x,zero_method='wilcox').pvalue) if np.any(x) else 1.
    return result


def grouped_folds(rows,labels):
    """Whole template families assigned greedily with balanced class counts."""
    groups={}
    classes=sorted(set(labels));k=min(5,len({r['template_family'] for r in rows}))
    if k<2:return []
    for i,r in enumerate(rows):groups.setdefault(r['template_family'],[]).append(i)
    counts=np.zeros((k,len(classes)));size=np.zeros(k);folds=[[] for _ in range(k)]
    for name,indices in sorted(groups.items(),key=lambda x:(-len(x[1]),x[0])):
        c=np.array([sum(labels[i]==label for i in indices) for label in classes])
        scores=[]
        for f in range(k):
            trial=counts.copy();trial[f]+=c
            scores.append((float(np.var(trial/(np.sum(trial,axis=0)+1),axis=0).sum()),size[f],f))
        f=min(scores)[2];folds[f].extend(indices);counts[f]+=c;size[f]+=len(indices)
    return [sorted(f) for f in folds if f]


def classification_metrics(y,prob,classes):
    y=np.asarray(y);pred=np.argmax(prob,axis=1);recall=[];f1=[]
    for c in range(classes):
        tp=np.sum((y==c)&(pred==c));fp=np.sum((y!=c)&(pred==c));fn=np.sum((y==c)&(pred!=c))
        recall.append(float(tp/(tp+fn)) if tp+fn else 0.);f1.append(float(2*tp/(2*tp+fp+fn)) if 2*tp+fp+fn else 0.)
    confidence=prob.max(1);correct=pred==y;ece=0.
    for left,right in zip(np.linspace(0,1,11)[:-1],np.linspace(0,1,11)[1:]):
        mask=(confidence>left)&(confidence<=right)
        if np.any(mask):ece+=mask.mean()*abs(confidence[mask].mean()-correct[mask].mean())
    auc=None
    if classes==2 and set(y)=={0,1}:
        n1=int((y==1).sum());n0=len(y)-n1;auc=float((rankdata(prob[:,1])[y==1].sum()-n1*(n1+1)/2)/(n1*n0))
    return {'balanced_accuracy':float(np.mean(recall)),'macro_F1':float(np.mean(f1)),'AUROC':auc,
        'brier_multiclass':float(np.square(prob-np.eye(classes)[y]).sum(1).mean()),'ECE10':float(ece)}


def grouped_logistic(rows,labels,features):
    classes=sorted(set(labels));counts={c:len({r['base_problem_id'] for r,y in zip(rows,labels) if y==c}) for c in classes}
    if len(classes)<2 or min(counts.values(),default=0)<12:return {'status':'insufficient','class_bases':counts,'features':features}
    folds=grouped_folds(rows,labels);x=np.array([[float(r.get(f)) if r.get(f) is not None else np.nan for f in features] for r in rows]);y=np.array([classes.index(c) for c in labels])
    predictions=[];fold_records=[];allindices=set(range(len(rows)))
    for test in folds:
        train=sorted(allindices-set(test));test=np.array(test);train=np.array(train)
        train_classes=set(y[train]);held_classes=set(y[test])
        if train_classes!=set(range(len(classes))):
            fold_records.append({'status':'unrun_missing_train_class','test_events':[rows[i]['event_id'] for i in test]});continue
        med=np.array([np.nanmedian(x[train,j]) if np.isfinite(x[train,j]).any() else 0. for j in range(x.shape[1])])
        imputed=np.where(np.isfinite(x),x,med);mean=imputed[train].mean(0);std=imputed[train].std(0);std[std<1e-12]=1
        z=np.column_stack(((imputed-mean)/std,np.ones(len(x))))
        # Equal base weight within each class; repeated events cannot dominate training.
        base_counts={b:sum(rows[i]['base_problem_id']==b for i in train) for b in {rows[i]['base_problem_id'] for i in train}}
        weights=np.array([1./base_counts[rows[i]['base_problem_id']] for i in train])
        for c in range(len(classes)):weights[y[train]==c]/=weights[y[train]==c].sum()
        weights/=weights.sum();target=np.eye(len(classes))[y[train]];design=z[train]
        def objective(flat):
            w=flat.reshape(z.shape[1],len(classes));logits=design@w;lp=logits-logsumexp(logits,axis=1,keepdims=True)
            loss=-np.sum(weights[:,None]*target*lp)+.5*.01*np.square(w[:-1]).sum()
            grad=design.T@(weights[:,None]*(np.exp(lp)-target));grad[:-1]+=.01*w[:-1]
            return loss,grad.ravel()
        fit=minimize(objective,np.zeros(z.shape[1]*len(classes)),jac=True,method='L-BFGS-B',options={'maxiter':400,'ftol':1e-10})
        logits=z[test]@fit.x.reshape(z.shape[1],len(classes));prob=np.exp(logits-logsumexp(logits,axis=1,keepdims=True))
        for i,p in zip(test,prob):predictions.append({'event_id':rows[i]['event_id'],'base_problem_id':rows[i]['base_problem_id'],'true_class':classes[y[i]],'probabilities':p.tolist()})
        fold_records.append({'status':'scored','optimizer_success':bool(fit.success),'train_bases':sorted({rows[i]['base_problem_id'] for i in train}),
            'test_bases':sorted({rows[i]['base_problem_id'] for i in test}),'train_templates':sorted({rows[i]['template_family'] for i in train}),
            'test_templates':sorted({rows[i]['template_family'] for i in test}),'train_imputation':med.tolist(),'train_mean':mean.tolist(),'train_std':std.tolist()})
    if not predictions:return {'status':'insufficient_grouped_folds','class_bases':counts,'folds':fold_records}
    # Primary metric aggregates probabilities once per base and task class.
    aggregate={}
    for r in predictions:aggregate.setdefault((r['base_problem_id'],r['true_class']),[]).append(r['probabilities'])
    bybase=[{'base_problem_id':b,'class':c,'probabilities':np.mean(p,axis=0).tolist()} for (b,c),p in aggregate.items()]
    metrics=classification_metrics([classes.index(r['class']) for r in bybase],np.array([r['probabilities'] for r in bybase]),len(classes))
    return {'status':'scored','class_bases':counts,'classes':classes,'features':features,'folds':fold_records,'metrics':metrics,
        'predictions':predictions,'base_class_predictions':bybase,'metric_unit':'base/class (a base can exhibit multiple states); all events kept in one template fold',
        'regularization_L2':.01,'hyperparameter_search':False,'circularity':'Causal features reconstruct causal labels; classifier scores are not independent mechanism validation.'}
