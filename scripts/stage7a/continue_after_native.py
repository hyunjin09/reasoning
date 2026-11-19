"""Advance two already-approved jobs in the existing allocation, never allocate.

This lightweight controller does no model or dataset computation. It stops on
any failed gate. Confirmation scoring and later research decisions remain gated.
"""
import subprocess
import sys
import time
from scripts.stage7a.common import ROOT, OUT, read_json, write_json, sha

sys.path.insert(0, str(ROOT/'infra'))
from harness_state import mutate_gpu_queue, now_iso


def status(stage, **extra):
    record = dict(stage=stage, updated_at=now_iso(), allocation='111485', new_allocation=False, **extra)
    write_json(OUT/'audit/continuation_controller.json', record)
    print(record, flush=True)


def shell_free():
    pane = subprocess.check_output(['tmux', 'capture-pane', '-p', '-t', '%21', '-S', '-1'], text=True).rstrip()
    return pane.endswith('$')


def wait_complete(run_id):
    while True:
        allocation = subprocess.check_output(['squeue', '-h', '-j', '111485', '-o', '%T %N %C %b'], text=True).strip()
        if allocation != 'RUNNING node06 4 gres/gpu:1':
            raise RuntimeError('Existing allocation changed: '+allocation)
        path = OUT/'raw'/run_id/'run_summary.json'
        free = shell_free()
        if path.exists():
            assert read_json(path)['completed'], 'Run did not complete successfully: '+run_id
            if free: return
        elif free:
            raise RuntimeError('Run returned to shell without successful summary: '+run_id)
        time.sleep(15)


def reconcile(run_id):
    assert read_json(OUT/'raw'/run_id/'run_summary.json')['completed'] and shell_free()
    def finish(queue):
        job = next(j for j in queue['jobs'] if j['id'] == 'stage7a_'+run_id)
        assert job['slurm_job_id'] == '111485' and job['status'] == 'running'
        job.update(status='succeeded', finished_at=now_iso(), exit_code=0)
    mutate_gpu_queue(ROOT, finish)


def launch(run_id, manifest, mechanics=False):
    args = [str(ROOT/'.venv/bin/python'), 'scripts/stage7a/launch_existing.py', '--runner', 'events',
            '--run-id', run_id, '--', '--manifest', manifest]
    if mechanics: args.append('--mechanics')
    subprocess.run(args, cwd=ROOT, check=True)
    time.sleep(3)


def main():
    assert sha(OUT/'config/discovery_events.jsonl') == read_json(OUT/'audit/discovery_events.json')['manifest_sha256']
    assert read_json(OUT/'audit/discovery_mechanics_events_v2.json')['status'] == 'FROZEN'
    status('waiting_native', run_id='native_01')
    wait_complete('native_01')
    reconcile('native_01')
    status('launching_fresh_mechanics')
    launch('fresh_mechanics_01', 'outputs/stage7a/config/discovery_mechanics_events_v2.jsonl', mechanics=True)
    status('waiting_fresh_mechanics', run_id='fresh_mechanics_01')
    wait_complete('fresh_mechanics_01')
    assert read_json(OUT/'audit/fresh_causal_mechanics.json')['passed']
    reconcile('fresh_mechanics_01')
    status('launching_discovery_causal')
    launch('discovery_causal_01', 'outputs/stage7a/config/discovery_events.jsonl')
    status('controller_complete_discovery_running', run_id='discovery_causal_01',
           next='Main agent validates completed discovery results, compiles metrics, and freezes discovery thresholds.')


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        status('stopped_on_error', error_type=type(error).__name__, error=str(error))
        raise
