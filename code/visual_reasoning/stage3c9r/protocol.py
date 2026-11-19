"""Same-execution contracts; scientific classification is inherited unchanged."""

from __future__ import annotations

import statistics

from visual_reasoning.stage3c9.analysis import (
    classify_checkpoint, lifetime_phenotype, source_and_rescue_effects,
)
from visual_reasoning.stage3c9.assay import CONDITIONS
from visual_reasoning.stage3c9.protocol import intervention_boundaries
from visual_reasoning.stage3c9.streaming import fixed_chunk_ranges


def shared_partition(event: dict, *, end: int) -> list[tuple[int, int]]:
    span = list(range(event['span_start_token'], event['span_end_token']))
    control = event['matched_neighbor_span']
    neighbor = list(range(control['start_token'], control['end_token']))
    if not span or len(neighbor) != len(span) or set(span) & set(neighbor):
        raise ValueError('Invalid frozen event/neighbor positions')
    if max(span + neighbor) + 1 >= end:
        raise ValueError('Every patch must leave a downstream bridge')
    return fixed_chunk_ranges(
        start=0, end=end, chunk_size=2048,
        mandatory_boundaries=intervention_boundaries(span, neighbor, end_generated_index=end),
    )


def classify_family(conditions: dict, *, effect_floor: float = .05,
                    final_rescue_gains: dict | None = None) -> dict:
    if set(conditions) != set(CONDITIONS):
        raise ValueError('Exactly O/O_sham/C/C_sham are required')
    partition = conditions['O']['partition']
    metrics = {}
    neighbors = {}
    for condition, row in conditions.items():
        if row['partition'] != partition:
            raise ValueError('Semantic/sham partition mismatch')
        for arm in ('event_rescue', 'neighbor_rescue'):
            if row[arm]['recipient_execution_id'] != row['execution_id']:
                raise ValueError('Rescue recipient execution mismatch')
        metrics[condition] = source_and_rescue_effects(
            condition=condition, native_D=row['native']['D'],
            suppressed_D=row['suppressed']['D'], rescue_D=row['event_rescue']['D'],
        )
        neighbors[condition] = source_and_rescue_effects(
            condition=condition, native_D=row['native']['D'],
            suppressed_D=row['suppressed']['D'], rescue_D=row['neighbor_rescue']['D'],
        )['rescue_gain']
    semantic = ('O', 'C')
    result = classify_checkpoint(
        source_losses={c: metrics[c]['source_loss'] for c in semantic},
        sham_source_effects={c: metrics[c]['source_loss'] for c in ('O_sham', 'C_sham')},
        rescue_gains={c: metrics[c]['rescue_gain'] for c in semantic},
        rescue_ratios={c: metrics[c]['rescue_ratio'] for c in semantic
                       if metrics[c]['rescue_ratio'] is not None},
        neighbor_gains={c: neighbors[c] for c in semantic},
        final_rescue_gains=final_rescue_gains, effect_floor=effect_floor,
    )
    return {**result, 'condition_metrics': metrics, 'neighbor_gains': neighbors,
            'source_loss_median': statistics.median(metrics[c]['source_loss'] for c in semantic),
            'event_minus_neighbor': result['rescue_gain_mean'] - result['neighbor_gain_mean']}


def lifetime_summary(*, local_gain: float, downstream: list[tuple[int, float]],
                     final_gain: float | None, effect_floor: float = .05) -> dict:
    censored = not downstream and final_gain is None
    return {
        'phenotype': 'RIGHT-CENSORED' if censored else lifetime_phenotype(
            local_gain=local_gain, downstream=downstream, final_gain=final_gain,
            effect_floor=effect_floor,
        ),
        'right_censored': censored,
        'first_observed_downstream_distance': min((d for d, _ in downstream), default=None),
        'decay_time_resolved_at_16_to_32': any(16 <= d <= 32 and g < effect_floor for d, g in downstream),
        'interpretation': ('No distinct downstream/final readout.' if censored else
                           'Lifetime label follows frozen readouts; unobserved intervals are unresolved.'),
    }
