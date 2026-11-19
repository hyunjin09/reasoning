"""Post-job CPU report. No answer scoring, model calls or follow-on launch."""
import json, subprocess, collections
from scripts.stage14d1_recovery.contracts import *

def main():
    launch=load(R/'audit/launch.json');job=str(launch['job']['slurm_job_id'])
    raw_account=subprocess.run(['sacct','-j',job,'-X','-n','-P',
        '--format=JobIDRaw,State,ElapsedRaw,AllocTRES,NodeList'],check=True,capture_output=True,text=True).stdout
    accounts=[]
    for line in raw_account.splitlines():
        ident,state,seconds,tres,node,*_=line.split('|')
        if ident!=job:continue
        gpus=1 if 'gres/gpu=1' in tres else 0
        accounts.append(dict(job_id=ident,state=state,elapsed_seconds=int(seconds),
                             allocated_gpus=gpus,gpu_seconds=int(seconds)*gpus,node=node))
    assert len(accounts)==1
    used=accounts[0]['gpu_seconds']
    assert remaining_seconds(1421,[used])>=0
    resource=dict(at=now(),prior_GPU_seconds=1421,recovery=accounts,
        total_GPU_hours=(1421+used)/3600,technical_ceiling_GPU_hours=2,
        remaining_technical_GPU_seconds=7200-1421-used,raw_sacct=raw_account)
    save(R/'audit/resource_accounting.json',resource)
    profiles=[];divergences=[]
    matrix=load(R/'protocol/execution_matrix.json')
    for profile in matrix['profiles']:
        name=profile['name'];root=R/'raw'/name;p=root/'replay_comparisons.json'
        if not p.exists():
            profiles.append(dict(profile=name,status='NOT_COMPLETED',error=load(root/'error.json') if (root/'error.json').exists() else None));continue
        comparisons=load(p)['comparisons']
        for offset in sorted({r['seed_offset'] for r in comparisons}):
            for decoding in ['sampled','greedy']:
                group=[r for r in comparisons if r['seed_offset']==offset and r['decoding']==decoding]
                profiles.append(dict(profile=name,status='MEASURED',seed_offset=offset,decoding=decoding,
                    exact_pairs=sum(r['pass'] for r in group),families=len(group)))
                for c in group:
                    if c['first_divergence'] is None:continue
                    a=load(root/c['a']/'generation.json');b=load(root/c['b']/'generation.json');k=c['first_divergence']
                    if k>=len(a['tokens']) or k>=len(b['tokens']):continue
                    la=a['raw_logits_top20_and_selected'][k];lb=b['raw_logits_top20_and_selected'][k]
                    common=set(la)&set(lb)
                    divergences.append(dict(profile=name,**c,a_token=a['tokens'][k],b_token=b['tokens'][k],
                        common_prefix=a['tokens'][:k]==b['tokens'][:k],
                        a_top_logits=la,b_top_logits=lb,
                        max_abs_delta_common_top_logits=max((abs(la[t]['value']-lb[t]['value']) for t in common),default=None),
                        a_path=str(root/c['a']/'generation.json'),b_path=str(root/c['b']/'generation.json')))
    save(R/'audit/replay_matrix_results.json',dict(at=now(),profiles=profiles,first_divergences=divergences))
    # Instrumented evidence is compared only at identical generated context.
    rng_comparisons=[]
    for profile in ['default_b8','deterministic_b8']:
        trace=R/'traces'/profile
        if not (trace/'sampling.jsonl').exists():continue
        samples={(r['request_id'],r['step']):r for r in rows(trace/'sampling.jsonl')}
        logits={(r['request_id'],r['step']):r for r in rows(trace/'logits.jsonl')}
        for item in ['107','33']:
            a_path=R/'raw'/profile/f'rng_{item}_a/generation.json';b_path=R/'raw'/profile/f'rng_{item}_b/generation.json'
            if not a_path.exists() or not b_path.exists():continue
            a=load(a_path);b=load(b_path);c=replay_comparison(a,b)
            k=c['first_divergence']
            record=dict(profile=profile,item_id=item,**c)
            if k is not None and (f'rng_{item}_a',k) in samples and (f'rng_{item}_b',k) in samples:
                sa=samples[(f'rng_{item}_a',k)];sb=samples[(f'rng_{item}_b',k)]
                la=logits[(f'rng_{item}_a',k)];lb=logits[(f'rng_{item}_b',k)]
                record.update(rng_state_equal=sa['rng_before']==sb['rng_before'],
                    raw_logits_equal=la['logits_sha256']==lb['logits_sha256'],
                    compared_generated_context_equal=la['generated_prefix_token_ids']==lb['generated_prefix_token_ids'],
                    a_sampling=sa,b_sampling=sb)
            # Instrumentation effects are an explicit diagnostic limitation.
            u=R/'raw'/profile/f'sampled_0_{item}_a/generation.json'
            record['instrumented_vs_uninstrumented_tokens_equal']=load(u)['tokens']==a['tokens'] if u.exists() else None
            rng_comparisons.append(record)
    save(R/'audit/logit_rng_comparisons.json',dict(at=now(),comparisons=rng_comparisons,
         limitation='Hooks synchronize CPU/GPU and can alter timing; infer no exact kernel cause without further evidence.'))
    validroot=R/'raw/independent_validation_b8'
    controlpath=validroot/'grammar_controls.json'
    controls=load(controlpath)['controls'] if controlpath.exists() else []
    statepath=validroot/'acquisition_states.json'
    states=load(statepath)['cases'] if statepath.exists() else {}
    read_records=[]
    for p in validroot.glob('*_read/input.json'):
        from scripts.stage14d1.contracts_v3 import parse_record, valid_readout
        gp=p.parent/'generation.json'
        read_records.append(dict(request_id=p.parent.name,valid=valid_readout(parse_record(load(gp)['raw'])) if gp.exists() else False))
    attempted_locators=len(list(validroot.glob('*_locate/input.json')))
    exact_validation=[p for p in profiles if p['profile']=='independent_validation_b8' and p.get('decoding')=='sampled']
    gates=dict(independent_exact_replay=len(exact_validation)==2 and all(p['exact_pairs']==p['families']==8 for p in exact_validation),
        synthetic_QUERY_NONE=len(controls)==12 and all(c['branch_match'] and not c['cap_hit'] for c in controls),
        query_contract_at_least6=sum(s['query_valid'] for s in states.values())>=6,
        actionable_queries_at_least4=sum(s['query_valid'] and s['query'].get('status')=='QUERY' for s in states.values())>=4,
        locator_contract_at_least75pct=attempted_locators>0 and sum(s.get('address_valid',False) for s in states.values())/attempted_locators>=.75,
        read_contract_at_least80pct=bool(read_records) and sum(r['valid'] for r in read_records)/len(read_records)>=.8)
    immutable=load(OLD/'audit/final_package_seal.json')
    preservation=all(sha(path)==digest for group in ['package_files','code_files'] for path,digest in immutable[group].items())
    physical=list((R/'raw').glob('*/*/result.json'))
    receipts=True
    runtime_inputs={r['item_id']:r for r in rows(R/'data/families.jsonl')}
    reconstruction=[]
    for p in physical:
        receipt=load(p)
        receipts &= sha(p.parent/'input.json')==receipt['input_sha256'] and sha(p.parent/'generation.json')==receipt['generation_sha256']
        inp=load(p.parent/'input.json')
        if inp['kind']=='solver':
            actual=load(p.parent/'generation.json')
            original=load(OLD/'raw/technical_v3'/f"{inp['item_id']}_replay_a/generation.json")
            row=runtime_inputs[inp['item_id']]
            reconstruction.append(dict(request_path=str(p.parent),
                original_prefix_token_identity=actual['prompt'][:len(original['prompt_token_ids'])]==original['prompt_token_ids'],
                original_image_identity=inp['pixels']==row['original_image_pixels'],
                original_prefix_bytes=inp['prompt'].startswith(row['original_chat_prompt']+row['prefix'])))
    save(R/'audit/recovered_input_identity.json',dict(at=now(),checks=reconstruction))
    gates['recovered_input_identity']=bool(reconstruction) and all(r['original_prefix_token_identity'] and r['original_image_identity'] and r['original_prefix_bytes'] for r in reconstruction)
    gates['old_records_preserved']=preservation;gates['all_completed_receipts_valid']=receipts
    software_pass=all(gates.values())
    # Source-semantic certification is not fabricated by an automated technical parser.
    decision='NO_GO_SOURCE_REVIEW_PENDING' if software_pass else 'NO_GO_TECHNICAL'
    result=dict(at=now(),gates=gates,software_gates_pass=software_pass,pilot_recommendation=decision,
        no_scientific_pilot_launched=True,physical_completed_requests=len(physical),controls=controls,
        acquisition_cases=states,read_records=read_records,attempted_locators=attempted_locators,
        semantic_source_review='NOT_AUTOMATICALLY_CERTIFIED; original source packets are provided for separate review',
        reason='Scientific syntax and source correctness are separate; no automatic pilot release')
    save(R/'audit/technical_revalidation_results.json',result)
    table=['| Runtime | Decode | Seed offset | Exact pairs |','|---|---|---:|---:|']
    for p in profiles:
        table.append(f"| {p['profile']} | {p.get('decoding',p['status'])} | {p.get('seed_offset','—')} | {str(p.get('exact_pairs','—'))+'/'+str(p.get('families','—'))} |")
    report=f'''# Stage14D1 SAVA technical recovery report

Status: **{decision}**. No 72-family scientific pilot was launched. Original records and the frozen cohort are preserved. This task tests runtime and interfaces, not SAVA efficacy or answer accuracy.

## Reconstruction and runtime evidence

All eight historical prompt-plus-512-token sequences exactly match the reconstructed native requests; original messages, chat prompts and prepared image pixels/sizes match. Historical RNG state is not resumed: the existing design restarts every arm with a fresh, fixed family seed. Therefore matching a historical future suffix was never the replay comparator. See `audit/reconstruction_audit_initial.json`.

The pinned vLLM 0.11.0 documentation specifies disabling V1 multiprocessing for deterministic offline scheduling, subject to identical hardware/version. Earlier attempts left it enabled. The pinned implementation initializes per-request generators from their explicit seeds and samples using exponential noise. Neither seed equality alone nor disabling prefix caching guarantees identical numerical execution. [Official versioned documentation](https://docs.vllm.ai/en/v0.11.0/usage/reproducibility.html).

{chr(10).join(table)}

Exact first-divergence tokens, raw top logits and receipt paths are in `audit/replay_matrix_results.json`; instrumented generator/logit evidence is in `audit/logit_rng_comparisons.json`. Scheduler batch membership is preserved under `traces/`. Differences with identical generated context and identical generator state support numerical forward-path sensitivity; different generator states support RNG/scheduling sensitivity. Absent measurements remain unresolved. Timing hooks can themselves change scheduling, so no precise kernel cause is inferred automatically.

## QUERY/NONE and bounded revalidation

CPU grammar tests show both status-first branches are reachable and reject a non-null answer slot. Synthetic branch controls: {sum(c['branch_match'] for c in controls)}/{len(controls)} expected branches; {sum(c['cap_hit'] for c in controls)} cap hits. These control cases were fixed before generation, and both branches remained available. They do not establish source correctness on MathVision.

Eight-family acquisition transport states saved: {len(states)}/8. Full parsed outputs and gates are in `audit/technical_revalidation_results.json`; source-only query/address packets exclude readouts/finals. Query/LOCATE/READ prompts and cases were not optimized using outcomes. Software gates pass: {software_pass}. Source-semantic certification is not supplied by a JSON parser and remains explicitly pending unless a separate source review is recorded.

## Gate and decision

The original exact-replay gate was retained. The prospective independent validation required all eight sampled pairs at both original and seed+100003 to match. No post-result threshold reduction was made. If exact replay is not reliable, the separately described fresh same-prefix, fixed-runtime, multiple-seed paired comparison remains a proposal; it has not silently replaced the old gate or been scientifically executed.

Recommendation: **{decision}**. Resolve whichever recorded gate remains unmet before scientific use. No method redesign, gold-based tuning, main pilot, Stage14E or old Stage14D grid was launched.

## Resources and preservation

Recovery GPU allocation: {used/3600:.6f} hours. Total including prior attempts: **{resource['total_GPU_hours']:.6f}/2.000000 technical GPU-hours**. The overall 16-hour stage ceiling is unchanged. Completed recovery receipts: {len(physical)}. Original package/code hashes preserved: {preservation}. This report is generated by CPU-only analysis after the diagnostic job; no final-answer scoring was performed.
'''
    (R/'reports/technical_recovery_report.md').write_text(report)
    print(decision, resource['total_GPU_hours'])

if __name__=='__main__':
    main()
