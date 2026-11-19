"""Exact canonical/bounded event-prefix comparison before causal scoring.

Fingerprint one tensor at a time on CPU and release the reference root before
building the bounded root. This avoids retaining two comparison roots on GPU.
The caller must choose a feasible frozen mechanics entry before seeing effects.
"""
import gc
import hashlib

import torch

from scripts.stage7a_bench.causal_prefix_v11 import (
    make_benchmark_root, require_canonical_assay_attention,
)
from visual_reasoning.stage4a.runtime import make_event_root
from visual_reasoning.stage6b.text_interface import prefill_condition


class PrefixMechanicsError(RuntimeError):
    def __init__(self, message, evidence):
        super().__init__(message)
        self.evidence = evidence


def tensor_fingerprint(value):
    if not isinstance(value, torch.Tensor) or not bool(torch.isfinite(value).all()):
        raise ValueError('Prefix mechanics requires finite tensors')
    raw = value.detach().contiguous().cpu().view(torch.uint8).numpy().tobytes()
    return dict(shape=list(value.shape), dtype=str(value.dtype),
        sha256=hashlib.sha256(raw).hexdigest())


def state_fingerprint(root):
    return dict(prompt_length=root.prompt_length, generated_length=root.generated_length,
        sequence_length=root.cache.get_seq_length(), layer_count=len(root.cache.layers),
        logits=tensor_fingerprint(root.last_logits), rope=tensor_fingerprint(root.rope_deltas),
        layers=[dict(keys=tensor_fingerprint(layer.keys), values=tensor_fingerprint(layer.values))
                for layer in root.cache.layers])


@torch.inference_mode()
def compare_prefix_to_canonical(model, prepared, entry):
    if (entry.get('causal_pilot_frozen') is not True or
            entry.get('selection_used_causal_or_passive_scores') is not False):
        raise ValueError('Prefix mechanics requires a frozen pre-score entry')
    if model.training or next(model.parameters()).dtype != torch.bfloat16:
        raise ValueError('Prefix mechanics requires the evaluation BF16 model')
    require_canonical_assay_attention()
    original = {k:tensor_fingerprint(v) for k, v in prepared.items()}
    device = prepared['input_ids'].device
    states, audits = {}, {}
    for name in ('canonical', 'bounded'):
        prefill, root = None, None
        try:
            if name == 'canonical':
                prefill, audit = prefill_condition(model, prepared, entry['row']['no_image'])
                root = make_event_root(model, prefill, entry['event'])
                prefill = None
            else:
                root, audit = make_benchmark_root(model, prepared, entry['row'], entry['event'])
            states[name] = state_fingerprint(root)
            audits[name] = audit
        finally:
            prefill, root = None, None
            gc.collect()
            if device.type == 'cuda':
                torch.cuda.empty_cache()
        require_canonical_assay_attention()
        after = {k:tensor_fingerprint(v) for k, v in prepared.items()}
        if original != after:
            raise PrefixMechanicsError('Canonical/bounded prefix modified the prepared input',
                dict(passed=False, route=name, original_input=original, changed_input=after,
                     states=states, prefill_audits=audits))
    if states['canonical'] != states['bounded']:
        raise PrefixMechanicsError('Canonical/bounded event prefix differs; no tolerance fallback',
            dict(passed=False, states=states, prefill_audits=audits))
    return dict(passed=True, id=entry['id'], canonical=states['canonical'],
        bounded=states['bounded'], prefill_audits=audits, all_layer_kv_exact=True,
        logits_exact=True, rope_exact=True, prepared_input_unchanged=True,
        actual_gpu_validation=device.type == 'cuda' and next(model.parameters()).device.type == 'cuda',
        parameter_dtype=str(next(model.parameters()).dtype),
        model_layers=len(model.model.language_model.layers),
        model_attention_heads=model.config.text_config.num_attention_heads,
        model_hidden_size=model.config.text_config.hidden_size,
        causal_or_passive_scores_used=False,
        scope='Exact tensor SHA256 equality for complete event-root KV, logits, RoPE and coordinates; '
              'no claim that other input sizes or backends were tested')
