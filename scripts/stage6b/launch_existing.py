"""Queue bookkeeping and launch in the existing two-GPU tmux shell only."""
import argparse,shlex,subprocess,sys
from scripts.stage6b.common import ROOT,OUT,read_json
sys.path.insert(0,str(ROOT/'infra'))
from harness_state import mutate_gpu_queue,now_iso


def main():
    p=argparse.ArgumentParser();p.add_argument('--runner',choices=['events','dense','dense_v2','memdiagnostic'],required=True)
    p.add_argument('--run-id',required=True);p.add_argument('arguments',nargs=argparse.REMAINDER);a=p.parse_args()
    args=a.arguments[1:] if a.arguments[:1]==['--'] else a.arguments
    assert a.run_id.replace('_','').isalnum() and '--run-id' not in args
    state=subprocess.check_output(['squeue','-h','-j','110860','-o','%T %N %C %b'],text=True).strip()
    assert state=='RUNNING node03 4 gres/gpu:2',state
    pane=subprocess.check_output(['tmux','capture-pane','-p','-t','%20','-S','-2'],text=True).rstrip()
    assert pane.endswith('$'),'Existing allocation shell is busy; do not overlap jobs'
    queue=read_json(ROOT/'state/gpu_experiment_queue.json')
    assert not [j['id'] for j in queue['jobs'] if j['id'].startswith('stage6b_') and j['status']=='running'],'Update completed job status before another launch'
    run='bash scripts/stage6b/run_'+a.runner+'_tmux.sh '+shlex.join(['--run-id',a.run_id]+args)
    jid='stage6b_'+a.run_id;log='runs/stage6b/'+a.run_id+'.log'
    subprocess.run([str(ROOT/'.venv/bin/python'),'infra/gpu_scheduler.py','add','--project','.',
        '--id',jid,'--exp-id',jid,'--gpu-type','a6000','--gpus','2','--node','node03','--mem','90G','--cpus','4',
        '--tmux-session','9','--shell-mode','plain','--command',run,'--log-path',log,'--result-path','outputs/stage6b/raw/'+a.run_id],check=True)
    def update(q):
        j=next(j for j in q['jobs'] if j['id']==jid)
        j.update(status='running',launcher='existing_tmux_allocation',slurm_job_id='110860',started_at=now_iso(),
            notes=['Only existing tmux9/node03 allocation; no srun or sbatch request.'])
    mutate_gpu_queue(ROOT,update)
    subprocess.run(['tmux','send-keys','-t','%20','-l',run+' > '+shlex.quote(log)+' 2>&1'],check=True)
    subprocess.run(['tmux','send-keys','-t','%20','Enter'],check=True)
    print('Started '+a.run_id+' inside Slurm110860 with both existing GPUs.')


if __name__=='__main__':main()
