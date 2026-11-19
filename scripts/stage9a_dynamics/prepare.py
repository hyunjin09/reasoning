"""Freeze outcome-independent conditions and provenance before scientific runs."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from scripts.stage8c.prepare import save, sha
from scripts.stage9a.run_native import now
from visual_reasoning.stage9a_dynamics.protocol import CUTOFFS, cumulative_interval, demand_control

ROOT=Path('outputs/stage9a_dynamics/v1');OLD=Path('outputs/stage9a/v1')
SPECIAL={'<|im_end|>','<|endoftext|>','<think>','</think>'}


def ranges(coords):
    result=[]
    for t in coords:
        if t<1:continue
        if result and result[-1][1]==t:result[-1][1]=t+1
        else:result.append([t,t+1])
    return result


def main():
    dest=ROOT/'audit/interventions.json';assert not dest.exists(),'Frozen manifest already exists'
    cfg=json.loads((OLD/'stage9a_generation_config_node07.json').read_text())
    tasks=json.loads((OLD/'audit/native_tasks.json').read_text())['rows']
    packet={r['packet_id']:r['task_id'] for r in json.loads((OLD/'annotations/packet_index.json').read_text())['rows']}
    semantic=json.loads((OLD/'annotations/semantic_review_complete.json').read_text())['rows']
    events=defaultdict(list)
    for r in semantic:events[packet[r['packet_id']]].append(r)
    sink_families=sorted({r['family_id'] for r in tasks},key=lambda f:hashlib.sha256(('dynamics_sink:'+f).encode()).hexdigest())[:32]
    output=[];baseline=[];conditions=[];full_tokens=0;rollout_estimate=0.;shared_base_estimate=0.;unique_counts=[]
    accuracy={r['task_id']:r for r in json.loads((OLD/'stage9a_accuracy_secondary.json').read_text())['rows']}
    for task in tasks:
        d=OLD/'native/examples'/task['task_id'];receipt=json.loads((d/'result.json').read_text())
        tokens=[json.loads(l) for l in (d/'tokens.jsonl').read_text().splitlines()]
        assert len(tokens)==receipt['tokens']
        for filename in ['input.json','generation.json','tokens.jsonl']:
            assert sha(d/filename)==receipt['provenance_sha256'][str(d/filename)]
        span=receipt['reasoning_span'];coords=[i for i in range(span['start'],span['end']) if tokens[i]['decoded_token'] not in SPECIAL]
        ids=[r['token_id'] for r in tokens];n=len(ids);L=len(coords)
        row=dict(task,native_dir=str(d),native_tokens=n,reasoning_span=span,reasoning_non_special_tokens=L,
                 native_receipt_sha256=sha(d/'result.json'),native_token_ids_sha256=hashlib.sha256(json.dumps(ids).encode()).hexdigest())
        output.append(row);base=dict(task_id=task['task_id'],family_id=task['family_id'],arm=task['arm'],
            native_dir=str(d),receipt_sha256=sha(d/'result.json'),native_tokens=n,reasoning_span=span,
            baseline_scoring=accuracy[task['task_id']],reuse_gate='stage9a_mask_backend_validation.json',verified=False)
        baseline.append(base);local=[]
        def add(name,assay,intervals,**meta):
            local.append(dict(task_id=task['task_id'],condition_id=name,assay=assay,mode='standard',intervals=intervals,**meta))
        for c in CUTOFFS:
            interval=cumulative_interval(c)
            add('cutoff_'+str(c if c is not None else 'full'),'cumulative',[] if interval is None else [list(interval)],cutoff=c)
        for k in range(10):
            chosen=coords[k*L//10:(k+1)*L//10]
            add(f'local_{k}','local',ranges(chosen),window=k,normalized_window=[k/10,(k+1)/10],native_exposure=len([t for t in chosen if t>=1]))
        accepted=[e for e in events[task['task_id']] if e['semantic_label']=='accepted']
        rejected=[e['demand_token'] for e in events[task['task_id']] if e['semantic_label']=='rejected']
        centers=[e['demand_token'] for e in accepted]
        for e in accepted:
            dpos=e['demand_token']
            norm=sum(t<dpos for t in coords)/L if L else None
            for radius in [16,32]:
                event,control=demand_control(dpos,radius,span['start'],span['end'],centers,rejected)
                for role,interval in [('demand',event),('control',control)]:
                    add(f"{e['event_id']}_r{radius}_{role}",'demand',[] if interval is None else [list(interval)],
                        event_id=e['event_id'],radius=radius,role=role,demand_token=dpos,normalized_position=norm,
                        paired=event is not None and control is not None,eligible=interval is not None,
                        control_label='shifted_time_without_annotated_demand_or_reviewed_rejection')
        if task['family_id'] in sink_families:
            source=[r for r in local if r['condition_id'] in ['local_0','local_7','cutoff_128']]
            paired=sorted([r for r in local if r['assay']=='demand' and r['role']=='demand' and r['radius']==16 and r['paired']],key=lambda r:(r['demand_token'],r['event_id']))
            if paired:source.append(paired[0])
            for r in source:local.append(dict(r,condition_id='sink_'+r['condition_id'],assay='redistribution',mode='null_sink',standard_condition=r['condition_id']))
        unique={}
        for r in local:
            effective=[(max(1,lo),hi) for lo,hi in r['intervals'] if max(1,lo)<n and (hi is None or hi>max(1,lo))]
            if not r.get('eligible',True):r['execution']='missing_window';r['result_key']=None
            elif not effective:r['execution']='identity_native';r['result_key']=None
            else:
                key=hashlib.sha256(json.dumps([task['task_id'],r['mode'],effective]).encode()).hexdigest()[:24]
                r['result_key']=key;r['execution']='alias' if key in unique else 'run'
                if key not in unique:
                    unique[key]=r
                    fraction=(n-min(lo for lo,hi in effective))/n
                    rollout_estimate+=receipt['runtime']['elapsed_seconds']*fraction
        if unique:
            latest=max(min(lo for lo,hi in r['intervals']) for r in unique.values())
            shared_base_estimate+=receipt['runtime']['elapsed_seconds']*latest/n
        conditions.extend(local);unique_counts.append(len(unique));full_tokens+=n
    inventory=dict(at=now(),frozen=True,selection_uses_scientific_outcomes=False,rows=conditions,
        sink_families=sink_families,accepted_demand_events=sum(e['semantic_label']=='accepted' for e in semantic),
        execution_counts=dict(Counter(r['execution'] for r in conditions)),assay_counts=dict(Counter(r['assay'] for r in conditions)))
    save(ROOT/'audit/tasks.json',dict(rows=output));save(dest,inventory)
    local_readouts=json.loads((OLD/'annotations/causal_selection_frozen.json').read_text())
    save(ROOT/'audit/local_readouts.json',dict(rows=local_readouts['rows'],selection='all50 frozen prior events; prior causal effects unused',source_sha256=sha(OLD/'annotations/causal_selection_frozen.json')))
    save(ROOT/'stage9a_full_access_baselines.json',dict(rows=baseline,gate_pending=True,originals_preserved=True))
    source_paths=[OLD/'audit/native_tasks.json',OLD/'annotations/semantic_review_complete.json',OLD/'annotations/packet_index.json',OLD/'annotations/causal_selection_frozen.json',OLD/'stage9a_accuracy_secondary.json',Path('plan/stage9a_direct_cot_thinking_visual_access_dynamics_plan.md'),Path('plan/stage9a_dynamics_execution_protocol_v1.md')]
    run_cfg=dict(root=str(ROOT),old_root=str(OLD),models=cfg['models'],generation_parameters=cfg['generation_parameters'],max_new_tokens=cfg['max_new_tokens'],allowed_nodes=cfg['allowed_nodes'],max_total_gpus=4,
        manifest_sha256=sha(dest),tasks_sha256=sha(ROOT/'audit/tasks.json'),source_sha256={str(p):sha(p) for p in source_paths})
    save(ROOT/'config.json',run_cfg)
    (ROOT/'stage9a_visual_access_dynamics_spec.md').write_text(Path('plan/stage9a_dynamics_execution_protocol_v1.md').read_text())
    estimate=dict(at=now(),method='Native per-task measured time times remaining-token fraction, plus one shared native prefix per trajectory. Rough estimate before masked-rollout timing; perturbed lengths and longer-context decoding can increase cost.',
        unique_rollouts=sum(unique_counts),native_trajectories=384,native_tokens=full_tokens,
        projected_gpu_hours=(rollout_estimate+shared_base_estimate)/3600,
        projected_days_at_four_gpus=(rollout_estimate+shared_base_estimate)/3600/4/24,
        excludes='readout scoring, annotation, analysis, queue delay, retries; no assumed success or early-stop pruning')
    save(ROOT/'audit/resource_estimate.json',estimate)
    print(json.dumps(dict(counts=inventory['execution_counts'],assays=inventory['assay_counts'],estimate=estimate),indent=2))


if __name__=='__main__':main()
