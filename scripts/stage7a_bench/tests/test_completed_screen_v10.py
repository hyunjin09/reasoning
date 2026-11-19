"""Reject provenance shortcuts introduced by native OOM continuation."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts.stage7a_bench import completed_screen_v10 as loader


def oom():
    return dict(unavailable=True, complete=False, unavailable_reason='cuda_oom',
        scientific_state=None, token_count=0, generation_sha256=None, tokens_sha256=None,
        truncated=None, ended_with_eos=None, error='CUDA out of memory.')


def test_real_runtime_exclusion_is_not_a_semantic_model_failure():
    loader.validate_oom(oom(), {'preflight_status': 'ready'}, False)


@pytest.mark.parametrize('defect', ['review', 'preflight', 'tokens', 'label', 'not_oom', 'partial_text'])
def test_oom_exception_does_not_admit_other_missingness_or_semantics(defect):
    result, row, reviewed = oom(), {'preflight_status': 'ready'}, False
    if defect == 'review':
        reviewed = True
    elif defect == 'preflight':
        row['preflight_status'] = 'missing_document'
    elif defect == 'tokens':
        result['token_count'] = 1
    elif defect == 'label':
        result['scientific_state'] = 'WRONG_SOURCE_READ'
    elif defect == 'partial_text':
        result['generation_sha256'] = 'partial'
    else:
        result['error'] = 'other failure'
    with pytest.raises(ValueError):
        loader.validate_oom(result, row, reviewed)


def test_import_requires_recorded_original_directory_and_hash(monkeypatch):
    actual = Path(__file__).resolve().parents[3]
    with TemporaryDirectory(dir=actual / 'outputs/stage7a_bench_v2/audit') as temp:
        root = Path(temp)
        out = root / 'outputs/stage7a_bench_v2'
        monkeypatch.setattr(loader, 'ROOT', root)
        monkeypatch.setattr(loader, 'OUT', out)
        old = out / 'native_screen/generations/old/examples/e'
        old.mkdir(parents=True)
        link = out / 'native_screen/generations/new/examples/e'
        link.parent.mkdir(parents=True)
        link.symlink_to(old, target_is_directory=True)
        ledger = dict(predecessor_run_id='old', preserved=[dict(event_id='e',
            source=str(old.relative_to(root)), result_sha256='exact')])
        assert loader.resolve_owner(link, ledger, 'e', 'exact') == 'old'
        with pytest.raises(ValueError):
            loader.resolve_owner(link, ledger, 'e', 'changed')
        other = deepcopy(ledger)
        other['preserved'] = []
        with pytest.raises(ValueError):
            loader.resolve_owner(link, other, 'e', 'exact')
        other = deepcopy(ledger)
        other['preserved'][0]['source'] = str(link.relative_to(root))
        with pytest.raises(ValueError):
            loader.resolve_owner(link, other, 'e', 'exact')


@pytest.mark.parametrize('benchmark', ['phantom_0', 'charxiv', 'mathsight', 'microvqa', 'medxpertqa_mm'])
def test_adapter_does_not_reopen_preserved_or_deferred_benchmarks(benchmark):
    with pytest.raises(ValueError):
        loader.load_completed_screen(benchmark, {})
