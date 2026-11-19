"""Register work, then use the already allocated tmux shell. Never allocate."""
import argparse
import shlex
import subprocess
import sys
from scripts.stage7a.common import ROOT, OUT, read_json

sys.path.insert(0, str(ROOT / 'infra'))
from harness_state import mutate_gpu_queue, now_iso


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--runner', choices=['mechanics', 'generation', 'events', 'passive', 'probes', 'prepare_objects', 'prepare_cohort', 'utilization'], required=True)
    p.add_argument('--run-id', required=True)
    p.add_argument('arguments', nargs=argparse.REMAINDER)
    args = p.parse_args()
    extra = args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments
    if not args.run_id.replace('_', '').isalnum() or '--run-id' in extra:
        raise ValueError('Invalid run id or duplicate argument')
    config = read_json(OUT / 'config/stage7a_config.json')
    allocation = config['runtime']
    status = subprocess.check_output(['squeue', '-h', '-j', allocation['slurm_allocation'],
                                     '-o', '%T %N %C %b'], text=True).strip()
    if status != 'RUNNING node06 4 gres/gpu:1':
        raise RuntimeError('Existing allocation is unavailable or changed: ' + status)
    pane = subprocess.check_output(['tmux', 'capture-pane', '-p', '-t', allocation['tmux_pane'],
                                    '-S', '-1'], text=True).rstrip()
    if not pane.endswith('$'):
        raise RuntimeError('Allocation shell is busy; no overlapping workload permitted')
    queue = read_json(ROOT / 'state/gpu_experiment_queue.json')
    if any(j['id'].startswith('stage7a_') and j['status'] == 'running' for j in queue['jobs']):
        raise RuntimeError('Reconcile the previous Stage7A job before launching')
    command = 'bash scripts/stage7a/run_tmux.sh ' + shlex.join([
        args.runner, '--run-id', args.run_id] + extra)
    job_id = 'stage7a_' + args.run_id
    log = 'runs/stage7a/' + args.run_id + '.log'
    (ROOT / 'runs/stage7a').mkdir(parents=True, exist_ok=True)
    subprocess.run([str(ROOT / '.venv/bin/python'), 'infra/gpu_scheduler.py', 'add', '--project', '.',
                    '--id', job_id, '--exp-id', job_id, '--gpu-type', 'a6000', '--gpus', '1',
                    '--node', allocation['node'], '--mem', '14G', '--cpus', '4',
                    '--tmux-session', allocation['tmux_session'], '--shell-mode', 'plain',
                    '--command', command, '--log-path', log,
                    '--result-path', 'outputs/stage7a/raw/' + args.run_id], check=True)

    def update(q):
        job = next(j for j in q['jobs'] if j['id'] == job_id)
        job.update(status='running', launcher='existing_tmux_allocation',
                   slurm_job_id=allocation['slurm_allocation'], started_at=now_iso(),
                   notes=['Existing one-GPU tmux10/node06 allocation only; no new Slurm request.'])

    mutate_gpu_queue(ROOT, update)
    subprocess.run(['tmux', 'send-keys', '-t', allocation['tmux_pane'], '-l',
                    command + ' > ' + shlex.quote(log) + ' 2>&1'], check=True)
    subprocess.run(['tmux', 'send-keys', '-t', allocation['tmux_pane'], 'Enter'], check=True)
    print('Started ' + job_id + ' in existing Slurm ' + allocation['slurm_allocation'])


if __name__ == '__main__':
    main()
