"""Two-pass gain around the unmodified Hugging Face generation/sampling loop.

Only model tensors, visual token coordinates, a frozen probe and policy enter
this interface. No benchmark records, answers, annotations or future tokens.
"""
from contextlib import AbstractContextManager
from functools import wraps

import numpy as np
import torch
import torch.nn.functional as F

from visual_reasoning.stage8b.passive import FEATURE_KEYS, passive_tensor, frozen_scores
from .trigger import OnlineEpisodes
from .native_partition import full_axis_parts


LAYERS = (19, 20, 21, 22)


class VisualGain(AbstractContextManager):
    def __init__(self, model, *, visual, prompt_length, detector, gain,
                 policy='retrieval', schedule=(), replay_noop=False, audit=False):
        if gain not in (1., 1.25, 1.5, 2.):
            raise ValueError('Gain is outside the preregistered dose grid')
        if policy not in ('retrieval', 'never', 'schedule'):
            raise ValueError('Unknown intervention timing')
        self.model, self.visual, self.prompt_length = model, list(visual), int(prompt_length)
        self.detector, self.gain, self.policy = detector, float(gain), policy
        self.schedule, self.replay_noop, self.audit = set(schedule), replay_noop, audit
        if any(p <= 0 for p in self.schedule):
            raise ValueError('Prefill has no valid retrieval score or replay intervention')
        self.episodes = OnlineEpisodes()
        self.features, self.scores, self.events, self.decompositions = [], [], [], []
        self.pending, self.contribution = {}, {}
        self.decomposition_pending = {}
        self.mode = 'probe'
        self.hooks = []
        self.committed_logit_hashes = []

    def __enter__(self):
        from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
        self.impl, self.original_attention = impl, impl.eager_attention_forward
        self.original_forward = self.model.forward
        impl.eager_attention_forward = self.attention
        layers = self.model.model.language_model.layers
        for layer in LAYERS:
            self.hooks.append(layers[layer].self_attn.o_proj.register_forward_hook(self.projection_hook(layer)))

        @wraps(self.original_forward)
        def forward(*args, **kwargs):
            if args:
                raise ValueError('Generation must use keyword inputs for replay')
            cache = kwargs.get('past_key_values')
            old_length = cache.get_seq_length() if cache is not None else 0
            self.mode = 'probe'
            out = self.original_forward(**kwargs)
            if self.pending:
                raise RuntimeError('Incomplete probe layers')
            score = self.scores[-1]
            onset = self.episodes.step(score)
            index = len(self.scores)-1
            selected = onset if self.policy == 'retrieval' else index in self.schedule if self.policy == 'schedule' else False
            rerun = selected and (self.gain != 1. or self.replay_noop)
            if rerun:
                if old_length < self.prompt_length or kwargs['input_ids'].shape[1] != 1:
                    raise RuntimeError('Expected one cached decode token, never multimodal prefill')
                if out.past_key_values is not cache:
                    raise RuntimeError('Unexpected cache ownership')
                # DynamicCache appends, so cropping removes precisely the probe's
                # token. Earlier prefix tensors remain unmodified.
                cache.crop(old_length)
                if cache.get_seq_length() != old_length:
                    raise RuntimeError('Probe cache rollback failed')
                self.mode = 'gain'
                out = self.original_forward(**kwargs)
                self.mode = 'probe'
                if out.past_key_values is not cache or cache.get_seq_length() != old_length+1:
                    raise RuntimeError('Intervention cache not committed')
                if self.contribution:
                    raise RuntimeError('Unconsumed visual projection')
            if selected:
                self.events.append(dict(token_index=index, probe_R=float(score), retrieval_onset=onset,
                                        gain=self.gain, rerun=rerun, cache_length=out.past_key_values.get_seq_length()))
            if self.audit:
                import hashlib
                self.committed_logit_hashes.append(hashlib.sha256(out.logits[0, -1].float().cpu().numpy().tobytes()).hexdigest())
            return out

        self.model.forward = forward
        return self

    def attention(self, module, query, key, value, attention_mask, scaling, dropout=0., **kwargs):
        result = self.original_attention(module, query, key, value, attention_mask,
                                         scaling=scaling, dropout=dropout, **kwargs)
        layer = getattr(module, 'layer_idx', None)
        if layer not in LAYERS:
            return result
        if module.training or dropout or query.shape[0] != 1:
            raise RuntimeError('Expected single-example eval attention')
        weights = result[1][0, :, -1, :]
        if self.mode == 'probe':
            z = torch.matmul(query[:, :, -1:, :], self.impl.repeat_kv(key, module.num_key_value_groups).transpose(2, 3))*scaling
            if attention_mask is not None:
                z = z + attention_mask[:, :, -1:, :]
            self.pending[layer] = passive_tensor(z[0, :, 0, :], weights, visual=self.visual, prompt_length=self.prompt_length)
            if layer == LAYERS[-1]:
                vector = torch.cat([self.pending[i] for i in LAYERS], dim=0).amax(0).detach().cpu().numpy()
                self.features.append(vector)
                self.scores.append(float(frozen_scores(vector[None, :], self.detector, FEATURE_KEYS)[0]))
                self.pending.clear()
        if (self.mode == 'gain' and self.gain != 1.) or (self.audit and query.shape[2] == 1):
            repeated = self.impl.repeat_kv(value, module.num_key_value_groups)[0]
            cv, _ = full_axis_parts(weights, repeated, self.visual)
            self.contribution[layer] = cv.flatten()[None, None, :] if self.mode == 'gain' and self.gain != 1. else None
            if self.contribution[layer] is None:
                del self.contribution[layer]
            if self.audit:
                nonvisual = torch.ones(weights.shape[-1], dtype=torch.bool, device=weights.device)
                nonvisual[self.visual] = False
                _, cn = full_axis_parts(weights, repeated, self.visual)
                native = result[0][0, -1].float()
                reconstructed = cv.float()+cn.float()
                delta = reconstructed-native
                fp32 = torch.matmul(weights.float().unsqueeze(1), repeated.float()).squeeze(1)
                self.decomposition_pending[layer] = (cv, cn)
                self.decompositions.append(dict(layer=layer, mode=self.mode,
                    site='head_output',
                    relative_l2=float(delta.norm()/native.norm().clamp_min(1e-12)),
                    max_abs=float(delta.abs().max()),
                    fp32_relative_l2=float((fp32-native).norm()/native.norm().clamp_min(1e-12))))
        return result

    def projection_hook(self, layer):
        def hook(module, args, output):
            if layer in self.decomposition_pending:
                cv, cn = self.decomposition_pending.pop(layer)
                projected = F.linear(cv.flatten()[None, None, :], module.weight, bias=None).float()
                projected = projected + F.linear(cn.flatten()[None, None, :], module.weight, bias=module.bias).float()
                difference = projected-output.float()
                self.decompositions.append(dict(layer=layer, mode=self.mode, site='projected_output',
                    relative_l2=float(difference.norm()/output.float().norm().clamp_min(1e-12)),
                    max_abs=float(difference.abs().max()), fp32_relative_l2=0.))
            if layer not in self.contribution:
                return output
            visual = self.contribution.pop(layer)
            if output.shape[1] != 1:
                raise RuntimeError('Gain must affect only the current query')
            cv = F.linear(visual, module.weight, bias=None)
            return output + (self.gain-1.)*cv
        return hook

    def arrays(self):
        return dict(features=np.asarray(self.features, dtype=np.float32),
                    retrieval_score=np.asarray(self.scores, dtype=np.float64),
                    feature_keys=np.asarray(FEATURE_KEYS))

    def __exit__(self, *exc):
        self.model.forward = self.original_forward
        self.impl.eager_attention_forward = self.original_attention
        for hook in self.hooks:
            hook.remove()
        return False
