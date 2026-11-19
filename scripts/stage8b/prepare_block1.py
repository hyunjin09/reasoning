"""Freeze definitions/covariates first, then join the approved outcome labels."""
import json
import shutil
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from visual_reasoning.stage8b.block1_data import (ROOT,B0,PREFIX,FAMILIES,PRIMARY,SECONDARY,PHASE_METRICS,
    digest,save,b0_path,interval_additions,matched_pairs)


def main():
    freeze_path=b0_path('freeze.json');base=json.loads(freeze_path.read_text())
    assert base['complete'] and base['tau_R']==0.5478025980771918 and base['primary_gap']==4
    for p,sha in {**base['artifacts_sha256'],**base['supporting_sha256']}.items():assert digest(p)==sha,p
    manifest='outputs/stage8b1a/cohort/census256_manifest_v1.jsonl'
    cohort=json.loads(b0_path('cohort_manifest.json').read_text())['rows']
    native=[json.loads(s) for s in Path(manifest).read_text().splitlines()]
    assert [(r['item_id'],r['family_id']) for r in native]==[(r['item_id'],r['family_id']) for r in cohort]
    metrics=pd.read_csv(b0_path('trajectory_metrics.csv'),dtype={'item_id':str,'family_id':str})
    geometry=pd.read_csv(b0_path('trajectory_geometry.csv'),dtype={'item_id':str,'family_id':str})
    counts=Counter(r['subject'] for r in native)
    covariates=pd.DataFrame([dict(item_id=r['item_id'],subject=r['subject'],
        subject_group=r['subject'] if counts[r['subject']]>=8 else 'OTHER',level=str(r['level']),
        answer_format='multiple_choice' if r['options'] else 'open',question_words=len(r['question'].split()),
        log_question_length=float(np.log1p(len(r['question'].split())))) for r in native])
    continuous={}
    for key,vals in [('log_reasoning_length',np.log(metrics.reasoning_tokens.to_numpy())),('log_question_length',covariates.log_question_length.to_numpy())]:
        continuous[key]=dict(mean=float(vals.mean()),scale=float(vals.std()) or 1)
    paths=['plan/stage8b_block1_whole_trajectory_success_failure_plan.md','plan/stage8b_block1_analysis_protocol_v1.md',str(freeze_path),manifest]
    protocol=dict(at=datetime.now(timezone.utc).isoformat(),source_sha256={p:digest(p) for p in paths},
        block0_sha256=digest(freeze_path),cohort=256,bootstrap_resamples=4000,seed=1234,families=FAMILIES,
        primary_metrics=PRIMARY,secondary_metrics=SECONDARY,phase_metrics=PHASE_METRICS,
        continuous=continuous,subject_pool_counts=dict(counts),subject_levels=sorted(covariates.subject_group.unique()),
        format_levels=sorted(covariates.answer_format.unique()),difficulty_levels=sorted(covariates.level.unique()),
        small_displacement_cutoff=float(geometry.standardized_net_displacement.quantile(.05)),
        fit_definitions='OLS wrong-minus-correct; bootstrap and covariates per immutable protocol',
        low_displacement_population='pooled256 before outcome contrasts',
        no_outcome_contrasts_opened=True)
    save(ROOT/'audit'/'analysis_definition_freeze.json',protocol)
    covariates.to_csv(ROOT/'audit'/'frozen_covariates.csv',index=False)
    # Outcome labels are opened only after analysis choices above are sealed.
    outcomes=pd.read_csv(b0_path('outcome_table.csv'),dtype={'item_id':str,'family_id':str})
    completion=pd.read_csv(b0_path('completion_table.csv'),dtype={'item_id':str,'family_id':str})
    frame=metrics.merge(geometry,on=['item_id','family_id','order'],validate='one_to_one',sort=False)
    frame=frame.merge(covariates,on='item_id',validate='one_to_one',sort=False)
    frame=frame.merge(outcomes[['item_id','benchmark_label']],on='item_id',validate='one_to_one',sort=False)
    frame=frame.merge(completion[['item_id','completion']],on='item_id',validate='one_to_one',sort=False)
    events=pd.read_parquet(b0_path('retrieval_episode_table.parquet'),columns=['item_id','episode_index','preceding_gap'])
    for key in ['short_gap_fraction','burstiness']:frame[key]=np.nan
    for i,row in frame.iterrows():
        for key,value in interval_additions(events.loc[events.item_id==row.item_id]).items():frame.loc[i,key]=value
    assert list(frame.item_id)==[r['item_id'] for r in cohort] and len(frame)==frame.family_id.nunique()==256
    frame.to_csv(ROOT/(PREFIX+'trajectory_metrics.csv'),index=False)
    shutil.copyfile(b0_path('retrieval_episode_table.parquet'),ROOT/(PREFIX+'retrieval_episode_table.parquet'))
    assert digest(ROOT/(PREFIX+'retrieval_episode_table.parquet'))==digest(b0_path('retrieval_episode_table.parquet'))
    pairs=matched_pairs(frame)
    by_id=frame.set_index('item_id');matched_ids=[v for p in pairs for v in [p['correct_id'],p['wrong_id']]]
    balances={}
    for name,sub in [('all_scorable',frame.loc[frame.benchmark_label!='unresolved']),('matched',by_id.loc[matched_ids])]:
        balances[name]={}
        for col,vals in [('log_reasoning_length',np.log(sub.reasoning_tokens)),('log_question_length',sub.log_question_length),('difficulty_level',sub.level.astype(float))]:
            c=vals[sub.benchmark_label=='correct'];w=vals[sub.benchmark_label=='wrong']
            denom=np.sqrt((c.var()+w.var())/2)
            balances[name][col]=dict(correct_mean=c.mean(),wrong_mean=w.mean(),standardized_difference=(w.mean()-c.mean())/denom if denom>0 else None)
    save(ROOT/'audit'/'matching_freeze.json',dict(pairs=pairs,pair_count=len(pairs),balance=balances,
        rule='exact completion/subject_group/format; log-length caliper .5; cost includes .25 log-question distance',
        no_metric_value_used=True,bootstrap_conditioning='matching held fixed'))
    counts=frame.benchmark_label.value_counts().to_dict();scorable=counts.get('correct',0)+counts.get('wrong',0)
    census=dict(at=datetime.now(timezone.utc).isoformat(),examples=256,families=256,outcomes=counts,
        completion=frame.completion.value_counts().to_dict(),
        outcome_by_completion=pd.crosstab(frame.benchmark_label,frame.completion).to_dict(),
        accuracy_on_scorable=counts.get('correct',0)/scorable,known_correct_fraction_all=counts.get('correct',0)/256,
        unresolved_excluded_from_primary=True,all_unresolved_retained_for_completion=True,
        scoring_limitation='Frozen local deterministic/blind-manual extraction; not upstream GPT-4o fallback',
        reasoning_length_by_outcome={g:dict(n=len(s),mean=s.reasoning_tokens.mean(),median=s.reasoning_tokens.median(),min=s.reasoning_tokens.min(),max=s.reasoning_tokens.max()) for g,s in frame.groupby('benchmark_label')},
        cohort_order_preserved=True,shared_freeze_sha256=digest(freeze_path))
    save(ROOT/(PREFIX+'outcome_census.json'),census)
    print('Block1 definitions and analysis tables frozen:256 items; no metric contrasts computed.')


if __name__=='__main__':main()
