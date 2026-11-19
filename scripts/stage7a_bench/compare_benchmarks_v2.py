"""Assemble raw benchmark dimensions without ranking incomplete evidence.

Completed reports are named explicitly. Structural feasibility, semantic
errors and selected-pilot certification retain their separate denominators.
"""
from collections import Counter
from copy import deepcopy
import math
import argparse

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha, write_json
from scripts.stage7a_bench.native_report_v2 import identity, verify_hashes
from scripts.stage7a_bench.render_native_v2 import report_rows
from scripts.stage7a_bench.render_causal_v2 import report_row

OUT = ROOT / 'outputs/stage7a_bench_v2'


def measured(value, reason):
    return dict(value=deepcopy(value), interpretation=reason)


def fraction(count, total):
    return dict(numerator=count, denominator=total, value=count/total if total else None)


def structural_dimensions(benchmark, source, readouts):
    source = [r for r in source if r['benchmark'] == benchmark]
    readouts = [r for r in readouts if r['benchmark'] == benchmark]
    if not source and not readouts:
        return None
    ids = [{r['example_id'] for r in rows} for rows in (source, readouts)]
    if (len(source) != 64 or len(readouts) != 64 or len(ids[0]) != 64 or ids[0] != ids[1] or
            any(r.get('model_outputs_read') is not False for r in source+readouts) or
            any(r['source_score'] not in ('S0','S1','S2','S3','S4') or
                type(r.get('independent_semantic_edit')) is not bool for r in source) or
            any(r['readout_score'] not in ('R0','R1','R2','R3','R4') or
                type(r.get('error_oriented_ground_truth_available')) is not bool for r in readouts)):
        raise ValueError('Complete matched output-blind source/readout audit required')
    s, r = Counter(x['source_score'] for x in source), Counter(x['readout_score'] for x in readouts)
    return dict(source=dict(distribution=dict(s), S3_S4=fraction(s['S3']+s['S4'],64)),
        readout=dict(distribution=dict(r), R3_R4=fraction(r['R3']+r['R4'],64),
            error_oriented_ground_truth=fraction(sum(x['error_oriented_ground_truth_available'] for x in readouts),64)),
        editable=fraction(sum(x['independent_semantic_edit'] for x in source),64))


def comparison_row(candidate, source, readouts, *, native=None, pilot=None, native_condition='image_present'):
    benchmark = identity(candidate['candidate_id'])
    structural = structural_dimensions(benchmark, source, readouts)
    if native is not None and native['benchmark'] != benchmark:
        raise ValueError('Native report benchmark differs from roster')
    if pilot is not None and native is None:
        raise ValueError('A pilot requires its completed native report')
    native_rows = {r['condition']:r for r in report_rows(native)} if native is not None else None
    causal = report_row(pilot, native, source, native_condition=native_condition) if pilot is not None else None
    native_seconds = (sum(r['native']['native_elapsed_seconds'] for r in native['conditions'].values())
                      if native is not None else None)
    paired = ({k:{name:deepcopy(value) for name,value in pair.items() if name != 'paired_evidence'}
               for k,pair in native['paired_conditions'].items()} if native is not None else None)
    dimensions = {
        'A_native': measured(native_rows, 'Completed native conditions only; missing reports are unknown. '
            'Final accuracy, local visual error, binding error and unsupported claims remain distinct.'),
        'B_source_identifiability': measured(structural['source'] if structural else None,
            'Output-blind structural S scores; not causal state certification.'),
        'C_readout_feasibility': measured(structural['readout'] if structural else None,
            'Structural feasibility only; each causal event needs its own exact oriented readout.'),
        'D_counterfactual_editability': measured(dict(structural=structural['editable'],
            measured_pilot_controls=pilot.get('measured_semantic_control_events') if pilot else None) if structural else None,
            'Structural editability is not a completed valid control bank; measured controls refer only to the frozen pilot.'),
        'E_faithful': measured(dict(screening={k:r['metrics']['f0_candidate'] for k,r in native_rows.items()} if native_rows else None,
            certified=causal['strong_faithful'] if causal else None),
            'F0 screening candidates and certified faithful events are different quantities; weak Tier2 is not certified.'),
        'F_causal_failure': measured({k:causal[k] for k in ('pilot','states','strong_unfaithful',
            'unfaithful_events_per_100','unfaithful_bases_per_100','certified_events','uncertified_events')} if causal else None,
            'Captured selected-pilot yield, not population prevalence. Untested or unresolved states are not proven absent.'),
        'G_paired_conditions': measured(paired,
            'Common-base behavioral comparisons only; advantage and causal B-Clean require separate interpretation.'),
        'H_diversity': measured(dict(native_bases=len(native['analysis_family_map']),
            source_families=len(set(native['analysis_family_map'].values())),
            pilot=causal['pilot'] if causal else None) if native else None,
            'Verified source-family counts are distinct from events and bases; they do not prove template independence.'),
        'I_annotation_cost': measured(None, 'Reliable per-example annotation minutes were not recorded.'),
        'J_gpu_cost': measured(dict(native_generation_gpu_seconds=native_seconds,
            pilot_accounting=causal['efficiency'] if causal else None) if native else None,
            'One assigned GPU. Accounted native/pilot time excludes unmeasured overhead; complete-pipeline cost remains unknown.'),
    }
    return dict(benchmark=benchmark, canonical_name=candidate['canonical_name'], tracks=deepcopy(candidate['track']),
        inventory_snapshot={k:candidate.get(k) for k in ('usable','status','reason')}, dimensions=dimensions,
        primary_gate_passed=None, selected=False,
        decision_status='RAW_DIMENSIONS_ONLY; separate Track A/B ranking and feasible-scale judgment remain pending')


def add_phantom_behavior(row, report):
    if (row['benchmark'] != 'phantom_0' or row['dimensions']['A_native']['value'] is not None or
            report.get('status') != 'PHANTOM_PAIRED_SCREEN_COMPLETE_ONLY' or
            report.get('causal_states_assigned') is not False or report.get('primary_benchmark_selected') is not False or
            set(report['conditions']) != {'silent_no_image','explicit_guess'}):
        raise ValueError('Separate completed Phantom behavioral report required')
    values, seconds = {}, 0
    for condition, native in report['conditions'].items():
        if (any(type(native.get(k)) is not int or native[k] != v for k,v in
                dict(frozen=200,generated=200,reviewed=200,unavailable=0,pending_generation=0,pending_review=0).items()) or
                native.get('screen_complete') is not True):
            raise ValueError('Both Phantom conditions must cover all200 frozen responses')
        metrics = {}
        for key, field in dict(final='final_accuracy',local_error='local_visual_error_rate',
                unsupported='unsupported_claim_rate',caveat='abstention_or_caveat_rate',
                guess='guessed_answer_rate',truncation='truncation_rate').items():
            m = native[field]
            if (any(type(m.get(k)) is not int or m[k] < 0 for k in ('numerator','denominator','unknown')) or
                    m['denominator']+m['unknown'] != 200 or m['numerator'] > m['denominator'] or
                    (m['denominator'] == 0 and m['value'] is not None) or
                    (m['denominator'] > 0 and (type(m['value']) not in (int,float) or
                     not math.isclose(m['value'],m['numerator']/m['denominator']))) or
                    key in ('final','local_error') and m['denominator'] != 0):
                raise ValueError('Phantom rates must preserve unknown factual correctness')
            metrics[key] = deepcopy(m)
        elapsed = native['native_elapsed_seconds']
        if type(elapsed) not in (int,float) or not math.isfinite(elapsed) or elapsed <= 0:
            raise ValueError('Positive measured native time required')
        seconds += elapsed
        values[condition] = dict(frozen=200,generated=200,unavailable=0,metrics=metrics)
    pair = report['paired_comparison']
    if pair['paired_reviewed'] != 200 or len(set(pair['paired_base_ids'])) != 200 or pair.get('causal_label') is not None:
        raise ValueError('Phantom requires200 common behavioral pairs without causal labels')
    dims = row['dimensions']
    dims['A_native'] = measured(values, 'No-image behavior; no factual image answer or local factual error is adjudicable.')
    dims['E_faithful'] = measured(None, 'No visual source exists for faithful-read controls.')
    dims['F_causal_failure'] = measured(None, 'Unsupported behavioral claims do not certify source-null causality or PRIOR_FILL.')
    dims['G_paired_conditions'] = measured(dict(comparison={k:v for k,v in pair.items() if k != 'paired_evidence'},
        class_transitions=report['class_transitions']), 'Same200 questions, silent versus explicit no-image; behavioral only.')
    dims['H_diversity'] = measured(dict(native_bases=200,source_families=None,categories=report['family_categories']),
        'Question categories are not independent source images or proof of template independence.')
    dims['J_gpu_cost'] = measured(dict(native_generation_gpu_seconds=seconds,pilot_accounting=None),
        'Measured native generation only; no source-causal pilot or complete-pipeline timing.')


def export(request_path):
    request_path = (ROOT/request_path).resolve()
    if not request_path.is_relative_to(OUT/'analysis/comparison_requests'):
        raise ValueError('Use an active comparison request')
    request = read_json(request_path)
    hashes = {str(request_path.relative_to(ROOT)):sha(request_path)}

    def remember(mapping):
        for key,digest in mapping.items():
            if key in hashes and hashes[key] != digest:
                raise ValueError('Conflicting comparison provenance')
            hashes[key] = digest

    def ref(record, directory, *, lines=False):
        path = (ROOT/record['path']).resolve()
        if not path.is_relative_to(OUT/directory):
            raise ValueError('Comparison source outside its required directory')
        if sha(path) != record['sha256']:
            raise ValueError('Comparison source changed')
        remember({str(path.relative_to(ROOT)):record['sha256']})
        return read_jsonl(path) if lines else read_json(path)

    roster = ref(request['roster'],'config')
    inventory = ref(request['inventory'],'cohort')['candidates']
    ids = [c['candidate_id'] for c in roster]
    available = {c['candidate_id']:c for c in inventory}
    if len(ids) != len(set(ids)) or len(available) != len(inventory) or set(ids) != set(available):
        raise ValueError('Inventory must cover every unique approved candidate')
    source = ref(request['source'],'structural_audit',lines=True)
    readouts = ref(request['readouts'],'structural_audit',lines=True)
    reports = {}
    for pair in request['reports']:
        native = ref(pair['native_report'],'native_screen/reports')
        benchmark = native['benchmark']
        if benchmark not in ids or benchmark in reports or benchmark == 'phantom_0':
            raise ValueError('Reports require distinct roster benchmarks; Phantom uses its separate report')
        remember(native['artifact_sha256'])
        pilot = ref(pair['pilot_yield'],'causal_pilot/reports') if pair.get('pilot_yield') else None
        if pilot:
            nref = pair['native_report']
            if pilot['source_sha256'].get(nref['path']) != nref['sha256']:
                raise ValueError('Pilot yield refers to a different native report')
            remember(pilot['source_sha256'])
        reports[benchmark] = dict(native=native,pilot=pilot,native_condition=pair.get('native_condition','image_present'))
    rows = [comparison_row({**c,**{k:available[c['candidate_id']].get(k) for k in ('usable','status','reason')}},
                           source,readouts,**reports.get(c['candidate_id'],{})) for c in roster]
    if request.get('phantom_report'):
        phantom = ref(request['phantom_report'],'mirage_prior_track')
        row = next(r for r in rows if r['benchmark'] == 'phantom_0')
        add_phantom_behavior(row,phantom)
        remember(phantom['source_sha256'])
        raw = phantom['raw_provenance']
        if len(raw) != 400 or len({r['event_id'] for r in raw}) != 400:
            raise ValueError('Complete Phantom raw provenance required')
        base = OUT/'native_screen/generations/phantom_native_01'
        for r in raw:
            event = identity(r['event_id'])
            if r.get('no_image_verified') is not True:
                raise ValueError('Phantom input must be verified no-image')
            for filename,key in [('input.json','input_sha256'),('result.json','result_sha256'),
                                 ('generation.json','generation_sha256'),('tokens.jsonl','tokens_sha256')]:
                remember({str((base/'examples'/event/filename).relative_to(ROOT)):r[key]})
        for path in (base/'run_summary.json',OUT/'raw/phantom_native_01/run_summary.json'):
            record = read_json(path)
            if record.get('completed') is not True or ('exit_code' in record and record['exit_code'] != 0):
                raise ValueError('Phantom native run and wrapper must complete')
            remember({str(path.relative_to(ROOT)):sha(path)})
        environment = base/'environment.json'
        if read_json(environment) != phantom['model_environment']:
            raise ValueError('Phantom recorded model environment changed')
        remember({str(environment.relative_to(ROOT)):sha(environment)})
    verify_hashes(hashes)
    dest = OUT/'analysis/comparison_batches'/identity(request['comparison_id'])
    if dest.exists():
        raise FileExistsError('Preserve the previous comparison snapshot')
    result = dict(status='RAW_COMPARISON_SNAPSHOT_ONLY',rows=rows,
        track_members={t:[r['benchmark'] for r in rows if t in r['tracks']] for t in ('A','B')},
        artifact_sha256=hashes,reporter_sha256=sha(__file__),
        primary_benchmark_selected=False,rankings_assigned=False,population_prevalence_estimated=False,
        scope='All approved candidates are retained in roster order, not ranked. Missing native or causal reports remain '
              'unknown. This descriptive snapshot does not complete the sweep, primary gate or next-stage recommendation.')
    verify_hashes(hashes)
    dest.mkdir(parents=True)
    write_json(dest/'benchmark_comparison.json',result)
    return dest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--request',required=True)
    print(export(parser.parse_args().request))
