"""Small CPU-only summaries of already-frozen time and source measurements."""
import json
from pathlib import Path

import numpy as np
import pyarrow.dataset as ds

from scripts.stage8c.prepare import save,sha
from visual_reasoning.stage9a.protocol import ARMS
from visual_reasoning.stage9a.statistics import mean_interval,paired

ROOT=Path('outputs/stage9a/v1')


def main():
    rows=json.loads((ROOT/'audit/trajectory_metrics.json').read_text())['rows']
    time={}
    for arm in ARMS:
        rr=[r for r in rows if r['arm']==arm];time[arm]={}
        for q in ('.25','.5','.75'):
            time[arm]['late_fraction_'+q]=mean_interval([r['primary']['late_fractions'][str(float(q))] for r in rr])
        for key in ('long_gap_at_risk','long_gap_successes','median_inactive_gap','max_inactive_gap','median_onset_gap','mean_episode_duration','valid_score_tokens'):
            time[arm][key]=mean_interval([r['primary'][key] for r in rr])
        time[arm]['no_episode_trajectories']=sum(r['primary']['episode_count']==0 for r in rr)
        time[arm]['no_at_risk_trajectories']=sum(r['primary']['long_gap_at_risk']==0 for r in rr)
    manifest=json.loads((ROOT/'annotations/causal_selection_frozen.json').read_text())
    selected={r['task_id'] for r in manifest['rows']}
    dataset=ds.dataset(ROOT/'stage9a_retrieval_features.parquet',format='parquet')
    table=dataset.to_table(columns=['task_id','family_id','arm','source_target_share','source_donor_share'],
        filter=ds.field('task_id').isin(sorted(selected)) & ds.field('in_primary_reasoning'))
    frame=table.to_pandas();a=frame['source_target_share'].to_numpy();b=frame['source_donor_share'].to_numpy();other=np.clip(1-a-b,0,1)
    probs=np.stack([a,b,other],axis=-1);assert np.allclose(probs.sum(-1),1,atol=1e-5)
    frame['target_donor_other_entropy']=-(probs*np.log(np.maximum(probs,1e-30))).sum(-1)/np.log(3)
    frame['top_partition_share']=probs.max(-1)
    frame['target_share_within_two_named_sources']=a/np.maximum(a+b,1e-30)
    grouped=frame.groupby(['task_id','family_id','arm'],as_index=False).mean(numeric_only=True)
    source=[]
    for r in grouped.to_dict('records'):
        source.append(dict(task_id=r['task_id'],family_id=r['family_id'],arm=r['arm'],primary={k:float(v) for k,v in r.items() if k not in {'task_id','family_id','arm'}}))
    source_summary={a:{key:mean_interval([r['primary'][key] for r in source if r['arm']==a]) for key in source[0]['primary']} for a in ARMS}
    out=dict(time_summaries=time,source_partition_trajectory_rows=source,source_partition_arm_summaries=source_summary,
        source_partition_paired={key:paired(source,key,confidence=.95) for key in source[0]['primary']},
        source_partition_scope='Only the50 pre-outcome-selected native trajectories; reviewed target ROI, donor ROI, all remaining visual tokens. Entropy of this3-way partition is distinct from full semantic inventory entropy.',
        spatial_entropy_scope='Full-trajectory mean-focus spatial entropy is stored per token in retrieval_features; not called semantic-source entropy',
        fine_subtype_support=dict(problem_type='unknown128/128',visual_density='unknown128/128',entity_count='unknown128/128',
            usable_controls='Frozen subject15 categories, difficulty1–5 and answer format; unknown fine subtype cannot establish robustness'),
        feature_sha256=sha(ROOT/'stage9a_retrieval_features.parquet'))
    save(ROOT/'audit/sensitivity_diagnostics.json',out)
    print('Additional time/source diagnostics saved')


if __name__=='__main__':main()
