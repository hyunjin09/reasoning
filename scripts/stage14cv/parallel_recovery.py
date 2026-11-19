"""One bounded handoff to disjoint frozen-wave queues, using sealed v2 inference."""
import shlex
import subprocess
import sys
from types import SimpleNamespace
from scripts.stage14cv.common import *
from scripts.stage14cv.launch import accounting
from scripts.stage14cv.operational_v2 import authorize_v2, completed_receipt, check_amended_budget
sys.path.insert(0,str(Path('infra').resolve()))
import gpu_scheduler as scheduler


def validate_shards(original,shards):
    ids=[r['task_id'] for r in original]
    flat=[r for s in shards for r in s]
    actual=[r['task_id'] for r in flat]
    if not shards or any(not s for s in shards) or len(set(ids))!=len(ids):
        raise ValueError('Invalid original/empty queue')
    if len(set(actual))!=len(actual) or set(actual)!=set(ids):
        raise ValueError('Duplicate or omitted task')
    for wave in {r['wave'] for r in original}:
        expected=[r for r in original if r['wave']==wave]
        pieces=[[r for r in s if r['wave']==wave] for s in shards]
        occupied=[p for p in pieces if p]
        if len(occupied)!=1 or occupied[0]!=expected:
            raise ValueError('Frozen wave membership/order changed')


def split_waves(rows,workers):
    groups={}
    for row in rows:groups.setdefault(row['wave'],[]).append(row)
    if not 1<=workers<=len(groups):raise ValueError('Invalid worker count')
    shards=[[] for _ in range(workers)]
    for group in groups.values():shards[min(range(workers),key=lambda i:(len(shards[i]),i))].extend(group)
    validate_shards(rows,shards)
    return shards


def live_R2_ids():
    live=set(subprocess.run(['squeue','-u','hyunjin','-h','-o','%i'],check=True,text=True,capture_output=True).stdout.split())
    claimed=set()
    for p in (ROOT/'audit/launches').glob('job_*.json'):
        r=load(p)
        if str(r['job']['slurm_job_id']) not in live or (r.get('panel'),r.get('model'),r.get('condition'))!=('R','T','R2'):continue
        args=shlex.split(r['job']['command'])
        marker=next((v for v in ['scripts.stage14cv.runner_v2','scripts.stage14cv.runner'] if v in args),None)
        assert marker,'Unknown active R2 command; cannot prove disjointness'
        m=load(args[args.index(marker)+1]);claimed.update(t['task_id'] for t in m['rows'])
    return claimed


def launch_shard(selected,rank,hours):
    assert not (ROOT/'audit/STOP_BETWEEN_WAVES').exists()
    assert not ({t['task_id'] for t in selected}&live_R2_ids()),'Overlapping live task ownership'
    assert all(not list((ROOT/'raw'/t['collection']/t['task_id']).glob('attempt_*')) for t in selected)
    charges=accounting();total=check_amended_budget([c['charge_GPUh'] for c in charges],[hours])
    m=dict(at=now(),panel='R',model_key='T',rows=selected,requested_hours=hours,
           context_ids=[],operational_version=2,parallel_recovery_rank=rank)
    authorize_v2(m)
    project=Path.cwd();args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
    status=scheduler.gpu_status(args,scheduler.load_gpu_queue(project))
    assert not status['warnings'] and status['remaining_user_slots']>=1,status
    stem=f'R_T_R2_parallel_v1_rank{rank}';mp=ROOT/'audit/shards'/f'{stem}.json';save(mp,m)
    ident=PREFIX+stem
    command=shlex.join(['bash','scripts/stage14cv/run.sh','-m','scripts.stage14cv.runner_v2',str(mp),'--manifest-sha256',sha(mp)])
    index=Path('reports/index.md');old=index.read_text()
    try:
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
            '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1','--mem','28G','--cpus','4',
            '--allow-slurm-pending','--exclude-node','node01','--exclude-node','node04','--exclude-node','node05',
            '--command',command,'--log-path',f'runs/stage14cv/{stem}/slurm.log','--result-path',str(ROOT)],check=True)
        registered=[j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id']==ident]
        planned=scheduler.plan_jobs({'jobs':registered},status);assert len(planned)==1
        job=planned[0];assert job['node'] in ALLOWED_NODES or not job['node']
        sbatch=scheduler.sbatch_args(project,job);sbatch.insert(1,'--time=01:30:00')
        assert hours==1.5
        Path(job['log_path']).parent.mkdir(parents=True,exist_ok=True)
        out=subprocess.run(sbatch,check=True,text=True,capture_output=True);jid=out.stdout.strip().split(';')[0]
        scheduler.mark_launched(project,job,jid)
        job=next(j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id']==ident)
        save(ROOT/'audit/launches'/f'job_{jid}.json',dict(at=now(),job=job,panel='R',model='T',condition='R2',
            hours=hours,exact_sbatch_args=sbatch,prior_charges=charges,reserved_total_GPUh=total,
            approved_ceiling_GPUh=32,parallel_rank=rank,manifest=str(mp)))
        subprocess.run(['.venv/bin/python','-m','scripts.stage14cv.submit_cpu','account_'+jid,
            ".venv/bin/python -c 'from scripts.stage14cv.launch import accounting; print(accounting())'",
            '--dependency','afterany:'+jid],check=True)
        print('PARALLEL_SUBMITTED',jid,'rank',rank,'calls',len(selected),flush=True)
        return jid
    finally:index.write_text(old)


def main():
    for p,h in load(ROOT/'audit/parallel_recovery_adapter_seal_v1.json')['files'].items():assert sha(p)==h,p
    a=load(ROOT/'audit/parallel_recovery_amendment_v1.json');assert a['old_job']=='140116'
    assert sha(a['old_manifest'])==a['old_manifest_sha256']
    charges=accounting();old=next(c for c in charges if str(c['job_id'])==a['old_job'])
    assert old['state']=='COMPLETED',old
    exit_receipt=load(ROOT/'audit/workers'/a['old_job']/'exit.json');assert exit_receipt.get('checkpoint')
    original=load(a['old_manifest']);by={t['task_id']:t for t in original['rows']}
    future=[by[tid] for tid in a['future_task_ids']]
    for t in original['rows']:
        if t['task_id'] in a['future_task_ids']:
            assert not list((ROOT/'raw'/t['collection']/t['task_id']).glob('attempt_*'))
        else:assert completed_receipt(t,original),t['task_id']
    shards=split_waves(future,a['concurrent_workers']);assert [len(s) for s in shards]==[30,18]
    total=check_amended_budget([c['charge_GPUh'] for c in charges],[1.5,1.5])
    save(ROOT/'audit/parallel_recovery_checkpoint_v1.json',dict(at=now(),status='PASS',old=old,
        shards=[[t['task_id'] for t in s] for s in shards],new_GPUh_reserved=3,
        conservative_total_GPUh=total,remaining_GPUh_for_C=32-total,
        planned_C_envelopes_GPUh=4,
        resource_rule='Every later C launch still requires actual cached allocation charge plus live reservations <=32GPUh.',
        worker_unchanged=True,extra_model_calls=0,scientific_outcomes_used=False))
    sentinel=ROOT/'audit/STOP_BETWEEN_WAVES'
    assert sentinel.exists()
    sentinel.rename(ROOT/'audit/STOP_BETWEEN_WAVES_parallel_applied_v1.txt')
    jobs=[launch_shard(s,i,1.5) for i,s in enumerate(shards)]
    subprocess.run(['.venv/bin/python','-m','scripts.stage14cv.submit_cpu','R_parallel_response_packet',
        '.venv/bin/python -m scripts.stage14cv.r_prepare','--dependency','afterok:'+':'.join(jobs)],check=True)
    save(ROOT/'audit/parallel_recovery_release_v1.json',dict(at=now(),job_ids=jobs,shard_counts=[30,18],
        calls_added=0,C_launched=False,follow_on_launched=False))


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        save(ROOT/'audit/parallel_recovery_hold_v1.json',dict(at=now(),error=repr(exc),action='HOLD_REVIEW_NO_AUTORETRY'))
        raise
