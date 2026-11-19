"""Estimate, freeze and partition the unchanged72; no job launch or score inspection."""
import argparse
import ast
import subprocess
from pathlib import Path
from scripts.stage14d1_pilot.common import *
from scripts.stage14d1_pilot.reuse import load_reusable_state


def main(workers):
    gates=load(P/'audit/technical_v6_gates.json')
    transport=load(P/'audit/technical_v6_transport.json')
    source_review=load(P/'annotations/technical_v6_source_review.json')
    assert gates['technical_execution_ready'] and transport['all_transport_pass']
    assert source_review['families']==8 and source_review['review_complete']
    assert 1<=workers<=4
    oldseal=load(P/'audit/execution_seal_v6.json')
    for path,digest in oldseal['files'].items():assert sha(path)==digest,path
    # Also verify unchanged call_batch runtime body between technical and main entrypoints.
    def find_callbatch(path):
        tree=ast.parse(Path(path).read_text())
        return ast.dump(next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='call_batch'),include_attributes=False)
    assert find_callbatch('scripts/stage14d1_pilot/worker_v6.py')==find_callbatch('scripts/stage14d1_pilot/main_worker.py')
    original=rows(P/'inference/families.jsonl')
    selected={r['family_id'] for r in original}
    historic={r['family_id']:int(r['native']['T']['tokens']) for r in rows('outputs/stage14d0/inventory/source_and_raw_output_manifest.jsonl') if r['family_id'] in selected}
    assert len(historic)==72
    allocations=[];spent=PRIOR_GPU_SECONDS
    for p in (P/'audit/launches').glob('*.json'):
        job=load(p)['job']['slurm_job_id']
        parts=subprocess.check_output(['sacct','-j',job,'-X','-n','-P','--format=JobID,State,ElapsedRaw,AllocTRES'],text=True).strip().split('|')
        assert parts[1] in ('COMPLETED','FAILED','TIMEOUT','OUT_OF_MEMORY') or parts[1].startswith('CANCELLED'),parts
        charged=int(parts[2]) if 'gres/gpu=1' in parts[3] else 0
        spent+=charged;allocations.append(dict(job=job,state=parts[1],gpu_seconds=charged))
    throughput=gates['solver_short_tokens_per_gpu_second']
    # Use six calls per family as conservative unaliased proxy, original measuredlengths.
    proxy=sum(historic.values())*6
    v5timings=load(P/'audit/technical_v5_gates.json')['timings']
    helper_seconds=sum(t['elapsed_seconds'] for t in v5timings if t['task_ids'] and all('_read' in rid or rid.endswith('_query') or rid.endswith('_locate') for rid in t['task_ids']))
    startup=load(P/'raw/technical_v6/environment.json')['ready_seconds']
    expected=proxy/(throughput*.8)+helper_seconds*9+startup*workers
    stress=proxy/(throughput*.5)+helper_seconds*9+startup*workers
    remaining=CEILING_GPU_SECONDS-spent
    assert expected<remaining,('Expected main exceeds remainingbudget',expected,remaining)
    # Twelve aggregateGPUhours reserved; remainder held for legitimateinfra recovery.
    wall=min(43200//workers,remaining//workers-60)
    assert wall>0
    estimate=dict(at=now(),prior_actual_gpu_seconds=spent,prior_allocations=allocations,
        remaining_gpu_seconds=remaining,short_solver_tokens_per_gpu_second=throughput,
        short_measurement_caveat='256token throughput is not long-context throughput;20%discountexpected,50%stress',
        historical_unaliased_solver_token_proxy=proxy,expected_new_gpu_hours=expected/3600,
        stress_new_gpu_hours=stress/3600,all_solver_caps_token_bound=72*6*81920,
        helper_cost_proxy_gpu_seconds=helper_seconds*9,startup_seconds_per_worker=startup,
        workers=workers,reservation_gpu_hours=workers*wall/3600,reserve_after_reservations_gpu_hours=(remaining-workers*wall)/3600,
        main_caps_unchanged=81920,physical_aliases_will_reduce_work=True,
        hard_ceiling_policy='Admission and allocation reservations bounded16h; preservepartials and reportgenuineinfeasibility ifactualcostexceedsremaining. No capreduction.')
    save(P/'audit/main_resource_estimate.json',estimate)
    reuse={}
    compatibility=load(P/'protocol/helper_reuse_v6.json')['files']
    byid={r['item_id']:r for r in original}
    for p in (P/'raw/technical_v6/states').glob('*.json'):
        s=load(p);load_reusable_state(p,byid[s['item_id']],sha(P/'protocol/runtime_v6.json'),compatibility)
        reuse[s['item_id']]=str(p)
    assert len(reuse)==8
    release=dict(at=now(),technical_pass=True,technical_pass_definition='Executionvalidity, not componentsemantic/acceptanceyield',
        original_component_gates_pass=gates['original_component_gates_pass'],original_gates=gates['gates'],
        source_transport_review_complete=True,protocol_sha256=sha(P/'protocol/runtime_v6.json'),
        gates=str(P/'audit/technical_v6_gates.json'),transport=str(P/'audit/technical_v6_transport.json'),
        source_review=str(P/'annotations/technical_v6_source_review.json'),no_scientific_answers_used=True)
    save(P/'audit/scientific_release.json',release)
    extra=[Path('scripts/stage14d1_pilot')/n for n in ['main_worker.py','launch_main.py','reuse.py','verify_transport.py','statistics.py','analyze.py','prepare_main.py','test_reuse.py','test_statistics.py']]
    extra += [P/'audit/scientific_release.json',P/'audit/main_resource_estimate.json',P/'protocol/analysis_v1.md',P/'protocol/offline_review_selection.json']
    extra += list((P/'raw/technical_v6/states').glob('*.json'))
    save(P/'audit/main_execution_seal.json',dict(at=now(),files=dict(oldseal['files'],**{str(p):sha(p) for p in extra})))
    shards=[[] for _ in range(workers)];cost=[0]*workers
    for row in sorted(original,key=lambda r:(-historic[r['family_id']],r['family_id'])):
        available=[i for i in range(workers) if len(shards[i])<(72+workers-1)//workers]
        i=min(available,key=lambda k:(cost[k],len(shards[k]),k))
        shards[i].append(row);cost[i]+=historic[row['family_id']]
    attempts=[]
    for i,shard in enumerate(shards):
        ident=f'main_v6_rank{i}';attempts.append(ident)
        save(P/'manifests'/f'{ident}.json',dict(id=ident,mode='main',families=[r['family_id'] for r in shard],
            wall_seconds=wall,seal=str(P/'audit/main_execution_seal.json'),scientific_release=str(P/'audit/scientific_release.json'),
            reuse_acquisition={r['item_id']:reuse[r['item_id']] for r in shard if r['item_id'] in reuse},
            historical_cost_proxy_tokens=cost[i]*6))
    assert sum(map(len,shards))==72 and {r['family_id'] for shard in shards for r in shard}==selected
    save(P/'manifests/main_design.json',dict(at=now(),attempts=attempts,logical_slots=432,families=72,
        partition_rule='LPT by frozen historicalnative tokenlength only;stable family tie;all72 unchanged;no answer outcomes',
        cohort_sha256=sha(P/'inference/families.jsonl'),runtime_sha256=sha(P/'protocol/runtime_v6.json')))
    print('READY',workers,'workers; expectedGPUh',round(expected/3600,2),'stress',round(stress/3600,2),'prior',round(spent/3600,2),'reserved',workers*wall/3600)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workers',type=int,required=True);main(p.parse_args().workers)
