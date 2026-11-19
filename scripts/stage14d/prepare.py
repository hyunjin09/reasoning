"""Materialize the CPU-only G0 proposal; intentionally contains no launch path."""
import hashlib, json, math, shutil
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from scripts.stage14d.design import select_panel,classify,hash_order,fingerprint,arm_order,TEMPLATES,WRAPPER

OUT=Path('outputs/stage14d');A=Path('outputs/stage14a/v1');B=Path('outputs/stage14b');CV=Path('outputs/stage14c_v_blindtest_validation')
SEED='stage14d-g0-v1-20261011';H={}
def now():return datetime.now(timezone.utc).isoformat()
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tracked(p):
    p=Path(p);b=p.read_bytes();h=hashlib.sha256(b).hexdigest();assert H.get(str(p),h)==h;H[str(p)]=h;return b

def load(p):return json.loads(tracked(p))
def rows(p):return [json.loads(x) for x in tracked(p).decode().splitlines() if x.strip()]
def save(path,obj):
    path=OUT/path;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def write_rows(path,rs):
    path=OUT/path;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:
        for r in rs:f.write(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n')
def summarize(rs):
    return {k:dict(Counter(str(r[k]) for r in rs)) for k in ['answer_type','has_structured_atom','subject','difficulty','num_e_star_atoms']}

plan=Path('plan/stage14d_causal_evidence_acquisition_localization_plan.md');tracked(plan)
with (OUT/'spec/stage14d_plan.md').open('xb') as f:f.write(plan.read_bytes())
source=load(A/'stage14a_mathvision_e_star1000_manifest.json')['rows'];annotations={r['family_id']:r for r in load(A/'stage14a_mathvision_e_star_annotations.json')['rows']}
e=[r for r in rows(B/'manifests/mathvision_e1000_eval_manifest.jsonl')];native={r['identity']:r for r in rows(B/'manifests/mathvision_3040_eval_manifest.jsonl')}
scores=rows(B/'scoring/scored_outputs.jsonl');sidx={(r['identity'],r['model'],r['condition']):r for r in scores if r['identity'].startswith('mv:')}
tasks={t['task_id']:t for t in rows(B/'manifests/main_tasks.jsonl')}
config=load(B/'spec/frozen_run_config.json');ss={m:load(B/f'audit/main_{m}_scoring_seal.json')['scores'] for m in 'IT'}
rawseal=load(B/'audit/main_raw_seal.json')['files'];proseal=load(B/'audit/prospective_seal.json')['files']
for p in [B/'spec/frozen_run_config.json',B/'manifests/main_tasks.jsonl',B/'manifests/mathvision_e1000_eval_manifest.jsonl',B/'manifests/mathvision_3040_eval_manifest.jsonl']:
    assert proseal[str(p)]==digest(p)
aidx={r['family_id']:r for r in source};assert len(e)==len(aidx)==1000 and {r['family_id'] for r in e}==set(aidx)
combined=[];strata={x:[] for x in ['S1','S2','S3']};score_receipts={}
for r in e:
    a=aidx[r['family_id']];n=native[r['identity']];ann=annotations[r['family_id']]
    assert r['item_id']==a['item_id']==n['item_id'] and n['family_id']==r['family_id']
    assert n['image_sha256']==a['image_hash']==ann['source_image_hash']
    assert r['prompt']==ann['equal_evidence_rendering'] and digest(n['image'])==n['image_sha256']
    H[n['image']]=n['image_sha256']
    outcome={}
    for m in 'IT':
        for cond in ['image','evidence']:
            v=sidx[r['identity'],m,cond];tid=v['task_id'];assert tasks[tid]['family_id']==r['family_id'] and v['family_id']==r['family_id']
            path=B/f'scoring/first_scores/{tid}.json'
            for folder in ['score_reviews','score_adjudications_v6']:
                if (B/f'scoring/{folder}/{tid}.json').exists():path=B/f'scoring/{folder}/{tid}.json'
            score=load(path);assert fingerprint(score)==ss[m][tid] and score['status']==v['status']
            score_receipts[tid]=dict(path=str(path),file_sha256=digest(path),canonical_sha256=fingerprint(score))
            outcome[m+'_'+cond]=v['status']
    st=classify(outcome['T_image'],outcome['T_evidence'])
    row=dict(r,stratum=st or 'OUTSIDE_DEFINED_STRATA',historical_outcomes=outcome,original_image=n['image'],original_image_sha256=n['image_sha256'],native_prompt_sha256=hashlib.sha256(n['prompt'].encode()).hexdigest(),stage14a_receipt=a['primary_receipt'],status='PROPOSED_G0_IDENTITY_ONLY_NOT_G1_SOURCE_CERTIFICATION')
    combined.append(row)
    if st:strata[st].append(row)
assert {k:len(v) for k,v in strata.items()}=={'S1':306,'S2':110,'S3':574}
selected=[];overlap=[]
for st in strata:
    chosen=select_panel(strata[st],100,SEED+'|'+st);selected.extend(chosen);overlap.extend(select_panel(chosen,40,SEED+'|I-overlap|'+st))
assert len({r['family_id'] for r in selected})==300 and len({r['family_id'] for r in overlap})==120
picked={r['family_id'] for r in selected};technical=select_panel([r for r in combined if r['family_id'] not in picked],4,SEED+'|technical')
write_rows('cohorts/thinking_strata_300.jsonl',selected);write_rows('cohorts/instruct_overlap_120.jsonl',overlap)
write_rows('cohorts/technical_source4_proposed.jsonl',technical)
write_rows('cohorts/source_pool_1000_status.jsonl',[dict(family_id=r['family_id'],item_id=r['item_id'],stratum=r['stratum'],historical_outcomes=r['historical_outcomes'],selected=r['family_id'] in picked) for r in combined])
write_rows('cohorts/future_outcome_unconditioned_order_NOT_EXECUTED.jsonl',[dict(family_id=r['family_id'],item_id=r['item_id'],order_hash=hash_order(SEED+'|future-source-only',r['family_id']),previously_outcome_observed=True,selected_or_executed=False) for r in sorted(combined,key=lambda r:hash_order(SEED+'|future-source-only',r['family_id']))])
save('audit/source_and_strata_identity_v1.json',dict(at=now(),families=1000,images_hash_checked=1000,original_score_records_verified=4000,available={k:len(v) for k,v in strata.items()},native_correct_e_unscorable=1,outside_strata=10,selected={k:100 for k in strata},overlap={k:40 for k in strata},source_and_historical_identity='PASS',new_source_fidelity_review='PENDING_G1',old_score_receipts=score_receipts))
save('audit/cohort_balance_v1.json',dict(pool={k:summarize(v) for k,v in strata.items()},selected={k:summarize([r for r in selected if r['stratum']==k]) for k in strata},overlap={k:summarize([r for r in overlap if r['stratum']==k]) for k in strata}))
# Inputs for genuine source-only review; no heuristic target/ROI or E0/E1/E2 labels.
work=[]
for r in selected+technical:
    ann=annotations[r['family_id']]
    work.append(dict(family_id=r['family_id'],item_id=r['item_id'],technical=r in technical,source_image=r['original_image'],source_image_sha256=r['original_image_sha256'],native_question=native[r['identity']]['prompt'],source_receipt=r['stage14a_receipt'],frozen_evidence_atoms=ann['e_star_atoms'],candidate_existing_requests=ann.get('evidence_request_per_atom',[]),atom_metadata=ann.get('atom_metadata',[]),target_state='PENDING_SOURCE_REVIEW',primary_target=None,irrelevant_target=None,ROI=None,no_automatic_scalar_decomposition=True,model_outcomes_in_review_packet=False))
write_rows('cohorts/source_only_target_review_worklist_v1.jsonl',work)
write_rows('cohorts/mechanism_source_review_order_v1.jsonl',[dict(family_id=r['family_id'],item_id=r['item_id'],order_hash=hash_order(SEED+'|mechanism',r['family_id']),source_validity='PENDING',included=False) for r in sorted(selected,key=lambda r:hash_order(SEED+'|mechanism',r['family_id']))])
# Verify selected raw joins and collect planning-only runtime metadata without reviewing trace content.
rawrefs=[];metrics=[];anchor_work=[]
for model,panel in [('T',selected),('I',overlap)]:
    for r in panel:
        for condition in ['image','evidence']:
            scored=sidx[r['identity'],model,condition];t=tasks[scored['task_id']]
            paths=list((B/'raw'/t['collection']/t['task_id']).glob('attempt_*/result.json'));assert len(paths)==1
            rp=paths[0];gp=rp.parent/'generation.json';ip=rp.parent/'input.json';receipt=load(rp)
            assert rawseal[str(rp)]==digest(rp);gb=tracked(gp);ib=tracked(ip)
            assert hashlib.sha256(gb).hexdigest()==receipt['generation_sha256']==scored['generation_sha256'] and hashlib.sha256(ib).hexdigest()==receipt['input_sha256']
            g=json.loads(gb);i=json.loads(ib);assert i['task']==t
            ref=dict(family_id=r['family_id'],model=model,condition=condition,task_id=t['task_id'],result=str(rp),input=str(ip),generation=str(gp),result_sha256=digest(rp),input_sha256=receipt['input_sha256'],generation_sha256=receipt['generation_sha256'])
            rawrefs.append(ref)
            if condition=='image':
                metrics.append(dict(family_id=r['family_id'],stratum=r['stratum'],model=model,tokens=g['tokens'],request_latency_seconds=g['request_latency_seconds'],job=g['job'],cap_hit=g['cap_hit']))
                anchor_work.append(dict(ref,state='PENDING_NATIVE_TRACE_REVIEW',E0=None,E1=None,E2=None,anchor_token_index=None,prefix_sha256=None,source_neutral=None,fallback=None,review_inference='None; missing fields are not absence labels',raw_token_count=len(g['generated_token_ids'])))
write_rows('audit/selected_historical_raw_receipts_v1.jsonl',rawrefs);write_rows('anchors/native_trace_annotation_worklist_v1.jsonl',anchor_work);write_rows('audit/historical_runtime_metadata_v1.jsonl',metrics)
# Frozen slot inventory carries no oracle text and is deliberately non-executable.
slots=[]
for model,panel in [('T',selected),('I',overlap)]:
    for st in strata:
        group=sorted([r for r in panel if r['stratum']==st],key=lambda r:hash_order(SEED+'|execution',r['family_id']))
        for rank,r in enumerate(group):
            seed=int(hash_order(SEED+'|generation',r['family_id']),16)%(2**31)
            for order,arm in enumerate(arm_order(rank)):
                slots.append(dict(task_id=f"{model}_{arm}_{r['family_id']}",family_id=r['family_id'],item_id=r['item_id'],model=model,stratum=st,arm=arm,condition_order=order,seed=seed,state='NON_EXECUTABLE_PENDING_G0_G1_G2_G3_G4',prefix_identity=None,source_request=None))
write_rows('spec/main_condition_slots_proposed_v1.jsonl',slots);assert len(slots)==2100
save('spec/condition_templates_frozen.json',dict(at=now(),version='G0_PROPOSAL_V1',templates=TEMPLATES,wrapper=WRAPPER,insertion='Append directive token IDs after exactly copied original assistant-prefix IDs, no turn reset. B0 appends zero tokens. Same image and native question. Requires G3 token-ID proof.',oracle_values_allowed=False,target_requests_pending_source_review=True))
save('spec/pinned_model_revisions_and_recipes.json',dict(parent_path=str(B/'spec/frozen_run_config.json'),parent_sha256=digest(B/'spec/frozen_run_config.json'),models=config['models'],precision=config['precision'],runtime=config['runtime'],environment=config['environment'],image_preprocessing=config['image_preprocessing'],stop=config['stop'],system_message=config['system_message'],chat_template=config['chat_template'],main_backend='Inherited vLLM0.11 BF16; exact prefix adapter requires validation',nested_backend='NOT_YET_VALIDATED for Qwen3-VL-4B under this pinned runtime; no silent backend replacement'))
cvseal=load(CV/'audit/C_raw_seal_v1.json');checked=0
for p,h in cvseal['files'].items():assert digest(p)==h;checked+=1
cvrequired=['C_contract_modes_seal_v1.json','C_fidelity_scoring_seal_v1.json','C_fixed_QC_seal_v1.json','C_primary_seal_v1.json','final_validation.json']
cv_missing=[str(CV/'audit'/p) for p in cvrequired if not (CV/'audit'/p).exists()]
save('audit/stage14cv_prerequisite_status_v1.json',dict(at=now(),raw_calls=cvseal['calls'],receipt_hashes_verified=checked,raw_generation_complete=True,closure_complete=False,missing_required_artifacts=cv_missing,explicit_waiver_received=False,main_launch_allowed=False,remaining_work='Response-mode classification; two-pass source fidelity; fixedQC; C primary analysis/seal; synthesis/figures/accounting/final closure.'))
# Historical effective token throughput, not sum of concurrent request latencies.
resource=load(B/'audit/resource_accounting.json');jobs={j['job_id']:j for j in resource['jobs']};total_by_job=Counter()
for sc in scores:
    tid=sc['task_id'];t=tasks.get(tid)
    if not t:continue
    # Main request outputs are partitioned by immutable worker manifests; avoid opening all trajectories.
for job,j in jobs.items():
    if j.get('mode')!='main' or not j.get('gpu_hours'):continue
    env=B/'audit/workers'/job/'environment.json'
    if not env.exists():continue
    d=load(env);mp=Path(d['manifest'])
    if not mp.exists():continue
    manifest=load(mp);tids={t['task_id'] for t in manifest['rows']}
    total_by_job[job]=sum(sc['tokens'] for sc in scores if sc['task_id'] in tids)
throughput=[dict(job=job,tokens=tokens,gpu_hours=jobs[job]['gpu_hours'],tokens_per_gpu_second=tokens/(jobs[job]['gpu_hours']*3600)) for job,tokens in total_by_job.items() if tokens>0]
assert throughput,'Missing historical throughput evidence'
rate=float(np.median([r['tokens_per_gpu_second'] for r in throughput]));slow=float(np.quantile([r['tokens_per_gpu_second'] for r in throughput],.25))
planned_tokens=5*sum(r['tokens'] for r in metrics)
tmedian=float(np.median([r['tokens'] for r in metrics if r['model']=='T']))
nested_tokens=144*tmedian;base_hours=(planned_tokens+nested_tokens)/(rate*3600)
stress_hours=(2*(planned_tokens+nested_tokens))/(slow*3600)+2+4
proposed_ceiling=int(math.ceil(stress_hours/10)*10)
planning=dict(at=now(),basis='Historical sealed native completion tokens, multiplied by five arms; main-job aggregate output tokens / retained observed-or-proxy allocated GPU-seconds. This is not a Stage14D calibration.',historical_main_job_throughput=throughput,median_effective_tokens_per_gpu_second=rate,p25_effective_tokens_per_gpu_second=slow,main_full_native_length_proxy_tokens=planned_tokens,nested_144_proxy_tokens=nested_tokens,historical_rate_point_gpu_hours=base_hours,stress_projection_gpu_hours=stress_hours,stress_assumptions='2x output-token length; p25 parent effective throughput; +2h technical calibration +4h startup/readouts/accounting margin. Prefix recomputation/runtime overhead may exceed this proxy.',proposed_stage_gpu_hour_ceiling=proposed_ceiling,approved_stage_gpu_hour_ceiling=None,technical_calibration_proposed_gpu_hours=2,concurrency_max=8,preflight_concurrency=2,current_stage_gpu_hours=0,scientific_continuation_ceiling=2244,technical_continuation_ceiling=24,short_readout_ceiling=150,maximum_physical_continuations=2268,maximum_physical_calls_including_readouts=2418,calibration_not_run=True,no_guaranteed_eta=True,main_release_requires_measured_reestimate=True)
save('audit/resource_projection_proposed_v1.json',planning)
# MDE planning is an assumption grid, not an estimate from intervention effects.
from statistics import NormalDist
z=NormalDist().inv_cdf(1-.025/2)+NormalDist().inv_cdf(.8)
save('analysis/power_planning_assumptions_v1.json',dict(n=100,two_sided_per_endpoint_alpha=.025,power=.8,approximation='Conservative first Holm threshold and paired Bernoulli disagreement variance; ignores delta^2. This is a planning approximation, not a post-hoc power test.',rows=[dict(disagreement=q,MDE_pp=100*z*math.sqrt(q/100)) for q in [.1,.2,.3,.5]],new_intervention_outcomes_used=False))
save('spec/approved_scope_and_gates.json',dict(at=now(),user_request='follow plan/stage14d_causal_evidence_acquisition_localization_plan.md',preparation_authorized=True,G0_numeric_compute_approval=False,proposed_scientific_calls=2244,proposed_technical_calls=24,proposed_short_readouts=150,proposed_gpu_hour_ceiling=proposed_ceiling,approved_gpu_hour_ceiling=None,existing_user_concurrency_authority=8,stage14cv_closure=False,stage14cv_waiver=False,technical_benchmark_before_main_approval='Requires bounded 2-GPU-hour /24-call approval first; no numeric budget was supplied by the draft.',state='HOLD_G0_NO_GENERATION'))
save('audit/immutable_source_hashes.json',dict(at=now(),files=H))
for path,h in H.items():assert digest(path)==h,path
save('audit/g0_cpu_validation_v1.json',dict(at=now(),status='PASS_PREPARATION_ONLY',source_families=1000,source_images=1000,sealed_score_records=4000,selected_T=300,selected_I_overlap=120,disjoint_technical=4,selected_raw_triples=840,proposed_main_slots=2100,source_annotations_completed=0,native_anchors_completed=0,prospective_model_calls=0,GPU_hours=0,stage14cv_raw_triples_verified=800,stage14cv_closure=False,input_hashes_unchanged=len(H),git_metadata_available=Path('.git').exists(),scientific_release=False))
print(json.dumps(dict(selected=300,overlap=120,technical=4,source_counts={k:len(v) for k,v in strata.items()},structured_selected=sum(r['has_structured_atom'] for r in selected),point_gpu_hours=base_hours,stress_gpu_hours=stress_hours,proposed_cap=proposed_ceiling,prerequisite='C-V raw complete; semantic reviews and final closure absent',gpu_launched=False),indent=2))
