"""Freeze a coarse canonical grid only after baseline validity passes."""
import argparse
from scripts.stage9a3.prepare import ROOT,load,save,sha,now


def canonical(fraction,token):
    return (0,0) if fraction==0 or token==0 else (fraction,token)


def unique_policies(times):
    return list(dict.fromkeys(canonical(f,t) for f in (0,.5,.75,1) for t in times))


def baseline_alias(fraction,token,tokens,normal_eos):
    return fraction==1 and normal_eos and (token is None or token>=tokens-1)


def policy_id(f,t):
    return f'l{round(f*100):03d}_t'+('FULL' if t is None else str(t))


def freeze(key):
    b=load(ROOT/f'stage9a3_{key}_full_access.json');assert b['gates']['pass']
    times=load(ROOT/'stage9a3_qwen25_full_access.json')['token_grid']
    rows=[];logical=[];baseline={r['query_id']:r for r in b['rows']}
    for q,r in baseline.items():
        for f,t in unique_policies(times):
            alias=baseline_alias(f,t,r['tokens'],r['normal_eos']);p=policy_id(f,t)
            dest=ROOT/key/('full_primary/results' if alias else 'grid_primary/results')/q/('full' if alias else p)
            rows.append(dict(query_id=q,image_id=r['image_id'],policy_id=p,fraction=f,token_cutoff=t,mode='standard',
                execution='reuse_full' if alias else 'run',result_path=str(dest/'result.json'),generation_path=str(dest/'generation.json'),
                proof='All layers retain access through final generated query N-1; identical greedy trajectory by induction.' if alias else None,
                reuse_result_sha256=sha(dest/'result.json') if alias else None))
        for f in (0,.5,.75,1):
            for t in times:
                cf,ct=canonical(f,t)
                logical.append(dict(query_id=q,image_id=r['image_id'],fraction=f,token_cutoff=t,policy_id=policy_id(cf,ct)))
    path=ROOT/f'audit/{key}_grid_primary_manifest.json'
    source_paths=['scripts/stage9a3/grid.py','scripts/stage9a3/worker.py','scripts/stage9a3/runtime.py',
                  'code/visual_reasoning/stage9a3/access.py','code/visual_reasoning/stage9a3/analysis.py']
    nrun=sum(r['execution']=='run' for r in rows)
    gen=[load(ROOT/key/'full_primary/results'/q/'full/generation.json') for q in baseline]
    seconds=sum(g['runtime_seconds'] for g in gen);tokens=sum(g['tokens'] for g in gen);rate=tokens/seconds
    expected_tokens=sum(baseline[r['query_id']]['tokens'] for r in rows if r['execution']=='run')
    cap=b['scientific_cap'];sink_max=128
    pre=load(ROOT/f'stage9a3_mask_validation_{key}.json')
    estimate=dict(at=now(),model=key,canonical_grid_rows=len(rows),logical_grid_rows=len(logical),
        already_generated_full=64,new_grid_continuations=nrun,exact_full_reuse=sum(r['execution']!='run' for r in rows),
        bounded_sink_additional_at_most=sink_max,expected_new_grid_tokens=expected_tokens,
        measured_tokens_per_second=rate,observed_full_gpu_hours=seconds/3600,
        expected_grid_gpu_hours=expected_tokens/rate/3600,
        expected_primary_and_sink_gpu_hours=(tokens+expected_tokens+sink_max*b['length_summary']['mean'])/rate/3600,
        all_cap_primary_and_sink_gpu_hours=(64+nrun+sink_max)*cap/rate/3600,
        optional_reserve_standard_at_most=320,optional_reserve_all_cap_gpu_hours=320*cap/rate/3600,
        timing_limitations='Generation kernel walltime; startup/hashing, CPU bookkeeping and queue wait are additional. All-cap projection is not a guaranteed upper runtime bound.',
        phase_b_projection='Same continuation budget and Qwen2.5 throughput proxy; measure Qwen3 only after Phase A passes.')
    assert estimate['expected_primary_and_sink_gpu_hours']<40,'Compute gate exceeded'
    save(path,dict(at=now(),frozen=True,model=key,token_grid=times,fractions=[0,.5,.75,1],rows=rows,logical_rows=logical,
        baseline_sha256=sha(ROOT/f'stage9a3_{key}_full_access.json'),source_sha256={p:sha(p) for p in source_paths},
        technical_gate_sha256=sha(ROOT/f'stage9a3_mask_validation_{key}.json'),config_sha256=sha(ROOT/'config.json'),
        scientific_cap=pre['scientific_cap'],no_masked_outcomes_used=True))
    save(ROOT/f'audit/{key}_grid_resource_estimate.json',estimate)
    print(estimate,flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--model',choices=['qwen25','qwen3'],required=True)
    freeze(ap.parse_args().model)
