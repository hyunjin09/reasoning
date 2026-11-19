"""Close at the plan's mandatory technical gate without inventing science results."""
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
import pandas as pd
from scripts.stage13b.execution import ROOT,load,save,sha,now
from scripts.stage13b.review import tasks,technical,technical_path,checked
from scripts.stage13b.resources import account


def main():
    gates={str(p):load(p) for p in (ROOT/'audit/gates').glob('*_initial8.json')}
    failed={p:g for p,g in gates.items() if not g['passed']}
    assert failed and all(g['n']==24 and g['technical_missing']>=5 for g in failed.values())
    ledger=account('technical_stop_final');assert not ledger['active_jobs'] and ledger['allocated_gpu_hours_upper']<=32
    rows=[];technical_files={};behavior=defaultdict(list);execution=[]
    for t in tasks():
        complete=(ROOT/'generations'/t['task_id']/'result.json').exists()
        started=(ROOT/'generations'/t['task_id']/'input.json').exists()
        assert complete or not started,'Started call must finish before closure'
        execution.append(dict(task_id=t['task_id'],phase=t['phase'],family_id=t['family_id'],
            model_key=t['model_key'],started=started,complete=complete,
            status='COMPLETE' if complete else 'NOT_EXECUTED_MANDATORY_STOP'))
        if not complete:continue
        g,checks=checked(t);a=technical(t['task_id']);technical_files[str(technical_path(t['task_id']))]=sha(technical_path(t['task_id']))
        behavior[t['phase']+'_'+t['scale']+'_'+t['arm']].append(dict(task_id=t['task_id'],family_id=t['family_id'],
            tokens=g['tokens'],cap_hit=g['cap_hit'],normal_stop=g['normal_stop'],
            technical_valid=a['validity']['TECHNICALLY_VALID'],latency_seconds=g['request_latency_seconds']))
        if t['phase']=='technical':continue
        rows.append(dict(task_id=t['task_id'],scale=t['scale'],mode=t['mode'],condition=t['arm'].split('_',1)[1],
            item_id=t['item_id'],family_id=t['family_id'],replicate=t['replicate'],seed=t['seed'],tokens=g['tokens'],
            cap_hit=g['cap_hit'],finish_reason=g['finish_reason'],outcome=a['outcome'],**a['validity'],
            label='UNSCOREABLE_TECHNICAL' if not a['validity']['TECHNICALLY_VALID'] else None,correct=None,
            scoring_status='NOT_SCORED_AFTER_MANDATORY_TECHNICAL_STOP',
            generation_path=str(ROOT/'generations'/t['task_id']/'generation.json'),
            generation_sha256=sha(ROOT/'generations'/t['task_id']/'generation.json')))
    assert not list((ROOT/'audit/first_scores').glob('*.json')),'Do not silently discard existing scoring'
    metrics={}
    for cell,rr in behavior.items():
        tokens=[r['tokens'] for r in rr]
        metrics[cell]=dict(n=len(rr),families=len({r['family_id'] for r in rr}),cap_hits=sum(r['cap_hit'] for r in rr),
            normal_stops=sum(r['normal_stop'] for r in rr),technical_valid=sum(r['technical_valid'] for r in rr),
            technical_missing=sum(not r['technical_valid'] for r in rr),
            cap_after_outcome=sum(r['cap_hit'] and r['technical_valid'] for r in rr),
            tokens_median=float(np.median(tokens)),tokens_q1=float(np.quantile(tokens,.25)),tokens_q3=float(np.quantile(tokens,.75)),
            tokens_max=max(tokens),request_latency_median_seconds=float(np.median([r['latency_seconds'] for r in rr])),
            missing_by_family=dict(Counter(r['family_id'] for r in rr if not r['technical_valid'])))
    save(ROOT/'audit/final_technical_behavior.json',dict(at=now(),cells=metrics,rows=dict(behavior),
        correctness_used=False,scope='Technical completion only; counts nested by source family, no scientific inference.'))
    save(ROOT/'audit/final_execution_status.json',dict(at=now(),rows=execution,
        pending_cancellations=load(ROOT/'audit/stop_job_actions.json'),no_follow_on=True))
    columns=list(rows[0])
    for scale,condition in [('2B','EQ'),('8B','EQ'),('2B','img'),('4B','img'),('8B','img')]:
        selected=[r for r in rows if r['scale']==scale and r['condition']==condition]
        name='equal_evidence' if condition=='EQ' else 'image';p=ROOT/f'stage13b_{scale.lower()}_{name}_results.parquet'
        assert not p.exists();pd.DataFrame(selected,columns=columns).to_parquet(p,index=False)
    families=[dict(family_id=r['family_id'],item_id=r['item_id'],status='NOT_INFERRED_TECHNICAL_STOP',
        completed_new_calls=sum(x['family_id']==r['family_id'] for x in rows),scientific_effect=None)
        for r in load(ROOT/'stage13b_frozen48_manifest.json')['rows']]
    p=ROOT/'stage13b_family_level_results.parquet';assert not p.exists();pd.DataFrame(families).to_parquet(p,index=False)
    unavailable=dict(at=now(),status='NOT_ESTIMATED_TECHNICAL_STOP',reason='Mandatory initial8 technical-missingness gate failed before completing the frozen48 study.',
        failed_gates=failed,primary_effect=None,confidence_interval=None,new_outcomes_selected_by_correctness=False)
    for name in ['scale_effects','missingness_bounds','32k_sensitivity','primary_inference']:
        save(ROOT/f'stage13b_{name}.json',unavailable)
    save(ROOT/'stage13b_scoring_audit.json',dict(at=now(),status='TECHNICAL_VALIDITY_REVIEW_ONLY',files=technical_files,
        correctness_opened=False,paired_scientific_outcomes_opened=False,
        reason='Stopped before Phase3; unscored scoreable outputs have null label, not an invented correct/incorrect label. Technical missingness is not scored incorrect.',
        scope='Own-response validity and ambiguity review; no independent-rater reliability claim'))
    recommendation='Retain the confirmed 4B post-evidence result as the strongest claim and stop scaling-based role interpretation.'
    save(ROOT/'stage13b_decision.json',dict(at=now(),decision='CROSS_SCALE_ROLE_UNRESOLVED',termination='MANDATORY_TECHNICAL_STOP',
        failed_gates=failed,recommendation=recommendation,follow_on_launched=False,full_scientific_study_completed=False))
    ledger.update(completed_technical_calls=48,completed_new_scientific_calls=len(rows),planned_new_scientific_calls=1440,
        all_allocations_released=True,correctness_evaluated=False,follow_on_launched=False,target_gpu_hours=24)
    ledger['worker_receipts']={}
    stop_at=load(ROOT/'audit/stop_trigger.json')['at']
    for job in ledger['jobs']:
        folder=ROOT/'workers'/job['slurm_job_id']
        receipts={str(p):sha(p) for p in folder.glob('*.json')}
        if job['state']=='COMPLETED':
            assert load(folder/'exit.json')['complete'] and not (folder/'failure.json').exists()
            for batch in folder.glob('batch_*_started.json'):
                assert load(batch)['at']<stop_at,'No batch may start after the mandatory stop'
        ledger['worker_receipts'][job['slurm_job_id']]=receipts
    ledger['all_started_batches_predate_stop']=True
    ledger['receipt_note']='Environment receipts preserve GPU model, node, checkpoint and packages; exit receipts preserve elapsed time and process memory counters. Latencies reflect concurrent requests, not additive GPU-hours.'
    save(ROOT/'stage13b_resource_accounting.json',ledger)
    previous=load(ROOT/'audit/historical_preservation.json')['files']
    for p,h in previous.items():assert sha(p)==h,p
    for p,h in load(ROOT/'stage13b_input_hashes.json')['files'].items():assert sha(p)==h,p
    for p,h in load(ROOT/'config.json')['source_sha256'].items():assert sha(p)==h,p
    lines=['# Stage13B: mandatory technical stop','','Decision: **CROSS_SCALE_ROLE_UNRESOLVED**. The full cross-scale scientific study was not completed.','',
        'The frozen 48-family cohort, separate four-family technical set, initial eight families, all six checkpoints, prompts, seeds and recipes remain unchanged.','',
        'Plan Section 31 requires stopping when technical missingness exceeds 20% in any scale/mode arm of the frozen initial eight-family tranche.','']
    for p,g in failed.items():lines.append(f"- {Path(p).stem}: {g['technical_missing']}/24 technical missing outcomes ({100*g['technical_missing']/24:.2f}%).")
    lines += ['',f'Completed 48 technical calls and {len(rows)} new scientific-tranche calls. All completed outputs and technical decisions are preserved. Pending work was cancelled at the gate; already-running work was allowed to finish with its original cap. No remaining 40-family calls or new native-image scientific calls were launched.',
        '', '| Initial equal-evidence arm | Calls | Normal stops | Cap hits | Scoreable capped | Technical missing |',
        '|---|---:|---:|---:|---:|---:|']
    for cell,m in sorted(metrics.items()):
        if cell.startswith('equal_'):
            lines.append(f'| {cell[6:]} | {m["n"]} | {m["normal_stops"]} | {m["cap_hits"]} | {m["cap_after_outcome"]} | {m["technical_missing"]} |')
    lines += ['', 'The 24 queued 8B-Thinking scientific calls were cancelled before starting; they are unexecuted, not model failures. All 288 selected Stage13A 4B equal-evidence replicates remain available for exact reuse.',
        '', 'The separate technical validation observed five cap hits in 2B Instruct: four pre-outcome missing and one cap-after-clear-final. All other technical-checkpoint calls normal-stopped. Input/sampling/checkpoint checks passed. Repetition itself is scientific behavior; only lack of a clear unretracted outcome at truncation is technical missingness. The cause of the behavior remains unknown.',
        '', 'No new scientific correctness or paired inference was opened. Unscored scoreable calls have null labels; unavailable cells are empty result tables with an explicit stop status in the analysis artifacts. Stage13A remains valid and unchanged; its selected 4B replicate reuse manifest is preserved, but no new subset comparison is claimed. This is a technical stop, not evidence of a null cross-scale effect. Phase 3 correctness scoring/second-pass audits and Phase 4 sensitivity were not reached; own-response validity review is same-agent QC, not independent-rater reliability.',
        '', 'All five required scientific figures are not estimable from this stopped study and were not fabricated. The inference, sensitivity and bounds artifacts explicitly record NOT_ESTIMATED_TECHNICAL_STOP.',
        '', f'Resources: {ledger["allocated_gpu_hours_upper"]:.6f} allocated GPU-hours; hard limit 32. All stage allocations released. {len(previous):,} historical files and all input/generation-code seals verified unchanged.',
        '', 'Exactly one recommendation: '+recommendation,'','STOP. Recommendation not launched.']
    with (ROOT/'stage13b_summary.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    required=['cross_scale_role_spec.md','frozen48_manifest.json','technical4_manifest.json','checkpoint_manifest.json','input_hashes.json','seed_manifest.json',
        '2b_image_results.parquet','2b_equal_evidence_results.parquet','4b_image_results.parquet','4b_equal_evidence_reuse.json','8b_image_results.parquet',
        '8b_equal_evidence_results.parquet','scoring_audit.json','family_level_results.parquet','scale_effects.json','missingness_bounds.json','32k_sensitivity.json',
        'primary_inference.json','decision.json','resource_accounting.json','summary.md']
    save(ROOT/'audit/final_verification.json',dict(at=now(),terminated_at_prespecified_gate=True,full_scientific_study_completed=False,
        artifacts={str(ROOT/('stage13b_'+n)):sha(ROOT/('stage13b_'+n)) for n in required},historical_files_unchanged=len(previous),
        figures_status='Not estimable at mandatory technical stop; no fabricated scientific plots',all_gpus_released=True))
    print('MANDATORY_TECHNICAL_STOP',failed.keys(),len(rows),'new calls;',ledger['allocated_gpu_hours_upper'],'GPUh')


if __name__=='__main__':main()
