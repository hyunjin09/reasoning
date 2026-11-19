"""Final reporting only after required gates/scoring and GPU release."""
from pathlib import Path
import json
from scripts.stage12ys.execution import ROOT,load,save,sha,now
from scripts.stage12ys.phases import results,write_parquet
from scripts.stage12ys.protocol import role_signals
from scripts.stage12ys.inference import transfer,bounded_endpoint
from scripts.stage12ys.resources import account
from scripts.stage12ys.figures import make

RECOMMENDATIONS={
 'state':'Repeat the same image-vs-equal-evidence role decomposition at one additional Qwen3-VL model scale to test whether state construction explains why Thinking is useful even in small VLMs.',
 'multi_role':'Replicate the access/downstream role mixture at one additional model scale before pursuing finer mechanisms.',
 'access':'Test whether the access-side Thinking advantage scales more strongly at small VLM sizes than equal-evidence reasoning advantage.',
 'downstream':'Focus the next mechanistic study entirely on post-evidence reasoning rather than image access.',
 'unresolved':'Stop role-mechanism expansion and retain the narrower supported claims about evidence bottlenecks and developmental state portability.'}

def main():
    a=load(ROOT/'audit/phaseA_inference.json');b=load(ROOT/'audit/phaseB_inference.json');m=load(ROOT/'stage12ys_phaseC_candidate_manifest.json')
    ledger=account('final');assert not ledger['active_jobs'] and ledger['allocated_gpu_hours_upper']<=16
    if m['n_selected']>=2:
        rows=results('C');cs=transfer(m['selected_ids'],rows)
        assert len(rows)==20*m['n_selected'];status='COMPLETE'
    else:
        assert not (ROOT/'audit/phaseC_execution.json').exists();rows=[];cs=[];status=m['status']
        save(ROOT/'stage12ys_phaseC_answer_safe_prefixes.json',dict(at=now(),status=status,rows=[]))
    write_parquet(ROOT/'stage12ys_phaseC_transfer_results.parquet',rows)
    c=dict(status=status,n_eligible=m['n_eligible'],n_selected=m['n_selected'],n_entered=len(cs),families=cs,
        support=sum(r['state_support'] is True for r in cs),resolved_controls=sum(r['controls_resolved'] for r in cs),
        endpoint=bounded_endpoint([r['state_support'] for r in cs]))
    signals=role_signals(b['access']['n'],b['access']['support'],b['downstream']['n'],b['downstream']['support'],len(cs),c['support'],c['resolved_controls'])
    key=next((x for x in ['state','multi_role','access','downstream'] if signals[x]),'unresolved')
    rec=RECOMMENDATIONS[key]
    for panel,label in [('access','in_access_panel'),('downstream','in_downstream_panel')]:b[panel]['bounded_endpoint']=bounded_endpoint([r[panel] for r in b['families'] if r[label]])
    save(ROOT/'stage12ys_primary_inference.json',dict(at=now(),phaseA=a,phaseB=b,phaseC=c,signals=signals,
        independent_unit='Conservative visual family; seeds within family are stochastic repeats.',
        claim='Functional differences of deployed model variants, not a pure Thinking switch or formal causal mediation.'))
    save(ROOT/'stage12ys_decision.json',dict(at=now(),**signals,recommendation=rec,follow_on_launched=False,
        missingness='Retained; candidate sparsity is not a negative role result.'))
    workers=[]
    for p in sorted((ROOT/'workers').glob('*/environment.json')):
        r=load(p);end=p.parent/'exit.json';assert end.exists();ex=load(end)
        workers.append(dict(job=r['job'],node=r['node'],gpu=r['gpu'],environment_path=str(p),exit_path=str(end),
            calls=ex['calls'],seconds=ex['seconds'],memory='Parent allocator counters do not measure vLLM child VRAM; engine logs retain memory allocation.'))
    ledger.update(workers=workers,new_calls=len(list((ROOT/'generations').glob('*/result.json'))),reused_calls=288,
        target_gpu_hours=12,all_allocations_released=True,annotation_counts={x:len(list((ROOT/'audit'/x).glob('*.json'))) for x in ['technical_decisions','technical_adjudications','first_scores','second_scores','score_adjudications']})
    save(ROOT/'stage12ys_resource_accounting.json',ledger)
    preserved=load(ROOT/'audit/historical_preservation.json')['files']
    for p,h in preserved.items():assert sha(p)==h,p
    for p,h in load(ROOT/'audit/input_seal.json')['files'].items():assert sha(p)==h,p
    save(ROOT/'audit/final_preservation.json',dict(at=now(),passed=True,historical_files=len(preserved),input_seal_sha256=sha(ROOT/'audit/input_seal.json')))
    make()
    lines=['# Stage12Y-S Thinking role decomposition','',f'Decision: **{signals["decision"]}**.',
        f'Confirmed role signals: access={signals["access"]}; equal-evidence reasoning={signals["downstream"]}; state construction={signals["state"]}.','',
        'Exact Stage12X-S source-frozen96 reused. This is a paired role-decomposition study, not a new held-out replication. Instruct historical single runs remain screens; all confirmatory calls use fresh frozen seeds.','',
        '| Screen arm | Correct / scoreable | Technical missing |','|---|---:|---:|']
    for arm,v in a['per_arm'].items():lines.append(f'| {arm} | {v["correct"]}/{v["scoreable"]} | {v["missing"]} |')
    lines+=['','| Paired descriptive contrast | Estimate | Family bootstrap95% | Common families |','|---|---:|---|---:|']
    for name in ['G_img','G_E','G_access','A_evidence']:
        v=a[name];lines.append(f'| {name} | {v["estimate"]} | {v["bootstrap95"]} | {v["n"]} |')
    lines+=['','Attenuation uses the common four-task denominator; pair-specific gaps can have different denominators. These are descriptive contrasts, not formal causal mediation.',
        f'Native Thinking-only transitions: {json.dumps(a["native_thinking_only_transitions"])}.','',
        '| Fresh confirmation | Supported / frozen candidates | Unresolved |','|---|---:|---:|',
        f'| Access | {b["access"]["support"]}/{b["access"]["n"]} | {b["access"]["unknown"]} |',
        f'| Equal-evidence downstream | {b["downstream"]["support"]}/{b["downstream"]["n"]} | {b["downstream"]["unknown"]} |','',
        f'Phase C: {status}; {c["support"]}/{len(cs)} state-construction support; {c["resolved_controls"]} families with resolved baseline/shuffle controls. All source/replay inputs are identical Q+E* without images; first successful source replicate and maximal answer-safe prefix were frozen before replay.',
        '','Majorities use2/3 in confirmation and3/5 in replay. Missing runs remain unknown if they can change a majority. All-seed counts, exact descriptive family intervals and missingness bounds are retained. No best-of selection or seed/prefix search.',
        '','Evidence-probe success requires every frozen atom and structured subfield. E− denotes incomplete or incorrect demonstrated reporting, not absent latent visual access. Historical E_I used256tokens; new Instruct probes use the plan\'s32768-token recipe; Thinking81920. Model checkpoints/recipes/budgets differ, so no pure Thinking-switch inference is justified.',
        '','Arm-separated scoring and ambiguity/random second passes were conducted by the same agent, not independent human raters. Source-eligible MathVision families do not establish benchmark-wide or other-domain prevalence. Text portability does not identify the complete neural mechanism.',
        '',f'Resources: {ledger["new_calls"]} new calls; {ledger["allocated_gpu_hours_upper"]:.3f} allocated GPU-hours (hard16). All jobs released. {len(preserved)} historical files and source/QC seals verified unchanged. Five PNG/PDF figure pairs saved under figures/.',
        '','Exactly one recommendation: '+rec,'','STOP. Recommendation not launched.']
    with (ROOT/'stage12ys_summary.md').open('x') as f:f.write('\n'.join(lines)+'\n')
    required=['role_decomposition_spec.md','frozen96_manifest.json','reused_stage12x_inputs.json','phaseA_thinking_evidence_results.parquet',
        'phaseA_thinking_image_results.parquet','phaseA_thinking_equal_evidence_results.parquet','phaseA_role_screen.parquet',
        'phaseB_candidate_manifest.json','phaseB_seed_manifest.json','phaseB_confirmation_results.parquet','phaseB_role_labels.parquet',
        'phaseC_candidate_manifest.json','phaseC_answer_safe_prefixes.json','phaseC_transfer_results.parquet','primary_inference.json','decision.json','resource_accounting.json','summary.md']
    save(ROOT/'audit/final_verification.json',dict(at=now(),complete=True,artifacts={str(ROOT/('stage12ys_'+x)):sha(ROOT/('stage12ys_'+x)) for x in required},
        figures={str(p):sha(p) for p in (ROOT/'figures').glob('*')},all_gpus_released=True,historical_unchanged=True))
    print(signals,rec)

if __name__=='__main__':main()
