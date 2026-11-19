from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import torch
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration


@dataclass
class PreparedPrefill:
    input_ids: torch.Tensor
    inputs_embeds: torch.Tensor
    attention_mask: torch.Tensor
    position_ids: torch.Tensor | None
    visual_pos_mask: torch.Tensor
    visual_positions: torch.Tensor
    deepstack_visual_embeds: list[torch.Tensor] | None
    image_grid_thw: torch.Tensor | None
    mm_token_type_ids: torch.Tensor | None

    @property
    def seq_len(self) -> int:
        return int(self.inputs_embeds.shape[1])

    @property
    def num_visual_tokens(self) -> int:
        return int(self.visual_positions.numel())


def load_processor(snapshot_path: str | Path):
    return AutoProcessor.from_pretrained(Path(snapshot_path), local_files_only=True)


def load_qwen_model(snapshot_path: str | Path, dtype_name: str = "bfloat16", device: str = "cuda"):
    dtype = torch.bfloat16 if dtype_name in {"bf16", "bfloat16"} else torch.float16
    model = Qwen3VLForConditionalGeneration.from_pretrained(
        Path(snapshot_path),
        local_files_only=True,
        dtype=dtype,
        low_cpu_mem_usage=True,
        attn_implementation="eager",
    )
    model.eval()
    if device:
        model.to(device)
    return model, dtype


def build_messages(image_path: str, prompt: str) -> list[dict[str, Any]]:
    return [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": prompt},
            ],
        }
    ]


def processor_inputs(processor: Any, image_path: str, prompt: str) -> dict[str, torch.Tensor]:
    return processor.apply_chat_template(
        build_messages(image_path, prompt),
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )


def move_inputs(inputs: dict[str, torch.Tensor], device: torch.device | str) -> dict[str, torch.Tensor]:
    moved = {}
    for key, value in inputs.items():
        moved[key] = value.to(device) if torch.is_tensor(value) else value
    return moved


def build_prefill(model: Any, inputs: dict[str, torch.Tensor]) -> PreparedPrefill:
    input_ids = inputs["input_ids"]
    attention_mask = inputs.get("attention_mask")
    if attention_mask is None:
        attention_mask = torch.ones_like(input_ids)
    mm_token_type_ids = inputs.get("mm_token_type_ids")
    image_grid_thw = inputs.get("image_grid_thw")

    model.model.rope_deltas = None
    inputs_embeds = model.model.get_input_embeddings()(input_ids)
    visual_pos_mask = torch.zeros(input_ids.shape, dtype=torch.bool, device=input_ids.device)
    deepstack_visual_embeds = None

    if inputs.get("pixel_values") is not None:
        image_outputs = model.model.get_image_features(
            inputs["pixel_values"],
            image_grid_thw,
            return_dict=True,
        )
        image_embeds = torch.cat(image_outputs.pooler_output, dim=0).to(inputs_embeds.device, inputs_embeds.dtype)
        image_mask, _ = model.model.get_placeholder_mask(
            input_ids,
            inputs_embeds=inputs_embeds,
            image_features=image_embeds,
        )
        inputs_embeds = inputs_embeds.masked_scatter(image_mask, image_embeds)
        visual_pos_mask = image_mask[..., 0].to(torch.bool)
        deepstack_visual_embeds = [
            features.to(inputs_embeds.device, inputs_embeds.dtype)
            for features in image_outputs.deepstack_features
        ]

    position_ids = model.model.compute_3d_position_ids(
        input_ids=input_ids,
        inputs_embeds=inputs_embeds,
        image_grid_thw=image_grid_thw,
        video_grid_thw=inputs.get("video_grid_thw"),
        attention_mask=attention_mask,
        past_key_values=None,
        mm_token_type_ids=mm_token_type_ids,
    )
    visual_positions = visual_pos_mask[0].nonzero(as_tuple=False).flatten()
    return PreparedPrefill(
        input_ids=input_ids,
        inputs_embeds=inputs_embeds,
        attention_mask=attention_mask,
        position_ids=position_ids,
        visual_pos_mask=visual_pos_mask,
        visual_positions=visual_positions,
        deepstack_visual_embeds=deepstack_visual_embeds,
        image_grid_thw=image_grid_thw,
        mm_token_type_ids=mm_token_type_ids,
    )


def prune_prefill(prefill: PreparedPrefill, retained_visual_indices: list[int]) -> PreparedPrefill:
    keep = torch.ones(prefill.seq_len, dtype=torch.bool, device=prefill.inputs_embeds.device)
    retained = set(retained_visual_indices)
    for visual_idx, seq_pos in enumerate(prefill.visual_positions.tolist()):
        if visual_idx not in retained:
            keep[seq_pos] = False

    pruned_visual_pos_mask = prefill.visual_pos_mask[:, keep]
    pruned_visual_positions = pruned_visual_pos_mask[0].nonzero(as_tuple=False).flatten()
    position_ids = prefill.position_ids
    if position_ids is not None:
        position_ids = position_ids[:, :, keep]
    deepstack = None
    if prefill.deepstack_visual_embeds is not None:
        index = torch.tensor(retained_visual_indices, dtype=torch.long, device=prefill.inputs_embeds.device)
        deepstack = [features.index_select(0, index) for features in prefill.deepstack_visual_embeds]

    return replace(
        prefill,
        input_ids=prefill.input_ids[:, keep],
        inputs_embeds=prefill.inputs_embeds[:, keep, :],
        attention_mask=prefill.attention_mask[:, keep],
        position_ids=position_ids,
        visual_pos_mask=pruned_visual_pos_mask,
        visual_positions=pruned_visual_positions,
        deepstack_visual_embeds=deepstack,
    )


def language_model_forward(model: Any, prefill: PreparedPrefill, past_key_values=None):
    return model.model.language_model(
        input_ids=None,
        inputs_embeds=prefill.inputs_embeds,
        attention_mask=prefill.attention_mask,
        position_ids=prefill.position_ids,
        past_key_values=past_key_values,
        use_cache=True,
        visual_pos_masks=prefill.visual_pos_mask,
        deepstack_visual_embeds=prefill.deepstack_visual_embeds,
        return_dict=True,
    )

