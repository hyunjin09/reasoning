"""Regression for the independent cached-forward validation caller."""
from types import SimpleNamespace
import torch
from transformers.models.qwen3_vl.modeling_qwen3_vl import Qwen3VLModel
from visual_reasoning.stage3b0.runtime import suffix_position_ids


def test_cached_reference_must_supply_one_token_positions():
    state = SimpleNamespace(rope_deltas=torch.tensor([[-600]]))
    cache = SimpleNamespace(get_seq_length=lambda:720)
    inferred = Qwen3VLModel.compute_3d_position_ids(state,
        input_ids=torch.ones((1,1),dtype=torch.long),inputs_embeds=torch.zeros((1,1,8)),
        past_key_values=cache,attention_mask=torch.ones((1,721),dtype=torch.long))
    # A direct model call with a full mask infers full-mask positions, unlike HF
    # generate which already slices position_ids to the current token.
    assert inferred.shape == (3,1,721)
    fixed = suffix_position_ids(prompt_length=720,suffix_length=1,
                                rope_deltas=state.rope_deltas,device=torch.device('cpu'))
    assert fixed.shape == (4,1,1)
    assert fixed[:,0,0].tolist() == [720,120,120,120]
