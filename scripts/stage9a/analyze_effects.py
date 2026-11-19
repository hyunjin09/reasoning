"""CPU-Slurm: frozen endpoints, length controls and heterogeneity diagnostics."""
import json
import os
from collections import Counter
from pathlib import Path

import numpy as np

from scripts.stage8c.prepare import save,sha
from visual_reasoning.stage9a.protocol import ARMS
from visual_reasoning.stage9a.statistics import paired,mean_interval,adjusted

ROOT=Path('outputs/stage9a/v1')


def main():
    assert os.environ.get('SLURM_JOB_ID')
    rows=json.loads((ROOT/'audit/trajectory_metrics.json').read_text())['rows']
    families={}
    for r in rows:families.setdefault(r['family_id'],{})[r['arm']]=r
    matching=[]
    for family,arms in families.items():
        a=arms['thinking']['primary']['reasoning_tokens'];b=arms['instruct_cot']['primary']['reasoning_tokens']
        distance=abs(np.log(a)-np.log(b)) if a>0 and b>0 else None
        matching.append(dict(family_id=family,item_id=arms['thinking']['item_id'],thinking_length=a,cot_length=b,log_distance=distance,
            included=bool(distance is not None and distance<=.15),reason='within_frozen_caliper' if distance is not None and distance<=.15 else 'outside_caliper_or_empty'))
    allowed={r['family_id'] for r in matching if r['included']}
    save(ROOT/'stage9a_length_matched_pairs.json',dict(rows=matching,caliper=.15,matched_families=len(allowed),total_families=len(families),
        selection='Same-item pairing only, no widening or replacement',metrics_sha256=sha(ROOT/'audit/trajectory_metrics.json')))
    result=dict(primary={},matched={},adjusted={},secondary_cot_direct={},common_assistant={},boundary_certain={},normal_completed={},
                descriptive={},raw_panel={},demand_specificity={},leave_one_subject_out={},subtypes={},sensitivities={})
    for arm in ARMS:
        rr=[r for r in rows if r['arm']==arm]
        result['descriptive'][arm]=dict(trajectories=len(rr),completion=dict(Counter(r['completion'] for r in rr)),
            uncertain_boundaries=sum(not r['boundary_certain'] for r in rr),
            mean_reasoning_length=float(np.mean([r['primary']['reasoning_tokens'] for r in rr])),
            median_reasoning_length=float(np.median([r['primary']['reasoning_tokens'] for r in rr])),
            mean_generated_length=float(np.mean([r['generated_tokens'] for r in rr])),
            reviewed_demand_events=sum(r['primary']['reviewed_demands'] for r in rr),
            trajectories_with_reviewed_demands=sum(r['primary']['reviewed_demands']>0 for r in rr),
            metrics={key:mean_interval([r['primary'].get(key) for r in rr]) for key in ['P1','P2','P3','P4','active_fraction','episode_count','mean_R','alignment32','alignment16_onset','median_inactive_gap','max_inactive_gap','median_onset_gap','mean_episode_duration','demand_minus_shift','demand_minus_nondemand']})
    for key in ('P1','P2','P3','P4'):
        result['primary'][key]=paired(rows,key)
        result['matched'][key]=paired(rows,key,allowed=allowed)
        result['adjusted'][key]=adjusted(rows,key)
        result['secondary_cot_direct'][key]=paired(rows,key,left='instruct_cot',right='instruct_direct',confidence=.95)
        result['common_assistant'][key]=paired(rows,key,scope='common',confidence=.95)
        certain={f for f,a in families.items() if a['thinking']['boundary_certain'] and a['instruct_cot']['boundary_certain']}
        complete={f for f,a in families.items() if a['thinking']['completion']=='normal completed' and a['instruct_cot']['completion']=='normal completed'}
        result['boundary_certain'][key]=paired(rows,key,allowed=certain,confidence=.95)
        result['normal_completed'][key]=paired(rows,key,allowed=complete,confidence=.95)
        result['leave_one_subject_out'][key]={str(s):paired([r for r in rows if r['subject']!=s],key,confidence=.95) for s in sorted({r['subject'] for r in rows})}
    for column in ('subject','difficulty','answer_format','problem_type','visual_density','entity_count'):
        result['subtypes'][column]={str(v):{key:paired([r for r in rows if str(r[column])==str(v)],key,confidence=.95) for key in ('P1','P2','P3','P4')} for v in sorted({str(r[column]) for r in rows})}
    for key in rows[0]['raw_mean']:
        result['raw_panel'][key]=dict(contrast=paired(rows,key,scope='raw_mean',confidence=.95),arms={a:mean_interval([r['raw_mean'][key] for r in rows if r['arm']==a]) for a in ARMS})
    for key in ('demand_minus_shift','demand_minus_nondemand','alignment16_onset','alignment32','alignment16_full_window','alignment32_full_window','mean_R','active_fraction','episode_count'):
        result['sensitivities'][key]=paired(rows,key,confidence=.95)
    for arm in ARMS:
        rr=[r for r in rows if r['arm']==arm]
        result['demand_specificity'][arm]={key:mean_interval([r['primary'].get(key) for r in rr]) for key in ('P1','shift_control_alignment16','nondemand_alignment16','demand_minus_shift','demand_minus_nondemand')}
    result.update(bootstrap_replicates=4000,seed=920260924,primary_confidence=.9875,secondary_confidence=.95,
        minimum_families_for_ci=20,independent_unit='conservative visual family; one base per family',
        unknown_annotation_policy='not zero; missing demand coverage excluded from alignment denominators',
        detector_caveat='Frozen Thinking-developed detector is not cross-checkpoint causal ground truth',
        source_hashes={str(ROOT/'audit/trajectory_metrics.json'):sha(ROOT/'audit/trajectory_metrics.json')})
    save(ROOT/'stage9a_primary_effects.json',result)
    print(json.dumps(dict(completed=True,matched_families=len(allowed))))


if __name__=='__main__':main()
