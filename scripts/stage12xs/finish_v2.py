"""Close only Stage12X-S after its frozen phase gates; never launch work."""
import json
from collections import Counter
from pathlib import Path
import pandas as pd
from scripts.stage12xs.execution_v2 import ROOT,load,save,sha,now
from scripts.stage12xs.phase_v2 import result_rows,write_parquet
from scripts.stage12xs.inference_v2 import infer_transfer
from scripts.stage12xs.resources_v2 import account
from scripts.stage12xs.figures_v2 import make

RECOMMENDATIONS={
 'HELDOUT_STATE_PRODUCTION_REPLICATED':'Replicate portable reasoning-state production at one additional Qwen3-VL model scale before promoting it to a broad Thinking-VLM claim.',
 'HELDOUT_PORTABILITY_PARTIAL':'Keep state production as a promising targeted mechanism and obtain one more independent held-out cohort before making a generalization claim.',
 'HELDOUT_CANDIDATE_SPARSE':'Build a harder fresh E*-annotated cohort to increase B4 Thinking-only yield before re-testing portability.',
 'HELDOUT_STATE_PRODUCTION_NOT_REPLICATED':'Restrict the paper claim to the developmental cohort and do not present portable state production as a general Thinking mechanism.',
 'UNRESOLVED_TECHNICAL':'Resolve the observed technical missingness before making a held-out portability claim.',
 'UNRESOLVED_LOW_YIELD':'Obtain one independently approved held-out cohort to resolve the low-yield result before making a generalization claim.'}

def preserve():
    checked={}
    for name in ['outputs/stage12xs/v1/audit/preserved_history.json',str(ROOT/'audit/preserved_pre_amendment.json'),str(ROOT/'audit/final_source_seal.json')]:
        d=load(name);files=dict(d['files']);files.update(d.get('review_files',{}))
        for p,h in files.items():assert sha(p)==h,p
        checked[name]=dict(n=len(files),sha256=sha(name))
    save(ROOT/'audit/final_preservation_check.json',dict(at=now(),all_unchanged=True,manifests=checked))

def empty_parquet(path):
    assert not path.exists()
    pd.DataFrame({k:pd.Series(dtype=t) for k,t in {'task_id':'str','item_id':'str','family_id':'str','arm':'str','replicate':'int64','correct':'boolean','label':'str'}.items()}).to_parquet(path,index=False)

def finish():
    a=load(ROOT/'audit/phaseA_inference.json');b=load(ROOT/'stage12xs_transfer_candidate_manifest.json')
    accounting=account('final');assert not accounting['active_jobs'];assert accounting['allocated_gpu_hours_upper']<=14
    transfer=None
    if b['n_selected']>=3:
        rows=result_rows('C');assert len(rows)==25*b['n_selected']
        write_parquet(ROOT/'stage12xs_transfer_results.parquet',rows)
        write_parquet(ROOT/'stage12xs_shuffled_controls.parquet',[r for r in rows if r['arm']=='SH_I'])
        transfer=infer_transfer(b['selected_ids'],rows);decision=transfer['decision']
    else:
        assert not (ROOT/'audit/phaseC_execution.json').exists()
        decision='HELDOUT_CANDIDATE_SPARSE'
        save(ROOT/'stage12xs_answer_safe_prefixes.json',dict(at=now(),status='NOT_RUN_CANDIDATE_GATE',rows=[],gate=b['gate']))
        for name in ['stage12xs_transfer_results.parquet','stage12xs_shuffled_controls.parquet']:empty_parquet(ROOT/name)
    b_arms={}
    for arm,name in [('C','cot'),('T','thinking')]:
        frame=pd.read_parquet(ROOT/f'stage12xs_{name}_results.parquet')
        b_arms[arm]=dict(calls=len(frame),scoreable=int(frame.correct.notna().sum()),correct=int(frame.correct.fillna(False).sum()),
            cap_hits=int(frame.cap_hit.sum()) if 'cap_hit' in frame else 0)
    inference=dict(at=now(),phaseA=a,phaseB=dict(n_screened=len(b['transitions']),n_all_candidates=b['n_all_eligible'],n_selected=b['n_selected'],
        per_arm=b_arms,transitions=dict(Counter(r['transition'] for r in b['transitions']))),transfer=transfer,
        independent_unit='Conservative visual family. Five seeds are within-family repeats.',
        developmental_reference='outputs/stage12us/v1/stage12us_primary_inference.json',
        scope='Outcome-independent E*-eligible mechanism-replication cohort; not benchmark prevalence.')
    save(ROOT/'stage12xs_primary_inference.json',inference)
    save(ROOT/'stage12xs_decision.json',dict(at=now(),decision=decision,recommendation=RECOMMENDATIONS[decision],
        n_all_candidates=b['n_all_eligible'],n_tested=b['n_selected'] if transfer else 0,follow_on_launched=False,
        interpretation='Candidate scarcity is a yield limitation, not a portability null.' if transfer is None else 'Apply frozen five-seed family thresholds with technical missingness bounds.'))
    workers=[]
    for p in sorted((ROOT/'workers').glob('*/environment.json')):
        d=load(p);folder=p.parent;exit_=load(folder/'exit.json') if (folder/'exit.json').exists() else None
        workers.append(dict(job=d['job'],node=d['node'],gpu=d['gpu'],packages=d['packages'],environment_path=str(p),
            exit_path=str(folder/'exit.json') if exit_ else None,calls=exit_['calls'] if exit_ else None,
            worker_seconds=exit_['seconds'] if exit_ else None,gpu_memory_measurement='Parent PyTorch allocator counters do not measure vLLM child memory; see Slurm engine logs.'))
    accounting.update(workers=workers,total_completed_calls=len(list((ROOT/'generations').glob('*/result.json'))),
        target_gpu_hours=10,hard_gpu_hours=14,all_allocations_released=True,
        annotation_counts=dict(source_candidates_reviewed=156,final_families=96,frozen_facts=193,source_deterministic_second_reviews=24,
            technical_reviews=len(list((ROOT/'audit/technical_decisions').glob('*.json'))),
            technical_adjudications=len(list((ROOT/'audit/technical_adjudications').glob('*.json'))),
            first_correctness_scores=len(list((ROOT/'audit/first_scores').glob('*.json'))),
            second_correctness_reviews=len(list((ROOT/'audit/second_scores').glob('*.json')))),
        allocation_not_token_time=True,annotation='Source primary96/193facts; extension28; source second24 plus ambiguities. Same-agent second-pass scoring, not independent human inter-rater QC.')
    save(ROOT/'stage12xs_resource_accounting.json',accounting)
    preserve();make()
    per=a['per_arm'];lines=['# Stage12X-S held-out replication', '',f"Decision: **{decision}**.", '',
        'The approved source-pool amendment produced exactly96 final-QC-passed fresh families. Selection stopped after28 of the64 approved extension candidates;14 were accepted,36 remain unused. The original96+32 manifests and preflight shortfall remain preserved. No model outcomes informed source selection.193 source facts and all prompts were sealed before generation.', '',
        '## Phase A', '', '| Arm | Correct / scoreable | Technical missing | Cap hits |','|---|---:|---:|---:|']
    for arm in 'ENO':
        v=per[arm];lines.append(f"| {arm} | {v['accuracy']['numerator']}/{v['scoreable']} | {96-v['scoreable']} | {v['cap_hits']} |")
    r=a['oracle_rescue_complete'];all_no=a['oracle_rescue_all_scoreable_Nminus_O'];lines+=['',f"Complete native-failure profiles: {json.dumps(a['B_counts'])}. Oracle rescue among complete native failures: {r['numerator']}/{r['denominator']}; Wilson95% {r['wilson95']}.",
        f"Across all scoreable N−/O pairs, including families with an unscoreable E probe, oracle rescue is {all_no['numerator']}/{all_no['denominator']}; Wilson95% {all_no['wilson95']}. Both denominators are preserved.",
        'All-required-atom E scoring includes structured subfields. E− means the requested report was incomplete or incorrect; it does not by itself establish an inaccessible latent visual representation. Repetition is retained; truncation before a scoreable outcome is missing.', '',
        '## Phase B and transfer', '',f"C/T screened {len(b['transitions'])} frozen B4 families. Transitions: {json.dumps(inference['phaseB']['transitions'])}. Fresh C−T+ yield: {b['n_all_eligible']}; selected under the pre-outcome transfer order: {b['n_selected']}.",
        f"Screen arm counts (correct, scoreable, cap hits): {json.dumps(b_arms)}. Unscoreable C/T pairs never become Thinking-only candidates or paired failures."]
    if transfer:
        lines+=['','| Family endpoint | Confirmed / frozen | Unknown | Exact95% among observed |','|---|---:|---:|---|']
        for key in ['RT_T','RT_I','Q_I','Q_T','SH_I','production_support','strict_production_support']:
            v=transfer['endpoints'][key];e=v['exact'];lines.append(f"| {key} | {e['numerator']}/{v['frozen_denominator']} | {v['unknown']} | {e['exact95']} |")
        lines+=['','Run-level outcomes, all five seeds, majority decisions and full-cohort missingness bounds are preserved in the parquet and primary-inference artifacts. Seeds are not independent population observations.']
    else:lines+=['','Phase C was not run because fewer than3 scoreable C−T+ candidates met the frozen gate. No answer-safe prefixes or replay outcomes were manufactured. This is a candidate-yield limitation, not evidence that portable state production fails.']
    lines+=['','## Validity and boundaries','','QC used arm-separated first scoring, all ambiguous cases and a deterministic20% unambiguous-family audit. Second passes were performed by the same agent; no independent human reliability estimate is claimed. Exact extraction and adjudication records remain immutable.',
        'The cohort is source-selected and E*-eligible, not representative benchmark prevalence. No fine-grained visible-text mechanism, complete hidden-state account, or pure post-training causal explanation follows from this stage.', '',
        '## Resources and preservation','',f"Allocated GPU-hours (conservative upper accounting): {accounting['allocated_gpu_hours_upper']:.3f}; hard budget14. Completed calls: {accounting['total_completed_calls']}. All Slurm allocations released. Historical artifacts, original source manifests and final source/QC hashes verified unchanged.",
        'Four required figures are saved under figures/ as PNG and PDF. Resource receipts retain exact commands, nodes, runtime versions and timings. No follow-on stage was launched.', '',
        '## Exactly one recommendation','',RECOMMENDATIONS[decision],'','STOP.']
    p=ROOT/'stage12xs_summary.md'
    with p.open('x') as f:f.write('\n'.join(lines)+'\n')
    required=['heldout_replication_spec.md','historical_exclusion_manifest.json','source_candidate_manifest.json','fresh96_manifest.json','reserve32_manifest.json','frozen_e_star.json','e_star_review.json','phaseA_results.parquet','fresh_failure_profiles.parquet','phaseB_b4_manifest.json','cot_results.parquet','thinking_results.parquet','transfer_candidate_manifest.json','answer_safe_prefixes.json','transfer_results.parquet','shuffled_controls.parquet','primary_inference.json','decision.json','resource_accounting.json','summary.md']
    save(ROOT/'audit/final_artifacts.json',dict(at=now(),complete=True,files={str(ROOT/('stage12xs_'+n)):sha(ROOT/('stage12xs_'+n)) for n in required}))
    print(decision,RECOMMENDATIONS[decision])

if __name__=='__main__':finish()
