# Phase 2 Summary

- status: `ok`
- samples_processed: `1`
- events_processed: `2`
- model_path: `/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-8B-Thinking/snapshots/92f3c4b4feadd3a016ef468d103bb5f58b2a2c6b`
- model_class: `Qwen3VLForConditionalGeneration`
- dtype: `torch.bfloat16`
- device_map: `single_device_explicit_to_cuda`
- selected_layers: `[2, 3, 18, 35]`
- number_of_heads: `32`
- head_dim: `128`
- fastv_status: `approximate_fastv_style_static_pruning`
- same_prefix_check: `True`
- same_position_check: `True`
- no_cross_condition_KV_reuse_check: `True`
- query_shape_check: `True`
- K_full_shape_check: `True`
- FastV_artifact_consistency_check: `True`
- phase3_safe_to_start: `true`
- phase3_requires_explicit_user_approval: `true`
- phase3_started: `false`

## Tensor Shapes
- Query tensors are stored per event as `[selected_layers, num_heads, head_dim]` in `phase2_event_queries.pt`.
- Full visual-bank keys are stored per sample as `[selected_layers, num_heads, num_visual_tokens, head_dim]` in `phase2_visual_keys.pt`.

## Visual Token Counts
See `phase2_visual_token_mapping.jsonl` for per-sample full and retained visual token counts.

## Unresolved Risks
- FastV remains `approximate_fastv_style_static_pruning`; faithful FastV validation is still required before final claims.
- Phase 2 stores queries and K_full only; it does not compute retrieval metrics or behavioral continuation.
