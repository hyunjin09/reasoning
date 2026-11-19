from copy import deepcopy

import pytest

from scripts.stage6a.close_workspace_state import (
    RECOMMENDATION, replace_between, section, validate_closeout,
)


def completed_artifacts():
    return [
        dict(events=2983, bases=1276, release_events_sha256='release',
             per_cohort_events=dict(C1=1199, C2=124, C3=660, C4=1000),
             per_cohort_bases=dict(C1=109, C2=31, C3=136, C4=1000)),
        dict(status='PASS', events=2983, bases=1276, release_sha256='release'),
        dict(status='CONTROLLED_PASS_NATURAL_ATLAS_INSUFFICIENT', release_sha256='release',
             gates=dict(C1=True, C2=True, C3=True, C4_unbiased_acquisition=True, C4_atlas=False),
             C4=dict(unbiased_images=1000, matched_pairs=10),
             recommendation=RECOMMENDATION, next_stage_executed=False,
             internal_state_features_used_for_selection=False),
        dict(status='COMPLETE_MEASURED_NATIVE_RESOURCE_SUMMARY', native_terminal_records=3182,
             physical_repeat_generations=13, native_completeness=dict(EOS_COMPLETE=3174, INCOMPLETE=8),
             physical_gpus=4, new_allocations_requested_by_agent=0, parameter_dtype='torch.bfloat16'),
        dict(status='PASS', events=1992, complete_manual_prefix_bases=109,
             manual_prefix_spans=1766, baseline_claims_preserved_in_prefix=105),
        [dict(number=i, columns=['metric', 'value'], rows=[['sample', i]]) for i in range(1, 19)],
    ]


def test_terminal_incompletes_and_low_natural_yield_allow_completed_reporting():
    validate_closeout(*completed_artifacts())


@pytest.mark.parametrize('index,field,value', [
    (0, 'events', 2982), (0, 'per_cohort_events', dict(C1=1198, C2=125, C3=660, C4=1000)),
    (1, 'status', 'FAIL'), (2, 'release_sha256', 'different'),
    (2, 'recommendation', 'GO — Stage 6B Causal Retrieval-Dynamics Analysis'),
    (2, 'next_stage_executed', True), (3, 'status', 'RESOURCE_SNAPSHOT'),
    (3, 'new_allocations_requested_by_agent', 1), (3, 'parameter_dtype', 'torch.float32'),
    (4, 'complete_manual_prefix_bases', 108),
])
def test_partial_unexpected_or_unfrozen_results_do_not_close_docs(index, field, value):
    artifacts = deepcopy(completed_artifacts())
    artifacts[index][field] = value
    with pytest.raises(AssertionError):
        validate_closeout(*artifacts)


def test_table_omission_or_malformed_rows_do_not_close_docs():
    artifacts = completed_artifacts()
    artifacts[-1].pop()
    with pytest.raises(AssertionError):
        validate_closeout(*artifacts)
    artifacts = completed_artifacts()
    artifacts[-1][0]['rows'][0].append('unexpected column')
    with pytest.raises(AssertionError):
        validate_closeout(*artifacts)


def test_section_update_preserves_adjacent_historical_evidence():
    text = '# State\n\n## Current\n\nstale\n\n## History\n\nraw evidence\n'
    updated = section(text, 'Current', 'complete')
    assert updated == '# State\n\n## Current\n\ncomplete\n\n## History\n\nraw evidence\n'
    assert section(updated, 'History', 'preserved') == '# State\n\n## Current\n\ncomplete\n\n## History\n\npreserved\n'


def test_ambiguous_document_markers_stop_instead_of_replacing_other_stage():
    with pytest.raises(AssertionError):
        replace_between('begin old end begin other end', 'begin', 'end', 'new')
    with pytest.raises(AssertionError):
        section('## Current\n\na\n## Current\n\nb', 'Current', 'new')
