from copy import deepcopy
from pathlib import Path

import pytest

from scripts.stage7a_bench import pilot_yield_v2 as module
from scripts.stage7a_bench import native_report_v2
from scripts.stage7a.common import read_json, sha, write_json, write_jsonl


def packet():
    # Two errors share a base; an uncertified Tier2 faithful state is not strong.
    states = [dict(id='a0', event_id='a_native', base_id='a', analysis_family_id='family_a',
                   benchmark='charxiv', pilot_stratum='failure', state='WRONG_SOURCE_READ', tier=1),
              dict(id='a1', event_id='a_native', base_id='a', analysis_family_id='family_a',
                   benchmark='charxiv', pilot_stratum='failure', state='SOURCE_COUPLED_EXTRACTION_ERROR', tier=1),
              dict(id='b0', event_id='b_native', base_id='b', analysis_family_id='family_b',
                   benchmark='charxiv', pilot_stratum='faithful', state='FAITHFUL_READ', tier=2,
                   strong_tier2=False),
              dict(id='c0', event_id='c_native', base_id='c', analysis_family_id='family_c',
                   benchmark='charxiv', pilot_stratum='faithful', state='FAITHFUL_READ', tier=1)]
    entries = [{k:s[k] for k in ('id','event_id','base_id','analysis_family_id','benchmark','pilot_stratum')}
               | dict(readout_type='V') for s in states]
    native = dict(benchmark='charxiv', analysis_family_map={f'base_{i}':f'f{i}' for i in range(200)},
                  verified_generated_event_ids=['a_native','b_native','c_native'],
                  conditions={'image_present':{'native':{'generated':200,'native_elapsed_seconds':3600}}})
    native['analysis_family_map'].update(a='family_a', b='family_b', c='family_c')
    for i in range(3): del native['analysis_family_map'][f'base_{i}']
    compiled = dict(benchmark='charxiv', events=4, native_bases=3, source_families=3,
                    scientific_run_seconds=1800, mechanics_run_seconds=600,
                    native_convergence_reviews={})
    return entries, states, native, compiled


def test_certification_and_repeated_bases_are_counted_separately():
    got = module.summarize(*packet())
    assert got['strong_unfaithful']['events'] == 2
    assert got['strong_unfaithful']['native_bases'] == 1
    assert got['strong_faithful']['events'] == 1
    assert got['uncertified_events'] == 1
    assert got['state_counts']['FAITHFUL_READ']['events'] == 2
    assert got['state_counts']['FAITHFUL_READ']['certified_events'] == 1
    assert got['strong_unfaithful_events_per_100_frozen_native_bases'] == 1
    assert got['strong_unfaithful_bases_per_100_frozen_native_bases'] == .5
    assert got['failure_stratum']['selected_events'] == 2
    assert got['failure_stratum']['strong_unfaithful_fraction'] == 1
    assert got['efficiency']['certified_events_per_scientific_gpu_hour'] == 6
    assert got['annotation_minutes_per_strong_failure'] is None


def test_unresolved_events_remain_in_the_pilot_denominator():
    args = packet()
    args[1][0].update(state='UNRESOLVED', tier=None, candidate_state='SOURCE_ANOMALY')
    got = module.summarize(*args)
    assert got['failure_stratum']['strong_unfaithful_fraction'] == .5
    assert got['candidate_anomaly_events'] == 1
    assert got['state_counts']['UNRESOLVED']['events'] == 1


def test_strong_prior_tier2_is_certified_using_inherited_rule():
    args = packet()
    args[1][0].update(state='PRIOR_FILL', tier=2, strong_tier2=True)
    got = module.summarize(*args)
    assert got['state_counts']['PRIOR_FILL']['certified_events'] == 1
    assert got['strong_unfaithful']['events'] == 2


@pytest.mark.parametrize('change', ['duplicate','swapped_base','missing','not_generated','wrong_family'])
def test_mismatched_or_partial_state_evidence_is_rejected(change):
    args = deepcopy(packet())
    if change == 'duplicate': args[1][1] = deepcopy(args[1][0])
    if change == 'swapped_base': args[1][0]['base_id'] = 'b'
    if change == 'missing': args[1].pop()
    if change == 'not_generated': args[2]['verified_generated_event_ids'].remove('a_native')
    if change == 'wrong_family': args[2]['analysis_family_map']['a'] = 'different'
    with pytest.raises(ValueError):
        module.summarize(*args)


def test_zero_failure_stratum_and_missing_control_cost_are_not_fabricated():
    args = packet()
    for entry, state in zip(args[0], args[1]):
        entry['pilot_stratum'] = state['pilot_stratum'] = 'faithful'
    args[3]['native_convergence_reviews'] = {'a0':{'path':'unread_control_review'}}
    got = module.summarize(*args)
    assert got['failure_stratum']['strong_unfaithful_fraction'] is None
    assert got['efficiency']['complete_pipeline_gpu_hours'] is None
    assert got['efficiency']['native_control_gpu_seconds'] is None


@pytest.fixture
def disk_request(tmp_path, monkeypatch):
    real_root = Path(module.__file__).resolve().parents[2]
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'OUT', tmp_path/'outputs/stage7a_bench_v2')
    monkeypatch.setattr(native_report_v2, 'ROOT', tmp_path)
    for name in ('scripts/stage7a_bench/pilot_yield_v2.py','code/visual_reasoning/stage7a/reporting.py'):
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((real_root/name).read_bytes())
    def put(name, value, lines=False):
        path = module.OUT/name
        (write_jsonl if lines else write_json)(path, value)
        return dict(path=str(path.relative_to(tmp_path)), sha256=sha(path))
    entries, states, native, compiled = packet()
    evidence = put('audit/synthetic_native_evidence.json', {'scope':'Synthetic report test only'})
    native.update(status='COMPLETED_BENCHMARK_NATIVE_REPORT_ONLY', causal_states_assigned=False,
                  primary_benchmark_selected=False, artifact_sha256={evidence['path']:evidence['sha256']})
    native_ref = put('native_screen/reports/synthetic/report.json', native)
    selection = put('causal_pilot/selection_reviews/synthetic.json', {'synthetic':True})
    pilot = put('causal_pilot/frozen/charxiv.json', dict(status='FROZEN_BEFORE_CAUSAL_SCORING',
        benchmark='charxiv', selected_entries=entries, request=selection,
        validation={'completed_screen_receipt':{'artifact_sha256':native['artifact_sha256']}}))
    compiled.update(status='COMPLETED_FROZEN_PILOT_COMPILED', thresholds_retuned=False,
        passive_features_used=False, ranking_selected=False, pilot=pilot, run_id='synthetic_science',
        execution_signature=dict(pilot=pilot, dependencies={}),
        mechanics_certificate=put('causal_pilot/mechanics/charxiv.json', {'synthetic':True}))
    for group in ('raw_run','mechanics'):
        raw = put(f'causal_pilot/raw/{group}/event.json', {'synthetic':True})
        compiled[group] = dict(summary=put(f'causal_pilot/raw/{group}/run_summary.json',
            dict(completed=True, events=[{'event':raw}])),
            wrapper=put(f'causal_pilot/wrappers/{group}.json',dict(completed=True,exit_code=0)))
    compiled['outputs'] = {
        'states':put('causal_pilot/compiled/charxiv/synthetic_science/states.jsonl', states, True),
        'metrics':put('causal_pilot/compiled/charxiv/synthetic_science/metrics.jsonl',
            [dict(id=e['id'],semantic_effects={'T':{}} if i == 3 else {}) for i,e in enumerate(entries)], True),
        'resources':put('causal_pilot/compiled/charxiv/synthetic_science/resources.jsonl',
            [dict(id=e['id'],seconds=1) for e in entries], True)}
    compiled_ref = put('causal_pilot/compiled/charxiv/synthetic_science/compilation.json', compiled)
    request = put('causal_pilot/report_requests/synthetic.json',
                  dict(compilation=compiled_ref, native_report=native_ref))
    return tmp_path/request['path'], evidence, compiled, native_ref


def test_hash_bound_disk_report_exports_without_certifying_weak_controls(disk_request):
    request, *_ = disk_request
    dest = module.export(request)
    result = read_json(dest/'yield.json')
    assert result['strong_faithful']['events'] == 1
    assert result['measured_semantic_control_events'] == {'T':1,'X':0}
    assert result['primary_benchmark_selected'] is False
    assert 'Strong unfaithful: 2 events across 1 native bases' in (dest/'summary.md').read_text()
    with pytest.raises(FileExistsError):
        module.export(request)


@pytest.mark.parametrize('change', ['evidence','state','native','wrapper'])
def test_changed_evidence_prevents_yield_publication(disk_request, change):
    request, evidence, compiled, native_ref = disk_request
    ref = {'evidence':evidence, 'state':compiled['outputs']['states'], 'native':native_ref,
           'wrapper':compiled['raw_run']['wrapper']}[change]
    (module.ROOT/ref['path']).write_text('{}')
    with pytest.raises(ValueError, match='changed'):
        module.export(request)
    assert not (module.OUT/'causal_pilot/reports').exists()
