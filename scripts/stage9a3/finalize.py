"""Close the approved stage at the observed Qwen3 baseline-validity stop."""
import os,subprocess
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scripts.stage9a3.prepare import ROOT,load,save,sha,now


def duration(s):
    days=0
    if '-' in s:day,s=s.split('-');days=int(day)
    h,m,sec=map(int,s.split(':'));return days*86400+h*3600+m*60+sec


def accounting():
    groups={}
    for key in ['qwen25','qwen3']:
        for stage in ['full_primary','grid_primary','full_reserve','grid_reserve','sink_primary']:
            rows=[load(p) for p in (ROOT/key/stage/'results').glob('*/*/result.json')]
            if rows:groups[key+'/'+stage]=dict(n=len(rows),tokens=sum(r['tokens'] for r in rows),
                generation_gpu_hours=sum(r['runtime_seconds'] for r in rows)/3600,capped=sum(r['at_length_cap'] for r in rows),
                peak_reserved_gib=(max(r.get('peak_reserved_bytes',0) for r in rows)/2**30) if any('peak_reserved_bytes' in r for r in rows) else None)
    technical=[load(p) for p in (ROOT/'audit').glob('*preflight*/image*.json')]
    snapshots=sorted([load(p) for p in (ROOT/'audit').glob('resource_snapshot_*.json')],key=lambda x:x['at'])
    fields={}
    for s in snapshots:
        for j in s['jobs']:
            f=j['slurm_fields']
            if f and f.get('JobState') not in ['PENDING','CONFIGURING']:fields[j['queue']['id']]=f
    ends={}
    for p in ROOT.glob('*/*/workers/slurm_*/complete.json'):
        sid=p.parent.name.removeprefix('slurm_');ends[sid]=load(p)['at']
    for p in (ROOT/'audit').glob('*preflight*/failure_*.json'):ends[p.stem.removeprefix('failure_')]=load(p)['at']
    records=[];total=0.;phase_a=0.
    jobs=[j for j in load('state/gpu_experiment_queue.json')['jobs'] if j['id'].startswith('stage9a3_')]
    live=subprocess.check_output(['squeue','-u','hyunjin','-h','-o','%A %T %N'],text=True)
    for j in jobs:
        if not j['gpus']:continue
        assert str(j['slurm_job_id']) not in live,'Stage GPU still allocated or pending'
        f=fields.get(j['id'],{});basis=None;seconds=0.
        if f.get('JobState') in ['COMPLETED','FAILED','CANCELLED'] and f.get('RunTime'):
            seconds=duration(f['RunTime']);basis='captured Slurm allocation runtime'
        elif str(j['slurm_job_id']) in ends:
            seconds=(datetime.fromisoformat(ends[str(j['slurm_job_id'])])-datetime.fromisoformat(j['created_at'])).total_seconds()
            basis='submission-to-final-receipt estimate; includes any queue/start delay, excludes final process teardown'
        else:
            assert j['id']=='stage9a3_qwen25_preflight_v1' and j['status']=='cancelled'
            basis='cancelled while pending, before allocation/inference'
        hours=seconds*j['gpus']/3600;total+=hours
        if 'qwen25' in j['id']:phase_a+=hours
        records.append(dict(id=j['id'],slurm_job_id=j['slurm_job_id'],queue_status=j['status'],command=j['command'],
            requested_node=j['node'],observed_node=f.get('NodeList'),log_path=j['log_path'],result_path=j['result_path'],
            cpus=j['cpus'],host_memory=j['mem'],gpus=j['gpus'],gpu_hours_estimate=hours,basis=basis))
    out=dict(at=now(),scientific_generation=groups,total_scientific_continuations=sum(g['n'] for g in groups.values()),
        scientific_generation_gpu_hours=sum(g['generation_gpu_hours'] for g in groups.values()),
        technical_completed_checks=len(technical),technical_validation_elapsed_gpu_hours=sum(r['elapsed_seconds'] for r in technical)/3600,
        approximate_allocation_gpu_hours=total,approximate_phase_a_gpu_hours=phase_a,phase_a_below_25gpu_hours=phase_a<25,
        max_simultaneous_stage_gpus=4,jobs=records,active_stage_gpu_jobs=[],all_stage_gpus_released=True,
        environment='Project .venv; BF16 weights, eager language, SDPA vision; Torch2.7.1+cu118 / Transformers5.12.1. Per-job environment receipts preserved.',
        accounting_limit='Slurm accounting storage disabled and completed jobs purge quickly. Captured runtimes used where available; other estimates include submission-to-receipt delay. Raw snapshots retained.',
        annotation_burden=dict(full_text_manual_reviews=160,masked_and_sink_manual_exceptions=10,
            automated_literal_extraction='All remaining masked/control outputs use the frozen terminal-option rule; exact FULL aliases reuse sealed reviews.'),
        prior_stage_control_compute_excluded=True,downloads=0)
    save(ROOT/'stage9a3_resource_accounting.json',out);return out


def final_artifacts():
    assert os.environ.get('SLURM_JOB_ID')
    p=load(ROOT/'stage9a3_qwen25_positive_control.json');q=load(ROOT/'stage9a3_qwen3_full_access.json');assert p['pass'] and not q['gates']['pass']
    assert q['counts']['correct']==20 and q['counts']['cot']==56 and q['counts']['valid_option']==46
    sink=load(ROOT/'audit/qwen25_bounded_sink_result.json')
    save(ROOT/'stage9a3_bounded_null_sink_control.json',dict(at=now(),qwen25=sink,qwen3=dict(status='not_run',reason='FULL-access validity gates failed before masked science.'),
        frozen_logical_conditions=['FULL','zero_access','all_layers_token64'],qwen25_control_images=32,
        qwen25_new_continuations=125,full_and_unreached_identity_rows_reused=67,qualitative_pattern_supported=True,
        scope='Three logical conditions on primary32 images only. Standard48-image calibration and32-image controls remain separate.'))
    save(ROOT/'stage9a3_generation_comparison.json',dict(at=now(),status='underidentified',stop_reason='Qwen3 FULL baseline fails accuracy/CoT/extraction gates.',
        qwen25_calibration_pass=True,qwen25_calibration_images=48,comparison_intended_images=32,
        selected_qwen25_condition=dict(fraction=1,token_cutoff=64),qwen3_baseline_accuracy=q['accuracy'],qwen3_cot_rate=q['cot_rate'],
        qwen3_masked_continuations=0,C1_qwen3_finite_preservation=None,C2_gamma=None,C3_surface_shift=None,
        validity_stop_sha256=sha(ROOT/'audit/qwen3_validity_stop.json'),interpretation='No claim about a Qwen model-generation visual-necessity shift, Thinking specialization, or an architectural component.'))
    schema=pa.schema([('query_id',pa.string()),('image_id',pa.string()),('fraction',pa.float64()),('token_cutoff',pa.int64()),
                      ('correct',pa.bool_()),('execution_status',pa.string())],metadata={
        b'execution_status':b'NOT RUN: Qwen3 FULL-access baseline validity failed',
        b'interpretation':b'Empty schema artifact, not a measured zero-effect surface. FULL evidence is in stage9a3_qwen3_full_access.json.'})
    path=ROOT/'stage9a3_qwen3_coarse_grid.parquet';assert not path.exists();pq.write_table(pa.Table.from_batches([],schema=schema),path)
    qwen3_diagnostic()
    return accounting()


def qwen3_diagnostic():
    q=load(ROOT/'stage9a3_qwen3_full_access.json')
    # A baseline diagnostic replaces an unavailable transfer surface; no effect is fabricated.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scripts.stage9a3.figures import export
    fig,ax=plt.subplots(figsize=(7,3.7));values=[q['accuracy']*100,q['cot_rate']*100,q['counts']['valid_option']/64*100]
    labels=['Accuracy','Intermediate reasoning','Valid final option'];thresholds=[60,90,95]
    ax.barh(range(3),values,color=['#b45c53']*3,height=.55)
    for i,(v,t) in enumerate(zip(values,thresholds)):
        ax.text(v-2 if v>80 else v+1,i,f'{v:.1f}%',va='center',ha='right' if v>80 else 'left',color='white' if v>80 else 'black')
        ax.plot([t,t],[i-.3,i+.3],color='black',lw=2)
        ax.text(t,i-.4,f'{t}% gate',ha='center',va='center',fontsize=8)
    ax.set(yticks=range(3),yticklabels=labels,xlim=(0,105),xlabel='Observed percentage',title='Qwen3 FULL baseline failed · transfer grid not run')
    ax.set_ylim(2.5,-.6);fig.tight_layout();export(fig,'figure3_qwen3_validity_stop')


if __name__=='__main__':
    import sys
    if '--figure-only' in sys.argv:qwen3_diagnostic()
    else:
        r=final_artifacts();print('Final stop artifacts and accounting saved; approximate GPU-hours',r['approximate_allocation_gpu_hours'],flush=True)
