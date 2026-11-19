from copy import deepcopy
import weakref

import numpy as np
import pytest
import torch

from scripts.stage7a_bench import causal_execution_v12 as execution


def install(monkeypatch, fault=None, document=False):
    meta = dict(event_id='chart', condition='image_present', no_image=False,
        prompt='Question', prompt_token_ids=[1, 2, 3, 4],
        visual_token_indices=[2, 3], image_grid_thw=[1, 2, 4])
    entry = dict(id='chart__e00', event_id='chart', base_id='chart', benchmark='charxiv',
        condition='image_present', causal_pilot_frozen=True, pilot_stratum='failure',
        selection_used_causal_or_passive_scores=False, native_input=meta,
        row=dict(event_id='chart', prompt='Question', no_image=False,
                 **({'document_path':'frozen.pdf'} if document else {})),
        event=dict(history_before_ed_token_ids=[7]*12), source_groups={'G':[2, 3]},
        source_annotation={'sources':{}}, analysis_family_id='source_family')
    state = dict(prepared=[], roots=[], calls=[])

    def prepare(processor, row, device):
        assert row is entry['row']
        pixels = torch.zeros(2, 3)
        state['prepared'].append(weakref.ref(pixels))
        changed = deepcopy(meta)
        if fault == 'metadata': changed['prompt_token_ids'][0] = 9
        return {'pixel_values':pixels}, changed

    def make_root(model, prepared, row, event):
        assert event is entry['event'] and row is entry['row']
        root = type('Root', (), {})()
        state['roots'].append(weakref.ref(root))
        return root, {'canonical_assay_attention_restored':True}

    def sources(model, root, candidate, *, mechanics):
        assert all(ref() is None for ref in state['prepared'])
        state['calls'].append(('sources', mechanics))
        if fault == 'source_exception': raise RuntimeError('source failed')
        return dict(arms={'N':{'finite':True}, 'G_W2':{'finite':True}},
            distributions={'N':np.array([.1, .9])},
            checks={'all_finite':fault != 'source_check'}, passive_features_collected=False)

    def controls(model, processor, candidate, native, device):
        assert native == meta
        assert all(ref() is None for ref in state['prepared'] + state['roots'])
        state['calls'].append(('controls', None))
        if fault == 'control_exception': raise RuntimeError('control failed')
        return dict(controls={'T_sham':{'finite':True}, 'T_semantic':{'finite':True}},
            distributions={'T_sham':np.array([.2, .8])}, control_audits={'T_sham':{}},
            control_provenance={'status':'REVIEWED_LOCAL_CONTROLS_VERIFIED'},
            semantic_controls_available=True,
            checks={'local_controls_all_finite':fault != 'control_check'},
            passive_features_collected=False)

    def wrong_prepare(*args): raise AssertionError('Wrong image/document loader')
    monkeypatch.setattr(execution, 'prepare_document', prepare if document else wrong_prepare)
    monkeypatch.setattr(execution, 'prepare_image', wrong_prepare if document else prepare)
    monkeypatch.setattr(execution, 'map_source_boxes', lambda m, s: {'groups':entry['source_groups']})
    monkeypatch.setattr(execution, 'make_benchmark_root', make_root)
    monkeypatch.setattr(execution, 'score_frozen_sources', sources)
    monkeypatch.setattr(execution, 'score_reviewed_local_controls', controls)
    return entry, state


@pytest.mark.parametrize('document', [False, True])
def test_same_native_input_and_history_release_root_before_controls(monkeypatch, document):
    entry, state = install(monkeypatch, document=document)
    original = deepcopy(entry)
    result, distributions = execution.execute_verified_event(None, None, entry, 'cpu', mechanics=True)
    assert entry == original
    assert result['complete'] and result['passive_features_collected'] is False
    assert result['checks']['native_input_exact'] is True
    assert result['fixed_prior_controls']['status'] == 'UNAVAILABLE'
    assert set(distributions) == {'N', 'T_sham'}
    assert state['calls'] == [('sources', True), ('controls', None)]
    assert all(ref() is None for ref in state['prepared'] + state['roots'])


@pytest.mark.parametrize('fault', ['metadata', 'source_check', 'control_check',
                                  'source_exception', 'control_exception'])
def test_failed_native_or_control_checks_never_return_complete(monkeypatch, fault):
    entry, state = install(monkeypatch, fault=fault)
    with pytest.raises((ValueError, RuntimeError)):
        execution.execute_verified_event(None, None, entry, 'cpu', mechanics=True)
    if fault == 'metadata': assert state['calls'] == []
    if fault == 'source_check': assert state['calls'] == [('sources', True)]
    assert all(ref() is None for ref in state['prepared'] + state['roots'])


@pytest.mark.parametrize('field,value', [('causal_pilot_frozen', False),
    ('selection_used_causal_or_passive_scores', True), ('pilot_stratum', 'unselected')])
def test_unfrozen_unselected_or_score_selected_entry_rejected(monkeypatch, field, value):
    entry, state = install(monkeypatch)
    entry[field] = value
    with pytest.raises(ValueError):
        execution.execute_verified_event(None, None, entry, 'cpu', mechanics=True)
    assert state['prepared'] == [] and state['calls'] == []


def test_source_mapping_changed_after_native_reconstruction_is_rejected(monkeypatch):
    entry, state = install(monkeypatch)
    monkeypatch.setattr(execution, 'map_source_boxes', lambda m, s: {'groups':{'G':[2]}})
    with pytest.raises(ValueError, match='mapping'):
        execution.execute_verified_event(None, None, entry, 'cpu', mechanics=True)
    assert state['calls'] == []


@pytest.mark.parametrize('fault', [None, 'failed_check', 'overlap', 'nonfinite'])
def test_prior_controls_are_integrated_only_after_validated_execution(monkeypatch, fault):
    entry, state = install(monkeypatch)
    def prior(model, processor, candidate, native, device):
        assert all(ref() is None for ref in state['prepared'] + state['roots'])
        name = 'N' if fault == 'overlap' else 'fixed_no_image'
        return dict(controls={'fixed_no_image':{'finite':fault != 'nonfinite'}},
            distributions={name:np.array([.3, .7])},
            control_audits={'fixed_no_image':{'fresh_generation':False}},
            provenance={'status':'REVIEWED_FIXED_PRIOR_CONTROLS_VERIFIED'},
            checks={'fixed_prior_inputs_verified':fault != 'failed_check'},
            native_convergence_certified=False, passive_features_collected=False)
    monkeypatch.setattr(execution, 'score_prior_controls', prior)
    if fault:
        with pytest.raises((RuntimeError, ValueError)):
            execution.execute_verified_event(None, None, entry, 'cpu', mechanics=True)
    else:
        result, distributions = execution.execute_verified_event(None, None, entry, 'cpu', mechanics=True)
        assert 'fixed_no_image' in result['controls'] and 'fixed_no_image' in distributions
        assert result['prior_convergence_certified'] is False
        assert result['fixed_prior_controls']['status'] == 'REVIEWED_FIXED_PRIOR_CONTROLS_VERIFIED'
