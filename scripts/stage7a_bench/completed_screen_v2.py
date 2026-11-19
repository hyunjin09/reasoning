"""Load a complete benchmark screen from verified native files, without scoring.

The receipt binds all conditions, individual outcomes, full semantic reviews,
and source families. It certifies recorded coverage and provenance, not the
scientific correctness of a human judgment or causal pilot eligibility.
"""
from pathlib import Path

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha
from scripts.stage7a_bench.causal_provenance_v2 import verified_families
from scripts.stage7a_bench.image_semantic_reviews_v2 import validate_judgment
from scripts.stage7a_bench.native_yield_v2 import indexed, summarize_condition

OUT = ROOT / 'outputs/stage7a_bench_v2'


def load_completed_screen(benchmark, bindings):
    if benchmark == 'phantom_0':
        raise ValueError('Phantom has no visual input for source-causal pilot admission')
    hashes = {}

    def path(name, directory):
        item = (ROOT / name).resolve()
        if not item.is_relative_to(OUT / directory):
            raise ValueError('Artifact outside active stage directory: ' + str(name))
        return item

    def read(item, lines=False):
        hashes[str(item.relative_to(ROOT))] = sha(item)
        return read_jsonl(item) if lines else read_json(item)

    frozen = read(OUT / 'cohort/sample_freeze.json')['native_screen']
    manifests = {}
    for spec in frozen.values():
        manifest = path(spec['manifest'], 'cohort/benchmark_manifests')
        rows = read(manifest, True)
        if sha(manifest) != spec['sha256'] or len(rows) != spec['count'] or not rows:
            raise ValueError('Native manifest no longer matches its freeze')
        if rows[0]['benchmark'] != benchmark:
            continue
        condition = rows[0]['condition']
        if (condition in manifests or any(r['benchmark'] != benchmark or
                r['condition'] != condition for r in rows)):
            raise ValueError('Duplicate or mixed frozen benchmark condition')
        manifests[condition] = (manifest, rows)
    if not manifests or set(bindings) != set(manifests):
        raise ValueError('Every frozen condition requires an explicit native/review binding')
    certificate = read(OUT / 'audit/native_source_family_integrity.json')
    screen, families, generated_ids = {}, None, []
    for condition, (manifest, rows) in manifests.items():
        binding = bindings[condition]
        if path(binding['manifest'], 'cohort/benchmark_manifests') != manifest:
            raise ValueError('Condition binding differs from frozen manifest')
        run = binding['native_run_id']
        if not isinstance(run, str) or Path(run).name != run or run in ('.', '..'):
            raise ValueError('Unsafe native run identity')
        base = path(OUT / 'native_screen/generations' / run, 'native_screen/generations')
        signature = read(base / 'signature.json')
        summary = read(base / 'run_summary.json')
        wrapper = read(path(OUT / 'raw' / run / 'run_summary.json', 'raw'))
        if (summary.get('completed') is not True or wrapper.get('completed') is not True or
                type(wrapper.get('exit_code')) is not int or wrapper['exit_code'] != 0):
            raise ValueError('Science run and registered wrapper must both complete successfully')
        manifest_key = str(manifest.relative_to(ROOT))
        ids = set(indexed(rows))
        if (signature.get('manifests', {}).get(manifest_key) != sha(manifest) or
                not ids <= set(signature.get('event_ids', []))):
            raise ValueError('Native signature does not cover this frozen condition')
        run_results = indexed(summary['results'])
        reviews = read(path(binding['review_path'], 'native_screen/manual_reviews'), True)
        labels = indexed(reviews)
        results = []
        for index, row in enumerate(rows):
            event_id = row['event_id']
            if Path(event_id).name != event_id or event_id in ('.', '..'):
                raise ValueError('Unsafe native event identity')
            directory = path(base / 'examples' / event_id, 'native_screen/generations')
            if read(directory / 'manifest_row.json') != row:
                raise ValueError('Native input row differs from frozen source/prompt')
            result = read(directory / 'result.json')
            if (result != run_results.get(event_id) or any(result.get(k) != row[k]
                    for k in ('event_id', 'base_id', 'benchmark', 'condition'))):
                raise ValueError('Individual native result differs from completed run')
            results.append(result)
            if result.get('unavailable'):
                if row.get('preflight_status', 'ready') == 'ready' or result.get('unavailable_reason') != row['preflight_status']:
                    raise ValueError('Unavailable input lacks its frozen preflight reason')
                continue
            if event_id not in labels:
                raise ValueError('Generated native response lacks a full semantic review')
            review = labels[event_id]
            if (review.get('native_index') != index or any(review.get(k) != row[k]
                    for k in ('event_id', 'base_id', 'benchmark', 'condition')) or
                    review.get('manifest_sha256') != sha(manifest) or
                    review.get('truncation') != result['truncated']):
                raise ValueError('Semantic review identity or truncation mismatch')
            if (review.get('causal_state') is not None or review.get('eligible_causal_event') is not None or
                    review.get('causal_or_passive_scores_used') is not False):
                raise ValueError('Native screen must precede causal interpretation')
            meta = read(directory / 'input.json')
            generation = read(directory / 'generation.json')
            tokens = read(directory / 'tokens.jsonl', True)
            for name in ('generation', 'tokens'):
                ext = '.jsonl' if name == 'tokens' else '.json'
                digest = hashes[str((directory / (name+ext)).relative_to(ROOT))]
                if result.get(name+'_sha256') != digest or review.get(name+'_sha256') != digest:
                    raise ValueError('Generated response/review artifact hash mismatch')
            length = len(meta['prompt_token_ids'])
            if (meta['prompt_token_count'] != length or
                    any(meta.get(k) != row[k] for k in ('event_id', 'condition', 'prompt', 'no_image')) or
                    ''.join(t['decoded_token'] for t in tokens) != generation['raw_decoded_response'] or
                    [t['token_id'] for t in tokens] != generation['generated_token_ids'] or
                    generation['generated_token_count'] != len(tokens) or result['token_count'] != len(tokens) or
                    any(t['token_index'] != i or t['generation_position'] != length+i for i, t in enumerate(tokens))):
                raise ValueError('Native prompt, response or token alignment mismatch')
            judgment = {k:v for k,v in review.items() if k not in
                ('causal_state', 'eligible_causal_event', 'manifest_sha256', 'generation_sha256')}
            if validate_judgment(judgment, generation['raw_decoded_response'])['claims'] != review['claims']:
                raise ValueError('Recorded local-claim offsets differ from full native response')
            generated_ids.append(event_id)
        screen[condition] = summarize_condition(rows, results, reviews)
        if not screen[condition]['screen_complete']:
            raise ValueError('Every frozen condition requires complete generation and semantic review')
        current = verified_families(certificate, manifest_key, sha(manifest), benchmark)
        if families is not None and families != current:
            raise ValueError('Paired conditions have different source-family certificates')
        families = current
    return dict(screen=screen, frozen_counts={k:len(v[1]) for k,v in manifests.items()},
        family_map=families, generated_event_ids=generated_ids, artifact_sha256=hashes,
        scope='Completed native artifacts and explicit semantic coverage; no pilot admission or causal scores')
