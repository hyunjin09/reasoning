"""Dimension-derived Qwen attention assays; never used for native generation.

The capture path reproduces the installed eager attention operations. Scientific
use additionally requires actual-model BF16/no-op and cache-isolation checks.
Fixed-route Value contrasts freeze the entire selected-layer attention output
and add only the declared source Value difference under native probabilities.
"""
from contextlib import AbstractContextManager
from types import MethodType

import torch


def passive_statistics(scores, weights, *, visual, reasoning):
    """Per-head QK/attention features without Value or source-ROI information."""
    if scores.ndim != 2 or weights.shape != scores.shape:
        raise ValueError("Expected aligned [head, source] tensors")
    visual, reasoning = list(visual), list(reasoning)
    size = scores.shape[-1]
    if (not visual or len(set(visual)) != len(visual)
            or len(set(reasoning)) != len(reasoning)
            or set(visual) & set(reasoning)
            or any(i < 0 or i >= size for i in visual + reasoning)):
        raise ValueError("Invalid source indices")
    nonvisual = sorted(set(range(size)) - set(visual))
    if not nonvisual:
        raise ValueError("Nonvisual competition requires a nonvisual source")
    z, a = scores.float(), weights.float()
    av = a[:, visual]
    mass = av.sum(-1)
    normalized = av / mass.clamp_min(1e-30)[:, None]
    entropy = -(normalized * normalized.clamp_min(1e-30).log()).sum(-1)
    qv = z[:, visual].logsumexp(-1)
    result = {
        "visual_mass": mass,
        "qk_visual_nonvisual": qv - z[:, nonvisual].logsumexp(-1),
        "visual_top4_mass": av.topk(min(4, len(visual)), dim=-1).values.sum(-1),
        "visual_max": av.max(-1).values,
        "visual_entropy": entropy / max(float(torch.tensor(len(visual)).log()), 1e-30),
        "visual_effective_count": entropy.exp(),
        "sink_mass": a[:, 0],
    }
    result = {k: v.detach().cpu().tolist() for k, v in result.items()}
    result["qk_visual_reasoning"] = (
        (qv-z[:, reasoning].logsumexp(-1)).detach().cpu().tolist()
        if reasoning else None)
    return result


def value_delta(weights, native, donor, *, positions, heads):
    """Return only a source-local, logical-head Value contrast, with fixed a."""
    if native.ndim != 4 or native.shape != donor.shape or weights.ndim != 4:
        raise ValueError("Invalid Value/attention shapes")
    batch, kv_heads, size, dim = native.shape
    if weights.shape[0] != batch or weights.shape[-1] != size or weights.shape[1] % kv_heads:
        raise ValueError("Value cache does not match attention/GQA")
    positions, heads = list(positions), list(heads)
    if (not positions or not heads or len(set(positions)) != len(positions)
            or len(set(heads)) != len(heads)
            or any(i < 0 or i >= size for i in positions)
            or any(h < 0 or h >= weights.shape[1] for h in heads)):
        raise ValueError("Invalid patch coordinates")
    repeats = weights.shape[1] // kv_heads
    delta = (donor[:, :, positions] - native[:, :, positions]).repeat_interleave(repeats, dim=1)
    result = torch.zeros((batch, weights.shape[2], weights.shape[1], dim),
                         device=native.device, dtype=native.dtype)
    result[:, :, heads] = torch.matmul(weights[:, heads, :, :][:, :, :, positions],
                                      delta[:, heads]).transpose(1, 2)
    return result


def js_divergence(left_logits, right_logits):
    """JS in nats for raw next-token distributions, accumulated in FP64."""
    lp = left_logits.double().log_softmax(-1)
    lq = right_logits.double().log_softmax(-1)
    lm = torch.logaddexp(lp, lq) - torch.log(torch.tensor(2., device=lp.device, dtype=lp.dtype))
    return float((.5 * (lp.exp()*(lp-lm) + lq.exp()*(lq-lm)).sum(-1)).item())


class AttentionAssay(AbstractContextManager):
    """Capture selected layers or suppress/replace visual Values at their queries.

    Use on an isolated clone of the native cache. For fixed-route arms, frozen
    states must come from this exact native query partition and prefix. Native
    keys/Values are restored to the current cache so the intervention does not
    silently write a different routing history into subsequent readouts.
    """
    def __init__(self, model, *, layers, visual, prompt_length, mode="capture",
                 frozen=None, donor_values=None, positions=None, heads=None):
        self.model, self.layers = model, list(layers)
        self.visual, self.prompt_length = list(visual), int(prompt_length)
        self.mode, self.frozen, self.donor_values = mode, frozen, donor_values
        self.positions, self.heads = positions, heads
        self.states, self.records, self.originals = {}, {}, {}
        if mode not in {"capture", "off"}:
            raise ValueError("Unknown assay mode")
        if (frozen is None) != (donor_values is None):
            raise ValueError("Fixed routing requires native states and donor Values")

    def _forward(self, module, hidden_states, position_embeddings, attention_mask,
                 past_key_values=None, **kwargs):
        from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
        layer = int(module.layer_idx)
        if layer in self.states:
            raise RuntimeError("One assay instance must execute exactly one query partition")
        if module.training or module.config._attn_implementation != "eager":
            raise ValueError("Assays require evaluation-mode eager attention")
        shape = (*hidden_states.shape[:-1], -1, module.head_dim)
        q = module.q_norm(module.q_proj(hidden_states).view(shape)).transpose(1, 2)
        k = module.k_norm(module.k_proj(hidden_states).view(shape)).transpose(1, 2)
        v = module.v_proj(hidden_states).view(shape).transpose(1, 2)
        q, k = impl.apply_rotary_pos_emb(q, k, *position_embeddings)
        if past_key_values is not None:
            k, v = past_key_values.update(k, v, layer)
        head_output, weights = impl.eager_attention_forward(
            module, q, k, v, attention_mask, scaling=module.scaling, dropout=0., **kwargs)
        scores = torch.matmul(q, impl.repeat_kv(k, module.num_key_value_groups).transpose(2, 3))*module.scaling
        if attention_mask is not None:
            scores = scores + attention_mask
        heads = list(range(q.shape[1])) if self.heads is None else self.heads
        positions = self.visual if self.positions is None else self.positions
        self.states[layer] = {"query": q.detach().clone(), "key": k.detach().clone(),
                              "value": v.detach().clone(), "weights": weights.detach().clone(),
                              "head_output": head_output.detach().clone()}
        features = []
        for i in range(q.shape[2]):
            absolute = k.shape[2] - q.shape[2] + i
            # Prompt-prefill rows before all image tokens are deliberately not features.
            features.append(passive_statistics(scores[0, :, i], weights[0, :, i],
                visual=self.visual, reasoning=list(range(self.prompt_length, absolute+1)))
                if absolute >= max(self.visual) else None)
        zero = v.clone()
        zero[:, :, self.visual] = 0
        visual_output = -value_delta(weights, v, zero, positions=self.visual, heads=heads)
        visual_projected = torch.nn.functional.linear(
            visual_output.reshape(*hidden_states.shape[:-1], -1).float(), module.o_proj.weight.float())
        all_projected = torch.nn.functional.linear(
            head_output.reshape(*hidden_states.shape[:-1], -1).float(), module.o_proj.weight.float())
        ratios = {
            "alphaV_ratio": (visual_output.float().flatten(2).norm(dim=-1) /
                              head_output.float().flatten(2).norm(dim=-1).clamp_min(1e-12))[0].cpu().tolist(),
            "postWO_ratio": (visual_projected.norm(dim=-1) /
                              all_projected.norm(dim=-1).clamp_min(1e-12))[0].cpu().tolist(),
        }
        record = {"passive": features, "transport": ratios, "fixed_routing": self.frozen is not None,
                  "query_shape": list(q.shape), "kv_shape": list(k.shape),
                  "attention_reconstruction_max_abs_error": float((scores.float().softmax(-1).to(q.dtype)-weights).abs().max())}
        if self.frozen is not None:
            base = self.frozen[layer]
            if base["head_output"].shape != head_output.shape or base["value"].shape != v.shape:
                raise ValueError("Frozen native partition differs from recipient")
            head_output = base["head_output"] + value_delta(
                base["weights"], base["value"], self.donor_values[layer], positions=positions, heads=heads)
            weights = base["weights"]
            record["routing_max_abs_delta"] = float((weights-base["weights"]).abs().max())
            if past_key_values is not None:
                past_key_values.layers[layer].keys = base["key"].clone()
                past_key_values.layers[layer].values = base["value"].clone()
        elif self.mode == "off":
            zero = v.clone()
            zero[:, :, positions] = 0
            head_output = head_output + value_delta(weights, v, zero, positions=positions, heads=heads)
        self.records[layer] = record
        output = module.o_proj(head_output.reshape(*hidden_states.shape[:-1], -1).contiguous())
        return output, weights

    def __enter__(self):
        modules = self.model.model.language_model.layers
        if not self.layers or len(set(self.layers)) != len(self.layers) or any(i < 0 or i >= len(modules) for i in self.layers):
            raise ValueError("Invalid layer selection")
        for i in self.layers:
            module = modules[i].self_attn
            self.originals[i] = module.forward
            module.forward = MethodType(self._forward, module)
        return self

    def __exit__(self, *exc):
        for i, forward in self.originals.items():
            self.model.model.language_model.layers[i].self_attn.forward = forward
        return False
