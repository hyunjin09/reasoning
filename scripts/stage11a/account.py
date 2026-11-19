"""Account for complete Slurm allocations, including startup and failed attempts."""
from datetime import datetime
from scripts.stage11a.common import ROOT,load,save,now
from scripts.stage9a5.account import seconds

def main():
    terminal={'COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY'};best={}
    for path in sorted((ROOT/'audit').glob('resource_snapshot_*.json')):
        for r in load(path)['jobs']:
            f=r['slurm_fields'];name=r['queue']['id'];old=best.get(name)
            if not f.get('RunTime'):continue
            if old is None or seconds(f['RunTime'])>seconds(old['slurm_fields']['RunTime']) or (seconds(f['RunTime'])==seconds(old['slurm_fields']['RunTime']) and f.get('JobState') in terminal):
                best[name]=dict(r,snapshot=str(path))
    expected={j['id'] for j in load('state/gpu_experiment_queue.json')['jobs'] if j['id'].startswith('stage11a_') and j['gpus']}
    jobs=[];timeline=[];gpu_seconds=0
    for name,r in sorted(best.items()):
        q=r['queue'];f=r['slurm_fields'];g=q['gpus'];secs=seconds(f['RunTime'])
        jobs.append(dict(id=name,slurm_job_id=q['slurm_job_id'],gpus=g,runtime_seconds=secs,state=f['JobState'],exit_code=f.get('ExitCode'),node=f.get('NodeList'),command=q['command'],snapshot=r['snapshot']))
        if g:
            assert f['JobState'] in terminal,(name,f['JobState']);gpu_seconds+=g*secs
            if secs:timeline.extend([(datetime.fromisoformat(f['StartTime']),g),(datetime.fromisoformat(f['EndTime']),-g)])
    assert expected=={j['id'] for j in jobs if j['gpus']}
    current=peak=0
    for _,change in sorted(timeline):current+=change;peak=max(peak,current)
    assert current==0 and peak<=8 and gpu_seconds<2.5*3600
    receipts=[load(p) for p in (ROOT/'probes/results').glob('*/result.json')]
    by_mode={}
    manifest=load(ROOT/'stage11a_probe_manifest.json')['rows']
    for arm in sorted({r['arm'] for r in manifest}):
        rr=[load(ROOT/'probes/results'/r['task_id']/'result.json') for r in manifest if r['arm']==arm]
        by_mode[arm]=dict(runs=len(rr),tokens=sum(r['tokens'] for r in rr),length_cap=sum(r['at_length_cap'] for r in rr),
            normal_eos=sum(r['normal_eos'] for r in rr))
    native=load(ROOT/'audit/native_key.json');suff=load(ROOT/'audit/e_star_gold.json')
    review_counts={}
    for name in ['e_star_a','e_star_b','sufficiency_a','sufficiency_b',
                 'repair_sufficiency_a','repair_sufficiency_b','repair2_sufficiency_a','repair2_sufficiency_b',
                 'native_a','native_b','native_main','native_adjudication','native_quality_audit_singles_a',
                 'probe_a','probe_b','probe_main','localization_a','localization_b']:
        path=ROOT/'annotations'/f'{name}.json'
        if path.exists():
            rr=load(path)['rows'];review_counts[name]=dict(records=len(rr))
            if 'sufficiency' in name:
                review_counts[name]['applicable_sufficiency_records']=sum(r['sufficiency']!='NOT_APPLICABLE' for r in rr)
    save(ROOT/'stage11a_resource_accounting.json',dict(at=now(),jobs=jobs,allocated_gpu_hours=gpu_seconds/3600,
        all_gpu_jobs_terminal=True,peak_gpus=peak,authorized_gpu_ceiling=8,hard_gpu_cap=2.5,
        new_short_probe_runs=len(receipts),probe_tokens=sum(r['tokens'] for r in receipts),probe_generation_seconds=sum(r['seconds'] for r in receipts),
        probe_length_cap_count=sum(r['at_length_cap'] for r in receipts),probe_normal_eos_count=sum(r['normal_eos'] for r in receipts),
        probe_by_mode=by_mode,
        native_traces_reused=len(native['rows']),new_native_baselines=0,
        annotation_burden=dict(construction_item_reviews=256,common_sufficiency_item_reviews=256,
            eligible_items=len(suff['rows']),native_primary_traces=len(native['rows']),
            native_extra_agreement_traces=3*len(native['agreement_item_ids']),probe_traces=len(receipts),review_records_by_artifact=review_counts),
        note='Allocation hours include startup, validation and any failures. Annotation counts are model-agent records/passes, not human hours; NOT_APPLICABLE sufficiency records are distinguished. Raw independent agreement excludes quality-audit rereads and adjudication. CPU final job need not be terminal.'))
    print('ALLOCATED_GPU_HOURS',gpu_seconds/3600)

if __name__=='__main__':main()
