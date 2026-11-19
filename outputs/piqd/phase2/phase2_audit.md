# Phase 2 Audit

## Conclusion

**B. Phase 2 passed for smoke only, but not final scientific evidence.**

The Phase 2 mechanics pass the audit checklist: event-position replay, CQ/CFQ alignment, all-head query storage, K_full storage, cache isolation, and use of Phase 1 retained visual indices are all supported by the listed artifacts.

However, Phase 1 and Phase 2 both report `fastv_status: approximate_fastv_style_static_pruning`. Therefore every artifact in this Phase 2 run is marked by this audit as:

```text
hook_smoke_only: true
final_scientific_evidence: false
```

Do not use the current Phase 2 outputs as final PIQD evidence.

## Artifacts Reviewed

- `outputs/piqd/phase2/phase2_summary.md`
- `outputs/piqd/phase2/phase2_event_position_convention.md`
- `outputs/piqd/phase2/phase2_query_tensors_metadata.jsonl`
- `outputs/piqd/phase2/phase2_same_prefix_checks.jsonl`
- `outputs/piqd/phase2/phase2_cache_recompute_checks.jsonl`
- `outputs/piqd/phase2/phase2_visual_token_mapping.jsonl`
- `outputs/piqd/phase2/phase2_event_queries.pt`
- `outputs/piqd/phase2/phase2_visual_keys.pt`
- `outputs/piqd/phase1/phase1_fastv_status.md`

## Requirement Audit

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Query extraction is at decoding event positions, not only prefill or prompt-end positions. | Pass | `phase2_event_position_convention.md` states Phase 2 extracts `q_t` at generated token `g_t`; metadata rows include non-prompt `generated_token_index` and event positions. |
| 2 | Event alignment is based on `generated_token_index` and decoded local context, not only absolute sequence position. | Pass | `phase2_same_prefix_checks.jsonl` has 20/20 rows with same generated-token IDs, generated-token index, decoded local context, and position token ID; CQ and CFQ absolute positions differ. |
| 3 | `q_CQ` and `q_CFQ` are extracted for the same `sample_id`, `event_type`, `generated_token_index`, and `token_id`. | Pass | Metadata rows pair CQ/CFQ shapes under one event key and include `sample_id`, `event_type`, `generated_token_index`, and `token_id_at_position`; same-prefix checks confirm token/index equality. |
| 4 | Selected layers include pruning boundary, `pruning_layer + 1`, middle layer, and late or near-final layer. | Pass | Phase 1 pruning layer is `2`; Phase 2 selected layers are `[2, 3, 18, 35]`. |
| 5 | All-head query tensors are stored before averaging. | Pass | Metadata uses `head_policy: all_heads_saved`; serialized query entries contain both `q_CQ` and `q_CFQ`. |
| 6 | Query tensor shape includes layer/head/head_dim information. | Pass | Metadata and tensor inspection both show `q_CQ` and `q_CFQ` shape `[4, 32, 128]`. |
| 7 | `K_full` is stored for the same selected layers and heads. | Pass | `phase2_visual_keys.pt` has 10 entries with `selected_layers`; shapes use 4 layers and 32 heads, matching Phase 2 summary. |
| 8 | `K_full` has shape compatible with `[num_heads, num_visual_tokens, head_dim]`. | Pass | Visual mapping metadata and tensor inspection show `K_full` as `[4, 32, num_visual_tokens, 128]`; visual-token counts match metadata. |
| 9 | CQ and CFQ visual conditions start independently with `past_key_values=None`. | Pass | `phase2_cache_recompute_checks.jsonl` has 10/10 rows with `CQ_starts_with_past_key_values_none: true` and `CFQ_starts_with_past_key_values_none: true`. |
| 10 | No text KV cache is reused across CQ and CFQ. | Pass | Cache checks show `past_key_values_reused_across_visual_conditions: false` and distinct cache context IDs for all 10 samples. |
| 11 | Phase 2 uses Phase 1 retained visual indices for the pruned visual condition. | Pass | `phase2_visual_token_mapping.jsonl` includes `retained_visual_indices_from_phase1`, matching retained counts, and `phase2_recomputed_retained_indices: false`. |
| 12 | If Phase 1 FastV is approximate input-level pruning, mark all Phase 2 outputs as hook smoke only, not final scientific evidence. | Smoke-only pass | `phase1_fastv_status.md` and `phase2_summary.md` report `approximate_fastv_style_static_pruning`; this audit marks the Phase 2 run `hook_smoke_only: true`. |

## Required Fixes Before Final PIQD Diagnostics

1. Replace `approximate_fastv_style_static_pruning` with a faithful Qwen3-VL-compatible FastV implementation, or a documented equivalent that performs the intended pruning at the model hook/layer boundary rather than only static input-level deletion.
2. Rerun Phase 1 with the faithful pruning path and regenerate the retained visual indices, event logs, similarity curves, and FastV status.
3. Rerun Phase 2 from the regenerated Phase 1 artifacts and emit outputs whose status is explicitly final-evidence eligible; the current Phase 2 run remains `hook_smoke_only: true`.

## Stop Status

Phase 3 was not implemented or started by this audit.
