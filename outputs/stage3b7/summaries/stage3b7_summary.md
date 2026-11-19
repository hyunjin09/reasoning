# Stage 3B.7 — Validation-Gate Result

**Status: FAIL before primary scoring.**

## Completed work

- Froze the exact 37-base primary cohort and disjoint 8-base validation cohort.
- Froze `E_d/W4/Top_4` heads `[11, 6, 15, 12]` and `E_d-1/W4/Top_2` heads `[16, 0]`.
- Constructed and manually validated exact edited-pixel target ROIs, complements, fixed rings, and cardinality-matched irrelevant regions for all 45 bases without using attention.
- Implemented and unit-tested query-head-selective K-only, V-only, and K+V mechanics under grouped-query attention.
- Ran only the disjoint 8-base Phase-A validation set in tmux 8 on two A5000 GPUs.

## Validation outcome

All mechanical and reproducibility checks passed:

- legacy all-V scores: exact;
- token layouts and ROI/source isolation: exact;
- self swaps: exact;
- non-target query heads unchanged;
- deterministic repeats: exact;
- finite scores: all;
- peak allocation: 9.01 GB per shard or lower.

The semantic validation gate failed for one of the two frozen targets:

- `E_d/W4/Top_4`: median BPR `0.8364`, bidirectional fraction `0.875`, median sham/semantic `0.1143` — passes.
- `E_d-1/W4/Top_2`: median BPR `0.2138`, bidirectional fraction `0.750`, median sham/semantic `0.2699` — fails the frozen `<0.25` rule.

The one permitted diagnostic found modest median absolute sham shift (`0.0597`) but near-zero semantic restoration on bases `83` and `101`; this is a real sham-relative validation limitation, not a mechanical implementation failure. The threshold was not changed and inference was not repeated.

## Stop boundary

No one from the 37-base primary cohort was scored in Stage 3B.7. Phase B, optional alpha, W5/head_10, attention triangulation, and all later experiments were not run. Empty required scoring manifests explicitly record this stop rather than masquerading as primary results.

Attention was not used to choose any ROI and no attention-only causal claim is made.

## Recommendation

**REDESIGN — Strengthen or replace the sham-sensitive E_d-1/W4/Top_2 target under a newly approved prospective protocol; do not reinterpret the current threshold or start the primary cohort from this failed gate.**
