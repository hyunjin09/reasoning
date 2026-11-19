"""Resume only immutable primary tasks interrupted by the recorded Slurm timeout."""
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import gpu_scheduler as scheduler
from scripts.stage13a.execution import ROOT, authorize, load, now, save, sha
from scripts.stage13a.resources import account


def main():
    ledger = account('recovery_prelaunch')
    assert not ledger['active_jobs']
    old = next(j for j in ledger['jobs'] if j['slurm_job_id'] == '133782')
    assert old['closed'] and old['state'] == 'TIMEOUT'
    tasks = load(ROOT / 'audit/phaseP_execution.json')['tasks']
    pending = [t for t in tasks if not (ROOT / 'generations' / t['task_id'] / 'result.json').exists()]
    approved = load(ROOT / 'audit/timeout_recovery_decision.json')
    assert [t['task_id'] for t in pending] == approved['unfinished_tasks']
    assert len(pending) == 13 and {t['model_key'] for t in pending} == {'T'}
    assert ledger['allocated_gpu_hours_upper'] + 1.25 + 2 <= 14
    project = Path.cwd()
    args = SimpleNamespace(max_user_gpus=8, squeue_output=None, all_squeue_output=None,
                           scontrol_output=None, available_gpus=None)
    status = scheduler.gpu_status(args, scheduler.load_gpu_queue(project))
    assert not status['warnings'] and status['own_gpus'] < 8
    save(ROOT / 'audit/recovery_capacity.json', status)
    completed = {str(p): sha(p) for p in (ROOT / 'generations').glob('*/*') if p.is_file()
                 and (p.parent / 'result.json').exists()}
    archived = []
    for task in pending:
        folder = ROOT / 'generations' / task['task_id']
        assert sorted(p.name for p in folder.iterdir()) == ['input.json']
        hashes = {p.name: sha(p) for p in folder.iterdir()}
        dest = ROOT / 'audit/interrupted_attempts/133782' / task['task_id']
        assert not dest.exists()
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(folder), str(dest))
        assert all(sha(dest / n) == h for n, h in hashes.items())
        archived.append(dict(task_id=task['task_id'],archive=str(dest),files=hashes))
    save(ROOT / 'audit/recovery_preservation.json', dict(at=now(), completed_files=completed,
         archived=archived, raw_generation_available=False,
         note='Interrupted requests had input receipts only; no finished generation was overwritten.'))
    manifest = ROOT / 'audit/manifests/P_T_recovery1.json'
    save(manifest, dict(at=now(), phase='P', model_key='T', config_sha256=sha(ROOT/'config.json'), rows=pending))
    authorize(load(manifest))
    ident = 'vr_stage13a_v1_P_recovery1'
    command = shlex.join(['bash','scripts/stage13a/run.sh','scripts/stage13a/worker.py',
                         str(manifest),'--manifest-sha256',sha(manifest)])
    index = Path('reports/index.md'); original_index = index.read_text()
    try:
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','update','--project','.',
                        '--id','vr_stage13a_v1_P_5','--status','failed',
                        '--note','Slurm TIMEOUT:59/72 preserved;13 unfinished frozen tasks in explicit recovery.'],check=True)
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
                        '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1',
                        '--mem','28G','--cpus','2','--allow-slurm-pending',
                        '--exclude-node','node01','--exclude-node','node04','--exclude-node','node05',
                        '--command',command,'--log-path','runs/stage13a/v1/P_recovery1/slurm.log',
                        '--result-path',str(ROOT)],check=True)
        jobs = [j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id']==ident]
        assert len(jobs)==1 and jobs[0]['status']=='queued'
        os.environ['SBATCH_TIMELIMIT']='01:15:00'
        planned=scheduler.plan_jobs({'jobs':jobs},status);assert len(planned)==1
        scheduler.execute_launch(project,planned[0])
        job=next(j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id']==ident)
        save(ROOT/'audit/launches'/f"{job['slurm_job_id']}.json",dict(at=now(),jobs=[dict(job,
             phase='P',minutes=75,registered_at=now(),recovery_of='133782')]))
        save(ROOT/'audit/recovery_launch_receipt.json',dict(at=now(),job=job,manifest_sha256=sha(manifest),
             scientific_change=False,logical_calls_repeated=13,completed_rows_recomputed=0))
    finally:
        index.write_text(original_index)
    assert all(sha(p)==h for p,h in completed.items())
    print('RECOVERY',job['slurm_job_id'],len(pending));account('recovery_submitted')


if __name__=='__main__':
    main()
