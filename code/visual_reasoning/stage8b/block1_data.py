"""Block1 input assembly; all core trajectory objects remain Block0 artifacts."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

ROOT=Path('outputs/stage8b_block1/v1')
B0=Path('outputs/stage8b_block0/v1')
PREFIX='stage8b_block1_'
FAMILIES={
 'amount':['retrieval_episode_count','retrieval_density','active_token_fraction'],
 'timing_recurrence':['first_retrieval_token','first_retrieval_normalized','median_gap',
                      'episodes_after_first','late_episode_fraction_gt_0.5','late_episode_fraction_gt_0.75'],
 'geometry':['standardized_transition_normalized_path_length','standardized_tortuosity']}
PRIMARY=sum(FAMILIES.values(),[])
SECONDARY=['mean_duration','median_duration','max_duration','mean_peak','max_peak','mean_auc',
           'mean_gap','min_gap','gap_cv','short_gap_fraction','burstiness',
           'returns_after_gap_gt_32','returns_after_gap_gt_64','returns_after_gap_gt_128',
           'late_episode_fraction_gt_0.25','late_episode_fraction_gt_0.9',
           'standardized_path_length','standardized_net_displacement','raw_path_length',
           'raw_transition_normalized_path_length','raw_net_displacement','raw_tortuosity']
PHASE_METRICS=['retrieval_density','active_token_fraction','mean_R','standardized_mean_movement']


def digest(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def sanitize(value):
    if isinstance(value,dict):return {str(k):sanitize(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,np.ndarray)):return [sanitize(v) for v in value]
    if isinstance(value,(float,np.floating)):return float(value) if np.isfinite(value) else None
    if isinstance(value,np.integer):return int(value)
    if isinstance(value,np.bool_):return bool(value)
    return value


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:json.dump(sanitize(value),stream,indent=2,ensure_ascii=False,allow_nan=False)


def b0_path(name):return B0/('stage8b_block0_'+name)


def load_frame():
    return pd.read_csv(ROOT/(PREFIX+'trajectory_metrics.csv'),dtype={'item_id':str,'family_id':str,'level':str})


def interval_additions(events):
    gaps=events.sort_values('episode_index')['preceding_gap'].dropna().to_numpy(dtype=float)
    return dict(short_gap_fraction=float(np.mean(gaps<=32)) if len(gaps) else np.nan,
                burstiness=float((gaps.std()-gaps.mean())/(gaps.std()+gaps.mean())) if len(gaps)>=3 and gaps.std()+gaps.mean()>0 else np.nan)


def episode_metrics(frame,events):
    """Derive gap sensitivity summaries from frozen events, never token crossings."""
    frame=frame.copy()
    for i,row in frame.iterrows():
        es=events.loc[events.item_id==row.item_id].sort_values('episode_index')
        count=len(es);length=row.reasoning_tokens
        values=dict(retrieval_episode_count=count,retrieval_density=count/length*1000,
                    episodes_after_first=max(count-1,0),
                    first_retrieval_token=es.start_token.iloc[0] if count else np.nan,
                    first_retrieval_normalized=es.normalized_start.iloc[0] if count else np.nan,
                    median_gap=es.preceding_gap.median() if count>=2 else np.nan)
        for threshold in [.5,.75]:values[f'late_episode_fraction_gt_{threshold}']=float((es.normalized_start>threshold).mean()) if count else np.nan
        for key,value in values.items():frame.loc[i,key]=value
    return frame


def nuisance(frame,mode,freeze):
    n=len(frame);columns=['intercept'];x=[np.ones(n)]
    def continuous(name,values):
        columns.append(name);x.append((values-freeze['continuous'][name]['mean'])/freeze['continuous'][name]['scale'])
    if mode in ['length','joint','full','completion_full']:
        continuous('log_reasoning_length',np.log(frame.reasoning_tokens.to_numpy()))
    if mode in ['joint','full']:
        for label in ['capped','other abnormal stop']:
            columns.append('completion_'+label);x.append((frame.completion==label).to_numpy(dtype=float))
    if mode in ['full','completion_full']:
        continuous('log_question_length',frame.log_question_length.to_numpy())
        for key,levels in [('subject_group',freeze['subject_levels']),('answer_format',freeze['format_levels']),('level',freeze['difficulty_levels'])]:
            for label in levels[1:]:
                columns.append(key+'_'+label);x.append((frame[key].astype(str)==label).to_numpy(dtype=float))
    return np.column_stack(x),columns


def matched_pairs(frame):
    scorable=frame.loc[frame.benchmark_label.isin(['correct','wrong'])]
    pairs=[]
    for stratum,sub in scorable.groupby(['completion','subject_group','answer_format'],sort=True):
        c=sub.loc[sub.benchmark_label=='correct'];w=sub.loc[sub.benchmark_label=='wrong']
        if not len(c) or not len(w):continue
        lc=np.log(c.reasoning_tokens.to_numpy());lw=np.log(w.reasoning_tokens.to_numpy())
        delta=np.abs(lc[:,None]-lw[None,:])
        cost=delta+.25*np.abs(c.log_question_length.to_numpy()[:,None]-w.log_question_length.to_numpy()[None,:])
        eligible=delta<=.5;cost=np.where(eligible,cost,1e6)
        ci,wi=linear_sum_assignment(cost)
        for a,b in zip(ci,wi):
            if eligible[a,b]:pairs.append(dict(correct_id=c.item_id.iloc[a],wrong_id=w.item_id.iloc[b],stratum=list(stratum),log_length_difference=float(delta[a,b]),cost=float(cost[a,b])))
    return sorted(pairs,key=lambda r:int(frame.loc[frame.item_id==r['correct_id'],'order'].iloc[0]))
