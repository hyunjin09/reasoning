import pytest

from scripts.stage7a.causal_variants import fixed_prefix_variants
from scripts.stage7a.common import OUT, read_jsonl


def test_frozen_cohort_retains_available_controls_and_reports_absent_object_masks():
    native = {r['event_id']: r for r in read_jsonl(OUT/'cohort/native_manifest.jsonl')}
    missing = []
    for split in ('discovery', 'confirmation'):
        for entry in read_jsonl(OUT/f'config/{split}_events.jsonl'):
            available, unavailable = fixed_prefix_variants(entry, native)
            assert len(available) + len(unavailable) == len(entry['fixed_prefix_controls'])
            for condition, variant in available:
                assert variant is native[entry['base_id']+'__'+condition]
                assert variant['prompt'] == entry['row']['prompt']
            if unavailable:
                assert set(unavailable) == {'fixed_mask'}
                assert unavailable['fixed_mask']['available'] is False
                assert entry['cohort'] == 'C3' and entry['row']['present'] is False
                missing.append(entry['base_id'])
    assert len(missing) == 20 and len(set(missing)) == 10


@pytest.mark.parametrize('cohort,present,condition', [
    ('C1', False, 'mask'), ('C3', True, 'mask'), ('C3', False, 'unrelated'),
])
def test_unexpected_missing_controls_still_fail(cohort, present, condition):
    row = dict(base_id='base', cohort=cohort, present=present,
               target_availability='queried_object_absent')
    entry = dict(row=row, fixed_prefix_controls=[condition])
    with pytest.raises(KeyError):
        fixed_prefix_variants(entry, {})
