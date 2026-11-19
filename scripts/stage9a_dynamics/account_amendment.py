"""Post-freeze artifact/compute accounting; never evaluates masked answers."""
import json
import math
import subprocess
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from scripts.stage8c.prepare import save,sha
from scripts.stage9a.run_native import now

OLD=Path('outputs/stage9a_dynamics/v1');ROOT=Path('outputs/stage9a_dynamics/amendment_v1')
WORKERS=['121703','121704','121705','121706']


def main():
    freeze=json.loads((ROOT/'audit/freeze_receipt.json').read_text())
    manifest=json.loads((ROOT/'stage9a_amended_condition_manifest.json').read_text())
    assert sha(ROOT/'stage9a_amended_family_selection.json')==freeze['family_selection_sha256']
    assert sha(ROOT/'stage9a_amended_condition_manifest.json')==freeze['manifest_sha256']
    live=set(subprocess.run(['squeue','--me','-h','-o','%i'],text=True,capture_output=True,check=True).stdout.split())
    assert not set(WORKERS).intersection(live),'Wait until all four old workers have stopped safely'
    old_manifest=json.loads((OLD/'audit/interventions.json').read_text())
    receipts=[];allowed=['result_key','task_id','family_id','arm','representative_condition','worker','at','runtime_seconds','generated_suffix_tokens','prefix_tokens','generation_sha256','config_sha256']
    for p in sorted((OLD/'rollouts/results').glob('*/result.json')):
        raw=json.loads(p.read_text());r={k:raw[k] for k in allowed};del raw
        assert sha(p.parent/'generation.json')==r['generation_sha256']
        r.update(receipt=str(p),receipt_sha256=sha(p),generation=str(p.parent/'generation.json'))
        receipts.append(r)
    by_key={r['result_key']:r for r in receipts}
    main_unique={r['result_key']:r for r in manifest['rows'] if r['execution']=='run'}
    control_unique={r['result_key']:r for r in manifest['deferred_control_rows'] if r['execution']=='run'}
    reusable=[by_key[key] for key in sorted(main_unique) if key in by_key]
    deferred_reuse=[by_key[key] for key in sorted(control_unique) if key in by_key]
    primary_keys=set(main_unique);control_keys=set(control_unique)
    for r in receipts:
        key=r['result_key'];r['disposition']='reusable_amended_main' if key in primary_keys else 'deferred_control_only' if key in control_keys else 'pre_amendment_exploratory_archive_only'
    by_worker=defaultdict(list)
    for r in receipts:by_worker[r['worker']].append(r)
    # Restore ordinary progress-log paths after the stopped FIFO boundary. The
    # original inode/log remains archived and no generation/receipt is changed.
    for sid in WORKERS:
        wd=OLD/'rollouts/workers'/('slurm_'+sid);path=wd/'progress.jsonl';archive=wd/'progress_pre_amendment.jsonl'
        old_lines=archive.read_text().splitlines();logged={json.loads(line)['result_key'] for line in old_lines}
        extra=[r for r in sorted(by_worker['slurm_'+sid],key=lambda r:r['at']) if r['result_key'] not in logged]
        tmp=wd/'progress_restored_amendment.tmp'
        with tmp.open('x') as out:
            for line in old_lines:out.write(line+'\n')
            for r in extra:out.write(json.dumps(json.loads(Path(r['receipt']).read_text()))+'\n')
        tmp.replace(path)
    status=dict(at=now(),freeze_at=freeze['at'],old_distinct_continuations=9874,old_condition_rows=len(old_manifest['rows']),
        completed_preserved=len(receipts),unexecuted_unique_cancelled=9874-len(receipts),
        completed_row_classification=dict(Counter(r['disposition'] for r in receipts)),rows=receipts,
        archive_policy='Old namespace remains immutable evidence; only exact matching masks can enter amended primary analysis. Superseded results may only be labeled pre-amendment exploratory.',
        old_workers_stopped=WORKERS,old_coordinator='121713 stopped_by_file',
        outcome_fields_inspected=False,accounting_fields=allowed,
        stop_proofs={sid:json.loads((OLD/'audit/compute_amendment_v1'/f'stopped_{sid}.json').read_text()) for sid in WORKERS})
    save(ROOT/'stage9a_old_manifest_status.json',status)
    tasks=json.loads((ROOT/'audit/tasks.json').read_text())['rows'];by_task={r['task_id']:r for r in tasks}
    all_old_tasks={r['task_id']:r for r in json.loads((OLD/'audit/tasks.json').read_text())['rows']}
    prompt={task:json.loads((Path(r['native_dir'])/'input.json').read_text())['prompt_token_count'] for task,r in all_old_tasks.items()}
    samples=defaultdict(list)
    for i,sid in enumerate(WORKERS):
        node='node07' if i==3 else 'node06';starts={};previous={}
        log=Path(f'runs/stage9a_dynamics/v1/stage9a_dynamics_worker{i}_v1_slurm.log')
        for line in log.read_text().splitlines():
            if not line.startswith('{'):continue
            r=json.loads(line)
            if r.get('event')=='condition_start':
                starts[r['task_id']+':'+r['condition']]=(r['task_id'],r['prefix_tokens'])
            elif r.get('event')=='token_progress' and r['item_id'] in starts:
                label=r['item_id'];task,prefix=starts[label];n=r['forward_tokens'];seconds=r['elapsed_seconds']
                if label in previous:
                    prev_n,prev_seconds=previous[label];width=n-prev_n
                    if width>=512:
                        samples[node].append([prompt[task]+prefix+(prev_n+n)/2,(seconds-prev_seconds)/width,width])
                previous[label]=(n,seconds)
    fits={}
    for node,rows in samples.items():
        x=np.array([r[0] for r in rows]);y=np.array([r[1] for r in rows]);w=np.sqrt(np.array([r[2] for r in rows]))
        coef=np.linalg.lstsq(np.c_[np.ones(len(x)),x]*w[:,None],y*w,rcond=None)[0]
        a=max(.001,float(coef[0]));b=max(0.,float(coef[1]))
        fits[node]=dict(intercept_seconds_per_token=a,context_slope_seconds_per_token_squared=b,
            observed_chunks=len(rows),observed_context_min=float(x.min()),observed_context_max=float(x.max()),
            aggregate_tokens_per_second=sum(r[2] for r in rows)/sum(r[1]*r[2] for r in rows))
    assert set(fits)=={'node06','node07'}
    def seconds(task,begin,end):
        p=prompt[task];return sum(weight*(f['intercept_seconds_per_token']*(end-begin)+f['context_slope_seconds_per_token_squared']*((p+end)**2-(p+begin)**2)/2)
            for node,weight in [('node06',.75),('node07',.25)] for f in [fits[node]])
    pending=[r for key,r in main_unique.items() if key not in by_key];latest=defaultdict(int)
    main_seconds=0.;cap_seconds=0.
    for r in pending:
        task=r['task_id'];begin=min(lo for lo,hi in r['intervals']);n=by_task[task]['native_tokens']
        main_seconds+=seconds(task,begin,n);cap_seconds+=seconds(task,begin,40960);latest[task]=max(latest[task],begin)
    prefix_seconds=sum(seconds(task,0,n) for task,n in latest.items())
    control_seconds=sum(seconds(r['task_id'],0,by_task[r['task_id']]['native_tokens']) for key,r in control_unique.items() if key not in by_key)
    readout_seconds=0.;readouts=json.loads((OLD/'audit/local_readouts.json').read_text())['rows']
    for event in readouts:
        task=event['task_id'];stop=event['readout_start'];conds=[r for r in old_manifest['rows'] if r.get('event_id')==event['event_id'] and r['assay']=='demand']
        early=min([stop]+[max(0,min(lo for lo,hi in r['intervals'])-1) for r in conds if r['intervals']])
        readout_seconds+=seconds(task,0,early)+5*seconds(task,early,stop)+5*seconds(task,stop,stop+len(event['original_token_ids'])+len(event['counterfactual_token_ids']))
    total=(main_seconds+prefix_seconds+control_seconds+readout_seconds)/3600
    estimate=dict(at=now(),after_manifest_freeze=True,main_unique=len(main_unique),main_reused=len(reusable),main_unfinished=len(pending),
        deferred_control_unique=len(control_unique),deferred_control_reused=len(deferred_reuse),
        distinct_free_rollouts_total=len(main_unique)+len(control_unique),local_readout_events=50,
        observed_throughput_fits=fits,assumed_resource_mix='Three node06 and one node07 A6000, maximum4 GPUs; revise if the eventual mix differs.',
        model='Fit seconds/token against context from token-progress timing only; integrate over frozen native suffix lengths. Add shared native prefix, bounded87 null-sink controls and unchanged50 local readouts. No masked answer/correctness/effect/divergence values used.',
        main_remaining_suffix_gpu_hours=main_seconds/3600,shared_prefix_gpu_hours=prefix_seconds/3600,
        deferred_controls_gpu_hours=control_seconds/3600,local_readouts_gpu_hours=readout_seconds/3600,
        estimated_total_remaining_gpu_hours=total,planning_range_gpu_hours=[.7*total,1.5*total],
        days_at_four_gpus=total/96,main_suffix_all_cap_scenario_gpu_hours=cap_seconds/3600,
        uncertainty='Planning range, not a statistical confidence interval. Masked length changes, long-context extrapolation, prefill/CPU overhead, queue delays and review can increase elapsed time.',
        completed_old_measured_suffix_gpu_hours=sum(r['runtime_seconds'] for r in receipts)/3600)
    save(ROOT/'stage9a_amended_resource_estimate.json',estimate)
    save(ROOT/'audit/reused_results.json',dict(rows=reusable,deferred=deferred_reuse))
    for r in reusable:
        dest=ROOT/'rollouts/results'/r['result_key'];dest.parent.mkdir(parents=True,exist_ok=True)
        dest.symlink_to(Path(r['receipt']).parent.resolve(),target_is_directory=True)
    print(json.dumps(dict(preserved=len(receipts),reuse=len(reusable),reuse_conditions=[dict(task_id=r['task_id'],condition=r['representative_condition']['condition_id'],result_key=r['result_key']) for r in reusable],estimate=estimate),indent=2))


if __name__=='__main__':main()
