"""Family-weighted descriptive contrasts under the frozen Block3B protocol."""
import numpy as np
import pandas as pd
from scipy.linalg import qr


def nuisance(frame, freeze):
    cols = ['intercept']; values = [np.ones(len(frame))]
    for name, scale in freeze['continuous'].items():
        cols.append(name)
        values.append((frame[name].to_numpy(float)-scale['mean'])/scale['scale'])
    for name, levels in freeze['categorical'].items():
        for level in levels[1:]:
            cols.append(f'{name}={level}')
            values.append((frame[name].astype(str)==level).to_numpy(float))
    return np.column_stack(values), cols


def estimate(y, wrong, controls, weight):
    keep = weight > 0
    y, wrong, controls, weight = y[keep], wrong[keep], controls[keep], weight[keep]
    groups = [wrong == value for value in [0, 1]]
    if not all(g.any() for g in groups):
        return np.nan, np.nan, 0
    raw = np.average(y[groups[1]], weights=weight[groups[1]])-np.average(y[groups[0]], weights=weight[groups[0]])
    root = np.sqrt(weight); x = controls*root[:, None]
    target = wrong*root; response = y*root
    # Redundant controls remain in the column span; do not remove confound families.
    residual = target-x@np.linalg.lstsq(x, target, rcond=None)[0]
    rank = int(np.linalg.matrix_rank(x))
    norm = residual@residual
    adjusted = residual@response/norm if norm > 1e-10 and len(y)>rank+1 else np.nan
    return float(raw), float(adjusted), rank


def contrast(frame, metric, freeze, *, group='benchmark_label',
             labels=('correct', 'wrong'), draws=4000, seed=820260922):
    selected = frame.loc[frame[group].isin(labels)].copy()
    selected[metric] = pd.to_numeric(selected[metric], errors='coerce')
    selected = selected.loc[np.isfinite(selected[metric])].copy()
    controls, columns = nuisance(selected, freeze)
    finite = np.isfinite(controls).all(axis=1)
    selected = selected.loc[finite].copy(); controls = controls[finite]
    y = selected[metric].to_numpy(float)
    wrong = (selected[group]==labels[1]).to_numpy(float)
    family, inverse, counts = np.unique(selected.analysis_family_id.astype(str), return_inverse=True, return_counts=True)
    weights = 1/counts[inverse] if len(selected) else np.array([])
    out = dict(metric=metric, contrast=f'{labels[1]} minus {labels[0]}',
        events=len(selected), families=len(family), group_events=selected[group].value_counts().to_dict(),
        group_families={label:selected.loc[selected[group]==label,'analysis_family_id'].nunique() for label in labels},
        columns=columns, seed=seed, draws=draws, means={}, raw=None, adjusted=None)
    for label in labels:
        mask=selected[group].eq(label).to_numpy()
        out['means'][label]=float(np.average(y[mask],weights=weights[mask])) if mask.any() else None
    if not len(selected) or not all((selected[group]==label).any() for label in labels):
        out['status']='insufficient outcome groups'; return out
    raw, adjusted, rank = estimate(y, wrong, controls, weights)
    _, _, pivots=qr(controls*np.sqrt(weights[:,None]),pivoting=True,mode='economic')
    out.update(control_rank=rank, residual_degrees=len(y)-rank-1,
        redundant_columns=[columns[j] for j in pivots[rank:]],
        overlap={name: {label: [float(selected.loc[selected[group]==label,name].min()),float(selected.loc[selected[group]==label,name].max())] for label in labels} for name in freeze['continuous']})
    rng=np.random.default_rng(seed); values=[]
    for _ in range(draws):
        multiplicity=rng.multinomial(len(family),np.full(len(family),1/len(family)))
        values.append(estimate(y,wrong,controls,weights*multiplicity[inverse])[:2])
    values=np.asarray(values)
    for index, (name, point) in enumerate([('raw',raw),('adjusted',adjusted)]):
        sample=values[:,index]; sample=sample[np.isfinite(sample)]
        valid=len(sample)>=.95*draws and np.isfinite(point)
        out[name]=dict(estimate=point,valid_bootstrap=len(sample),valid_fraction=len(sample)/draws,
            ci95=np.quantile(sample,[.025,.975]).tolist() if valid else None,
            ci9875=np.quantile(sample,[.00625,.99375]).tolist() if valid else None)
    out['status']='estimated' if np.isfinite(adjusted) else 'full adjustment unidentified or saturated'
    return out


def missing_bounds(frame, metric):
    output={}
    for label in ['correct','wrong']:
        f=frame.loc[frame.benchmark_label==label]
        values=pd.to_numeric(f[metric],errors='coerce')
        weights=1/f.groupby('analysis_family_id').analysis_family_id.transform('size')
        total=weights.sum()
        output[label]=dict(events=len(f),known=int(values.notna().sum()),unknown=int(values.isna().sum()),
            family_weighted_lower=float((values.fillna(0)*weights).sum()/total) if total else None,
            family_weighted_upper=float((values.fillna(1)*weights).sum()/total) if total else None)
    if all(output[k]['events'] for k in ['correct','wrong']):
        output['difference_bounds']=[output['wrong']['family_weighted_lower']-output['correct']['family_weighted_upper'],output['wrong']['family_weighted_upper']-output['correct']['family_weighted_lower']]
    return output
