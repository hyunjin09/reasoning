"""Verify a frozen causal pilot, register work and use the existing tmux shell.

Never submit a new Slurm allocation or overlap the native sequence. Registration
uses the machine-local scheduler; the allocation must already be running.
"""
import argparse
import re
import shlex
import subprocess
import sys

from transformers import AutoTokenizer

from scripts.stage7a.common import ROOT, read_json, sha
from scripts.stage7a_bench.pilot_freeze_v11 import load_frozen_pilot, dependency_hashes
from scripts.stage7a_bench.causal_run_v11 import validate_mechanics
from scripts.stage7a_bench.prior_controls_v11 import requested_native_banks

OUT = ROOT / 'outputs/stage7a_bench_v2'
sys.path.insert(0, str(ROOT / 'infra'))
from harness_state import mutate_gpu_queue, now_iso


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--pilot', required=True)
    parser.add_argument('--pilot-sha256', required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--mechanics', action='store_true')
    mode.add_argument('--native-controls', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch('[a-z0-9_]+', args.run_id):
        raise ValueError('Unsafe run identity')
    if ((OUT / 'causal_pilot/raw' / args.run_id).exists() or
            (OUT / 'causal_pilot/native_controls' / args.run_id).exists() or
            (OUT / 'causal_pilot/wrappers' / (args.run_id+'.json')).exists()):
        raise FileExistsError('Existing causal run cannot be retried or overwritten automatically')
    config = read_json(OUT / 'config/runtime_node02_v3.json')
    allocation = config['runtime']
    if allocation['gpus'] != 4 or config['new_allocations_permitted'] is not False:
        raise ValueError('This launcher requires the existing four-GPU allocation')
    tokenizer = AutoTokenizer.from_pretrained(config['model_checkpoint'], local_files_only=True)
    pilot_ref = dict(path=args.pilot, sha256=args.pilot_sha256)
    pilot = load_frozen_pilot(pilot_ref, tokenizer)
    if args.native_controls and not requested_native_banks(pilot['selected_entries']):
        raise ValueError('Frozen pilot has no requested reviewed fresh-native control banks')
    certificate_path = OUT / 'causal_pilot/mechanics' / (pilot['benchmark']+'.json')
    if args.mechanics:
        if certificate_path.exists():
            raise FileExistsError('Existing mechanics certificate cannot be replaced')
    else:
        validate_mechanics(read_json(certificate_path), dict(pilot=pilot_ref,
            dependencies=dependency_hashes(), runtime_sha256=sha(OUT / 'config/runtime_node02_v3.json')),
            pilot['selected_entries'])
    status = subprocess.check_output(['squeue','-h','-j',allocation['slurm_allocation'],
                                     '-o','%T %N %C %b'], text=True).strip()
    expected = f"RUNNING {allocation['node']} {allocation['cpus']} gres/gpu:4"
    if status != expected:
        raise RuntimeError('Existing allocation unavailable or changed: '+status)
    # Read only current pane metadata; never inspect shell or tmux history.
    current_command = subprocess.check_output(['tmux','display-message','-p',
        '-t',allocation['tmux_pane'],'#{pane_current_command}'], text=True).strip()
    steps = subprocess.check_output(['squeue','--steps','-h','-j',
        allocation['slurm_allocation'],'-o','%i %j %N'], text=True)
    expected_shell = [[allocation['slurm_allocation']+'.0', 'bash', allocation['node']]]
    if (current_command not in ('bash', 'srun') or
            [line.split() for line in steps.splitlines() if line.strip()] != expected_shell):
        raise RuntimeError('Allocation shell is busy or changed; overlapping workloads are forbidden')
    queue = read_json(ROOT / 'state/gpu_experiment_queue.json')
    if any(j['id'].startswith('stage7a_') and j['status']=='running' for j in queue['jobs']):
        raise RuntimeError('A Stage7A job is still running; reconcile it before launching')
    arguments = ['--run-id',args.run_id,'--pilot',args.pilot,'--pilot-sha256',args.pilot_sha256]
    if args.mechanics:
        arguments.append('--mechanics')
    if args.native_controls:
        arguments.append('--native-controls')
    command = 'bash scripts/stage7a_bench/run_causal_v11_tmux.sh '+shlex.join(arguments)
    job_id = 'stage7a_bench_v2_causal_'+args.run_id
    log = 'runs/stage7a_bench/'+args.run_id+'.log'
    subprocess.run([str(ROOT / '.venv/bin/python'),'infra/gpu_scheduler.py','add','--project','.',
        '--id',job_id,'--exp-id',job_id,'--gpu-type','a6000','--gpus','1',
        '--node',allocation['node'],'--mem','30G','--cpus','8',
        '--tmux-session',allocation['tmux_session'],'--shell-mode','plain',
        '--command',command,'--log-path',log,
        '--result-path','outputs/stage7a_bench_v2/causal_pilot/'+
            ('native_controls/' if args.native_controls else 'raw/')+args.run_id], check=True)
    def register(current):
        job = next(j for j in current['jobs'] if j['id']==job_id)
        job.update(status='running',launcher='existing_tmux_allocation',
            slurm_job_id=allocation['slurm_allocation'],started_at=now_iso(),
            notes=['Frozen benchmark causal pilot; one Slurm-bound GPU within authorized113280; no new allocation.'])
    mutate_gpu_queue(ROOT, register)
    subprocess.run(['tmux','send-keys','-t',allocation['tmux_pane'],'-l',
                    command+' > '+shlex.quote(log)+' 2>&1'], check=True)
    subprocess.run(['tmux','send-keys','-t',allocation['tmux_pane'],'Enter'], check=True)
    print('Started '+job_id+' in existing Slurm '+allocation['slurm_allocation'])


if __name__ == '__main__':
    main()
