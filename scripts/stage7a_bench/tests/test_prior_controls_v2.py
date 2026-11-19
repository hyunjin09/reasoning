from copy import deepcopy
from pathlib import Path
import weakref

import numpy as np
from PIL import Image
import pytest
import torch

from scripts.stage7a.common import write_json, write_jsonl, sha
from scripts.stage7a_bench import prior_controls_v2 as prior
from scripts.stage7a_bench import causal_provenance_v2 as provenance
from scripts.stage7a_bench.image_inputs_v2 import describe


def packet(tmp_path):
    def asset(name, pixels, slot='image_1'):
        path = tmp_path / (name + '.png')
        Image.fromarray(pixels).save(path)
        return describe(dict(kind='file', path=str(path), slot=slot), path.read_bytes())

    pixels = np.full((8, 10, 3), 200, dtype=np.uint8)
    native = asset('native', pixels)
    changed = pixels.copy(); changed[2:5, 3:6] = 127
    masked = asset('masked', changed)
    donor = asset('donor', np.full((5, 7, 3), 20, dtype=np.uint8))
    box = dict(slot='image_1', source_size=[10, 8], pixels=[3, 2, 6, 5])
    row = dict(event_id='native__image_present', base_id='native', benchmark='charxiv',
        condition='image_present', prompt='Read the target.', no_image=False,
        image_assets=[native], image_path=None, image_layout='images_first')
    entry = dict(id='native__e00', event_id=row['event_id'], base_id='native',
        benchmark='charxiv', row=row, source_annotation={'sources':{'T':[box]}},
        source_groups={'T':[2], 'G':[2, 3]}, semantic_review_sha256='review-hash',
        provenance={'input':{'sha256':'input-hash'}}, analysis_family_id='family-native',
        causal_pilot_frozen=True, selection_used_causal_or_passive_scores=False,
        event={'history_before_ed_token_ids':[7]*12})
    review = dict(status='MANUALLY_REVIEWED_FIXED_PRIOR_CONTROLS', event_id=entry['event_id'],
        native_input_sha256='input-hash', semantic_review_sha256='review-hash',
        causal_or_passive_scores_used=False, control_outputs_used=False,
        native_assets=[native], target_boxes=[deepcopy(box)], controls={
            'mask':dict(assets=[masked], all_target_encodings_erased=True,
                review_note='All target boxes are erased; alternatives stay intact.'),
            'unrelated':dict(donors=[dict(base_id='donor', donor_slot='image_1', slot='image_1')],
                target_evidence_absent=True, review_note='Donor has no demanded content.'),
            'no_image':dict(review_note='Same question with zero image inputs.')})
    donors = {'donor':dict(base_id='donor', image_assets=[donor])}
    families = {'native':'family-native', 'donor':'family-donor'}
    return entry, review, donors, families


def test_builds_three_real_controls_without_changing_question_or_native(tmp_path):
    args = packet(tmp_path); before = deepcopy(args)
    variants, audit = prior.verify_prior_controls(*args)
    assert args == before
    assert set(variants) == {'fixed_mask', 'fixed_unrelated', 'fixed_no_image'}
    assert all(row['prompt'] == args[0]['row']['prompt'] for row in variants.values())
    assert variants['fixed_no_image']['no_image'] is True
    assert variants['fixed_no_image']['image_assets'] == []
    assert variants['fixed_no_image']['image_path'] is None
    assert variants['fixed_unrelated']['image_assets'][0]['size'] == [7, 5]
    assert audit['mask']['outside_target_exact'] is True
    assert audit['mask']['all_target_pixels_equal_127'] is True
    assert audit['native_convergence_certified'] is False


@pytest.mark.parametrize('fault', ['wrong_event', 'wrong_input', 'wrong_review', 'scores',
    'outputs', 'missing_erasure_review', 'same_family', 'same_pixels', 'wrong_slot',
    'extra_condition', 'changed_question', 'missing_note', 'wrong_target_box'])
def test_corrupt_or_unreviewed_prior_control_is_rejected(tmp_path, fault):
    entry, review, donors, families = packet(tmp_path)
    if fault == 'wrong_event': review['event_id'] = 'other'
    if fault == 'wrong_input': review['native_input_sha256'] = 'changed'
    if fault == 'wrong_review': review['semantic_review_sha256'] = 'changed'
    if fault == 'scores': review['causal_or_passive_scores_used'] = True
    if fault == 'outputs': review['control_outputs_used'] = True
    if fault == 'missing_erasure_review': review['controls']['mask']['all_target_encodings_erased'] = False
    if fault == 'same_family': families['donor'] = families['native']
    if fault == 'same_pixels': donors['donor']['image_assets'] = deepcopy(entry['row']['image_assets'])
    if fault == 'wrong_slot': review['controls']['unrelated']['donors'][0]['slot'] = 'image_2'
    if fault == 'extra_condition': review['controls']['explicit_guess'] = {}
    if fault == 'changed_question': review['controls']['no_image']['prompt'] = 'Guess the answer.'
    if fault == 'missing_note': review['controls']['mask']['review_note'] = ''
    if fault == 'wrong_target_box': review['target_boxes'][0]['pixels'] = [2, 2, 6, 5]
    with pytest.raises(ValueError): prior.verify_prior_controls(entry, review, donors, families)


@pytest.mark.parametrize('fault', ['outside', 'partial', 'wrong_fill'])
def test_mask_requires_exact_full_target_erasure_and_unchanged_outside(tmp_path, fault):
    args = packet(tmp_path); asset = args[1]['controls']['mask']['assets'][0]
    pixels = np.array(Image.open(asset['path']))
    if fault == 'outside': pixels[0, 0] = 10
    if fault == 'partial': pixels[2, 3] = 200
    if fault == 'wrong_fill': pixels[2:5, 3:6] = 128
    Image.fromarray(pixels).save(asset['path'])
    with open(asset['path'], 'rb') as stream:
        args[1]['controls']['mask']['assets'][0] = describe(
            {k:asset[k] for k in ('kind', 'path', 'slot')}, stream.read())
    with pytest.raises(ValueError): prior.verify_prior_controls(*args)


def test_missing_bank_is_explicitly_unavailable():
    variants, receipt = prior.load_prior_controls({'source_annotation':{}})
    assert variants == {} and receipt['status'] == 'UNAVAILABLE'


@pytest.mark.parametrize('fault', [None, 'review', 'manifest', 'family', 'pixels'])
def test_loader_binds_bank_pixels_donors_and_family_certificate(tmp_path, monkeypatch, fault):
    out = tmp_path / 'outputs/stage7a_bench_v2'
    bank = out / 'causal_pilot/prior_controls'; bank.mkdir(parents=True)
    entry, review, donors, families = packet(bank)
    monkeypatch.setattr(provenance, 'ROOT', tmp_path)
    monkeypatch.setattr(provenance, 'OUT', out)
    manifest = out / 'cohort/benchmark_manifests/native.jsonl'
    manifest.parent.mkdir(parents=True)
    write_jsonl(manifest, [entry['row'], donors['donor']])
    manifest_key = str(manifest.relative_to(tmp_path))
    family = out / 'audit/families.json'
    write_json(family, dict(status='PASS', manifest_sha256={manifest_key:sha(manifest)},
        causal_scores_read=False, native_outputs_read=False, benchmarks={'charxiv':dict(
            cross_family_identity_conflicts=[], paired_conditions_stay_together=True,
            per_base_source_family=families)}))
    review_path = bank / 'review.json'; write_json(review_path, review)
    entry['source_annotation']['fixed_prior_control_review'] = dict(
        path=str(review_path.relative_to(tmp_path)), sha256=sha(review_path))
    for name, path in [('manifest', manifest), ('source_family_audit', family)]:
        entry['provenance'][name] = dict(path=str(path.relative_to(tmp_path)), sha256=sha(path))
    corrupt = {'review':review_path, 'manifest':manifest, 'family':family,
               'pixels':Path(review['controls']['mask']['assets'][0]['path'])}
    if fault:
        with corrupt[fault].open('ab') as stream: stream.write(b'changed')
        with pytest.raises(ValueError): prior.load_prior_controls(entry)
    else:
        variants, receipt = prior.load_prior_controls(entry)
        assert len(variants) == 3 and receipt['status'] == 'REVIEWED_FIXED_PRIOR_CONTROLS_VERIFIED'
        assert receipt['review_sha256'] == sha(review_path)


def test_no_image_input_rejects_retained_visual_data_or_changed_question():
    entry = dict(row={'prompt':'Read it.'})
    variant = dict(event_id='event', condition='no_image', no_image=True,
        prompt='Read it.', image_assets=[], image_path=None)
    meta = dict(variant, visual_token_indices=[])
    prior.verify_fixed_input(entry, {}, variant, meta)
    for field, value in [('visual_token_indices', [4]), ('image_path', 'retained.png'),
                         ('image_assets', [{'slot':'image_1'}]), ('prompt', 'Guess it.')]:
        changed = dict(meta, **{field:value})
        with pytest.raises(ValueError): prior.verify_fixed_input(entry, {}, variant, changed)


def test_mask_input_keeps_native_token_geometry_but_unrelated_can_change_size(monkeypatch):
    from scripts.stage7a_bench.tests.test_causal_controls_v2 import packet as local_packet
    entry, native, _ = local_packet()
    native['image_assets'] = [{'slot':'image_1'}]
    variant = dict(entry['row'], event_id='chart__fixed_mask', condition='mask',
        image_assets=[{'slot':'image_1', 'edited':True}])
    changed = dict(deepcopy(native), event_id=variant['event_id'], condition='mask',
                   image_assets=variant['image_assets'])
    monkeypatch.setattr('scripts.stage7a_bench.causal_controls_v2.map_source_boxes',
        lambda m, s:{'groups':entry['source_groups']})
    prior.verify_fixed_input(entry, native, variant, changed)
    changed['prompt_token_ids'][0] = 99
    with pytest.raises(ValueError, match='geometry'):
        prior.verify_fixed_input(entry, native, variant, changed)
    variant['condition'] = changed['condition'] = 'unrelated'
    prior.verify_fixed_input(entry, native, variant, changed)


@pytest.mark.parametrize('fail', [False, True])
def test_fixed_prefix_scoring_releases_each_root_and_never_certifies_native_convergence(monkeypatch, fail):
    entry = dict(causal_pilot_frozen=True, selection_used_causal_or_passive_scores=False,
        event={'history_before_ed_token_ids':[4]*9}, source_groups={'G':[2]},
        row={'prompt':'Question'}, event_id='event')
    variants = {name:{'prompt':'Question', 'condition':name, 'no_image':True}
                for name in ('fixed_mask', 'fixed_no_image')}
    roots, pixels = [], []
    monkeypatch.setattr(prior, 'load_prior_controls', lambda e:(variants, {'status':'VERIFIED'}))
    def prepare(processor, row, device):
        assert all(ref() is None for ref in roots + pixels)
        p = torch.zeros(1); pixels.append(weakref.ref(p))
        return {'pixel_values':p}, {'prompt':'Question', 'no_image':True, 'visual_token_indices':[]}
    def root(model, prepared, row, event):
        assert event is entry['event']
        r = type('Root', (), {})(); roots.append(weakref.ref(r))
        return r, {'canonical_assay_attention_restored':True}
    def score(model, root, event, groups):
        assert all(ref() is None for ref in pixels)
        if fail: raise RuntimeError('score failure')
        return {'finite':True}, np.array([.1, .9])
    monkeypatch.setattr(prior, 'prepare_condition', prepare)
    monkeypatch.setattr(prior, 'make_benchmark_root', root)
    monkeypatch.setattr(prior, 'score_bundle', score)
    monkeypatch.setattr(prior, 'verify_fixed_input', lambda *args:None)
    if fail:
        with pytest.raises(RuntimeError, match='score failure'):
            prior.score_prior_controls(None, None, entry, {}, 'cpu')
    else:
        result = prior.score_prior_controls(None, None, entry, {}, 'cpu')
        assert set(result['controls']) == set(variants)
        assert set(result['distributions']) == set(variants)
        assert result['native_convergence_certified'] is False
        assert result['passive_features_collected'] is False
    assert all(ref() is None for ref in roots + pixels)
