"""Only the approved technical release, with two one-hour scheduler jobs."""
import json
import shlex
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from scripts.stage14d.prepare_technical_v1 import ROOT,save,sha
sys.path.insert(0,str(Path('infra').resolve()))
import gpu_scheduler as scheduler


def run():
    approval=json.loads((ROOT/'spec/technical_release_approved_v1.json').read_text())
    assert approval['technical_calibration'] and approval['max_allocated_gpu_hours']==2
    assert not approval['main_scientific_execution']
    assert not list((ROOT/'audit/technical_launches_v1').glob('job_*.json')),'Already submitted; never silently resubmit'
    seal=json.loads((ROOT/'audit/technical_execution_seal_v1.json').read_text())
    for p,h in seal['files'].items():assert sha(p)==h,p
    project=Path.cwd()
    status_args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
    index=Path('reports/index.md');original_index=index.read_text()
    try:
        for model in 'IT':
            status=scheduler.gpu_status(status_args,scheduler.load_gpu_queue(project))
            assert not status['warnings'] and status['remaining_user_slots']>=1,status
            assert status['available_gpus']['a6000']>=1,'No compatible free GPU; no unrequested pending job'
            ident='stage14d_technical_v1_'+model
            cmd=shlex.join(['bash','scripts/stage14d/run_technical_v1.sh',model])
            subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
                '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1','--mem','28G','--cpus','4',
                '--exclude-node','node01','--exclude-node','node04','--exclude-node','node05',
                '--command',cmd,'--log-path',f'runs/stage14d/technical_v1_{model}/slurm.log',
                '--result-path',str(ROOT/'audit/technical_workers_v1')],check=True)
            selected=[j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id']==ident]
            planned=scheduler.plan_jobs({'jobs':selected},status);assert len(planned)==1
            job=planned[0];assert job['node'] in {'node02','node03','node06','node07'}
            sbatch=scheduler.sbatch_args(project,job);sbatch.insert(1,'--time=01:00:00')
            # Persist authorization before releasing the allocation from Slurm hold.
            sbatch.insert(1,'--hold')
            Path(job['log_path']).parent.mkdir(parents=True,exist_ok=True)
            reply=subprocess.run(sbatch,text=True,capture_output=True,check=True)
            jid=reply.stdout.strip().split(';')[0]
            scheduler.mark_launched(project,job,jid)
            save(ROOT/'audit/technical_launches_v1'/f'job_{jid}.json',dict(job_id=jid,model=model,job=job,
                 reserved_GPUh=1,total_release_GPUh=2,exact_sbatch_args=sbatch,
                 command=cmd,execution_seal_sha256=sha(ROOT/'audit/technical_execution_seal_v1.json')))
            subprocess.run(['scontrol','release',jid],check=True)
            print('SUBMITTED',model,jid,job['node'],flush=True)
    finally:index.write_text(original_index)


if __name__=='__main__':run()
