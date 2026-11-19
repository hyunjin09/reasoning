from copy import deepcopy
import pytest
import torch
from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen

from scripts.stage7a_bench.causal_assay_v2 import score_frozen_sources
from scripts.stage7a_bench.causal_prefix_v2 import make_benchmark_root
from scripts.stage7a_bench.tests.test_causal_prefix_v2 import fixture


def test_all_source_windows_preserve_root_and_match_inherited_assay():
    small, prepared, event=fixture()
    config=deepcopy(small.config);config.text_config.num_hidden_layers=36
    torch.manual_seed(123)
    model=qwen.Qwen3VLForConditionalGeneration(config).to(torch.bfloat16).eval()
    event.update(original_divergent_suffix_ids=[10],counterfactual_divergent_suffix_ids=[11],
        native_claim_suffix_ids=[11],candidate_ids=dict(correct=[10],foil=[11],native=[11],
            target_semantic=[11],alternative_original=[11],alternative_semantic=[12]))
    row=dict(no_image=False)
    root,_=make_benchmark_root(model,prepared,row,event)
    before=[(a.keys.clone(),a.values.clone()) for a in root.cache.layers]
    e=dict(causal_pilot_frozen=True,event=event,source_groups=dict(T=[2],X=[3],G=[2,3,4,5]),
        w2_sources=['T','X','G'],w8_sources=['T','X'],selection_used_causal_or_passive_scores=False)
    result=score_frozen_sources(model,root,e,mechanics=True)
    assert set(result['arms'])=={'N','T_W2','X_W2','G_W2','T_W8','X_W8'}
    assert all(result['checks'].values())
    for role in ('T','X'):
        for window in (2,8):
            arm=result['arms'][f'{role}_W{window}']
            active=[s for s in arm['step_audits'] if s['active_roi']==role]
            assert len(active)==window and all(s['layers']==list(range(36)) for s in active)
            assert len(arm['source_audits'])==36*window
            assert all(a['explicit_source_reference_exact'] for a in arm['source_audits'])
    for layer,(keys,values) in zip(root.cache.layers,before):
        torch.testing.assert_close(layer.keys,keys,atol=0,rtol=0)
        torch.testing.assert_close(layer.values,values,atol=0,rtol=0)
    assert root.generated_length==4
    assert result['distributions']['N'].shape==(64,)


@pytest.mark.parametrize('change', ['unfrozen','score_selected','missing_w8','empty_group','future_token'])
def test_invalid_pilot_or_source_scope_is_rejected_before_model_execution(change):
    e=dict(causal_pilot_frozen=True,event={},source_groups=dict(T=[2],X=[3],G=[2,3]),
        w2_sources=['T','X','G'],w8_sources=['T','X'],selection_used_causal_or_passive_scores=False)
    if change=='unfrozen':e['causal_pilot_frozen']=False
    if change=='score_selected':e['selection_used_causal_or_passive_scores']=True
    if change=='missing_w8':e['w8_sources']=['T']
    if change=='empty_group':e['source_groups']['T']=[]
    if change=='future_token':e['source_groups']['T']=[100]
    root=type('Root',(),dict(prompt_length=8))()
    with pytest.raises(ValueError):score_frozen_sources(None,root,e)
