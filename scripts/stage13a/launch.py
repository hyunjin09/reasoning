import argparse,os,shlex,subprocess
from pathlib import Path
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage13a.execution import ROOT,PREFIX,ALLOWED_NODES,load,save,sha,now,authorize
from scripts.stage13a.resources import account

def main(phase,manifests,minutes):
    assert phase in ['P','S'] and 5<=minutes<=120 and 1<=len(manifests)<=8
    for p in manifests:
        m=load(p);assert m['phase']==phase;authorize(m)
    ledger=account('prelaunch_'+phase)
    upper=ledger['committed_gpu_hours_upper']+len(manifests)*minutes/60
    assert upper<=14,upper
    args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
    project=Path.cwd();status=scheduler.gpu_status(args,scheduler.load_gpu_queue(project))
    assert not status['warnings'] and status['own_gpus']+len(manifests)<=8
    save(ROOT/'audit'/f'phase{phase}_launch_envelope.json',dict(at=now(),upper_gpu_hours=upper,minutes=minutes,manifests=manifests,status=status))
    index=Path('reports/index.md');saved_index=index.read_text()
    ids=set()
    for i,p in enumerate(manifests):
        ident=PREFIX+phase+f'_{i}';ids.add(ident)
        command=shlex.join(['bash','scripts/stage13a/run.sh','scripts/stage13a/worker.py',p,'--manifest-sha256',sha(p)])
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
            '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1','--mem','28G','--cpus','4',
            '--allow-slurm-pending','--exclude-node','node01','--exclude-node','node04','--exclude-node','node05',
            '--command',command,'--log-path',f'runs/stage13a/v1/{phase}_{i}/slurm.log','--result-path',str(ROOT)],check=True)
    jobs=[j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] in ids]
    assert all(j['status']=='queued' for j in jobs)
    os.environ['SBATCH_TIMELIMIT']=f'{minutes//60:02d}:{minutes%60:02d}:00'
    planned=scheduler.plan_jobs({'jobs':jobs},status);assert len(planned)==len(jobs)
    for j in planned:
        assert not j['node'] or j['node'] in ALLOWED_NODES
        scheduler.execute_launch(project,j)
        registered=next(x for x in scheduler.load_gpu_queue(project)['jobs'] if x['id']==j['id'])
        save(ROOT/'audit/launches'/f"{registered['slurm_job_id']}.json",dict(at=now(),jobs=[dict(registered,phase=phase,minutes=minutes,registered_at=now())]))
    jobs=[dict(j,phase=phase,minutes=minutes,registered_at=now()) for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] in ids]
    save(ROOT/'audit'/f'phase{phase}_launch_receipt.json',dict(at=now(),jobs=jobs))
    index.write_text(saved_index)
    print([(j['id'],j['slurm_job_id']) for j in jobs]);account('immediate_'+phase)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase');p.add_argument('manifests',nargs='+');p.add_argument('--minutes',type=int,required=True)
    a=p.parse_args();main(a.phase,a.manifests,a.minutes)
