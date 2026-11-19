"""Completed-screen provenance tests use tiny on-disk native artifacts."""
from copy import deepcopy
import json

import pytest

from scripts.stage7a_bench import completed_screen_v2 as module
from scripts.stage7a_bench.image_semantic_reviews_v2 import BOOLEAN, UNKNOWN_OK
from scripts.stage7a.common import sha


@pytest.fixture
def screen(tmp_path, monkeypatch):
    root = tmp_path
    out = root / 'outputs/stage7a_bench_v2'
    monkeypatch.setattr(module, 'ROOT', root)
    monkeypatch.setattr(module, 'OUT', out)

    def put(path, value, lines=False):
        path = root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text((''.join(json.dumps(x)+'\n' for x in value) if lines else json.dumps(value)))
        return str(path.relative_to(root))

    def get(path):
        return json.loads((root / path).read_text())

    bindings, frozen, families = {}, {}, {}
    for condition, count in [('image_present', 2), ('silent_no_image', 1)]:
        rows, results, reviews = [], [], []
        run = condition + '_run'
        base = 'outputs/stage7a_bench_v2/native_screen/generations/' + run
        for i in range(count):
            row = dict(event_id=f'charxiv_{i}_{condition}', base_id=f'base{i}',
                benchmark='charxiv', condition=condition, prompt='Read the image',
                no_image=condition != 'image_present')
            rows.append(row)
            directory = base + '/examples/' + row['event_id']
            put(directory+'/manifest_row.json', row)
            put(directory+'/input.json', dict(row, prompt_token_count=2, prompt_token_ids=[8, 9]))
            gen = put(directory+'/generation.json', dict(raw_decoded_response='OK',
                generated_token_ids=[1, 2], generated_token_count=2))
            tokens = put(directory+'/tokens.jsonl', [dict(decoded_token=t, token_id=i+1,
                token_index=i, generation_position=i+2) for i, t in enumerate('OK')], True)
            result = dict(row, token_count=2, truncated=False, generation_sha256=sha(root/gen),
                          tokens_sha256=sha(root/tokens), complete=True)
            put(directory+'/result.json', result)
            results.append(result)
            review = dict(row, native_index=i, truncation=False, screen_label='F6',
                claims=[], causal_state=None, eligible_causal_event=None,
                causal_or_passive_scores_used=False, generation_sha256=sha(root/gen),
                tokens_sha256=sha(root/tokens))
            review.update({k: None if k in UNKNOWN_OK else False for k in BOOLEAN})
            review.update({k:'Manual full-response review' for k in ('final_correctness_reason',
                'review_note', 'source_review_note', 'task_quality', 'output_confidence')})
            reviews.append(review)
            families[row['base_id']] = 'family'+str(i)
        manifest = put(f'outputs/stage7a_bench_v2/cohort/benchmark_manifests/{condition}.jsonl', rows, True)
        for review in reviews:
            review['manifest_sha256'] = sha(root/manifest)
        review_path = put(f'outputs/stage7a_bench_v2/native_screen/manual_reviews/{run}.jsonl', reviews, True)
        put(base+'/signature.json', dict(manifests={manifest:sha(root/manifest)},
            event_ids=[r['event_id'] for r in rows]))
        put(base+'/run_summary.json', dict(completed=True, results=results))
        put(f'outputs/stage7a_bench_v2/raw/{run}/run_summary.json', dict(completed=True, exit_code=0))
        frozen[condition] = dict(manifest=manifest, sha256=sha(root/manifest), count=count)
        bindings[condition] = dict(native_run_id=run, manifest=manifest, review_path=review_path)
    put('outputs/stage7a_bench_v2/cohort/sample_freeze.json', dict(native_screen=frozen))
    put('outputs/stage7a_bench_v2/audit/native_source_family_integrity.json', dict(status='PASS',
        manifest_sha256={v['manifest']:v['sha256'] for v in frozen.values()},
        causal_scores_read=False, native_outputs_read=False, benchmarks={'charxiv':dict(
            cross_family_identity_conflicts=[], paired_conditions_stay_together=True,
            per_base_source_family=families)}))
    return bindings, put, get, root


def test_complete_screen_is_rebuilt_from_artifacts(screen):
    bindings, _, _, _ = screen
    record = module.load_completed_screen('charxiv', bindings)
    assert record['frozen_counts'] == {'image_present':2, 'silent_no_image':1}
    assert all(v['screen_complete'] for v in record['screen'].values())
    assert record['family_map'] == {'base0':'family0', 'base1':'family1'}
    assert len(record['artifact_sha256']) > 20


def test_missing_paired_condition_is_rejected(screen):
    bindings, *_ = screen
    with pytest.raises(ValueError, match='Every frozen condition'):
        module.load_completed_screen('charxiv', {'image_present':bindings['image_present']})


@pytest.mark.parametrize('mutation', ['missing_review', 'duplicate_review', 'false_claim',
    'wrong_index', 'wrong_hash', 'causal_label', 'wrong_condition'])
def test_invalid_semantic_coverage_or_provenance_is_rejected(screen, mutation):
    bindings, put, _, root = screen
    path = bindings['image_present']['review_path']
    rows = [json.loads(x) for x in (root/path).read_text().splitlines()]
    if mutation == 'missing_review': rows.pop()
    elif mutation == 'duplicate_review': rows.append(deepcopy(rows[0]))
    elif mutation == 'false_claim': rows[0]['screen_label'] = 'F0'
    elif mutation == 'wrong_index': rows[0]['native_index'] = 1
    elif mutation == 'wrong_hash': rows[0]['tokens_sha256'] = 'wrong'
    elif mutation == 'causal_label': rows[0]['causal_state'] = 'FAITHFUL_READ'
    elif mutation == 'wrong_condition': rows[0]['condition'] = 'silent_no_image'
    put(path, rows, True)
    with pytest.raises(ValueError):
        module.load_completed_screen('charxiv', bindings)


@pytest.mark.parametrize('mutation', ['wrapper_failure', 'science_incomplete', 'result_changed',
    'token_position', 'manifest_row', 'signature'])
def test_native_artifact_failures_are_rejected(screen, mutation):
    bindings, put, get, root = screen
    base = 'outputs/stage7a_bench_v2/native_screen/generations/image_present_run'
    example = base+'/examples/charxiv_0_image_present'
    if mutation == 'wrapper_failure':
        put('outputs/stage7a_bench_v2/raw/image_present_run/run_summary.json', dict(completed=False,exit_code=1))
    elif mutation == 'science_incomplete':
        record = get(base+'/run_summary.json'); record['completed'] = False; put(base+'/run_summary.json',record)
    elif mutation == 'result_changed':
        record = get(example+'/result.json'); record['token_count']=8; put(example+'/result.json', record)
    elif mutation == 'token_position':
        path=example+'/tokens.jsonl'
        rows=[json.loads(x) for x in (root/path).read_text().splitlines()]
        rows[0]['generation_position']=999; put(path, rows, True)
    elif mutation == 'manifest_row':
        record=get(example+'/manifest_row.json');record['prompt']='changed';put(example+'/manifest_row.json',record)
    elif mutation == 'signature':
        record=get(base+'/signature.json');record['event_ids']=[];put(base+'/signature.json',record)
    with pytest.raises(ValueError):
        module.load_completed_screen('charxiv', bindings)


def test_outside_stage_path_is_rejected_before_read(screen):
    bindings, *_ = screen
    bindings['image_present']['review_path']='ACCESS_POLICY.md'
    with pytest.raises(ValueError, match='outside'):
        module.load_completed_screen('charxiv', bindings)
