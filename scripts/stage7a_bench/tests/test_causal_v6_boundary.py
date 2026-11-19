"""Allocation adaptation must preserve every causal/PRIOR_FILL operation."""
import ast
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('stem', ['causal_run', 'native_prior_run',
    'native_prior_convergence', 'causal_metrics', 'compile_causal', 'queue_worker_causal'])
def test_versioned_worker_and_parser_preserve_scientific_ast(stem):
    old = (HERE / (stem+'_v2.py')).read_text()
    new = (HERE / (stem+'_v6.py')).read_text()
    for dependency in ('pilot_freeze', 'causal_run', 'native_prior_run',
                       'native_prior_convergence', 'causal_metrics'):
        new = new.replace(dependency+'_v6', dependency+'_v2')
    new = new.replace('config/runtime_node02_v3.json', 'config/runtime.json')
    assert ast.dump(ast.parse(new), include_attributes=False) == ast.dump(
        ast.parse(old), include_attributes=False)


def test_shell_uses_one_slurm_bound_gpu_inside_existing_allocation():
    shell = (HERE / 'run_causal_v6_tmux.sh').read_text()
    for literal in ('--jobid=113280', '--ntasks=1', '--gres=gpu:1', '--gpus-per-task=1',
                    '--cpus-per-task=8', '--mem=30G', 'queue_worker_causal_v6.py'):
        assert literal in shell
    assert 'CUDA_VISIBLE_DEVICES=' not in shell
    assert 'sbatch' not in shell and 'salloc' not in shell


def test_launcher_checks_four_gpu_allocation_and_registers_only_one_gpu_step():
    text = (HERE / 'launch_causal_v6_existing.py').read_text()
    assert "allocation['gpus'] != 4" in text
    assert 'gres/gpu:4' in text
    assert "'--gpus','1'" in text
    assert "'--mem','30G','--cpus','8'" in text
    assert 'run_causal_v6_tmux.sh' in text
    assert 'capture-pane' not in text
    assert 'display-message' in text


def test_freeze_receipt_covers_entire_versioned_execution_chain():
    from scripts.stage7a_bench.pilot_freeze_v6 import dependency_hashes
    hashes = dependency_hashes()
    for name in ('causal_run_v6.py', 'launch_causal_v6_existing.py', 'queue_worker_causal_v6.py',
                 'run_causal_v6_tmux.sh', 'native_prior_run_v6.py',
                 'native_prior_convergence_v6.py', 'causal_metrics_v6.py', 'compile_causal_v6.py'):
        assert 'scripts/stage7a_bench/'+name in hashes


@pytest.mark.parametrize('pane,steps,ready', [
    ('srun', '113280.0 bash node02', True),
    ('bash', '113280.0 bash node02', True),
    ('srun', '113280.0 bash node02\n113280.4 python node02', False),
    ('python', '113280.0 bash node02', False),
    ('srun', '', False),
    ('srun', '113280.0 bash node06', False),
])
def test_causal_launch_runtime_guard_handles_outer_srun_without_overlap(pane, steps, ready):
    # Execute the actual small readiness guard without importing model/scoring.
    tree = ast.parse((HERE / 'launch_causal_v6_existing.py').read_text())
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name=='main')
    first = next(i for i,n in enumerate(main.body) if isinstance(n,ast.Assign) and
                 any(isinstance(t,ast.Name) and t.id=='expected_shell' for t in n.targets))
    scope = dict(allocation=dict(slurm_allocation='113280',node='node02'),
                 current_command=pane, steps=steps)
    guard = compile(ast.Module(body=main.body[first:first+2], type_ignores=[]), '<actual_guard>', 'exec')
    if ready:
        exec(guard,scope)
    else:
        with pytest.raises(RuntimeError): exec(guard,scope)
