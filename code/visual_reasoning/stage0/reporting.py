"""Markdown and aggregate-summary rendering for Stage 0."""

from __future__ import annotations

from typing import Any


def environment_markdown(info: dict[str, Any]) -> str:
    return f"""# Stage 0 Environment

- Model checkpoint requested: `{info['model_checkpoint_requested']}`
- Model checkpoint resolved: `{info['model_checkpoint_resolved']}`
- Python environment: `{info['python_environment']}`
- Python: `{info['python_version']}`
- PyTorch: `{info['torch_version']}`
- Transformers: `{info['transformers_version']}`
- CUDA available: `{str(info['cuda_available']).lower()}`
- CUDA runtime used by PyTorch: `{info['torch_cuda_version']}`
- GPU: `{info['gpu_name']}`
- GPU total memory bytes: `{info['gpu_total_memory_bytes']}`
- Attention implementations: language=`eager`, vision=`sdpa`
- Generation: greedy, sampling disabled, max new tokens `{info['max_new_tokens']}`
- Conda environment: none; project-local `uv` environment `.venv` is used as required by `AGENTS.md`.
"""


def dataset_report_markdown(dataset_root: str, inventory: dict[str, Any]) -> str:
    variant_lines = "\n".join(f"  - {name}: {count}" for name, count in inventory["variant_counts"].items())
    return f"""# Stage 0 MathVerse Dataset Report

- Data location: `{dataset_root}`
- Metadata file: `testmini.json`
- Total rows: {inventory['total_rows']}
- Unique underlying problems: {inventory['unique_problem_count']}
- Pairing key: `{inventory['pairing_key']}`
- Complete variant groups: {inventory['complete_variant_group_count']}
- Selected examples: {inventory['selected_count']}
- Selected underlying problems: {inventory['selected_problem_count']}
- Selected sample indices: `{inventory['selected_sample_indices']}`

## Available variants

{variant_lines}

Rows sharing `problem_index` represent the same underlying problem. Locally, each
complete group contains Text Dominant, Text Lite, Vision Intensive, Vision
Dominant, and Vision Only variants. Questions and image references are stored per
variant. Stage 0 selects paired Vision Intensive and Vision Dominant rows in
numeric `problem_index` order; it does not run the paired-condition experiment.

JSON image references resolve under the local `images/` directory, for example
`images/images_version_1-4/image_1.png`.
"""


def model_report_markdown(info: dict[str, Any]) -> str:
    return f"""# Stage 0 Model Report

- Architecture: `{info['architecture']}`
- Checkpoint: `{info['model_checkpoint_resolved']}`
- Parameters: {info['parameter_count']}
- Language layers: {info['language_layers']}
- Attention heads: {info['attention_heads']}
- KV heads: {info['kv_heads']}
- Head dimension: {info['head_dimension']}
- Image token ID: {info['image_token_id']}
- Vision patch size: {info['vision_patch_size']}
- Vision spatial merge size: {info['vision_merge_size']}
- Weights modified: false
- Local-files-only loading: true

The released Transformers generation path is used. Language self-attention is
set through the public attention interface to `eager`, because the installed
`sdpa` implementation does not return attention weights. Vision attention
remains `sdpa`. Baseline and instrumented faithfulness runs use the same backend
configuration, weights, inputs, cache behavior, and greedy decoding.
"""


def instrumentation_markdown(info: dict[str, Any]) -> str:
    return f"""# Stage 0 Instrumentation

## Hook and computation path

Read-only forward hooks are attached to each of the {info['language_layers']}
Qwen3-VL language self-attention modules. The hook observes the attention
probabilities returned by the official eager implementation; these same
probabilities are used immediately by the model to compute the attention output.
The hook never changes module inputs, outputs, weights, KV caches, or logits.

## Prediction-step convention

The attention row recorded for generated token `t` is the final query row from
the forward pass whose logits select token `t`. For the first generated token,
this is the last prompt query in the prefill. For later tokens, it is the most
recent generated-token query. This is a prediction-time timeline, not a claim
that the emitted token retrospectively attends.

## Token regions

- Visual: initial-prompt positions whose token ID equals the checkpoint's image token ID.
- Prompt/question: every other initial-prompt position, including chat and visual-boundary tokens.
- Previous reasoning: cache positions at or after the initial prompt length.

These three regions partition the available language-attention keys at every
generation step. Their masses are retained per language layer after averaging
heads. Per-head modality masses are additionally retained for layers
`{info['selected_head_layers']}`.

## Online aggregation

Only the final query row is summarized. Full attention tensors are neither
retained nor transferred to CPU. Per step, the pipeline stores:

- modality mass with shape `[layers, 3]`;
- selected-layer head mass with shape `[selected_layers, heads, 3]`;
- visual focus averaged over layers and heads with shape `[visual_tokens]`;
- query and key lengths.

Arrays are detached, transferred to CPU once per generation step, streamed per
example to compressed NPZ, and released before the next example. The visual
focus is descriptive attention, not causal evidence.

## Spatial mapping

The processor emits `image_grid_thw`. Qwen's image processor groups
`merge_size × merge_size` patches and emits merged visual placeholders in
temporal-major, then row-major spatial order. Stage 0 verifies placeholder count
equals `t × (h/merge_size) × (w/merge_size)` before generation and records the
original image size, resized size, patch size, merge size, and both grids.

## Approximations and limitations

- Head-resolved modality mass is retained only at selected layers; all layers remain separately available after head averaging.
- Visual focus snapshots average attention over language layers and heads.
- Sentence/rule-based spans are provisional semantic groupings.
- Attention is descriptive and cannot establish visual causal dependence.
- Language eager attention may differ numerically from the default SDPA backend; the mandatory faithfulness comparison isolates hook effects by using eager for both conditions.
"""


def stage0_summary_markdown(summary: dict[str, Any]) -> str:
    criteria_lines = []
    for item in summary["acceptance_criteria"]:
        label = "PASS" if item["passed"] else "FAIL"
        criteria_lines.append(f"| {item['id']} | {item['name']} | {label} | {item['evidence']} |")
    criteria_table = "\n".join(criteria_lines)
    observations = "\n".join(f"- {value}" for value in summary.get("qualitative_observations", [])) or "- None recorded."
    hypotheses = "\n".join(f"- {value}" for value in summary.get("stage1_hypotheses", [])) or "- None proposed."
    stats = summary["correctness_and_filtering"]
    return f"""# Stage 0 Summary

- Mode: `{summary['mode']}`
- Examples processed: {summary['examples_processed']}
- Stage 0 pass: `{str(summary['stage0_pass']).lower()}`
- Stage 1 started: `false`
- Correct: {stats['correct']}
- Wrong: {stats['wrong']}
- Invalid: {stats['invalid']}
- Truncated: {stats['truncated']}
- Average generated tokens: {stats['average_reasoning_length_tokens']:.2f}
- Median generated tokens: {stats['median_reasoning_length_tokens']:.2f}

## Acceptance criteria

| ID | Criterion | Status | Evidence |
|---|---|---|---|
{criteria_table}

## Qualitative observations / hypotheses for later causal analysis

{observations}

These are descriptive Stage 0 observations, not established mechanisms.

## Promising Stage 1 hypotheses

{hypotheses}

## Known limitations

- Eager language attention is required to observe exact attention probabilities.
- Attention summaries are descriptive, not causal visual-usage measurements.
- Reasoning spans are provisional rule-based segments.
- The selected 30–50 examples are an instrumentation subset, not a benchmark estimate.
- A 2,048-token safety cap can truncate repetitive trajectories; these are retained and reported rather than silently discarded.

Stage 0 stops here. Stage 1 was not started automatically.
"""
