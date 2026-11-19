"""Publish required technical outcomes only after review and resource release."""
from pathlib import Path
from datetime import datetime
import json
import subprocess
import pandas as pd
from scripts.qwen3vl_official_eval.common import ROOT,load,save,sha,now

def verify_evidence(m,reviews,resource):
    """Verify provenance and chronology before publishing any final artifact."""
    freeze=load(ROOT/'audit/audit_freeze.json')
    manifest_path=ROOT/'qwen3vl_official_sanity_manifest.json'
    assert sha(ROOT/'audit/audit_freeze.json')==m['audit_freeze_sha256']
    assert sha(m['case_source'])==m['case_source_sha256']
    for group in ['files','preserved_old']:
        for p,d in freeze[group].items():assert sha(p)==d,p
    for p,d in m['source_sha256'].items():assert sha(p)==d,p
    assert sha('scripts/qwen3vl_official_eval/review.py')==load(ROOT/'audit/prelaunch_validation.json')['review_code_sha256']
    expected={r['item_id']:r for r in m['cases']}
    assert len(expected)==12
    jobs={r['slurm_job_id']:r for r in resource['jobs']}
    earliest=None
    for condition,review in reviews.items():
        assert len(review['rows'])==12
        assert {r['item_id'] for r in review['rows']}==set(expected)
        job_ids={r['slurm_job_id'] for r in review['rows']};assert len(job_ids)==1
        job=next(iter(job_ids));dest=ROOT/'workers'/job
        assert jobs[job]['status']=='COMPLETED' and jobs[job]['exit_code']=='0:0'
        assert load(dest/'exit.json')['complete']
        started=datetime.fromisoformat(load(dest/'generation_started.json')['at'])
        earliest=min(earliest,started) if earliest else started
        assert datetime.fromisoformat(freeze['at'])<datetime.fromisoformat(m['at'])<started
        if not condition.startswith('official_'):
            assert datetime.fromisoformat(load(ROOT/'audit/sanity_technical_gate.json')['at'])<started
        engine=load(dest/'engine_ready.json');requested=load(dest/'llm_requested.json')['kwargs']
        assert engine['dtype']=='torch.bfloat16' and engine['max_model_len']==128000
        assert requested['seed']==42 and requested['tensor_parallel_size']==1
        env=load(dest/'environment.json')
        assert env['packages']==m['environment']
        native=[json.loads(line) for line in (dest/'official_predictions.jsonl').read_text().splitlines()]
        assert len(native)==12 and [str(r['question_id']) for r in native]==[r['item_id'] for r in m['cases']]
        native={str(r['question_id']):r for r in native}
        for r in review['rows']:
            folder=ROOT/'results'/condition/r['item_id'];g=load(folder/'generation.json')
            receipt=load(folder/'result.json');inp=load(folder/'input.json')
            assert sha(folder/'generation.json')==r['generation_sha256']==receipt['generation_sha256']
            assert sha(folder/'input.json')==receipt['input_sha256']
            assert g['manifest_sha256']==sha(manifest_path) and not g['budget_interrupted']
            assert g['tokens']==len(g['generated_token_ids']) and g['visual_tokens']>0
            assert g['prompt_token_count']+g['tokens']<128000
            assert g['family_id']==expected[r['item_id']]['family_id']
            assert g['recipe']==inp['recipe']
            assert g['raw_decoded_response']==native[r['item_id']]['result']['gen_raw']
            assert g['official_final_response']==native[r['item_id']]['result']['gen']
            assert started<=datetime.fromisoformat(g['at'])<datetime.fromisoformat(review['at'])
            if g['finish_reason']=='length':assert g['at_length_cap']
            elif g['finish_reason']=='stop':assert g['normal_eos_or_official_stop']
            else:raise AssertionError(g['finish_reason'])
    return dict(earliest_generation_started=earliest.isoformat(),raw_official_output_matches=True,
        exact_case_order=True,manifest_and_audit_precede_generation=True,
        reviewed_generation_rows=sum(len(r['rows']) for r in reviews.values()))

def main():
    m=load(ROOT/'qwen3vl_official_sanity_manifest.json')
    resource=load(ROOT/'qwen3vl_official_eval_resource_accounting.json')
    assert resource['all_stage_allocations_released'] and resource['allocated_gpu_hours']<=3
    gate=load(ROOT/'audit/sanity_technical_gate.json')
    conditions=['official_instruct_direct','official_thinking']
    variants=[v['name'] for v in m['ablations'] if (ROOT/'annotations'/f"{v['name']}_review.json").exists()]
    reviews={c:load(ROOT/'annotations'/f'{c}_review.json') for c in conditions+variants}
    verification=verify_evidence(m,reviews,resource)
    records=[]
    for condition,review in reviews.items():
        for r in review['rows']:
            records.append(dict(condition=condition,arm=r['arm'],item_id=r['item_id'],family_id=r['family_id'],
                cap_hit=r['at_length_cap'],official_stop=r['normal_eos_or_official_stop'],
                committed_final=r['committed_final'],repetition_pathology=r['pathological_repetition'],
                generated_tokens=r['tokens'],request_latency_seconds=r['batch_request_latency_seconds'],
                finish_reason=r['finish_reason'],stop_reason=str(r['stop_reason']),correct=None,
                status='COMPLETED_TECHNICAL_REVIEW',generation_path=str(ROOT/'results'/condition/r['item_id']/'generation.json'),
                generation_sha256=r['generation_sha256'],slurm_job_id=r['slurm_job_id']))
    df=pd.DataFrame(records)
    p=ROOT/'qwen3vl_official_sanity_results.parquet';assert not p.exists()
    df[df.condition.isin(conditions)].to_parquet(p,index=False)
    if variants:
        assert gate['instruct_gate_pass']
        p=ROOT/'qwen3vl_instruct_loop_factor_ablation.parquet';assert not p.exists()
        df[df.condition.isin(variants)].to_parquet(p,index=False)
    baseline=reviews['official_instruct_direct']['summary'];causes=[]
    for c in variants:
        s=reviews[c]['summary']
        causes.append(dict(variant=c,caps_delta=s['caps']-baseline['caps'],finals_delta=s['finals']-baseline['finals'],
            pathologies_delta=s['pathologies']-baseline['pathologies'],
            supported_on_fixed_cases=s['caps']>baseline['caps'] or s['pathologies']>baseline['pathologies'] or s['finals']<baseline['finals']))
    save(ROOT/'audit/ablation_interpretation.json',dict(at=now(),comparisons=causes,
        scope='Completion-only, single stochastic run per condition,12 paired families. No unique historical root cause established.',accuracy_used=False))
    v='96588727e44c78b25ba03ea03b8e12f7e64fd0da';base=f'https://github.com/QwenLM/Qwen3-VL/blob/{v}/evaluation/MathVision/'
    lines=['# Qwen3-VL official MathVision baseline sanity\n',
        '## A. What Qwen officially does\n',
        f'Pinned source commit `{v}`. [Instruct]({base}infer_instruct.sh), [Thinking]({base}infer_think.sh), [inference and CoT]({base}run_mathv.py).\n',
        '| Arm | Temperature | top-p | top-k | Repetition | Presence | Max output |\n|---|---:|---:|---:|---:|---:|---:|\n| Instruct Direct |0.7|0.8|20|1.0|1.5|32768|\n| Thinking |1.0|0.95|20|1.0|0|40960|\n',
        'One user message, images first and canonical TSV question last; no system message or added Direct reasoning suffix. The TSV already supplies a final-answer/option-letter hint. CoT appends exactly `" Let\'s think step by step."` on the same Instruct checkpoint. Root generic Thinking temperature0.6 and seeds3407/1234 conflict with benchmark temperature1.0 and engine seed42; the benchmark code governs.\n',
        '## B. What our project did differently\n',
        '| Field | Official Instruct | Stage11C | Stage11C-R |\n|---|---|---|---|\n| Prompt | Canonical Hint/Question/Choices | Raw question + Options; no hint | Same project prompt |\n| Decoding | Sample0.7/top-p0.8/presence1.5 | Greedy/no presence penalty | Sample1.0/top-p0.95/no presence penalty |\n| Output cap |32768|4096/8192|40960|\n| Runtime |vLLM, dynamic batching, seed42|HF/SDPA,batch1|HF/eager text,batch1,item seed|\n',
        'The full field-by-field comparison for both models is in qwen3vl_mathvision_official_protocol_audit.md and protocol_diff.json. Original snapshots remain pinned. Canonical and project images have identical dimensions and source identities but slightly different JPEG pixels; old files were preserved. Therefore success of the official bundle alone cannot isolate prompt, penalty, sampling, backend or image-serialization effects.\n',
        '## C. Technical behavior on the frozen12 cases\n',
        '| Condition | Calls | Cap hits | EOS/official stop | Committed final | Pathology | Tokens median [Q25,Q75];max |\n|---|---:|---:|---:|---:|---:|---|']
    for c in conditions+variants:
        s=reviews[c]['summary'];t=s['tokens']
        lines.append(f"|{c}|12|{s['caps']}|{s['stops']}|{s['finals']}|{s['pathologies']}|{t['median']:g} [{t['q25_q75'][0]:g},{t['q25_q75'][1]:g}];{t['max']}|")
    lines+=['\nTiming: vLLM runs requests concurrently; amortized batch time per case and request completion latency are distinct.\n',
        '| Condition | Batch seconds | Amortized seconds/case | Median request latency seconds |\n|---|---:|---:|---:|']
    for c in conditions+variants:
        ids={r['slurm_job_id'] for r in reviews[c]['rows']};assert len(ids)==1
        timing=load(ROOT/'workers'/next(iter(ids))/'batch_timing.json')['batch_seconds']
        lines.append(f"|{c}|{timing:.2f}|{timing/12:.2f}|{reviews[c]['summary']['request_latency_seconds_median']:.2f}|")
    lines+=['\nRaw outputs and native official gen/gen_raw records are preserved. Literal commitments and repetition were reviewed without correctness scoring. Caps were not imputed as wrong. Thinking final commitments require its closing think marker; Direct requires an unretracted answer.\n',
        '## D. Supported explanation\n',
        'Established: the prior Direct prompt and generation/runtime configuration were not faithful to the benchmark-specific Qwen recipe. Stage11C-R reproduced the historical project configuration, not the official operating regime.\n']
    for c in causes:
        wording='worsened completion/repetition on these fixed cases, supporting a contributor under the official runtime' if c['supported_on_fixed_cases'] else 'did not worsen the three completion-gate counts on these fixed cases; this does not prove no effect'
        lines.append(f"- `{c['variant']}` {wording}: cap delta{c['caps_delta']:+d},final delta{c['finals_delta']:+d},pathology delta{c['pathologies_delta']:+d} versus official Instruct.")
    if variants:
        lines+=['\nThe sampling variant is a joint temperature/top-p substitution, not separate attribution to either parameter. These bounded stochastic comparisons do not establish a universal or unique cause of the historical loops. Prompt and backend effects remain unresolved; no post-outcome prompt search was performed.\n']
    else:
        lines+=['\nConditional single-factor ablations were not run because the official Instruct completion gate did not pass. The official recipe therefore does not establish a remedy on this fixed set. Missing presence penalty remains a historical protocol discrepancy, not an established explanation of the loops. Prompt, model behavior and numerical/runtime interactions remain unresolved; no further tuning or protocol search was performed.\n']
    failed=[r['item_id'] for r in reviews['official_instruct_direct']['rows'] if r['pathological_repetition']]
    if failed:
        lines+=[f"Instruct severe-loop case IDs: {', '.join(failed)}. Terminal and fixed midpoint passages plus whole-token repetition descriptors support these labels. The completed outputs can still contain redundant self-correction; the severe-pathology count is not a count of every repeated phrase.\n"]
    lines+=['Output format: the seven normally stopped Direct responses contain terminal boxed answers or an explicit final-answer line; all12 Thinking responses close the think section and provide a terminal boxed answer. Direct is unprompted for CoT, not constrained to answer-only text.\n' if not gate['instruct_gate_pass'] else '',
        'Runtime inspection found no concrete mismatch explaining the remaining loops: frozen canonical inputs match, official SamplingParams include the requested presence penalty with EOS enabled, both jobs exit0, and capped outputs reach the exact official cap. The original unpublished package/model revisions and hardware are not specified by Qwen, so residual numerical/runtime effects cannot be excluded. See audit/runtime_faithfulness_review.json.\n',
        'Historical Stage11C-R Direct had8/12 finals and4/12 caps/loops; official Direct here has7/12 finals and5/12 caps/loops. These are different stochastic/runtime/input configurations, so this comparison does not establish that the official recipe causally worsens behavior.\n' if not gate['instruct_gate_pass'] else '']
    lines+=[
        '## E. Scientific rerun decision\n',
        f"Unchanged Instruct gate: at least10/12 committed finals, at most1/12 cap hit, at most1/12 repetition pathology. Result: **{gate['decision']}**.\n",
        'Fair comparison means each model variant operates under its validated intended evaluation recipe; it does not require identical decoding settings. A later Equal-Evidence Oracle may share evidence content while preserving model-appropriate decoding. No80-family primary rerun, oracle, CoT generation, reserve or new benchmark was launched.\n',
        f"Allocated compute: **{resource['allocated_gpu_hours']:.6f} GPU-hours**, including startup and any failed attempts; hard3 respected. All stage allocations released. Environment installation and source audit used CPU only.\n",
        'Limitations:12 fixed cases, one sampled run per condition, execution-agent completion review, canonical JPEG serialization differs slightly from historical exports, and the official repository does not pin its original model/package revisions. Exact installed versions, source commits, model hashes, input hashes and job receipts are retained.\n']
    lines+=['Runtime validation: vLLM0.11.0/Torch2.8.0/Transformers4.57.1 ran BF16 with the automatically selected Flash Attention backend. Both initial jobs failed before generation because the project temporary socket path was too long; shortening only TMPDIR repaired startup. Those failures, the original manifest, and all allocated time are preserved. The runtime-only repair preceded every model output.\n']
    if gate['instruct_gate_pass']:
        lines+=['The Stage11C/11C-R Instruct baseline was not benchmark-faithful enough for the intended comparison. A scientific rerun using the official model-specific recipes is justified, subject to its own completion gates and separate user authorization.\n',
                'OFFICIAL_PROTOCOL_VALID — scientific rerun justified']
    else:lines+=['OFFICIAL_PROTOCOL_STILL_INVALID — do not rerun Claim 3']
    (ROOT/'qwen3vl_official_sanity_summary.md').write_text('\n'.join(lines)+'\n')
    freeze=load(ROOT/'audit/audit_freeze.json')
    for group in ['files','preserved_old']:
        for p,d in freeze[group].items():assert sha(p)==d,p
    for p,d in m['source_sha256'].items():assert sha(p)==d,p
    assert sha('scripts/qwen3vl_official_eval/review.py')==load(ROOT/'audit/prelaunch_validation.json')['review_code_sha256']
    assert len(df[df.condition.isin(conditions)])==24 and df['correct'].isna().all()
    live=subprocess.run(['squeue','-u','hyunjin','-h','-o','%i'],capture_output=True,text=True,check=True).stdout.split()
    assert set(live).isdisjoint(j['slurm_job_id'] for j in resource['jobs'])
    files=[p for p in ROOT.iterdir() if p.is_file()]
    expected=8+bool(variants);assert len(files)==expected,(len(files),expected)
    save(ROOT/'audit/closure_validation.json',dict(at=now(),status='PASS',decision=gate['decision'],
        preserved_old_unchanged=True,audit_and_manifest_precede_gpu_outputs=True,
        all_stage_allocations_released=True,no_scientific_rerun=True,
        verification=verification,
        artifacts={str(p):sha(p) for p in files}))
    print('OFFICIAL_EVAL_CLOSURE_PASS',gate['decision'])

if __name__=='__main__':main()
