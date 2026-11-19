"""Move inactive canonical caches without changing dtype, values or partition."""
import torch
from visual_reasoning.stage3c9.streaming import clone_streaming_state


def move_state(state, device):
    device = torch.device(device)
    for layer in state.cache.layers:
        layer.keys = layer.keys.to(device)
        layer.values = layer.values.to(device)
        layer.device = device
    state.rope_deltas = state.rope_deltas.to(device)
    state.last_logits = state.last_logits.to(device)
    return state


def clone_to_device(state, device):
    return move_state(clone_streaming_state(state), device)
