"""Stage 3C.3 relevant-vs-distractor routing causality helpers."""

from visual_reasoning.stage3c3.protocol import (
    choose_query_formulation,
    phase_a_target_passes,
    split_validation_primary,
)
from visual_reasoning.stage3c3.runtime import splice_current_query_heads

__all__ = [
    "choose_query_formulation",
    "phase_a_target_passes",
    "splice_current_query_heads",
    "split_validation_primary",
]
