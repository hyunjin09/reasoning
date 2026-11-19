"""A scheduling amendment cannot silently change native model execution."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def science_tail(path):
    tree = ast.parse(path.read_text())
    # The separately tested v3 wrapper changes short-prefill query tiling only.
    # All native generation, document processing and mechanics gates stay exact.
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == 'scripts.stage7a_bench.bounded_attention_v3':
            node.module = 'scripts.stage7a_bench.bounded_attention_v2'
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    start = next(i for i, node in enumerate(main.body) if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == 'cap' for target in node.targets))
    return ast.dump(ast.Module(body=main.body[start:], type_ignores=[]), include_attributes=False)


def test_native_generation_mechanics_and_document_processing_unchanged():
    assert science_tail(ROOT / 'scripts/stage7a_bench/native_images_v6.py') == science_tail(
        ROOT / 'scripts/stage7a_bench/native_images_v5.py')


def test_new_runner_requires_verified_selection_and_explicit_execution_plan():
    source = (ROOT / 'scripts/stage7a_bench/native_images_v6.py').read_text()
    assert 'from scripts.stage7a_bench.reduced_native_selection_v6 import select_retained_rows' in source
    assert 'rows = select_retained_rows(rows, read_json(selection_path), args.run_id)' in source
    assert "parser.add_argument('--execution-plan', required=True)" in source
    assert "'outputs/stage7a_bench_v2/config/native_parallel_execution_v5.json'" not in source


def test_new_launcher_uses_only_existing_four_gpu_allocation():
    source = (ROOT / 'scripts/stage7a_bench/run_native_parallel_v6_tmux.sh').read_text()
    assert 'srun --overlap --jobid=113280' in source
    assert '--ntasks=4' in source and '--gpus-per-task=1' in source
    assert '--execution-plan "$1"' in source
    assert 'CUDA_VISIBLE_DEVICES' not in source


def test_parallel_worker_passes_the_same_frozen_execution_plan_to_native_child():
    source = (ROOT / 'scripts/stage7a_bench/parallel_native_v6.py').read_text()
    assert "'--execution-plan', str(plan_path.relative_to(ROOT))" in source
    assert "parser.add_argument('--execution-plan', required=True)" in source
    assert 'native_images_v5.py' not in source


def test_dispatch_ownership_and_failure_semantics_are_unchanged():
    functions = []
    for version in ('v5', 'v6'):
        tree = ast.parse((ROOT / f'scripts/stage7a_bench/parallel_native_{version}.py').read_text())
        functions.append({node.name: ast.dump(node, include_attributes=False) for node in tree.body
                          if isinstance(node, ast.FunctionDef) and node.name in
                          ('locked_state', 'claim_next', 'finish_batch')})
    assert functions[0] == functions[1]
