"""A retained screen must cover all conditions without copying old runs."""
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from scripts.stage7a_bench import completed_screen_v6 as loader
from scripts.stage7a_bench.tests.test_reviewed_units_v5 import bundle


@pytest.fixture
def screen_fixture(monkeypatch):
    actual = Path(__file__).resolve().parents[3]
    with TemporaryDirectory(dir=actual / 'outputs/stage7a_bench_v2/audit') as temporary:
        root = Path(temporary)
        out = root / 'outputs/stage7a_bench_v2'
        monkeypatch.setattr(loader, 'ROOT', root)
        monkeypatch.setattr(loader, 'OUT', out)

        def save(name, value, lines=False):
            p = out / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(''.join(json.dumps(v)+'\n' for v in value) if lines else json.dumps(value))
            return str(p.relative_to(root))

        data = bundle()
        data['row']['image_path'] = 'frozen_image.png'
        data['meta'].update(image_path='frozen_image.png', visual_token_indices=[0])
        manifest = save('cohort/benchmark_manifests/photo.jsonl', [data['row']], True)
        digest = loader.sha(root / manifest)
        data['review']['manifest_sha256'] = digest
        run = 'shard0'
        base = f'native_screen/generations/{run}/examples/e0/'
        for name, value in [('input', data['meta']), ('generation', data['generation']),
                            ('manifest_row', data['row'])]:
            save(base+name+'.json', value)
        save(base+'tokens.jsonl', data['tokens'], True)
        for name in ('generation', 'tokens'):
            suffix = '.jsonl' if name == 'tokens' else '.json'
            h = loader.sha(out / (base+name+suffix))
            data['result'][name+'_sha256'] = data['review'][name+'_sha256'] = h
        save(base+'result.json', data['result'])
        save(f'native_screen/generations/{run}/signature.json',
             dict(manifests={manifest:digest}, event_ids=['e0']))
        save(f'native_screen/generations/{run}/run_summary.json',
             dict(completed=True, results=[data['result']]))
        save(f'raw/{run}/run_summary.json', dict(completed=True, exit_code=0))
        review_path = save(f'native_screen/manual_reviews/{run}__photo.jsonl', [data['review']], True)
        freeze = dict(native_screen={'mathvision_wild_photo':dict(manifest=manifest, sha256=digest, count=1)})
        save('cohort/sample_freeze.json', freeze)
        save('audit/native_source_family_integrity.json', dict(status='PASS', native_outputs_read=False,
             causal_scores_read=False, manifest_sha256={manifest:digest}, benchmarks={'mathvision_wild':
             dict(cross_family_identity_conflicts=[], paired_conditions_stay_together=True,
                  per_base_source_family={'b0':'f0'})}))
        bindings = {'photo':dict(manifest=manifest, runs=[dict(native_run_id=run,
                       event_ids=['e0'], review_path=review_path)])}
        yield root, out, bindings, save, freeze


def test_complete_retained_screen_uses_original_shard_and_review(screen_fixture):
    _, _, bindings, _, _ = screen_fixture
    result = loader.load_completed_screen('mathvision_wild', bindings)
    assert result['generated_event_ids'] == ['e0']
    assert result['screen']['photo']['screen_complete'] is True
    assert result['unit_provenance'][0]['native_run_id'] == 'shard0'


@pytest.mark.parametrize('defect', ['missing_review', 'failed_wrapper', 'duplicate_owner',
                                   'wrong_image', 'extra_condition', 'unverified_prefix'])
def test_incomplete_or_unbound_shard_evidence_rejected(screen_fixture, defect):
    root, out, bindings, save, freeze = screen_fixture
    if defect == 'missing_review':
        save('native_screen/manual_reviews/shard0__photo.jsonl', [], True)
    elif defect == 'failed_wrapper':
        save('raw/shard0/run_summary.json', dict(completed=False, exit_code=1))
    elif defect == 'duplicate_owner':
        bindings['photo']['runs'].append(deepcopy(bindings['photo']['runs'][0]))
    elif defect == 'wrong_image':
        path = out / 'native_screen/generations/shard0/examples/e0/input.json'
        meta = json.loads(path.read_text())
        meta['image_path'] = 'other_image.png'
        path.write_text(json.dumps(meta))
    elif defect == 'extra_condition':
        bindings['screenshot'] = deepcopy(bindings['photo'])
    else:
        bindings['photo']['runs'][0]['preserved_prefix'] = dict(path='outside.json', sha256='bad')
    with pytest.raises(ValueError):
        loader.load_completed_screen('mathvision_wild', bindings)


@pytest.mark.parametrize('benchmark', ['mathsight', 'microvqa', 'medxpertqa_mm', 'charxiv', 'phantom_0'])
def test_completed_or_deferred_benchmark_not_admitted_to_retained_loader(benchmark):
    with pytest.raises(ValueError):
        loader.load_completed_screen(benchmark, {})


def change_row(fixture, mutation):
    root, out, bindings, save, freeze = fixture
    base = 'native_screen/generations/shard0/examples/e0/'
    row = json.loads((out / (base+'manifest_row.json')).read_text())
    meta = json.loads((out / (base+'input.json')).read_text())
    mutation(row, meta)
    save(base+'manifest_row.json', row)
    save(base+'input.json', meta)
    manifest = bindings['photo']['manifest']
    (root / manifest).write_text(json.dumps(row)+'\n')
    digest = loader.sha(root / manifest)
    freeze['native_screen']['mathvision_wild_photo']['sha256'] = digest
    save('cohort/sample_freeze.json', freeze)
    save('native_screen/generations/shard0/signature.json',
         dict(manifests={manifest:digest}, event_ids=['e0']))
    rp = out / 'native_screen/manual_reviews/shard0__photo.jsonl'
    review = json.loads(rp.read_text())
    review['manifest_sha256'] = digest
    save('native_screen/manual_reviews/shard0__photo.jsonl', [review], True)
    cp = out / 'audit/native_source_family_integrity.json'
    certificate = json.loads(cp.read_text())
    certificate['manifest_sha256'][manifest] = digest
    save('audit/native_source_family_integrity.json', certificate)


def test_noimage_condition_cannot_retain_visual_tokens(screen_fixture):
    def mutation(row, meta):
        row.pop('image_path')
        meta.pop('image_path')
        row['no_image'] = meta['no_image'] = True
    change_row(screen_fixture, mutation)
    with pytest.raises(ValueError, match='no-image'):
        loader.load_completed_screen('mathvision_wild', screen_fixture[2])


def test_document_must_preserve_all_physical_pages(screen_fixture):
    def mutation(row, meta):
        row.pop('image_path')
        meta.pop('image_path')
        row.update(document_path='document.pdf', document_sha256='doc',
                   renderer_version='frozen', render_scale=1.0, page_count=2)
        meta.update({k:row[k] for k in ('document_path', 'document_sha256',
                                       'renderer_version', 'render_scale')})
        meta['visual_images'] = [dict(physical_page=1)]
    change_row(screen_fixture, mutation)
    with pytest.raises(ValueError, match='physical page'):
        loader.load_completed_screen('mathvision_wild', screen_fixture[2])


def test_frozen_unavailable_input_preserves_missingness_without_semantic_review(screen_fixture):
    def mutation(row, meta):
        row['preflight_status'] = 'missing_input'
    change_row(screen_fixture, mutation)
    _, out, bindings, save, _ = screen_fixture
    base = 'native_screen/generations/shard0/examples/e0/'
    result = json.loads((out / (base+'result.json')).read_text())
    result.update(unavailable=True, unavailable_reason='missing_input')
    save(base+'result.json', result)
    save('native_screen/generations/shard0/run_summary.json', dict(completed=True, results=[result]))
    save('native_screen/manual_reviews/shard0__photo.jsonl', [], True)
    report = loader.load_completed_screen('mathvision_wild', bindings)
    assert report['screen']['photo']['unavailable'] == 1
    assert report['screen']['photo']['reviewed'] == 0
    assert report['screen']['photo']['final_accuracy']['value'] is None
    assert report['generated_event_ids'] == []


def test_omitted_frozen_paired_condition_is_incomplete(screen_fixture):
    _, _, bindings, save, freeze = screen_fixture
    freeze['native_screen']['mathvision_wild_screenshot'] = deepcopy(
        freeze['native_screen']['mathvision_wild_photo'])
    save('cohort/sample_freeze.json', freeze)
    with pytest.raises(ValueError, match='All frozen'):
        loader.load_completed_screen('mathvision_wild', bindings)
