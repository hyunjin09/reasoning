from copy import deepcopy

import pytest
import torch

from scripts.stage7a_bench import causal_mechanics_v12 as mechanics
from scripts.stage7a_bench.tests.test_causal_prefix_v2 import fixture


def inputs(document=False):
    model, prepared, event = fixture()
    entry = dict(id='frozen_event', causal_pilot_frozen=True,
        selection_used_causal_or_passive_scores=False,
        row=dict(no_image=False, document_path='test.pdf' if document else None), event=event)
    return model, prepared, entry


@pytest.mark.parametrize('document', [False, True])
def test_full_canonical_and_bounded_prefix_have_identical_all_layer_state(document):
    model, prepared, entry = inputs(document)
    before = deepcopy(prepared)
    result = mechanics.compare_prefix_to_canonical(model, prepared, entry)
    assert result['passed'] and result['all_layer_kv_exact'] and result['logits_exact']
    assert result['actual_gpu_validation'] is False
    assert result['canonical']['layer_count'] == 2
    assert result['canonical']['generated_length'] == 4
    assert result['canonical'] == result['bounded']
    assert all(torch.equal(value, prepared[k]) for k, value in before.items())


@pytest.mark.parametrize('fault', ['kv', 'logits', 'rope'])
def test_any_state_difference_fails_without_approximate_fallback(monkeypatch, fault):
    model, prepared, entry = inputs()
    original = mechanics.make_benchmark_root
    def changed(*args):
        root, audit = original(*args)
        if fault == 'kv': root.cache.layers[-1].values[..., -1, 0] += 1
        if fault == 'logits': root.last_logits[0] += 1
        if fault == 'rope': root.rope_deltas[0, 0] += 1
        return root, audit
    monkeypatch.setattr(mechanics, 'make_benchmark_root', changed)
    with pytest.raises(mechanics.PrefixMechanicsError, match='prefix') as failure:
        mechanics.compare_prefix_to_canonical(model, prepared, entry)
    assert failure.value.evidence['passed'] is False
    assert failure.value.evidence['states']['canonical'] != failure.value.evidence['states']['bounded']


def test_prefill_input_mutation_is_detected(monkeypatch):
    model, prepared, entry = inputs()
    original = mechanics.prefill_condition
    def changed(model, tensors, no_image):
        result = original(model, tensors, no_image)
        tensors['pixel_values'][0, 0] += 1
        return result
    monkeypatch.setattr(mechanics, 'prefill_condition', changed)
    with pytest.raises(mechanics.PrefixMechanicsError, match='input') as failure:
        mechanics.compare_prefix_to_canonical(model, prepared, entry)
    assert failure.value.evidence['original_input'] != failure.value.evidence['changed_input']


def test_unfrozen_candidate_cannot_be_a_mechanics_selection():
    model, prepared, entry = inputs()
    entry['causal_pilot_frozen'] = False
    with pytest.raises(ValueError, match='frozen'):
        mechanics.compare_prefix_to_canonical(model, prepared, entry)
