"""Native HF generation and exact cache/RNG branching (validated before use)."""
from dataclasses import dataclass
import torch
from visual_reasoning.stage0.modeling import _clone_inputs, _reset_generation_state
from visual_reasoning.stage3b0.cache import clone_cache
from visual_reasoning.stage8b.v2_protocol import generation_parameters


@dataclass
class BranchState:
    sequences: torch.Tensor
    cache: object
    rope: torch.Tensor
    cuda_rng: torch.Tensor
    cpu_rng: torch.Tensor


def snapshot(model, result):
    assert result.past_key_values.get_seq_length() == result.sequences.shape[1]-1
    return BranchState(result.sequences, result.past_key_values,
                       model.model.rope_deltas.clone(), torch.cuda.get_rng_state(), torch.get_rng_state())


@torch.inference_mode()
def start(model, prepared, seed, count, *, sample=True, logits=False):
    _reset_generation_state(model, seed)
    params=generation_parameters() if sample else dict(do_sample=False)
    result=model.generate(**_clone_inputs(prepared),**params,max_new_tokens=count,
                          use_cache=True,return_dict_in_generate=True,output_logits=logits)
    return snapshot(model,result),result


@torch.inference_mode()
def resume(model, state, count, *, copy_cache=True, sample=True, logits=False):
    model.model.rope_deltas=state.rope.clone()
    torch.cuda.set_rng_state(state.cuda_rng);torch.set_rng_state(state.cpu_rng)
    params=generation_parameters() if sample else dict(do_sample=False)
    cache=clone_cache(state.cache) if copy_cache else state.cache
    result=model.generate(input_ids=state.sequences.clone(),
        attention_mask=torch.ones_like(state.sequences),past_key_values=cache,
        **params,max_new_tokens=count,use_cache=True,return_dict_in_generate=True,output_logits=logits)
    return snapshot(model,result),result
