"""The reduced release preserves sample sizes, ordering and prerequisite reviews."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts.stage7a.common import write_json, write_jsonl, sha
from scripts.stage7a_bench import reduced_native_selection_v6 as selector


@pytest.fixture
def release(monkeypatch):
    actual = Path(__file__).resolve().parents[3]
    with TemporaryDirectory(dir=actual / 'outputs/stage7a_bench_v2/audit') as temporary:
        root = Path(temporary)
        out = root / 'outputs/stage7a_bench_v2'
        monkeypatch.setattr(selector, 'ROOT', root)
        monkeypatch.setattr(selector, 'OUT', out)
        monkeypatch.setattr(selector, 'verify_mathwild_gate', lambda ref:
                            {'decision': 'CONTINUE_FROZEN_MATHWILD_SAMPLE'})
        checked = []
        monkeypatch.setattr(selector, 'load_completed_screen',
                            lambda benchmark, bindings: checked.append(benchmark))

        def make(benchmark):
            amendment = root / 'plan/amendment.md'
            amendment.parent.mkdir(parents=True, exist_ok=True)
            amendment.write_text('Approved reduced scope')
            authority = dict(path=str(amendment.relative_to(root)), sha256=sha(amendment))
            write_json(out / 'config/mathwild_gate96_selection_v5.json', {'amendment': authority})
            freeze, manifests, all_rows, batches = {}, {}, {}, []
            for condition, count in selector.EXPECTED_COUNTS[benchmark].items():
                rows = [dict(event_id=f'{condition}_{i}', benchmark=benchmark, condition=condition)
                        for i in range(count)]
                path = out / 'cohort/benchmark_manifests' / f'{condition}.jsonl'
                write_jsonl(path, rows)
                name = str(path.relative_to(root))
                freeze[benchmark+'_'+condition] = dict(manifest=name, sha256=sha(path), count=count)
                manifests[name] = sha(path)
                all_rows[condition] = rows
                pending = rows[96:] if benchmark == 'mathvision_wild' and condition == 'photo' else rows
                for rank in range(4):
                    batches.append(dict(run_id=f'{condition}_{rank}',
                                        event_ids=[r['event_id'] for r in pending[rank::4]]))
            write_json(out / 'cohort/sample_freeze.json', {'native_screen': freeze})
            prerequisites = {}
            names = [] if benchmark == 'mathvision_wild' else ['mathvision_wild']
            if benchmark == 'mmlongbench_doc':
                names.append('mmmu_pro')
            for name in names:
                path = out / 'config' / f'{name}_bindings.json'
                write_json(path, {})
                prerequisites[name] = dict(path=str(path.relative_to(root)), sha256=sha(path))
            selection = dict(status='FROZEN_REDUCED_REMAINDER', benchmark=benchmark,
                amendment=authority, mathwild_gate={}, prerequisites=prerequisites,
                manifests=manifests, batches=batches)
            return selection, all_rows, checked

        yield make


@pytest.mark.parametrize('benchmark', ['mathvision_wild', 'mmmu_pro', 'mmlongbench_doc'])
def test_retained_release_uses_full_original_conditions_and_completed_prerequisites(release, benchmark):
    selection, rows, checked = release(benchmark)
    condition = next(iter(rows))
    result = selector.select_retained_rows(rows[condition], selection, condition+'_0')
    expected = rows[condition][96::4] if benchmark == 'mathvision_wild' else rows[condition][::4]
    assert result == expected
    assert checked == list(selection['prerequisites'])


@pytest.mark.parametrize('benchmark', ['mathsight', 'microvqa', 'medxpertqa_mm', 'charxiv', 'phantom_0'])
def test_deferred_or_completed_benchmark_cannot_be_released(benchmark):
    with pytest.raises(ValueError):
        selector.select_retained_rows([], {'benchmark': benchmark}, 'unused')


@pytest.mark.parametrize('defect', ['rerun_gate_item', 'duplicate', 'omitted', 'reordered',
    'mixed_condition', 'wrong_input', 'missing_prerequisite', 'changed_authority'])
def test_selection_cannot_skip_replay_or_cross_frozen_units(release, defect):
    benchmark = 'mmmu_pro' if defect == 'missing_prerequisite' else 'mathvision_wild'
    selection, rows, _ = release(benchmark)
    condition = next(iter(rows))
    provided = deepcopy(rows[condition])
    batch = selection['batches'][0]
    if defect == 'rerun_gate_item': batch['event_ids'][0] = 'photo_0'
    elif defect == 'duplicate': batch['event_ids'].append(batch['event_ids'][0])
    elif defect == 'omitted': batch['event_ids'].pop()
    elif defect == 'reordered': batch['event_ids'].reverse()
    elif defect == 'mixed_condition':
        other = selection['batches'][4]
        batch['event_ids'][0], other['event_ids'][0] = other['event_ids'][0], batch['event_ids'][0]
    elif defect == 'wrong_input': provided[0]['event_id'] = 'changed'
    elif defect == 'missing_prerequisite': selection['prerequisites'] = {}
    else: selection['amendment']['sha256'] = 'changed'
    with pytest.raises(ValueError):
        selector.select_retained_rows(provided, selection, condition+'_0')


def test_failed_mathwild_gate_cannot_release_its_remaining_sample(release, monkeypatch):
    selection, rows, _ = release('mathvision_wild')
    monkeypatch.setattr(selector, 'verify_mathwild_gate', lambda ref: {'decision': 'STOP_MATHWILD_LOW_YIELD'})
    with pytest.raises(ValueError):
        selector.select_retained_rows(rows['photo'], selection, 'photo_0')


def test_stopped_mathwild_allows_mmmu_without_fabricating_a_complete264_screen(release, monkeypatch):
    selection, rows, checked = release('mmmu_pro')
    selection['prerequisites'] = {}
    monkeypatch.setattr(selector, 'verify_mathwild_gate', lambda ref: {'decision': 'STOP_MATHWILD_LOW_YIELD'})
    assert len(selector.select_retained_rows(rows['image_present'], selection, 'image_present_0')) == 50
    assert checked == []


def test_unfinished_mmmu_reviews_block_documents(release, monkeypatch):
    selection, rows, _ = release('mmlongbench_doc')
    def unfinished(benchmark, bindings):
        if benchmark == 'mmmu_pro':
            raise ValueError('Missing full native review')
    monkeypatch.setattr(selector, 'load_completed_screen', unfinished)
    with pytest.raises(ValueError, match='Missing full native review'):
        selector.select_retained_rows(rows['image_present'], selection, 'image_present_0')
