from copy import deepcopy
import weakref

import numpy as np
import pytest
import torch

from scripts.stage7a_bench import causal_controls_v2 as controls


def packet():
    meta = dict(event_id='chart', condition='image_present', no_image=False,
        prompt='Question', prompt_token_ids=[1, 2, 3, 4], visual_token_indices=[2, 3],
        image_grid_thw=[1, 2, 4], image_order=['image_1'], visual_images=[dict(
            slot='image_1', image_grid_thw=[1, 2, 4], image_size=[64, 32],
            visual_token_indices=[2, 3], decoded_image_sha256='native')])
    entry = dict(causal_pilot_frozen=True, selection_used_causal_or_passive_scores=False,
        event_id='chart', row=dict(event_id='chart', condition='image_present',
            no_image=False, prompt='Question'), event=dict(history_before_ed_token_ids=[7]*12),
        source_groups=dict(T=[2], X=[3], G=[2, 3]), source_annotation=dict(sources={}))
    variants = {role+'_'+kind: dict(entry['row'], control=role+'_'+kind)
        for role in ('T', 'X') for kind in ('semantic', 'sham')}
    return entry, meta, variants


def install(monkeypatch, *, fault=None):
    entry, meta, variants = packet()
    monkeypatch.setattr(controls, 'load_reviewed_controls', lambda e: (
        deepcopy(variants), dict(status='REVIEWED_LOCAL_CONTROLS_VERIFIED')))
    monkeypatch.setattr(controls, 'map_source_boxes', lambda m, s: dict(groups=entry['source_groups']))
    state = dict(calls=[], prepared=[], roots=[])

    def prepare(processor, row, device):
        assert all(ref() is None for ref in state['prepared'] + state['roots'])
        pixels = torch.zeros(2, 3)
        state['prepared'].append(weakref.ref(pixels))
        changed = deepcopy(meta)
        changed['visual_images'][0]['decoded_image_sha256'] = row['control']
        if fault == 'tokens': changed['prompt_token_ids'][0] = 9
        if fault == 'order': changed['image_order'] = ['image_2']
        if fault == 'size': changed['visual_images'][0]['image_size'][0] = 96
        if fault == 'prompt': changed['prompt'] = 'Different question'
        return dict(pixel_values=pixels), changed

    def root(model, prepared, row, event):
        assert event is entry['event']
        value = type('Root', (), {})()
        value.name = row['control']
        state['roots'].append(weakref.ref(value))
        return value, dict(canonical_assay_attention_restored=True)

    def score(model, root, event, groups):
        assert groups == entry['source_groups'] and event is entry['event']
        assert all(ref() is None for ref in state['prepared'])
        state['calls'].append(root.name)
        return dict(finite=fault != 'nonfinite', name=root.name), np.array([0.1, 0.9])

    monkeypatch.setattr(controls, 'prepare_condition', prepare)
    monkeypatch.setattr(controls, 'make_benchmark_root', root)
    monkeypatch.setattr(controls, 'score_bundle', score)
    return entry, meta, variants, state


def test_controls_preserve_native_history_and_release_each_prefix(monkeypatch):
    entry, meta, variants, state = install(monkeypatch)
    before = deepcopy(entry)
    result = controls.score_reviewed_local_controls(None, None, entry, meta, 'cpu')
    assert set(result['controls']) == set(variants)
    assert set(result['distributions']) == {'T_sham', 'X_sham'}
    assert result['checks']['local_control_input_geometry_exact'] is True
    assert result['checks']['local_controls_all_finite'] is True
    assert result['passive_features_collected'] is False
    assert entry == before
    assert all(ref() is None for ref in state['prepared'] + state['roots'])
    assert len(state['calls']) == 4


@pytest.mark.parametrize('fault', ['tokens', 'order', 'size', 'prompt', 'nonfinite'])
def test_changed_input_or_nonfinite_control_cannot_be_certified(monkeypatch, fault):
    entry, meta, _, state = install(monkeypatch, fault=fault)
    with pytest.raises(ValueError):
        controls.score_reviewed_local_controls(None, None, entry, meta, 'cpu')
    if fault != 'nonfinite': assert state['calls'] == []


@pytest.mark.parametrize('field', ['causal_pilot_frozen', 'selection_used_causal_or_passive_scores'])
def test_unfrozen_or_score_selected_entry_rejected_before_loading(monkeypatch, field):
    entry, meta, _ = packet()
    entry[field] = not entry[field]
    def forbidden(_): raise AssertionError('Should reject before loading controls')
    monkeypatch.setattr(controls, 'load_reviewed_controls', forbidden)
    with pytest.raises(ValueError):
        controls.score_reviewed_local_controls(None, None, entry, meta, 'cpu')


def test_unavailable_edits_remain_explicitly_unavailable(monkeypatch):
    entry, meta, _ = packet()
    monkeypatch.setattr(controls, 'load_reviewed_controls', lambda e: (
        {}, dict(status='UNAVAILABLE', reason='No frozen source-control review')))
    result = controls.score_reviewed_local_controls(None, None, entry, meta, 'cpu')
    assert result['controls'] == result['distributions'] == {}
    assert result['control_provenance']['status'] == 'UNAVAILABLE'
    assert result['semantic_controls_available'] is False


def test_canonical_file_metadata_preserves_single_image_geometry(monkeypatch):
    entry, meta, _ = packet()
    meta['image_size'] = meta['visual_images'][0]['image_size']
    del meta['visual_images'], meta['image_order']
    changed = deepcopy(meta)
    changed['image_path'] = 'reviewed_edit.png'
    changed['decoded_image_sha256'] = 'edited_pixels'
    monkeypatch.setattr(controls, 'map_source_boxes', lambda m, s: dict(groups=entry['source_groups']))
    controls.verify_local_control_geometry(entry, meta, changed)
    changed['image_size'] = [96, 32]
    with pytest.raises(ValueError): controls.verify_local_control_geometry(entry, meta, changed)
