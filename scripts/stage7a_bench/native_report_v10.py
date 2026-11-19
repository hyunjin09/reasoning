"""Export completed MMLong native review without rescoring historical evidence."""
import argparse

from scripts.stage7a.common import ROOT, read_json, sha
from scripts.stage7a_bench.completed_screen_v10 import OUT, load_completed_screen
from scripts.stage7a_bench.native_report_v2 import dimension_summary, identity, write_report


def build_report(request_path):
    request_path = (ROOT / request_path).resolve()
    if not request_path.is_relative_to(OUT / 'native_screen/report_requests'):
        raise ValueError('Report request outside active stage')
    request = read_json(request_path)
    if (request.get('status') != 'NATIVE_REPORT_REQUEST' or
            request.get('benchmark') != 'mmlongbench_doc' or
            request.get('causal_or_passive_scores_used') is not False):
        raise ValueError('Explicit MMLong native-only request required')
    identity(request['report_id'])
    receipt = load_completed_screen('mmlongbench_doc', request['bindings'])
    reviews = receipt['reviews']['image_present']
    hashes = receipt['artifact_sha256']
    hashes[str(request_path.relative_to(ROOT))] = sha(request_path)
    for name in ('native_report_v10.py', 'completed_screen_v10.py', 'native_report_v2.py',
                 'native_yield_v2.py', 'reviewed_units_v5.py', 'causal_provenance_v2.py'):
        p = ROOT / 'scripts/stage7a_bench' / name
        hashes[str(p.relative_to(ROOT))] = sha(p)
    wrappers = receipt['wrappers']
    wrapper_seconds = sum(w['elapsed_wall_seconds'] for w in wrappers.values())
    return dict(status='COMPLETED_BENCHMARK_NATIVE_REPORT_ONLY',
        report_id=request['report_id'], benchmark='mmlongbench_doc',
        conditions={'image_present': dict(native=receipt['screen']['image_present'],
            dimensions=dimension_summary(reviews),
            reviewed_unique_bases=len({r['base_id'] for r in reviews}),
            reviewed_unique_families=len({receipt['family_map'][r['base_id']] for r in reviews}))},
        paired_conditions={}, native_runs=receipt['native_runs'], artifact_sha256=hashes,
        verified_generated_event_ids=receipt['generated_event_ids'],
        analysis_family_map=receipt['family_map'], unit_provenance=receipt['unit_provenance'],
        original_artifact_owners=receipt['artifact_owners'],
        cost_accounting=dict(unique_wrapper_runs=list(wrappers),
            wrapper_gpu_hours=wrapper_seconds/3600,
            successful_native_outer_gpu_hours=receipt['screen']['image_present']['native_elapsed_seconds']/3600,
            approximate_review_elapsed_minutes=135,
            scope='One GPU per native wrapper; sum each v8/v9 wrapper once. '
                  'Includes startup, mechanics and OOM work; excludes idle allocation time and earlier release diagnostics. '
                  'Review elapsed minutes are agent session time, not measured per-example human labor.'),
        causal_states_assigned=False, pilot_selected=False, primary_benchmark_selected=False,
        scope='All200 frozen document rows retained:190 fully reviewed responses and10 source/resource exclusions. '
              'Original v8 output owners and v9 continuation wrappers are explicitly verified. '
              'Final accuracy, local claims, binding errors, caps and unknown judgments remain separate. '
              'Incidental page/label errors are included in semantic rates but do not automatically enter a pilot. '
              'F0 controls and F1/F2 failures are screening candidates, not causal states. '
              'Source geometry, fresh singleton demand and oriented error readouts require separate review.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    print(write_report(build_report(parser.parse_args().request)))
