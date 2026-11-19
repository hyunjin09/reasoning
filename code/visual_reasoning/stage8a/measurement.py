"""Passive main-cohort extensions; the validated attention implementation is unchanged."""
import math

import numpy as np
import torch

from .instrumentation import AttentionAssay, value_delta


def zero_mass_convention(passive):
    result = {k: list(v) if v is not None else None for k,v in passive.items()}
    for i, mass in enumerate(result["visual_mass"]):
        if mass == 0:
            result["visual_entropy"][i] = 0.
            result["visual_effective_count"][i] = 0.
    return result


def projected_transport(visual, total, weight, residual):
    """Diagnostics on [batch,query,head,dim]; residual is PRE-input-layernorm."""
    if visual.shape != total.shape or visual.ndim != 4 or residual.shape[:2] != visual.shape[:2]:
        raise ValueError("Misaligned contribution/residual tensors")
    heads, dim = visual.shape[-2:]
    if weight.shape != (residual.shape[-1], heads*dim):
        raise ValueError("Projection dimensions do not match heads/residual")
    by_head = torch.einsum("bqhd,ehd->bqhe", visual.float(), weight.float().reshape(-1,heads,dim))
    summed = by_head.sum(-2)
    total_projected = torch.nn.functional.linear(total.flatten(2).float(), weight.float())
    visual_norm = summed.norm(dim=-1)
    residual_norm = residual.float().norm(dim=-1)
    head_norm = by_head.norm(dim=-1)
    normalized = by_head / head_norm.clamp_min(1e-12)[...,None]
    cosine = normalized @ normalized.transpose(-2,-1)
    valid = (head_norm[..., :,None]>1e-12) & (head_norm[...,None,:]>1e-12)
    valid &= torch.triu(torch.ones(heads,heads,dtype=torch.bool,device=visual.device),diagonal=1)
    count = valid.sum((-2,-1))
    disagreement = ((1-cosine)*valid).sum((-2,-1))/count.clamp_min(1)
    metrics = dict(alphaV_ratio=visual.float().flatten(2).norm(dim=-1)/total.float().flatten(2).norm(dim=-1).clamp_min(1e-12),
                   postWO_ratio=visual_norm/total_projected.norm(dim=-1).clamp_min(1e-12),
                   residual_ratio=visual_norm/residual_norm.clamp_min(1e-12),
                   head_cancellation_ratio=visual_norm/head_norm.sum(-1).clamp_min(1e-12),
                   head_cosine_disagreement=disagreement, valid_head_pairs=count,
                   visual_postWO_norm=visual_norm, total_postWO_norm=total_projected.norm(dim=-1), residual_norm=residual_norm)
    return {k:v[0].detach().cpu().tolist() for k,v in metrics.items()}


class MeasurementAssay(AttentionAssay):
    """Adds raw residual and cancellation observations, without modifying tensors."""
    def __enter__(self):
        self.residuals, self.hooks = {}, []
        self.shallow_state = None
        modules = self.model.model.language_model.layers
        def shallow(module, args, output):
            if not isinstance(output, torch.Tensor):
                raise ValueError("Unexpected shallow decoder output")
            self.shallow_state = output[0,-1].detach().float().cpu().tolist()
        self.hooks.append(modules[0].register_forward_hook(shallow))
        for i in self.layers:
            def capture(module, args, kwargs, index=i):
                hidden = kwargs.get("hidden_states", args[0] if args else None)
                if hidden is None:
                    raise ValueError("Decoder raw residual unavailable")
                self.residuals[index] = hidden.detach().clone()
            self.hooks.append(modules[i].register_forward_pre_hook(capture, with_kwargs=True))
        try:
            return super().__enter__()
        except Exception:
            for hook in self.hooks:
                hook.remove()
            raise

    def _forward(self, module, hidden_states, *args, **kwargs):
        output = super()._forward(module, hidden_states, *args, **kwargs)
        layer = int(module.layer_idx)
        state = self.states[layer]
        zero = state["value"].clone()
        zero[:,:,self.visual] = 0
        heads = list(range(state["weights"].shape[1])) if self.heads is None else self.heads
        visual = -value_delta(state["weights"], state["value"], zero, positions=self.visual, heads=heads)
        self.records[layer]["transport"] = projected_transport(visual, state["head_output"], module.o_proj.weight, self.residuals[layer])
        self.records[layer]["passive"] = [zero_mass_convention(p) if p is not None else None for p in self.records[layer]["passive"]]
        return output

    def __exit__(self, *exc):
        try:
            return super().__exit__(*exc)
        finally:
            for hook in self.hooks:
                hook.remove()


def feature_vector(current, past, *, aggregation, window):
    if not past or window < 1:
        raise ValueError("Temporal feature requires strict past queries")
    if aggregation not in {"median", "trimmed_mean", "max"}:
        raise ValueError("Unknown aggregation")

    def aggregate(record):
        values = {}
        for layer in record.values():
            features = layer["passive"]
            if len(features) != 1 or features[0] is None:
                raise ValueError("Features require one generated query")
            for k,v in features[0].items():
                if v is None or not all(math.isfinite(x) for x in v):
                    raise ValueError("Incomplete passive feature")
                values.setdefault(k,[]).extend(v)
        result = {}
        for k,v in values.items():
            if aggregation == "median":
                result[k] = float(np.median(v))
            elif aggregation == "max":
                result[k] = float(np.max(v))
            else:
                v = sorted(v)
                trim = int(len(v)*.1)
                result[k] = float(np.mean(v[trim:len(v)-trim]))
        return result

    result = aggregate(current)
    history = [aggregate(r) for r in past[-window:]]
    for key in list(result):
        result["delta_"+key] = result[key]-float(np.median([r[key] for r in history]))
    return result
