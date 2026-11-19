"""Observe native eager attention without changing model outputs or caches."""
from contextlib import AbstractContextManager

import numpy as np
import torch


FEATURE_KEYS = ["visual_mass", "qk_visual_nonvisual", "qk_visual_reasoning",
                "visual_top4_mass", "visual_max", "visual_entropy",
                "visual_effective_count", "sink_mass"]


def passive_tensor(scores, weights, *, visual, prompt_length):
    """Stage8A statistics, retained on device until all selected layers finish."""
    if scores.ndim != 2 or weights.shape != scores.shape:
        raise ValueError("Expected [head, source] scores/weights")
    visual = list(visual)
    if not visual or len(set(visual)) != len(visual) or not all(0 <= x < prompt_length <= scores.shape[-1] for x in visual):
        raise ValueError("Invalid visual/prompt coordinates")
    nonvisual_prompt = sorted(set(range(prompt_length)) - set(visual))
    z, a = scores.float(), weights.float()
    av = a[:, visual]
    mass = av.sum(-1)
    p = av / mass.clamp_min(1e-30)[:, None]
    entropy = -(p * p.clamp_min(1e-30).log()).sum(-1)
    qv = z[:, visual].logsumexp(-1)
    # Same ordered nonvisual vector as Stage8A, without constructing long CPU indices.
    zn = torch.cat((z[:, nonvisual_prompt], z[:, prompt_length:]), dim=-1)
    qn = qv - zn.logsumexp(-1)
    qr = qv - z[:, prompt_length:].logsumexp(-1) if scores.shape[-1] > prompt_length else torch.full_like(qv, float("nan"))
    return torch.stack((mass, qn, qr, av.topk(min(4,len(visual)), dim=-1).values.sum(-1),
                        av.max(-1).values, entropy / max(float(torch.tensor(len(visual)).log()),1e-30),
                        torch.where(mass > 0, entropy.exp(), 0.), a[:,0]), dim=-1)


def frozen_scores(features, model, feature_keys):
    if list(feature_keys) != FEATURE_KEYS:
        raise ValueError("Unexpected feature order for frozen Stage8A model")
    features = np.asarray(features, dtype=float)
    if features.ndim != 2 or features.shape[1] != len(FEATURE_KEYS):
        raise ValueError("Invalid feature matrix")
    x = features[:, :3]
    valid = np.isfinite(x).all(axis=1)
    out = np.full(len(features), np.nan)
    if valid.any():
        out[valid] = model.predict_proba(x[valid])[:,1]
    return out


def episode_summary(scores, *, threshold):
    scores = np.asarray(scores, dtype=float)
    valid = np.isfinite(scores)
    active = valid & (scores > threshold)
    onsets = np.flatnonzero(active & ~np.r_[False,active[:-1]]).tolist()
    return dict(active_tokens=int(active.sum()), valid_score_tokens=int(valid.sum()),
                density=float(active.sum()/valid.sum()) if valid.any() else None,
                episodes=len(onsets), episode_onsets=onsets,
                first_retrieval=onsets[0] if onsets else None,
                intervals=np.diff(onsets).tolist())


class PassiveRecorder(AbstractContextManager):
    """Only observe the original eager function; no cache mutation or replacement."""
    def __init__(self, *, visual, prompt_length, model, layers=(19,20,21,22), reference_check=False):
        self.visual, self.prompt_length = list(visual), int(prompt_length)
        self.model, self.layers = model, tuple(layers)
        self.pending, self.rows, self.focus, self.scores = {}, [], [], []
        self.reference_check = reference_check
        self.reference_rows = 0

    def __enter__(self):
        from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
        self.impl, self.original = impl, impl.eager_attention_forward
        def observe(module, query, key, value, attention_mask, scaling, dropout=0., **kwargs):
            result = self.original(module, query, key, value, attention_mask, scaling=scaling, dropout=dropout, **kwargs)
            layer = getattr(module,"layer_idx",None)
            if layer not in self.layers:
                return result
            if module.training or dropout != 0 or query.shape[0] != 1:
                raise ValueError("Expected evaluation-mode single-example native attention")
            if layer in self.pending:
                raise ValueError("Repeated layer before observation completed")
            weights = result[1][0,:,-1,:]
            # Full prefill is untouched; only its last observation row is computed.
            z = torch.matmul(query[:,:,-1:,:], impl.repeat_kv(key,module.num_key_value_groups).transpose(2,3))*scaling
            if attention_mask is not None:
                z = z + attention_mask[:,:,-1:,:]
            z = z[0,:,0,:]
            features = passive_tensor(z, weights, visual=self.visual, prompt_length=self.prompt_length)
            if self.reference_check and key.shape[2] > self.prompt_length:
                from visual_reasoning.stage8a.instrumentation import passive_statistics
                ref = passive_statistics(z, weights, visual=self.visual, reasoning=list(range(self.prompt_length,key.shape[2])))
                for i,name in enumerate(FEATURE_KEYS):
                    expected = torch.tensor(ref[name],dtype=features.dtype,device=features.device)
                    if name == "visual_effective_count":
                        expected = torch.where(features[:,0]>0,expected,0.)
                    assert torch.equal(features[:,i],expected), name
                self.reference_rows += 1
            self.pending[layer] = (features, weights[:,self.visual].float().mean(0))
            if layer == self.layers[-1]:
                if set(self.pending) != set(self.layers):
                    raise ValueError("Missing selected-layer observation")
                vector = torch.cat([self.pending[i][0] for i in self.layers],dim=0).amax(0)
                focus = torch.stack([self.pending[i][1] for i in self.layers]).mean(0)
                host = torch.cat((vector,focus)).detach().cpu().numpy()
                self.rows.append(host[:len(FEATURE_KEYS)])
                self.focus.append(host[len(FEATURE_KEYS):])
                self.scores.append(frozen_scores(host[None,:len(FEATURE_KEYS)],self.model,FEATURE_KEYS)[0])
                self.pending.clear()
            return result
        impl.eager_attention_forward = observe
        return self

    def __exit__(self,*exc):
        self.impl.eager_attention_forward = self.original
        if exc[0] is None and self.pending:
            raise ValueError("Incomplete final observation")
        return False

    def arrays(self):
        return dict(features=np.asarray(self.rows,dtype=np.float32),
                    visual_focus=np.asarray(self.focus,dtype=np.float32),
                    retrieval_score=np.asarray(self.scores,dtype=np.float64),
                    feature_keys=np.asarray(FEATURE_KEYS),
                    visual_positions=np.asarray(self.visual,dtype=np.int32))
