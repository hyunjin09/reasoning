from copy import deepcopy

import pytest

from scripts.stage7a_bench.oom_continuation_v9 import claim_next, restart_after_oom


def test_oom_exit_advances_past_failure_without_retrying_completed_events():
    results = {'a': {'complete': True}, 'b': {'unavailable': True, 'unavailable_reason': 'cuda_oom'}}
    assert restart_after_oom(75, {'a'}, results, {'a', 'b', 'c'}) is True


@pytest.mark.parametrize('code, before, results', [
    (1, set(), {'a': {'unavailable': True, 'unavailable_reason': 'cuda_oom'}}),
    (75, {'a'}, {'a': {'unavailable': True, 'unavailable_reason': 'cuda_oom'}}),
    (75, set(), {'a': {'complete': True}}),
    (75, {'a'}, {'b': {'unavailable': True, 'unavailable_reason': 'cuda_oom'}}),
    (75, set(), {'unknown': {'unavailable': True, 'unavailable_reason': 'cuda_oom'}}),
])
def test_unproven_oom_or_no_forward_progress_is_fatal(code, before, results):
    with pytest.raises(ValueError):
        restart_after_oom(code, before, results, {'a', 'b', 'c'})


def test_success_does_not_restart():
    assert restart_after_oom(0, set(), {}, set()) is False


def test_active_predecessor_is_never_claimed_but_unstarted_work_can_advance():
    s = {'batches': [dict(run_id='a9', predecessor_run_id='a8', status='pending'),
                     dict(run_id='b9', predecessor_run_id='b8', status='pending')]}
    old = {'batches': [dict(run_id='a8', status='running'), dict(run_id='b8', status='pending')]}
    assert claim_next(s, 0, old)['run_id'] == 'b9'
    assert s['batches'][0]['status'] == 'pending'
    old['batches'][0]['status'] = 'failed'
    assert claim_next(s, 1, old)['run_id'] == 'a9'


def test_non_oom_worker_failure_still_stops_new_dispatch():
    s = {'worker_errors': {'0': 'ValueError'}, 'batches': [dict(run_id='a9', predecessor_run_id='a8', status='pending')]}
    before = deepcopy(s)
    assert claim_next(s, 1, {'batches': []}) is None
    assert s == before


def test_worker_cannot_claim_two_batches():
    s = {'batches': [dict(run_id='a9', predecessor_run_id='a8', status='running', rank=0)]}
    with pytest.raises(ValueError):
        claim_next(s, 0, {'batches': []})


def test_real_subprocess_restarts_after_oom_and_never_retries_the_event(tmp_path):
    import json
    import sys
    from scripts.stage7a_bench.oom_continuation_v9 import run_attempts
    dest = tmp_path / 'native'
    dest.mkdir()
    program = tmp_path / 'fake_native.py'
    program.write_text('''import json, os, sys
from pathlib import Path
p = Path(sys.argv[1])
(p / 'signature.json').write_text('{}')
with (p / 'processes.jsonl').open('a') as f: f.write(json.dumps(os.getpid())+'\\n')
for event in ['a', 'b', 'c']:
    out = p / 'examples' / event / 'result.json'
    if out.exists(): continue
    with (p / 'attempted.jsonl').open('a') as f: f.write(json.dumps(event)+'\\n')
    out.parent.mkdir(parents=True, exist_ok=True)
    result = {'unavailable': True, 'unavailable_reason': 'cuda_oom'} if event == 'b' else {'complete': True}
    out.write_text(json.dumps(result))
    if event == 'b': sys.exit(75)
''')
    code, attempts = run_attempts([sys.executable, str(program), str(dest)], dest,
                                 tmp_path / 'native.log', {'a', 'b', 'c'})
    assert code == 0 and [a['exit_code'] for a in attempts] == [75, 0]
    assert [json.loads(x) for x in (dest / 'attempted.jsonl').read_text().splitlines()] == ['a', 'b', 'c']
    assert len(set((dest / 'processes.jsonl').read_text().splitlines())) == 2
    assert '--resume' in attempts[1]['command']


def test_non_oom_subprocess_failure_is_not_restarted(tmp_path):
    import sys
    from scripts.stage7a_bench.oom_continuation_v9 import run_attempts
    code, attempts = run_attempts([sys.executable, '-c', 'raise SystemExit(1)'],
        tmp_path / 'native', tmp_path / 'failure.log', {'a'})
    assert code == 1 and len(attempts) == 1


@pytest.fixture
def predecessor_fixture(tmp_path, monkeypatch):
    from scripts.stage7a.common import write_json, sha
    from scripts.stage7a_bench import oom_continuation_v9 as m
    out = tmp_path / 'outputs/stage7a_bench_v2'
    monkeypatch.setattr(m, 'ROOT', tmp_path)
    monkeypatch.setattr(m, 'OUT', out)
    rows = [dict(event_id=e, base_id=e, benchmark='mmlongbench_doc', condition='image_present', family_id=e) for e in ['a', 'b', 'c']]
    selection = out / 'config/selection.json'
    write_json(selection, {'batches': [dict(run_id='old', event_ids=['a', 'b', 'c'])]})
    plan = out / 'config/plan.json'
    write_json(plan, dict(batches=[dict(run_id='old', log_path='old.log')],
                         selection=dict(path=str(selection.relative_to(tmp_path)), sha256=sha(selection))))
    ref = dict(path=str(plan.relative_to(tmp_path)), sha256=sha(plan))
    source = out / 'native_screen/generations/old'
    write_json(source / 'signature.json', dict(event_ids=['a', 'b', 'c'], dependencies={}))
    write_json(source / 'mechanics.json', dict(checks=[dict(repeat_token_ids_exact=True)]))
    write_json(out / 'raw/old/run_summary.json', dict(plan_sha256=sha(plan), exit_code=1))
    old = dict(run_id='old', status='failed', exit_code=1, log_path='old.log')
    (tmp_path / 'old.log').write_text('MECHANICS_PASSED 1\nscripts/stage7a_bench/document_runtime_v2.py\ntorch.OutOfMemoryError: CUDA out of memory.\n')
    a = source / 'examples/a'
    write_json(a / 'manifest_row.json', rows[0])
    write_json(a / 'generation.json', {'response': 'saved'})
    (a / 'tokens.jsonl').write_text('{}\n')
    write_json(a / 'result.json', dict(event_id='a', complete=True,
        generation_sha256=sha(a / 'generation.json'), tokens_sha256=sha(a / 'tokens.jsonl')))
    write_json(source / 'examples/b/manifest_row.json', rows[1])
    write_json(source / 'examples/b/input.json', {'pages': 196})
    return m, out / 'native_screen/generations/new', rows, old, ref, source


def test_predecessor_preserves_success_records_exact_failed_sample_and_leaves_remainder(predecessor_fixture):
    from scripts.stage7a.common import read_json, sha
    m, dest, rows, old, ref, source = predecessor_fixture
    digest = sha(source / 'examples/a/result.json')
    ledger = m.preserve_predecessor(dest, rows, old, ref)
    assert (dest / 'examples/a').is_symlink()
    assert sha(source / 'examples/a/result.json') == digest
    assert read_json(dest / 'examples/b/result.json')['unavailable_reason'] == 'cuda_oom'
    assert not (dest / 'examples/c/result.json').exists()
    assert ledger['runtime_oom'] == ['b']
    assert m.preserve_predecessor(dest, rows, old, ref) == ledger


def test_active_predecessor_cannot_be_imported(predecessor_fixture):
    m, dest, rows, old, ref, source = predecessor_fixture
    old['status'] = 'running'
    with pytest.raises(ValueError, match='active'):
        m.preserve_predecessor(dest, rows, old, ref)


def test_non_oom_predecessor_is_not_silently_skipped(predecessor_fixture):
    m, dest, rows, old, ref, source = predecessor_fixture
    (m.ROOT / 'old.log').write_text('MECHANICS_PASSED 1\nRuntimeError: numerical failure\n')
    with pytest.raises(ValueError, match='verified native sample CUDA OOM'):
        m.preserve_predecessor(dest, rows, old, ref)
