"""Descriptive yield from a complete immutable causal pilot and native report.

Reuse inherited certification, keep repeated events/bases/families separate,
and report captured yield rather than extrapolating a selected pilot to natural
prevalence. Missing time measurements never become zero-cost evidence.
"""
from collections import Counter
import argparse
import math

from visual_reasoning.stage7a.reporting import certified
from scripts.stage7a_bench.native_yield_v2 import indexed
from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.native_report_v2 import identity, verify_hashes

OUT = ROOT / 'outputs/stage7a_bench_v2'

STATES = ('FAITHFUL_READ', 'PRIOR_FILL', 'WRONG_SOURCE_READ', 'STALE_SOURCE_READ',
          'SOURCE_COUPLED_EXTRACTION_ERROR', 'DOWNSTREAM_INTEGRATION_ERROR',
          'SOURCE_ANOMALY', 'UNRESOLVED')
UNFAITHFUL = set(STATES[1:6])


def summarize(entries, labels, native_report, compilation):
    pool, states = indexed(entries, 'id'), indexed(labels, 'id')
    if not pool or set(pool) != set(states) or len(pool) != compilation['events']:
        raise ValueError('Every frozen pilot event needs exactly one compiled state')
    native_ids = set(native_report['verified_generated_event_ids'])
    families = native_report['analysis_family_map']
    benchmark = compilation['benchmark']
    if benchmark != native_report['benchmark'] or not families:
        raise ValueError('Native report and causal pilot benchmark differ')
    for key, entry in pool.items():
        state = states[key]
        fields = ('event_id', 'base_id', 'analysis_family_id', 'benchmark', 'pilot_stratum')
        if (any(entry[k] != state[k] for k in fields) or entry['benchmark'] != benchmark or
                entry['event_id'] not in native_ids or
                families.get(entry['base_id']) != entry['analysis_family_id'] or
                entry.get('readout_type') != 'V' or
                entry['pilot_stratum'] not in ('failure','faithful') or state['state'] not in STATES or
                state.get('tier') is not None and (type(state['tier']) is not int or state['tier'] not in (1,2))):
            raise ValueError('Compiled state differs from frozen entry or reviewed native source family')
    if (len({e['base_id'] for e in entries}) != compilation['native_bases'] or
            len({e['analysis_family_id'] for e in entries}) != compilation['source_families']):
        raise ValueError('Compiled base/family counts differ from the complete selected pilot')
    for field in ('scientific_run_seconds','mechanics_run_seconds'):
        if type(compilation[field]) not in (int,float) or not math.isfinite(compilation[field]) or compilation[field] <= 0:
            raise ValueError('Positive finite completed-run time required')
    def counts(rows):
        return dict(events=len(rows), native_bases=len({s['base_id'] for s in rows}),
                    source_families=len({s['analysis_family_id'] for s in rows}))
    certified_rows = [s for s in labels if certified(s)]
    bad = [s for s in certified_rows if s['state'] in UNFAITHFUL]
    good = [s for s in certified_rows if s['state'] == 'FAITHFUL_READ']
    failures = [s for s in labels if s['pilot_stratum'] == 'failure']
    bad_failures = [s for s in failures if certified(s) and s['state'] in UNFAITHFUL]
    native_seconds = sum(r['native']['native_elapsed_seconds'] for r in native_report['conditions'].values())
    if type(native_seconds) not in (int,float) or not math.isfinite(native_seconds) or native_seconds <= 0:
        raise ValueError('Positive measured native generation time required')
    science = compilation['scientific_run_seconds']
    mechanics = compilation['mechanics_run_seconds']
    accounted = native_seconds+science+mechanics
    state_counts = {}
    for name in STATES:
        rows = [s for s in labels if s['state'] == name]
        strong = [s for s in rows if certified(s)]
        state_counts[name] = dict(**counts(rows), certified_events=len(strong),
            certified_native_bases=len({s['base_id'] for s in strong}),
            certified_source_families=len({s['analysis_family_id'] for s in strong}))
    return dict(benchmark=benchmark, pilot=counts(labels), state_counts=state_counts,
        certified_events=len(certified_rows), uncertified_events=len(labels)-len(certified_rows),
        candidate_anomaly_events=sum(s.get('candidate_state') == 'SOURCE_ANOMALY' for s in labels),
        strong_unfaithful=counts(bad), strong_faithful=counts(good),
        selected_strata=dict(Counter(s['pilot_stratum'] for s in labels)),
        native_frozen_bases=len(families), native_frozen_source_families=len(set(families.values())),
        strong_unfaithful_events_per_100_frozen_native_bases=100*len(bad)/len(families),
        strong_unfaithful_bases_per_100_frozen_native_bases=100*len({s['base_id'] for s in bad})/len(families),
        strong_faithful_events_per_100_frozen_native_bases=100*len(good)/len(families),
        failure_stratum=dict(selected_events=len(failures), strong_unfaithful_events=len(bad_failures),
            strong_unfaithful_fraction=len(bad_failures)/len(failures) if failures else None,
            denominator='All selected failure events, including unresolved or weak Tier2 outcomes'),
        efficiency=dict(scientific_gpu_seconds=science, mechanics_gpu_seconds=mechanics,
            native_generation_gpu_seconds=native_seconds,
            native_control_gpu_seconds=None if compilation['native_convergence_reviews'] else 0,
            accounted_gpu_hours=accounted/3600,
            certified_events_per_scientific_gpu_hour=3600*len(certified_rows)/science,
            certified_events_per_accounted_gpu_hour=3600*len(certified_rows)/accounted,
            complete_pipeline_gpu_hours=None,
            scope='One assigned GPU per worker. For MMLong, scientific seconds are the sum of two one-GPU worker runtimes, including their per-device mechanics and waits; the initial single-GPU mechanics is separate. Accounted time includes native generation. '
                  'Separate native preflight/other overhead and requested fresh native-control times are not supplied here; '
                  'accounted efficiency can overestimate complete-pipeline efficiency.'),
        annotation_minutes_per_strong_failure=None,
        annotation_time_reason='Reliable per-example annotation time was not recorded',
        scope='Captured certification yield in the frozen selected pilot, divided by all frozen native bases where indicated. '
              'This is not an estimate of natural prevalence or proof that untested/uncertified events lack a causal state. '
              'Repeated claims, native bases and shared source families remain distinct. No primary benchmark is selected.')


def export(request_path):
    request_path = (ROOT/request_path).resolve()
    if not request_path.is_relative_to(OUT/'causal_pilot/report_requests'):
        raise ValueError('Use an active pilot report request')
    hashes = {str(request_path.relative_to(ROOT)):sha(request_path)}
    request = read_json(request_path)

    def reference(ref, directory='', *, lines=False, read=True):
        path = (ROOT/ref['path']).resolve()
        if not path.is_relative_to(OUT/directory):
            raise ValueError('Report artifact outside its active stage directory')
        key, digest = str(path.relative_to(ROOT)), sha(path)
        if digest != ref['sha256'] or key in hashes and hashes[key] != digest:
            raise ValueError('Report artifact changed')
        hashes[key] = digest
        return (read_jsonl(path) if lines else read_json(path)) if read else None

    compilation = reference(request['compilation'], 'causal_pilot/compiled')
    native = reference(request['native_report'], 'native_screen/reports')
    if (compilation.get('status') != 'COMPLETED_FROZEN_PILOT_COMPILED' or
            any(compilation.get(k) is not False for k in ('thresholds_retuned','passive_features_used','ranking_selected')) or
            native.get('status') != 'COMPLETED_BENCHMARK_NATIVE_REPORT_ONLY' or
            native.get('causal_states_assigned') is not False or native.get('primary_benchmark_selected') is not False):
        raise ValueError('Completed compiled pilot and native-only report required')
    pilot = reference(compilation['pilot'], 'causal_pilot/frozen')
    if (pilot.get('status') != 'FROZEN_BEFORE_CAUSAL_SCORING' or
            pilot['benchmark'] != compilation['benchmark'] or
            compilation['execution_signature']['pilot'] != compilation['pilot']):
        raise ValueError('Pilot freeze differs from compiled execution')
    reference(pilot['request'], 'causal_pilot/selection_reviews')
    reference(compilation['mechanics_certificate'], 'causal_pilot/mechanics')
    for group in ('raw_run','mechanics'):
        records = {key:reference(ref) for key,ref in compilation[group].items()}
        if (records['summary'].get('completed') is not True or
                records['wrapper'].get('completed') is not True or
                type(records['wrapper'].get('exit_code')) is not int or records['wrapper']['exit_code'] != 0):
            raise ValueError('Science and mechanics wrappers must complete successfully')
        for event in records['summary']['events']:
            for ref in event.values():
                reference(ref, 'causal_pilot/raw', read=False)
    for ref in compilation['native_convergence_reviews'].values():
        reference(ref, 'causal_pilot/native_control_reviews')
    evidence = pilot['validation']['completed_screen_receipt']['artifact_sha256']
    if any(native['artifact_sha256'].get(k) != v for k,v in evidence.items()):
        raise ValueError('Native report and frozen pilot cover different completed-screen evidence')
    for mapping in (native['artifact_sha256'], compilation['execution_signature']['dependencies']):
        for key, value in mapping.items():
            if key in hashes and hashes[key] != value:
                raise ValueError('Conflicting native/causal provenance')
            hashes[key] = value
    verify_hashes(hashes)
    states = reference(compilation['outputs']['states'], 'causal_pilot/compiled', lines=True)
    metrics = reference(compilation['outputs']['metrics'], 'causal_pilot/compiled', lines=True)
    resources = reference(compilation['outputs']['resources'], 'causal_pilot/compiled', lines=True)
    entries = pilot['selected_entries']
    expected = set(indexed(entries, 'id'))
    if any(set(indexed(rows, 'id')) != expected for rows in (states, metrics, resources)):
        raise ValueError('All compiled metrics, states and resources must cover the frozen pilot')
    result = summarize(entries, states, native, compilation)
    result['measured_semantic_control_events'] = {
        role:sum(role in row['semantic_effects'] for row in metrics) for role in ('T','X')}
    result.update(status='COMPLETED_PILOT_YIELD_ONLY', run_id=compilation['run_id'],
        source_sha256=hashes, reporter_sha256=sha(ROOT/'scripts/stage7a_bench/pilot_yield_v12.py'),
        inherited_certification_sha256=sha(ROOT/'code/visual_reasoning/stage7a/reporting.py'),
        thresholds_retuned=False, primary_benchmark_selected=False)
    dest = (OUT/'causal_pilot/reports'/identity(compilation['run_id'])).resolve()
    if not dest.is_relative_to(OUT/'causal_pilot/reports'):
        raise ValueError('Report destination outside active stage directory')
    if dest.exists():
        raise FileExistsError('Preserve the previous pilot yield report')
    verify_hashes(hashes)
    dest.mkdir(parents=True)
    write_json(dest/'yield.json', result)
    text = [f"# {result['benchmark']} completed causal pilot", '', result['scope'], '',
        '| State | Events | Certified events | Certified native bases |', '|---|---:|---:|---:|']
    text += [f"| {name} | {r['events']} | {r['certified_events']} | {r['certified_native_bases']} |"
             for name,r in result['state_counts'].items()]
    text += ['', f"Strong unfaithful: {result['strong_unfaithful']['events']} events across "
        f"{result['strong_unfaithful']['native_bases']} native bases. Strong faithful: "
        f"{result['strong_faithful']['events']} events across {result['strong_faithful']['native_bases']} bases.", '',
        result['efficiency']['scope'], '', 'Annotation minutes are unavailable. Exact denominators, '
        'efficiency components, control availability and file provenance: [yield.json](yield.json).', '']
    (dest/'summary.md').write_text('\n'.join(text))
    return dest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    print(export(parser.parse_args().request))
