"""A retained dispatch cannot change scope or reuse an existing run."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts.stage7a.common import sha, write_json, write_jsonl
from scripts.stage7a_bench import launch_native_v6_existing as launcher


@pytest.fixture
def dispatch(monkeypatch):
    actual = Path(__file__).resolve().parents[3]
    with TemporaryDirectory(dir=actual / 'outputs/stage7a_bench_v2/audit') as tmp:
        root = Path(tmp)
        out = root / 'outputs/stage7a_bench_v2'
        monkeypatch.setattr(launcher, 'ROOT', root)
        monkeypatch.setattr(launcher, 'OUT', out)
        allocation = dict(slurm_allocation='113280', node='node02', gpus=4, cpus=32,
                          host_memory='120G', tmux_session='10', tmux_pane='%21')
        write_json(out / 'config/runtime_node02_v3.json',
                   dict(runtime=allocation, new_allocations_permitted=False))
        uuids = ['gpu'+str(i) for i in range(4)]
        write_json(out / 'config/native_parallel_execution_v5.json',
                   dict(assigned_gpu_uuids=uuids))
        manifest = out / 'cohort/benchmark_manifests/photo.jsonl'
        rows = [dict(event_id='photo_'+str(i), benchmark='mathvision_wild', condition='photo')
                for i in range(8)]
        write_jsonl(manifest, rows)
        name = str(manifest.relative_to(root))
        selection = dict(status='FROZEN_REDUCED_REMAINDER', benchmark='mathvision_wild',
            batches=[dict(run_id='batch_'+str(i), event_ids=[r['event_id'] for r in rows[i*4:i*4+4]])
                     for i in range(2)], manifests={name: sha(manifest)})
        selected = []
        def verify(provided, value, run):
            assert provided == rows and value == selection
            selected.append(run)
            return rows[:4]
        monkeypatch.setattr(launcher, 'select_retained_rows', verify)
        path = out / 'config/selection.json'
        write_json(path, selection)
        plan = dict(status='FROZEN_RETAINED_NATIVE_EXECUTION', pool_id='mathwild_test',
            allocation=allocation, assigned_gpu_uuids=uuids, workers=4, gpus_per_worker=1,
            new_allocation=False, total_pending_events=8,
            launcher_sha256=sha(launcher.__file__),
            selection=dict(path=str(path.relative_to(root)), sha256=sha(path)),
            batches=[dict(run_id=b['run_id'], queue_id='stage7a_bench_v6_'+b['run_id'],
                log_path='runs/stage7a_bench/'+b['run_id']+'.log', manifest_hashes={name:sha(manifest)},
                selection=str(path.relative_to(root)), expected_event_count=4, status='pending')
                for b in selection['batches']])
        plan_path = out / 'config/execution.json'
        yield root, out, plan_path, plan, selected


def test_complete_dispatch_revalidates_scope_before_any_registration(dispatch):
    _, _, path, plan, selected = dispatch
    write_json(path, plan)
    assert launcher.validate_execution(path) == plan
    assert selected == ['batch_0']


@pytest.mark.parametrize('defect', ['allocation', 'uuid', 'duplicate', 'missing_batch',
    'event_count', 'manifest', 'selection', 'log_escape', 'queue_id', 'new_allocation', 'launcher'])
def test_changed_execution_cannot_be_registered(dispatch, defect):
    _, _, path, source, _ = dispatch
    plan = deepcopy(source)
    if defect == 'allocation': plan['allocation']['gpus'] = 3
    elif defect == 'uuid': plan['assigned_gpu_uuids'][0] = 'foreign'
    elif defect == 'duplicate': plan['batches'][1] = deepcopy(plan['batches'][0])
    elif defect == 'missing_batch': plan['batches'].pop()
    elif defect == 'event_count': plan['batches'][0]['expected_event_count'] = 5
    elif defect == 'manifest': plan['batches'][0]['manifest_hashes'] = {}
    elif defect == 'selection': plan['selection']['sha256'] = 'changed'
    elif defect == 'log_escape': plan['batches'][0]['log_path'] = '../foreign.log'
    elif defect == 'queue_id': plan['batches'][0]['queue_id'] = 'stage7a_bench_v2_old'
    elif defect == 'new_allocation': plan['new_allocation'] = True
    else: plan['launcher_sha256'] = 'changed'
    write_json(path, plan)
    with pytest.raises(ValueError):
        launcher.validate_execution(path)


@pytest.mark.parametrize('kind', ['pool', 'generation', 'wrapper', 'log'])
def test_prior_dispatch_artifacts_block_automatic_retry(dispatch, kind):
    root, out, path, plan, _ = dispatch
    locations = dict(pool=out/'raw/mathwild_test', generation=out/'native_screen/generations/batch_0',
                     wrapper=out/'raw/batch_0', log=root/'runs/stage7a_bench/batch_0.log')
    target = locations[kind]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('Preserved prior evidence')
    write_json(path, plan)
    with pytest.raises(FileExistsError):
        launcher.validate_execution(path)


def test_unfinished_semantic_gate_blocks_execution(dispatch, monkeypatch):
    _, _, path, plan, _ = dispatch
    def incomplete(*args):
        raise ValueError('All96 reviews are required')
    monkeypatch.setattr(launcher, 'select_retained_rows', incomplete)
    write_json(path, plan)
    with pytest.raises(ValueError, match='All96'):
        launcher.validate_execution(path)


@pytest.mark.parametrize('registration_failure', [False, True])
def test_registration_uses_existing_shell_and_cancels_partial_queue_on_failure(
        dispatch, monkeypatch, registration_failure):
    import subprocess
    import sys
    actual = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(actual / 'infra'))
    import harness_state
    root, out, path, plan, _ = dispatch
    write_json(path, plan)
    queue = {'jobs': []}
    write_json(root/'state/gpu_experiment_queue.json', queue)
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        if 'add' in command:
            if registration_failure and queue['jobs']:
                raise subprocess.CalledProcessError(1, command)
            queue['jobs'].append(dict(id=command[command.index('--id')+1], status='queued'))
        return subprocess.CompletedProcess(command, 0)
    monkeypatch.setattr(launcher.subprocess, 'run', run)
    monkeypatch.setattr(launcher.subprocess, 'check_output',
        lambda command, **kwargs: '113280.0 bash node02' if '--steps' in command else
        'RUNNING node02 32 gres/gpu:4' if command[0]=='squeue' else 'bash')
    monkeypatch.setattr(harness_state, 'mutate_gpu_queue', lambda root, edit: edit(queue))
    monkeypatch.setattr(sys, 'argv', ['launcher', '--execution-plan', str(path)])
    if registration_failure:
        with pytest.raises(subprocess.CalledProcessError):
            launcher.main()
        assert all(job['status']=='cancelled' for job in queue['jobs'])
        assert (out/'raw/mathwild_test/launch_failure.json').exists()
        assert not any(command[0]=='tmux' for command in calls)
    else:
        launcher.main()
        state = launcher.read_json(out/'raw/mathwild_test/dispatch.json')
        assert state['workers']=={} and state['batches']==plan['batches']
        assert len(queue['jobs'])==2 and all(job['status']=='queued' for job in queue['jobs'])
        assert any('run_native_parallel_v6_tmux.sh' in ' '.join(command) for command in calls)
    assert not any(command[0] in ('srun','sbatch') for command in calls)
    assert not any('capture-pane' in command or 'launch' in command for command in calls)


@pytest.mark.parametrize('pane', ['bash', 'srun'])
def test_ready_remote_shell_accepts_interactive_allocation_wrapper(pane):
    launcher.verify_allocation_shell(dict(slurm_allocation='113280', node='node02'),
                                     pane, '113280.0 bash node02\n')


@pytest.mark.parametrize('pane,steps', [
    ('python', '113280.0 bash node02'),
    ('srun', '113280.0 bash node02\n113280.3 python node02'),
    ('bash', ''),
    ('srun', '113280.0 bash node06'),
    ('srun', '113280.1 bash node02'),
    ('srun', '113280.0 python node02'),
])
def test_busy_or_changed_allocation_shell_is_rejected(pane, steps):
    with pytest.raises(RuntimeError):
        launcher.verify_allocation_shell(dict(slurm_allocation='113280', node='node02'), pane, steps)
