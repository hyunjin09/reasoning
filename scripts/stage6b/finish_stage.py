"""Finish the prescribed CPU analyses after both existing GPU workers complete."""
from datetime import datetime, timezone
import os
import subprocess
import time

from scripts.stage6b.common import ROOT, OUT, read_json, write_json


def main():
    env = dict(os.environ, PYTHONPATH='code:.', OPENBLAS_NUM_THREADS='1',
               OMP_NUM_THREADS='1', MPLCONFIGDIR=str(OUT/'analysis/matplotlib_cache'))
    python = str(ROOT/'.venv/bin/python')
    status_path = OUT/'audit/completion_pipeline.json'
    status = {'status': 'WAITING_FOR_NATIVE', 'completed_steps': [],
              'new_allocation_requested': False}

    def record():
        status['updated_at'] = datetime.now(timezone.utc).isoformat()
        write_json(status_path, status)

    def run(name, command):
        status.update(status='RUNNING', current_step=name)
        record()
        log = ROOT/'runs/stage6b'/f'completion_{name}.log'
        with log.open('w') as stream:
            subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                           stderr=subprocess.STDOUT, check=True)
        status['completed_steps'].append(name)
        record()
        print(name, 'complete', flush=True)

    record()
    try:
        deadline = time.monotonic() + 18*3600
        while True:
            paths = [OUT/'raw/native_primary_02'/f'shard_{rank:02d}/run_summary.json'
                     for rank in range(2)]
            if all(p.exists() and read_json(p)['completed'] for p in paths):
                break
            pane_command = subprocess.check_output(
                ['tmux', 'display-message', '-p', '-t', '%20', '#{pane_current_command}'],
                text=True).strip()
            if pane_command == 'bash':
                raise RuntimeError('Native worker returned to shell before both completion records existed')
            if time.monotonic() >= deadline:
                raise TimeoutError('Native completion still pending after 18 hours')
            time.sleep(30)
        run('queue', [python, 'infra/gpu_scheduler.py', 'update', '--project', '.',
            '--id', 'stage6b_native_primary_02', '--status', 'succeeded', '--note',
            'Both native shards completed; full endpoint replay and analysis audits follow.'])
        for name, script, extra in [
            ('trajectory', 'analyze_trajectory.py', []),
            ('sink', 'analyze_sink.py', []),
            ('geometry_figures', 'figures_native_validation.py', ['geometry']),
            ('audit', 'audit_completion.py', []),
            ('synthesis', 'write_synthesis.py', []),
        ]:
            run(name, [python, 'scripts/stage6b/'+script, *extra])
        status.update(status='COMPLETE_PENDING_HUMAN_READABLE_REPORT_REVIEW', current_step=None)
        record()
    except Exception as error:
        status.update(status='FAILED', error=repr(error))
        record()
        raise


if __name__ == '__main__':
    main()
