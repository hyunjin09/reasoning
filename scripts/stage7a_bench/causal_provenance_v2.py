"""Bind a reviewed causal candidate to exact frozen native evidence.

Loading a candidate does not admit or freeze a pilot. The immutable per-review
digest permits other native reviews to be appended without invalidating this
candidate; changing this review requires renewing its source annotation.
"""
import hashlib
import json
from pathlib import Path

from scripts.stage7a.common import ROOT, read_json, read_jsonl, sha
from scripts.stage7a_bench.causal_events_v2 import compile_event
from scripts.stage7a_bench.image_semantic_reviews_v2 import validate_judgment
from scripts.stage7a_bench.source_value_policy_v2 import numeric_replacement

OUT = ROOT / 'outputs/stage7a_bench_v2'


def object_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def verify_native_evidence(row, meta, generation, tokens, result, review, annotation, hashes):
    if result.get('unavailable'):
        raise ValueError('An unavailable input has no native claim')
    for evidence in (result, review):
        if any(evidence.get(k) != row[k] for k in ('event_id', 'base_id', 'benchmark', 'condition')):
            raise ValueError('Native result/review identity mismatch')
    if (any(meta.get(k) != row[k] for k in ('event_id', 'condition', 'prompt', 'no_image')) or
            (meta.get('image_assets') or []) != (row.get('image_assets') or []) or
            row.get('image_path') and meta.get('image_path') != row['image_path']):
        raise ValueError('Native input differs from frozen prompt/source identity')
    if row.get('document_path') and (any(meta.get(k) != row[k] for k in
            ('document_path', 'document_sha256', 'renderer_version', 'render_scale')) or
            len(meta.get('visual_images', [])) != row['page_count'] or
            [p.get('physical_page') for p in meta['visual_images']] != list(range(1, row['page_count']+1))):
        raise ValueError('Native document identity, rendering or complete physical page order mismatch')
    length = len(meta['prompt_token_ids'])
    if meta['prompt_token_count'] != length:
        raise ValueError('Native prompt length mismatch')
    raw = generation['raw_decoded_response']
    if (''.join(t['decoded_token'] for t in tokens) != raw or
            [t['token_id'] for t in tokens] != generation['generated_token_ids'] or
            generation['generated_token_count'] != len(tokens) or result['token_count'] != len(tokens) or
            any(t['token_index'] != i or t['generation_position'] != length+i
                for i, t in enumerate(tokens))):
        raise ValueError('Native generated text, token IDs, or positions disagree')
    if (any(result.get(k+'_sha256') != hashes[k] or review.get(k+'_sha256') != hashes[k]
            for k in ('generation', 'tokens')) or review.get('manifest_sha256') != hashes['manifest']):
        raise ValueError('Result/review native artifact hash mismatch')
    if review.get('truncation') != result['truncated']:
        raise ValueError('Review truncation differs from native outcome')
    if (review.get('causal_or_passive_scores_used') is not False or
            annotation.get('causal_or_passive_scores_used') is not False or
            review.get('causal_state') is not None or review.get('eligible_causal_event') is not None):
        raise ValueError('Candidate semantics must precede causal scores/labels')
    if (annotation.get('event_id') != row['event_id'] or
            annotation.get('native_input_sha256') != hashes['input'] or
            annotation.get('semantic_review_sha256') != object_sha(review) or
            any(annotation.get(k+'_sha256') != hashes[k] for k in ('generation', 'tokens'))):
        raise ValueError('Source annotation is not bound to the current input and semantic review')
    # Revalidate semantic assertions and recompute spans; recorded offsets may
    # not silently point to a different repetition of the same literal.
    judgment = {k: v for k, v in review.items() if k not in
        ('causal_state', 'eligible_causal_event', 'manifest_sha256', 'generation_sha256')}
    validated = validate_judgment(judgment, raw)
    if validated['claims'] != review['claims']:
        raise ValueError('Recorded native claim span differs from the reviewed quote')


def stage_path(name, subdirectory):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(OUT / subdirectory):
        raise ValueError('Artifact outside its active-stage directory: ' + str(name))
    return path


def verified_families(certificate, manifest_key, manifest_hash, benchmark):
    if (certificate.get('status') != 'PASS' or
            certificate.get('manifest_sha256', {}).get(manifest_key) != manifest_hash or
            certificate.get('causal_scores_read') is not False or
            certificate.get('native_outputs_read') is not False):
        raise ValueError('Family audit does not certify this frozen native manifest')
    record = certificate['benchmarks'][benchmark]
    if record['cross_family_identity_conflicts'] or record['paired_conditions_stay_together'] is not True:
        raise ValueError('Family grouping has unresolved identity/condition conflicts')
    return record['per_base_source_family']


def verify_numeric_values(annotation):
    bounds = annotation['source_domain_review']
    candidates = annotation['candidates']
    replacement = numeric_replacement(annotation['target_ground_truth'],
        lower=bounds['lower'], upper=bounds['upper'])
    expected = dict(correct=annotation['target_ground_truth'], foil=replacement, target_semantic=replacement)
    if annotation.get('alternative'):
        other = candidates['alternative_original']
        expected.update(alternative_original=other, alternative_semantic=numeric_replacement(
            other, lower=bounds['lower'], upper=bounds['upper']))
    if candidates != expected:
        raise ValueError('Candidate values differ from the frozen source-only numeric rule')


def load_native_claim(run, manifest, index, review_path, annotation_path, claim_index, tokenizer):
    if Path(run).name != run or run in ('.', '..'):
        raise ValueError('Unsafe native run identity')
    manifest = stage_path(manifest, 'cohort/benchmark_manifests')
    review_path = stage_path(review_path, 'native_screen/manual_reviews')
    annotation_path = stage_path(annotation_path, 'causal_pilot/source_reviews')
    rows = read_jsonl(manifest)
    frozen = read_json(OUT / 'cohort/sample_freeze.json')['native_screen'].values()
    if sum(f['sha256'] == sha(manifest) and f['count'] == len(rows) for f in frozen) != 1:
        raise ValueError('Native manifest is not uniquely frozen')
    if type(index) is not int or not 0 <= index < len(rows):
        raise ValueError('Native index outside frozen manifest')
    row = rows[index]
    if Path(row['event_id']).name != row['event_id'] or row['event_id'] in ('.', '..'):
        raise ValueError('Unsafe native event identity')
    run_path = stage_path(OUT / 'native_screen/generations' / run, 'native_screen/generations')
    directory = stage_path(run_path / 'examples' / row['event_id'], 'native_screen/generations')
    signature = read_json(run_path / 'signature.json')
    manifest_key = str(manifest.relative_to(ROOT))
    if (signature['manifests'].get(manifest_key) != sha(manifest) or
            row['event_id'] not in signature['event_ids']):
        raise ValueError('Native worker signature does not cover the frozen row')
    if read_json(directory / 'manifest_row.json') != row:
        raise ValueError('Native worker row differs from frozen manifest')
    matches = [r for r in read_jsonl(review_path) if r['event_id'] == row['event_id']]
    if len(matches) != 1 or matches[0]['native_index'] != index:
        raise ValueError('Expected exactly one review at the native index')
    review, annotation = matches[0], read_json(annotation_path)
    paths = dict(manifest=manifest, input=directory / 'input.json',
        generation=directory / 'generation.json', tokens=directory / 'tokens.jsonl',
        result=directory / 'result.json', annotation=annotation_path,
        native_signature=run_path / 'signature.json',
        source_family_audit=OUT / 'audit/native_source_family_integrity.json')
    hashes = {k: sha(p) for k, p in paths.items()}
    if annotation.get('source_value_policy'):
        reference = annotation['source_value_policy']
        policy_path = stage_path(reference['path'], 'config')
        if sha(policy_path) != reference['sha256']:
            raise ValueError('Reviewed numeric replacement policy changed')
        policy = read_json(policy_path)
        implementation = (ROOT / policy['implementation_path']).resolve()
        if (not implementation.is_relative_to(ROOT / 'scripts/stage7a_bench') or
                implementation != Path(__file__).with_name('source_value_policy_v2.py').resolve()):
            raise ValueError('Unsupported source-value implementation')
        if (sha(implementation) != policy['implementation_sha256'] or
                policy['status'] != 'FROZEN_BEFORE_BENCHMARK_CAUSAL_SCORES' or
                policy['causal_scores_exist'] is not False or policy['threshold_retuning'] is not False):
            raise ValueError('Source-only numeric rule certificate mismatch')
        verify_numeric_values(annotation)
        paths.update(source_value_policy=policy_path, source_value_implementation=implementation)
        hashes.update({k: sha(paths[k]) for k in ('source_value_policy', 'source_value_implementation')})
    meta, generation = read_json(paths['input']), read_json(paths['generation'])
    tokens, result = read_jsonl(paths['tokens']), read_json(paths['result'])
    verify_native_evidence(row, meta, generation, tokens, result, review, annotation, hashes)
    families = verified_families(read_json(paths['source_family_audit']), manifest_key,
                                hashes['manifest'], row['benchmark'])
    entry = compile_event(row, review, claim_index, meta, tokens, annotation, families, tokenizer)
    entry.update(native_run_id=run, native_index=index, native_truncated=result['truncated'],
        semantic_review=review, semantic_review_sha256=object_sha(review),
        provenance={k: dict(path=str(p.relative_to(ROOT)), sha256=hashes[k]) for k, p in paths.items()},
        compilation_dependencies_sha256={str(p.relative_to(ROOT)): sha(p) for p in
            (Path(__file__), Path(__file__).with_name('causal_events_v2.py'),
             Path(__file__).with_name('causal_readouts_v2.py'),
             Path(__file__).with_name('source_mapping_v2.py'),
             Path(__file__).with_name('source_value_policy_v2.py'),
             Path(__file__).with_name('image_semantic_reviews_v2.py'))},
        native_input=meta, annotation_path=str(annotation_path.relative_to(ROOT)))
    return entry
