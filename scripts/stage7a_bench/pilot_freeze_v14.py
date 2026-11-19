"""Persist a retained pre-score pilot across verified native worker ownership.

The request names every completed native condition, prepared candidate, full
pool-coverage review, eligibility decision and chosen event. Loading a frozen
pilot rechecks native evidence and recompiles all candidates before exposing
selected entries to the GPU worker. No model is loaded or scored here.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from scripts.stage7a.common import ROOT, read_json, sha
from scripts.stage7a_bench.causal_provenance_v2 import load_native_claim, object_sha
from scripts.stage7a_bench.completed_screen_v10 import load_completed_screen, RETAINED
from scripts.stage7a_bench.pilot_freeze_v13 import dependency_hashes as inherited_dependency_hashes
from scripts.stage7a_bench.control_provenance_v11 import load_reviewed_controls
from scripts.stage7a_bench.native_yield_v2 import indexed
from scripts.stage7a_bench.pilot_selection_v2 import validate_selection
from scripts.stage7a_bench.prior_controls_v11 import load_prior_controls

OUT = ROOT / 'outputs/stage7a_bench_v2'


def stage_file(name, directory):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(OUT / directory):
        raise ValueError('Artifact outside active stage directory: ' + str(name))
    return path


def dependency_hashes():
    result = inherited_dependency_hashes()
    paths = [ROOT / 'scripts/stage7a_bench' / name for name in ('causal_run_v14.py', 'compile_causal_v14.py', 'launch_causal_v14_existing.py', 'queue_worker_causal_v14.py', 'aggregate_causal_pool_v14.py', 'run_causal_v14_tmux.sh', 'causal_execution_v14.py', 'causal_controls_v14.py', 'pilot_freeze_v14.py', 'document_causal_inputs_v14.py')]
    paths.append(OUT / 'config/runtime_node02_two_gpu_v14.json')
    result.update({str(path.relative_to(ROOT)):sha(path) for path in paths})
    return result


def candidate_binding(prepared, bindings, receipt):
    binding = bindings.get(prepared['condition'])
    if not binding:
        raise ValueError('Candidate condition lacks completed native ownership')
    indexed(binding['runs'], 'native_run_id')
    owners = [owner for owner in binding['runs']
              if prepared['event_id'] in owner['event_ids']]
    if len(owners) != 1 or owners[0]['native_run_id'] != prepared['native_run_id']:
        raise ValueError('Prepared candidate has missing, duplicate or foreign native ownership')
    owner = owners[0]
    provenance = indexed(receipt['unit_provenance'])
    if provenance.get(prepared['event_id']) != dict(event_id=prepared['event_id'],
            native_run_id=prepared['native_run_id'], review_path=owner['review_path']):
        raise ValueError('Candidate owner/review differs from the completed native provenance')
    return binding['manifest'], owner['review_path']


def build_selection(request, tokenizer):
    if (request.get('status') != 'REVIEWED_PILOT_SELECTION_REQUEST' or
            request.get('causal_or_passive_scores_used') is not False or
            not isinstance(request.get('selection_review_note'), str) or
            not request['selection_review_note'].strip()):
        raise ValueError('Explicit pre-score selection review is required')
    benchmark = request['benchmark']
    if not isinstance(benchmark, str) or not re.fullmatch('[a-z0-9_]+', benchmark):
        raise ValueError('Unsafe benchmark identity')
    if benchmark not in RETAINED:
        raise ValueError('Only retained remaining benchmarks may enter this pilot adapter')
    receipt = load_completed_screen(benchmark, request['bindings'])
    entries, candidate_files = [], {}
    for reference in request['candidates']:
        path = stage_file(reference['path'], 'causal_pilot/prepared_candidates')
        if sha(path) != reference['sha256']:
            raise ValueError('Prepared candidate file changed')
        prepared = read_json(path)
        manifest, review_path = candidate_binding(prepared, request['bindings'], receipt)
        entry = load_native_claim(prepared['native_run_id'], manifest,
            prepared['native_index'], review_path, prepared['annotation_path'],
            prepared['source_annotation']['claim_index'], tokenizer)
        if object_sha(entry) != object_sha(prepared):
            raise ValueError('Prepared candidate differs from verified native re-compilation')
        entries.append(entry)
        candidate_files[str(path.relative_to(ROOT))] = sha(path)
    pool = indexed(entries, 'id')
    coverage = indexed(request['coverage'])
    if set(coverage) != set(receipt['generated_event_ids']):
        raise ValueError('Coverage review must account for every generated native event')
    covered = []
    for event_id, review in coverage.items():
        if (review.get('causal_or_passive_scores_used') is not False or
                not isinstance(review.get('review_note'), str) or not review['review_note'].strip() or
                not isinstance(review.get('candidate_ids'), list)):
            raise ValueError('Explicit candidate-coverage review or exclusion reason required')
        for key in review['candidate_ids']:
            if key not in pool or pool[key]['event_id'] != event_id:
                raise ValueError('Coverage candidate does not belong to this native event')
            covered.append(key)
    if len(covered) != len(set(covered)) or set(covered) != set(pool):
        raise ValueError('Coverage review must account for every prepared candidate exactly once')
    for review in request['eligibility_decisions']:
        if review.get('eligible') is True and (review.get('fresh_visual_retrieval_demand') is not True or
                not isinstance(review.get('fresh_demand_review_note'), str) or
                not review['fresh_demand_review_note'].strip()):
            raise ValueError('Eligible reads require explicit fresh visual demand review')
    selection = validate_selection(receipt['screen'], receipt['frozen_counts'], entries,
        request['eligibility_decisions'], request['selected_ids'], receipt['family_map'])
    controls, prior_controls = {}, {}
    for entry in selection['selected_entries']:
        _, controls[entry['id']] = load_reviewed_controls(entry)
        _, prior_controls[entry['id']] = load_prior_controls(entry)
    selection.update(completed_screen_receipt=receipt, candidate_files_sha256=candidate_files,
        coverage_review_sha256=object_sha(request['coverage']), reviewed_control_provenance=controls,
        reviewed_prior_control_provenance=prior_controls,
        dependencies_sha256=dependency_hashes())
    seal = read_json(OUT / 'audit/mmlong_scientific_selection_seal_v15.json')
    if sha(ROOT / seal['selection']['path']) != seal['selection']['sha256']:
        raise ValueError('Scientific selection seal changed')
    sealed = read_json(ROOT / seal['selection']['path'])
    current_science = {k:v for k,v in selection.items() if k != 'dependencies_sha256'}
    sealed_science = {k:v for k,v in sealed.items() if k != 'dependencies_sha256'}
    if object_sha(current_science) != object_sha(sealed_science):
        raise ValueError('Runtime rebind changed sealed scientific membership or evidence')
    return selection


def frozen_content(selection):
    validation = deepcopy(selection)
    selected = validation.pop('selected_entries')
    for entry in selected:
        entry['causal_pilot_frozen'] = True
    return dict(validation=validation, selected_entries=selected)


def freeze_pilot(request_path, tokenizer):
    request_path = stage_file(request_path, 'causal_pilot/selection_reviews')
    request = read_json(request_path)
    benchmark = request.get('benchmark')
    if not isinstance(benchmark, str) or not re.fullmatch('[a-z0-9_]+', benchmark):
        raise ValueError('Unsafe benchmark identity')
    destination = stage_file(OUT / 'causal_pilot/frozen/runtime_v14' / (benchmark+'.json'), 'causal_pilot/frozen/runtime_v14')
    if destination.exists():
        raise FileExistsError('Pilot already frozen; do not replace membership: ' + str(destination))
    request_hash = sha(request_path)
    content = frozen_content(build_selection(request, tokenizer))
    if sha(request_path) != request_hash:
        raise ValueError('Selection request changed during verification')
    payload = dict(status='FROZEN_BEFORE_CAUSAL_SCORING', benchmark=benchmark,
        frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        request=dict(path=str(request_path.relative_to(ROOT)),sha256=request_hash), **content)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('x') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    return dict(path=str(destination.relative_to(ROOT)), sha256=sha(destination))


def load_frozen_pilot(reference, tokenizer):
    path = stage_file(reference['path'], 'causal_pilot/frozen/runtime_v14')
    if sha(path) != reference['sha256']:
        raise ValueError('Pilot freeze differs from the launch reference')
    payload = read_json(path)
    if (payload.get('status') != 'FROZEN_BEFORE_CAUSAL_SCORING' or
            path.name != payload.get('benchmark', '')+'.json'):
        raise ValueError('Unrecognized frozen pilot identity')
    request_path = stage_file(payload['request']['path'], 'causal_pilot/selection_reviews')
    if sha(request_path) != payload['request']['sha256']:
        raise ValueError('Selection request changed after freezing')
    request = read_json(request_path)
    if request['benchmark'] != payload['benchmark']:
        raise ValueError('Frozen benchmark differs from selection request')
    rebuilt = frozen_content(build_selection(request, tokenizer))
    if any(object_sha(rebuilt[key]) != object_sha(payload[key]) for key in rebuilt):
        raise ValueError('Frozen pilot evidence, membership or implementation changed')
    return payload
