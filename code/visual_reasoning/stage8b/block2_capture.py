"""Read-only source observation around the untouched native eager attention call."""
import math
from contextlib import AbstractContextManager

import numpy as np
import torch

from visual_reasoning.stage8b.passive import passive_tensor


def routing_summary(qk, mass, density, visual_mass, roles):
    """Equal head weighting; QK is log-mean-exp, attention shares are raw mass."""
    qk, mass, density, visual_mass = map(np.asarray, (qk, mass, density, visual_mass))
    assert qk.shape == mass.shape == density.shape and qk.ndim == 2
    assert 'T' in roles and len(roles) == mass.shape[1]
    t = roles.index('T'); shares = mass/np.maximum(visual_mass[:, None], 1e-30)
    mean_share = shares.mean(0); candidates = mean_share/max(mean_share.sum(), 1e-30)
    k = len(roles)
    result = dict(target_share=float(mean_share[t]), target_attention_density=float(density[:, t].mean()),
                  target_rank=float(1+np.sum(mean_share > mean_share[t])) if k >= 2 else None,
                  top_source=roles[int(np.argmax(mean_share))] if k >= 2 else None,
                  source_entropy=float(-(candidates*np.log(np.maximum(candidates, 1e-30))).sum()/math.log(k)) if k >= 2 and mean_share.sum() > 0 else None,
                  top2_margin=float(np.sort(candidates)[-1]-np.sort(candidates)[-2]) if k >= 2 and mean_share.sum() > 0 else None,
                  target_consensus=float((np.argmax(shares, axis=1) == t).mean()) if k >= 2 else None,
                  candidate_count=k, candidate_visual_shares=dict(zip(roles, mean_share.tolist())))
    for role in ['X', 'I', 'rest']:
        for name, values in [('qk', qk), ('share', shares), ('density', density)]:
            result[f'{name}_T_{role}'] = float((values[:, t]-values[:, roles.index(role)]).mean()) if role in roles else None
    if 'X' in roles:
        x = roles.index('X'); qdiff = qk[:, t]-qk[:, x]; adiff = shares[:, t]-shares[:, x]
        result.update(target_over_X_head_fraction=float((qdiff > 0).mean()),
                      head_qk_margin_variance=float(qdiff.var()), head_attention_margin_variance=float(adiff.var()))
    else:
        result.update(target_over_X_head_fraction=None, head_qk_margin_variance=None, head_attention_margin_variance=None)
    winners = np.argmax(shares, axis=1)
    fractions = np.bincount(winners, minlength=k)/len(winners)
    result['cross_head_source_entropy'] = float(-(fractions*np.log(np.maximum(fractions, 1e-30))).sum()/math.log(k)) if k >= 2 else None
    return result


class SourceObserver(AbstractContextManager):
    def __init__(self, model, metadata, positions, layers=(19, 20, 21, 22)):
        self.model, self.metadata, self.positions, self.layers = model, metadata, positions, layers
        self.records, self.residuals, self.handles = {}, {}, []

    def __enter__(self):
        from transformers.models.qwen3_vl import modeling_qwen3_vl as impl
        self.impl, self.original = impl, impl.eager_attention_forward
        for layer in self.layers:
            def residual(module, args, kwargs, index=layer):
                hidden = kwargs.get('hidden_states', args[0] if args else None)
                assert hidden is not None
                self.residuals[index] = hidden[0, -1].detach().float().clone()
            self.handles.append(self.model.model.language_model.layers[layer].register_forward_pre_hook(residual, with_kwargs=True))
        impl.eager_attention_forward = self.observe
        return self

    def __exit__(self, *exc):
        self.impl.eager_attention_forward = self.original
        for handle in self.handles:
            handle.remove()
        if exc[0] is None:
            assert set(self.records) == set(self.layers)
        return False

    def observe(self, module, query, key, value, attention_mask, scaling, dropout=0., **kwargs):
        output = self.original(module, query, key, value, attention_mask, scaling=scaling, dropout=dropout, **kwargs)
        layer = getattr(module, 'layer_idx', None)
        if layer not in self.layers:
            return output
        assert query.shape[0] == query.shape[2] == 1 and not module.training and dropout == 0
        assert layer not in self.records
        scores = torch.matmul(query, self.impl.repeat_kv(key, module.num_key_value_groups).transpose(2, 3))*scaling
        if attention_mask is not None:
            scores = scores+attention_mask
        scores = scores[0, :, 0]
        weights = output[1][0, :, 0]
        visual = self.metadata['visual_token_indices']
        passive = passive_tensor(scores, weights, visual=visual, prompt_length=self.metadata['prompt_token_count'])
        # Floating-point diagnostic reductions only: native output/cache are untouched.
        values = self.impl.repeat_kv(value, module.num_key_value_groups)[0].float()
        z, a = scores.float(), weights.float()
        roles = [role for role in ['T', 'X', 'I'] if self.positions.get(role)]
        assert roles and roles[0] == 'T'
        qk, mass, density, alpha = [], [], [], {}
        for role in roles+['visual']:
            positions = visual if role == 'visual' else self.positions[role]
            alpha[role] = torch.einsum('hk,hkd->hd', a[:, positions], values[:, positions])
            if role != 'visual':
                qk.append(z[:, positions].logsumexp(-1)-math.log(len(positions)))
                mass.append(a[:, positions].sum(-1))
                density.append(mass[-1]/len(positions))
        qk = torch.stack(qk, dim=1); mass = torch.stack(mass, dim=1); density = torch.stack(density, dim=1)
        visual_mass = a[:, visual].sum(-1)
        other = sorted(set(visual)-set(self.positions['T']))
        rest_qk = z[:, other].logsumexp(-1)-math.log(len(other)) if other else None
        rest_share = a[:, other].sum(-1)/visual_mass.clamp_min(1e-30) if other else None
        projection = module.o_proj.weight.float().reshape(-1, alpha['T'].shape[0], alpha['T'].shape[1])
        projected = {role: torch.einsum('hd,ehd->he', v, projection) for role, v in alpha.items()}
        vnorm = projected['visual'].sum(0).norm()
        transport = dict(target_alphaV_norm=float(alpha['T'].norm()),
                         target_X_alphaV_margin=float(alpha['T'].norm()-alpha['X'].norm()) if 'X' in alpha else None,
                         visual_alphaV_norm=float(alpha['visual'].norm()),
                         target_postWO_norm=float(projected['T'].sum(0).norm()), visual_postWO_norm=float(vnorm),
                         visual_residual_ratio=float(vnorm/self.residuals[layer].norm().clamp_min(1e-30)),
                         head_cancellation_ratio=float(vnorm/projected['visual'].norm(dim=-1).sum().clamp_min(1e-30)),
                         target_X_value_cosine=float(torch.nn.functional.cosine_similarity(alpha['T'].flatten(), alpha['X'].flatten(), dim=0)) if 'X' in alpha else None)
        self.records[layer] = dict(roles=roles, qk=qk.cpu().tolist(), mass=mass.cpu().tolist(),
                                   density=density.cpu().tolist(), visual_mass=visual_mass.cpu().tolist(),
                                   rest_qk=rest_qk.cpu().tolist() if rest_qk is not None else None,
                                   rest_share=rest_share.cpu().tolist() if rest_share is not None else None,
                                   passive=passive.cpu().tolist(), transport=transport)
        return output

    def result(self):
        records = [self.records[layer] for layer in self.layers]
        roles = records[0]['roles']; assert all(r['roles'] == roles for r in records)
        arrays = {key: np.concatenate([r[key] for r in records], axis=0) for key in ['qk', 'mass', 'density', 'visual_mass']}
        summary = routing_summary(**arrays, roles=roles)
        per_layer = {str(layer): routing_summary(**{key: self.records[layer][key] for key in arrays}, roles=roles) for layer in self.layers}
        winners = [r['top_source'] for r in per_layer.values()]
        summary['layer_top_source_agreement'] = max(winners.count(v) for v in set(winners))/len(winners) if len(roles) >= 2 else None
        if all(r['rest_qk'] is not None for r in records):
            summary['qk_T_rest'] = float((arrays['qk'][:, 0]-np.concatenate([r['rest_qk'] for r in records])).mean())
            summary['share_T_rest'] = float((arrays['mass'][:, 0]/np.maximum(arrays['visual_mass'], 1e-30)-np.concatenate([r['rest_share'] for r in records])).mean())
        transport = {key: float(np.mean([r['transport'][key] for r in records])) if all(r['transport'][key] is not None for r in records) else None for key in records[0]['transport']}
        return dict(routing=summary, per_layer=per_layer, transport=transport,
                    native_global_features=np.concatenate([r['passive'] for r in records], axis=0).max(0).tolist(),
                    per_head_records=self.records, accumulation='BF16 model/native attention; FP32 diagnostic vector reductions')
