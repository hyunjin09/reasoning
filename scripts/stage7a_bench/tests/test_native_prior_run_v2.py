from copy import deepcopy
from types import SimpleNamespace
import time

import pytest

from scripts.stage7a.common import read_json
import scripts.stage7a_bench.native_prior_run_v2 as runner


def setup(monkeypatch, *, mismatch=False, truncated=False):
    calls, checks, releases = [], [], []
    monkeypatch.setattr(runner, 'prepare_condition',
        lambda processor, row, device: ({'unchanged': True}, {'condition': row['condition']}))
    monkeypatch.setattr(runner, 'verify_fixed_input', lambda *args: checks.append(args[2]['condition']))
    monkeypatch.setattr(runner, 'release', lambda: releases.append(True))
    monkeypatch.setattr(runner.torch.cuda, 'reset_peak_memory_stats', lambda: None)
    monkeypatch.setattr(runner.torch.cuda, 'max_memory_allocated', lambda: 100)
    monkeypatch.setattr(runner, 'dependency_hashes', lambda: {'test': 'frozen'})
    def generate(model, processor, prepared, cap, attention, **kwargs):
        calls.append(dict(cap=cap, attention=attention, **deepcopy(kwargs)))
        ids = [3, 9] if cap == 128 or not truncated else list(range(40960))
        if mismatch and len(calls) == 2: ids = [2, 9]
        return dict(generated_token_ids=ids, generated_token_count=len(ids),
            raw_decoded_response='</think>answer' if not truncated else 'unfinished',
            token_rows=[dict(token_id=i) for i in ids], attention_arrays=None)
    monkeypatch.setattr(runner, 'generate_once', generate)
    entry = dict(id='e00', native_input={})
    signature = dict(control_rows={'e00':{'fixed_'+c:dict(condition=c, event_id='e00__'+c)
                 for c in ('mask', 'unrelated', 'no_image')}},
                 execution_signature=dict(dependencies={'test': 'frozen'}))
    config = dict(locked_generation_protocol=dict(max_new_tokens=40960, seed=1234))
    model = SimpleNamespace(generation_config=SimpleNamespace(eos_token_id=[9]))
    return (model, None, [entry], signature, config), calls, checks, releases


@pytest.mark.parametrize('truncated', [False, True])
def test_all_three_frozen_controls_use_fresh_locked_generation(monkeypatch, tmp_path, truncated):
    args, calls, checks, releases = setup(monkeypatch, truncated=truncated)
    model, processor, entries, signature, config = args
    runner.run_native_controls(model, processor, entries, tmp_path, signature, config, time.perf_counter())
    assert [c['cap'] for c in calls] == [128, 128, 40960]*3
    assert all(c['attention'] is None and c['seed'] == 1234 and
               c['collect_predictive_metrics'] is False for c in calls)
    assert calls[0]['generation_kwargs'] == calls[-1]['generation_kwargs']
    assert checks == ['mask', 'unrelated', 'no_image'] and len(releases) == 6
    summary = read_json(tmp_path/'run_summary.json')
    assert summary['completed'] and summary['native_convergence_certified'] is False
    for condition in checks:
        row = read_json(tmp_path/'examples/e00'/condition/'result.json')
        assert row['truncated'] is truncated and row['complete'] is (not truncated)
        assert row['native_reasoning_prefix_supplied'] is False


def test_actual_token_parity_failure_stops_before_scientific_generation(monkeypatch, tmp_path):
    args, calls, checks, releases = setup(monkeypatch, mismatch=True)
    model, processor, entries, signature, config = args
    with pytest.raises(ValueError, match='parity failed'):
        runner.run_native_controls(model, processor, entries, tmp_path, signature, config, time.perf_counter())
    assert len(calls) == 2 and releases == [True]
    assert not read_json(tmp_path/'native_mechanics.json')['checks'][0]['exact']
    assert not (tmp_path/'examples').exists()
