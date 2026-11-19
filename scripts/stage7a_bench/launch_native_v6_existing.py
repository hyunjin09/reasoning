"""Validate and register a retained dispatch inside the existing allocation.

This launcher never allocates, resumes a run or selects a benchmark. The frozen
selection must already pass the semantic gate and ordered-review prerequisites.
"""
import argparse
from copy import deepcopy
import re
import shlex
import subprocess
import sys

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.reduced_native_selection_v6 import select_retained_rows

OUT = ROOT / 'outputs/stage7a_bench_v2'


def validate_execution(path):
    path = (ROOT / path).resolve()
    if not path.is_relative_to(OUT / 'config'):
        raise ValueError('Execution plan outside active config directory')
    plan = read_json(path)
    config = read_json(OUT / 'config/runtime_node02_v3.json')
    allocation = config['runtime']
    authorized = read_json(OUT / 'config/native_parallel_execution_v5.json')['assigned_gpu_uuids']
    if (plan.get('status') != 'FROZEN_RETAINED_NATIVE_EXECUTION' or
            not re.fullmatch('[a-z0-9_]+', plan.get('pool_id', '')) or
            plan.get('allocation') != allocation or allocation['gpus'] != 4 or
            allocation['cpus'] != 32 or allocation['host_memory'] != '120G' or
            config.get('new_allocations_permitted') is not False or
            plan.get('new_allocation') is not False or plan.get('workers') != 4 or
            plan.get('gpus_per_worker') != 1 or
            sorted(plan.get('assigned_gpu_uuids', [])) != sorted(authorized) or
            len(set(authorized)) != 4 or plan.get('launcher_sha256') != sha(__file__)):
        raise ValueError('Changed retained execution, launcher or authorized allocation')
    reference = plan['selection']
    selection_path = (ROOT / reference['path']).resolve()
    if not selection_path.is_relative_to(OUT / 'config') or sha(selection_path) != reference['sha256']:
        raise ValueError('Frozen selection changed or is outside active config')
    selection = read_json(selection_path)
    selected = {b['run_id']: b for b in selection['batches']}
    batches = plan['batches']
    if (len(selected) != len(selection['batches']) or len(batches) != len(selected) or
            {b['run_id'] for b in batches} != set(selected)):
        raise ValueError('Execution must cover every selected batch exactly once')
    manifests, by_event = {}, {}
    for name, digest in selection['manifests'].items():
        manifest = (ROOT / name).resolve()
        if not manifest.is_relative_to(OUT / 'cohort/benchmark_manifests') or sha(manifest) != digest:
            raise ValueError('Frozen native manifest changed')
        rows = manifests[name] = read_jsonl(manifest)
        by_event.update({row['event_id']: name for row in rows})
    verified_conditions = set()
    for batch in batches:
        run = batch['run_id']
        members = selected[run]['event_ids']
        names = {by_event.get(event) for event in members}
        if len(names) != 1 or None in names:
            raise ValueError('Batch must belong to one complete retained condition manifest')
        manifest = next(iter(names))
        if (batch.get('queue_id') != 'stage7a_bench_v6_'+run or
                batch.get('log_path') != 'runs/stage7a_bench/'+run+'.log' or
                batch.get('selection') != reference['path'] or
                batch.get('manifest_hashes') != {manifest: selection['manifests'][manifest]} or
                type(batch.get('expected_event_count')) is not int or
                batch['expected_event_count'] != len(members) or batch.get('status') != 'pending'):
            raise ValueError('Queued batch differs from its frozen native ownership')
        if manifest not in verified_conditions:
            # The selector verifies the entire selection, all frozen conditions
            # and the prior complete screens, not merely this returned batch.
            select_retained_rows(manifests[manifest], selection, run)
            verified_conditions.add(manifest)
        if any(p.exists() for p in (OUT/'native_screen/generations'/run,
                                   OUT/'raw'/run, ROOT/batch['log_path'])):
            raise FileExistsError('Existing native evidence requires explicit reconciliation')
    if plan.get('total_pending_events') != sum(len(b['event_ids']) for b in selected.values()):
        raise ValueError('Dispatch accounting differs from the frozen selection')
    if (OUT / 'raw' / plan['pool_id']).exists():
        raise FileExistsError('Existing dispatch cannot be retried automatically')
    return plan


def verify_allocation_shell(allocation, pane, steps):
    # tmux sees the login-side srun foreground process for an interactive
    # allocation even while its remote bash is ready for the next command.
    # The sole remaining Slurm step must be that allocation shell.
    expected = [[allocation['slurm_allocation']+'.0', 'bash', allocation['node']]]
    if pane not in ('bash', 'srun') or [line.split() for line in steps.splitlines() if line.strip()] != expected:
        raise RuntimeError('Allocation shell is busy or changed; wait for the safe completion boundary')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execution-plan', required=True)
    args = parser.parse_args()
    path = (ROOT / args.execution_plan).resolve()
    plan = validate_execution(path)
    digest = sha(path)
    allocation = plan['allocation']
    status = subprocess.check_output(['squeue', '-h', '-j', allocation['slurm_allocation'],
        '-o', '%T %N %C %b'], text=True).strip()
    if status != f"RUNNING {allocation['node']} 32 gres/gpu:4":
        raise RuntimeError('Existing allocation unavailable or changed: '+status)
    pane = subprocess.check_output(['tmux', 'display-message', '-p', '-t',
        allocation['tmux_pane'], '#{pane_current_command}'], text=True).strip()
    steps = subprocess.check_output(['squeue', '--steps', '-h', '-j',
        allocation['slurm_allocation'], '-o', '%i %j %N'], text=True)
    verify_allocation_shell(allocation, pane, steps)
    queue = read_json(ROOT / 'state/gpu_experiment_queue.json')
    ids = {b['queue_id'] for b in plan['batches']}
    if any(j['id'] in ids or j['id'].startswith('stage7a_') and j['status'] == 'running'
           for j in queue['jobs']):
        raise RuntimeError('Existing Stage7A work requires reconciliation before registration')
    sys.path.insert(0, str(ROOT / 'infra'))
    from harness_state import mutate_gpu_queue, now_iso
    base = OUT / 'raw' / plan['pool_id']
    command = 'bash scripts/stage7a_bench/run_native_parallel_v6_tmux.sh '+shlex.quote(str(path.relative_to(ROOT)))
    pool_log = 'runs/stage7a_bench/'+plan['pool_id']+'.log'
    if (ROOT / pool_log).exists():
        raise FileExistsError('Preserve the previous pool log')
    try:
        for batch in plan['batches']:
            child = [str(ROOT/'.venv/bin/python'), 'scripts/stage7a_bench/native_images_v6.py',
                     '--run-id', batch['run_id'], '--bounded-attention']
            child += ['--manifest', next(iter(batch['manifest_hashes'])), '--selection',
                      batch['selection'], '--execution-plan', str(path.relative_to(ROOT))]
            subprocess.run([str(ROOT/'.venv/bin/python'), 'infra/gpu_scheduler.py', 'add',
                '--project', '.', '--id', batch['queue_id'], '--exp-id', batch['queue_id'],
                '--gpu-type', 'a6000', '--gpus', '1', '--node', allocation['node'],
                '--mem', '30G', '--cpus', '8', '--tmux-session', allocation['tmux_session'],
                '--shell-mode', 'plain', '--command', shlex.join(child),
                '--log-path', batch['log_path'], '--result-path',
                'outputs/stage7a_bench_v2/raw/'+batch['run_id']], check=True)
        if sha(path) != digest:
            raise ValueError('Execution plan changed during registration')
        write_json(base/'dispatch.json', dict(plan_sha256=digest, workers={},
                   batches=deepcopy(plan['batches'])), freeze=True)
        write_json(base/'launch.json', dict(registered_at=now_iso(), plan_sha256=digest,
            command=command, allocation=allocation, new_allocation=False), freeze=True)
        subprocess.run(['tmux', 'send-keys', '-t', allocation['tmux_pane'], '-l',
                        command+' > '+shlex.quote(pool_log)+' 2>&1'], check=True)
        subprocess.run(['tmux', 'send-keys', '-t', allocation['tmux_pane'], 'Enter'], check=True)
    except BaseException as error:
        def cancel_unstarted(current):
            for job in current['jobs']:
                if job['id'] in ids and job['status'] == 'queued':
                    job.update(status='cancelled', completed_at=now_iso(),
                               cancellation_reason='Retained dispatch registration/launch failed')
        mutate_gpu_queue(ROOT, cancel_unstarted)
        write_json(base/'launch_failure.json', dict(error=repr(error), plan_sha256=digest,
            observed_at=now_iso(), automatic_retry=False), freeze=True)
        raise
    print('Started retained dispatch '+plan['pool_id']+' in existing Slurm '+allocation['slurm_allocation'])


if __name__ == '__main__':
    main()
