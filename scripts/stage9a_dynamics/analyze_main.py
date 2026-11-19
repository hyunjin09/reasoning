"""Complete sealed-answer scoring and preregistered 64-family primary inference."""
import json,os
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from scripts.stage9a_dynamics.prepare_answers import MAIN,BASE,save,sha
from visual_reasoning.stage8b.v2_scoring import score_answer
from visual_reasoning.stage9a_dynamics.analysis import family_metrics,contrast,descriptive,PRIMARY
from visual_reasoning.stage9a.protocol import ARMS


def load(path):return json.loads(Path(path).read_text())

def score_panel(root):
    review=load(root/'annotations/answer_extraction_review_frozen.json');assert review['frozen']
    assert sha(root/'annotations/answer_packets.json')==review['packets_sha256']
    idx=load(root/'annotations/answer_packet_index.json');dec={r['packet_id']:r for r in review['rows']}
    answers={r['result_key']:dict(answer=dec[r['packet_id']]['reviewed_answer'],method=dec[r['packet_id']]['method']) for r in idx['rows']}
    answers.update({r['result_key']:dict(answer=r['reviewed_answer'],method=r['review_source']) for r in idx['exact_native_reuse']})
    native={r['task_id']:r for r in load(BASE/'stage9a_accuracy_secondary.json')['rows']}
    cohort={r['item_id']:r for r in load(BASE/'stage9a_cohort_manifest.json')['rows']}
    tasks={r['task_id']:r for r in load(root/'audit/tasks.json')['rows']}
    manifest=load(root/'audit/interventions.json')['rows'];cache={};rows=[];scores=[]
    for c in manifest:
        task=tasks[c['task_id']];gold=cohort[task['item_id']];n=native[task['task_id']]
        if c['execution']=='identity_native':
            raw,rev=n['raw_adapter'],n['reviewed'];receipt=load(Path(task['native_dir'])/'result.json')
            answer=rev['extracted'];method='sealed_native_identity';key=None
        else:
            key=c['result_key']
            if key not in cache:
                directory=root/'rollouts/results'/key;receipt=load(directory/'result.json')
                assert receipt['generation_sha256']==sha(directory/'generation.json')
                text=load(directory/'generation.json')['raw_decoded_response'];a=answers[key]
                raw=score_answer(text,gold)
                rev=score_answer('' if a['answer'] is None else '\\boxed{'+a['answer']+'}',gold)
                cache[key]=(raw,rev,receipt,a)
                scores.append(dict(result_key=key,raw=raw,reviewed=rev,review_answer=a['answer'],review_method=a['method']))
            raw,rev,receipt,a=cache[key];answer=a['answer'];method=a['method']
        rows.append(dict(c,family_id=task['family_id'],arm=task['arm'],item_id=task['item_id'],subject=gold['subject'],difficulty=gold['level'],answer_format=gold['answer_format'],
            accuracy_no_credit=float(rev['correct'] is True),accuracy_raw=float(raw['correct'] is True),scorable=rev['correct'] is not None,
            benchmark_label=rev['benchmark_label'],raw_label=raw['benchmark_label'],reviewed_answer=answer,review_method=method,
            normal_eos=receipt['normal_eos'],at_length_cap=receipt['at_length_cap'],completion=receipt['completion'],
            tokens=receipt['tokens'],native_tokens=task['native_tokens'],native_completion=n['completion'],native_boundary_certain=task['reasoning_span']['certain'],
            native_reasoning_start=task['reasoning_span']['start'],native_reasoning_end=task['reasoning_span']['end'],
            first_divergence_token=receipt.get('first_divergence_token'),identical_native=c['execution']=='identity_native' or receipt.get('identical_native',False)))
    return rows,scores,tasks,review


def summarize(rows):
    groups={}
    for arm in ARMS:
        rr=[r for r in rows if r['arm']==arm];counts=Counter(r['benchmark_label'] for r in rr);n=len(rr);sc=counts['correct']+counts['wrong']
        groups[arm]=dict(n=n,counts=dict(counts),accuracy_no_credit=counts['correct']/n if n else None,
            scorable_only_accuracy=counts['correct']/sc if sc else None,normal_eos=sum(r['normal_eos'] for r in rr),capped=sum(r['at_length_cap'] for r in rr))
    return groups


def main():
    assert os.environ.get('SLURM_JOB_ID')
    root=MAIN;rows,scores,tasks,review=score_panel(root)
    assert len(rows)==2138 and len(scores)==1904
    families=sorted({r['family_id'] for r in rows});assert len(families)==64
    save(root/'audit/scored_answers.json',dict(rows=scores,review_sha256=sha(root/'annotations/answer_extraction_review_frozen.json')))
    save(root/'audit/scored_conditions.json',dict(rows=rows))
    for assay,name in [('cumulative','cumulative_cutoff_results'),('local','local_window_results'),('demand','demand_aligned_knockout')]:
        frame=pd.DataFrame([r for r in rows if r['assay']==assay]);dest=root/f'stage9a_{name}.parquet';assert not dest.exists();frame.to_parquet(dest,index=False)
    full=[r for r in rows if r['condition_id']=='cutoff_full'];assert len(full)==192
    save(root/'stage9a_full_access_baselines.json',dict(rows=full,arms=summarize(full),baseline='Exact frozen native outputs, unchanged backend configuration; backend/cache/RNG parity validated in 12 actual-model cases; native prefix parity checked in every worker task',validation_sha256=sha(root/'stage9a_mask_backend_validation.json')))
    metrics=family_metrics(rows);save(root/'audit/family_metrics.json',dict(rows=metrics))
    primary={p:dict(simultaneous=contrast(metrics,key),descriptive95=contrast(metrics,key,confidence=.95)) for p,key in PRIMARY.items()}
    rawmetrics=family_metrics([dict(r,accuracy_no_credit=r['accuracy_raw']) for r in rows])
    subjects={r['family_id']:r['subject'] for r in full};bytask={r['task_id']:r for r in full}
    primarypairs={p:primary[p]['simultaneous']['paired_families'] for p in PRIMARY}
    sensitivities={}
    for p,key in PRIMARY.items():
        # Restrict on baseline metadata only. Common-length exposure also requires both modes to reach the tested region natively.
        normal={f for f in families if all(bytask[t]['native_completion']=='normal completed' and bytask[t]['native_boundary_certain'] for t in bytask if bytask[t]['family_id']==f and bytask[t]['arm'] in ['thinking','instruct_cot'])}
        condition_names={'P1_512':['cutoff_full','cutoff_512'],'P1_2048':['cutoff_full','cutoff_2048'],'P2':['cutoff_full','local20_3','local20_4']}
        relevant=[r for r in rows if r['arm'] in ['thinking','instruct_cot'] and (r['condition_id'] in condition_names[p] if p in condition_names else r['assay']=='demand')]
        scorable={f for f in primarypairs[p] if all(r['scorable'] for r in relevant if r['family_id']==f)}
        similar={f for f in families if (lambda lens: min(lens)>0 and max(lens)/min(lens)<=2)([r['native_tokens'] for r in full if r['family_id']==f and r['arm'] in ['thinking','instruct_cot']])}
        cutoff=512 if p=='P1_512' else 2048 if p=='P1_2048' else None
        exposed={f for f in families if cutoff is None or all(r['native_tokens']>cutoff+1 for r in full if r['family_id']==f and r['arm'] in ['thinking','instruct_cot'])}
        sensitivities[p]=dict(raw_adapter=contrast(rawmetrics,key,confidence=.95),scorable_complete_pairs=contrast(metrics,key,confidence=.95,allowed=scorable),
            native_normal_certain=contrast(metrics,key,confidence=.95,allowed=normal),native_length_ratio_at_most2=contrast(metrics,key,confidence=.95,allowed=similar),
            both_natively_exposed=contrast(metrics,key,confidence=.95,allowed=exposed),
            leave_one_subject_out={s:contrast(metrics,key,confidence=.95,allowed={f for f in families if subjects[f]!=s}) for s in sorted(set(subjects.values()))})
    infer=dict(at=datetime.now(timezone.utc).isoformat(),frozen=True,primary=primary,sensitivities=sensitivities,independent_unit='conservative visual family',n_families=64,bootstrap_draws=4000,seed=920260924,
        multiplicity='Three primary groups; four scalar components. Bonferroni 98.75% simultaneous intervals; 95% intervals descriptive.',
        denominator='All64 families per arm, missing/unscorable answers retained separately with zero credit. P3 uses only paired eligible families; missing demand is not zero.',
        sensitivity_limitations='Scorable-only conditions on intervention output and can select by outcome. Native completion/length are nonrandom arm-specific characteristics. Normal/certain intersection may be small. No causal covariate interpretation.',
        subject_counts=dict(Counter(subjects.values())),review_sha256=sha(root/'annotations/answer_extraction_review_frozen.json'),manifest_sha256=sha(root/'audit/interventions.json'),analysis_source_sha256=sha('code/visual_reasoning/stage9a_dynamics/analysis.py'))
    save(root/'stage9a_primary_inference.json',infer)
    profile={a:{k:descriptive(metrics,a,k) for k in ['baseline_accuracy']+[f'cutoff{x}_damage' for x in (0,128,512,2048)]+[f'local{k}_damage' for k in range(5)]+['late_damage','demand_damage','control_damage','demand_minus_control']} for a in ARMS}
    save(root/'stage9a_temporal_necessity_profiles.json',dict(arms=profile,windows=[[i/5,(i+1)/5] for i in range(5)],normalization='Fixed native reasoning-span coordinates, not post-intervention length',descriptive=True))
    save(root/'stage9a_late_half_effects.json',dict(definition='Mean damage in [.6,.8] and [.8,1.0]; final40%, called late-half in compute amendment',arms={a:profile[a]['late_damage'] for a in ARMS},P2=primary['P2']))
    save(root/'stage9a_demand_vs_control_effects.json',dict(arms={a:{k:profile[a][k] for k in ['demand_damage','control_damage','demand_minus_control']} for a in ARMS},P3=primary['P3'],paired_events=109,eligibility_limitations='At most one explicit accepted demand per family/arm; matched control lacks annotated demand, not proven demand-free.'))
    save(root/'audit/main_analysis_ready.json',dict(at=infer['at'],slurm_job_id=os.environ['SLURM_JOB_ID'],main_analysis_sha256=sha(root/'stage9a_primary_inference.json'),review_sha256=infer['review_sha256'],controls_authorized=87))
    print(json.dumps({k:{'n':v['simultaneous']['n_families'],'effect':v['simultaneous']['mean'],'ci':v['simultaneous']['ci']} for k,v in primary.items()}))

if __name__=='__main__':main()
