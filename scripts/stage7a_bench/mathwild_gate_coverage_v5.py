"""Compose the amended96-item interim screen without rewriting native runs."""
from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha
from scripts.stage7a_bench.causal_provenance_v2 import verified_families
from scripts.stage7a_bench.mathwild_gate_v5 import select_gate_rows
from scripts.stage7a_bench.native_yield_v2 import indexed, summarize_condition
from scripts.stage7a_bench.reviewed_units_v5 import ordered_owners, verify_unit

OUT = ROOT / 'outputs/stage7a_bench_v2'


def load_gate_coverage(require_complete=True):
    hashes = {}

    def read(path, lines=False):
        path = (ROOT / path).resolve()
        if not path.is_relative_to(OUT) and not path.is_relative_to(ROOT / 'plan'):
            raise ValueError('Gate evidence is outside stage/plan roots')
        hashes[str(path.relative_to(ROOT))] = sha(path)
        return read_jsonl(path) if lines else read_json(path)

    rules = read(OUT / 'config/mathwild_gate96_rules_v5.json')
    selection = read(rules['selection']['path'])
    if sha(ROOT / rules['selection']['path']) != rules['selection']['sha256']:
        raise ValueError('Frozen gate selection changed')
    manifest = selection['manifest']['path']
    rows = read(manifest, True)
    digest = sha(ROOT / manifest)
    if digest != selection['manifest']['sha256']:
        raise ValueError('MathWild manifest changed')
    frozen = read(OUT / 'cohort/sample_freeze.json')['native_screen']
    if not any(x['sha256'] == digest and x['count'] == len(rows) for x in frozen.values()):
        raise ValueError('MathWild manifest is not in the original sample freeze')
    if rules['gate_review_target'] != 96 or rules['primary_event_ids'] != [r['event_id'] for r in rows[:96]]:
        raise ValueError('Gate must cover exactly the first96 frozen primary photos')
    # This revalidates all original completed bundles, their immutable prefix,
    # authority hashes and all four disjoint shard memberships without scoring.
    select_gate_rows(ROOT, rows, selection, selection['shards'][0]['run_id'])
    packet = read(selection['continuation']['path'])
    old_run = packet['predecessor_run_id']
    ownership = {old_run: packet['completed_event_ids']}
    ownership.update({x['run_id']: x['event_ids'] for x in selection['shards']})
    owners = ordered_owners(rules['primary_event_ids'], ownership)
    records, labels, completed_runs, review_paths = {}, {}, {}, {}
    for run, ids in ownership.items():
        base = OUT / 'native_screen/generations' / run
        signature = read(base / 'signature.json')
        if signature['manifests'].get(manifest) != digest or not set(ids) <= set(signature['event_ids']):
            raise ValueError('Native signature does not cover its exact selected IDs')
        path = OUT / 'native_screen/manual_reviews' / (run + '__photo.jsonl')
        review_paths[run] = str(path.relative_to(ROOT))
        labels[run] = indexed(read(path, True)) if path.exists() else {}
        if not set(labels[run]) <= set(ids):
            raise ValueError('Review contains an event outside its selected run ownership')
        if run == old_run:
            completed_runs[run] = 'PRESERVED_COMPLETED_PREFIX_OF_INTERRUPTED_RUN'
            continue
        summary_path, wrapper_path = base / 'run_summary.json', OUT / 'raw' / run / 'run_summary.json'
        complete = False
        if summary_path.exists() and wrapper_path.exists():
            summary, wrapper = read(summary_path), read(wrapper_path)
            complete = (summary.get('completed') is True and wrapper.get('completed') is True
                        and type(wrapper.get('exit_code')) is int and wrapper['exit_code'] == 0)
            if complete:
                records[run] = indexed(summary['results'])
                if set(records[run]) != set(ids):
                    raise ValueError('Completed shard results differ from frozen membership')
        completed_runs[run] = 'COMPLETED' if complete else 'INCOMPLETE'
        if require_complete and not complete:
            raise ValueError('Gate coverage incomplete: a registered shard has not completed')
    results, reviews, provenance = [], [], []
    for index, (event_id, run) in enumerate(owners):
        row = rows[index]
        directory = OUT / 'native_screen/generations' / run / 'examples' / event_id
        if not (directory / 'result.json').exists():
            continue
        result = read(directory / 'result.json')
        if read(directory / 'manifest_row.json') != row:
            raise ValueError('Native source/prompt row changed')
        if run in records and result != records[run].get(event_id):
            raise ValueError('Individual native result differs from completed shard summary')
        results.append(result)
        if event_id not in labels[run]:
            continue
        review = labels[run][event_id]
        meta, generation = read(directory / 'input.json'), read(directory / 'generation.json')
        tokens = read(directory / 'tokens.jsonl', True)
        verify_unit(row=row, index=index, manifest_sha256=digest, result=result, review=review,
                    meta=meta, generation=generation, tokens=tokens,
                    generation_sha256=sha(directory / 'generation.json'),
                    tokens_sha256=sha(directory / 'tokens.jsonl'))
        reviews.append(review)
        provenance.append(dict(event_id=event_id, native_run_id=run, review_path=review_paths[run]))
    screen = summarize_condition(rows[:96], results, reviews)
    if require_complete and not screen['screen_complete']:
        raise ValueError('Gate coverage incomplete: all96 frozen IDs require full semantic review')
    certificate = read(OUT / 'audit/native_source_family_integrity.json')
    families = verified_families(certificate, manifest, digest, 'mathvision_wild')
    return dict(status='COMPLETE_INTERIM_COVERAGE' if require_complete else 'PROVISIONAL_INTERIM_COVERAGE',
                screen=screen, run_status=completed_runs, family_map=families,
                reviews=reviews, unit_provenance=provenance, artifact_sha256=hashes,
                gate_decision=None, causal_or_passive_scores_used=False,
                scope='Exact96-primary-item semantic coverage only; not the full264 screen or causal pilot admission')
