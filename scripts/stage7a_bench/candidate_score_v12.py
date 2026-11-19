"""Unchanged candidate arithmetic with inactive parent-cache CPU storage."""
from __future__ import annotations
from typing import Any, Sequence
import torch
from visual_reasoning.stage3c9.streaming import StreamingPrefixState,advance_streaming_state
from visual_reasoning.stage3a.runtime import summarize_candidate_log_probs
from scripts.stage7a_bench.cache_residency_v12 import clone_streaming_state

@torch.inference_mode()
def score_candidate_from_streaming_state(
    *, model: Any, state: StreamingPrefixState, candidate_token_ids: Sequence[int], seed: int,
) -> dict[str, Any]:
    candidate = [int(value) for value in candidate_token_ids]
    if not candidate:
        raise ValueError("Streaming evidence candidate must be nonempty")
    token_log_probabilities = []
    first_log_probs = torch.log_softmax(state.last_logits.float(), dim=-1)
    token_log_probabilities.append(float(first_log_probs[candidate[0]].item()))
    working = None
    if len(candidate) > 1:
        working = clone_streaming_state(state)
        for index, token in enumerate(candidate[:-1]):
            advance_streaming_state(
                model=model, state=working, token_ids=[token], seed=seed, chunk_size=1,
            )
            log_probs = torch.log_softmax(working.last_logits.float(), dim=-1)
            token_log_probabilities.append(float(log_probs[candidate[index + 1]].item()))
    summary = summarize_candidate_log_probs(token_log_probabilities)
    summary.update({
        "candidate_token_ids": candidate,
        "runtime_mode": "bounded_native_eager_cache",
        "finite": bool(all(torch.isfinite(torch.tensor(token_log_probabilities)).tolist())),
        "distribution_definition": "raw model next-token distribution; only divergent suffix rows are summarized",
    })
    if working is not None:
        del working
    return summary
