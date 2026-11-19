"""Frozen MathVision-specific generation; completion is independent of outcome."""

MIN_PIXELS = 768 * 28 * 28
MAX_PIXELS = 5120 * 28 * 28


def prepared_input(processor, row, device='cuda:0'):
    import hashlib
    from pathlib import Path
    import torch
    from PIL import Image
    from qwen_vl_utils import process_vision_info
    from visual_reasoning.stage0.attention import visual_grid_metadata

    source = Path(row['image'])
    assert hashlib.sha256(source.read_bytes()).hexdigest() == row['image_sha256']
    messages = [{'role': 'user', 'content': [
        {'type': 'image', 'image': str(source), 'min_pixels': MIN_PIXELS, 'max_pixels': MAX_PIXELS},
        {'type': 'text', 'text': row['generation_query']},
    ]}]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    images, videos, video_kwargs = process_vision_info(messages,
        image_patch_size=processor.image_processor.patch_size,
        return_video_kwargs=True, return_video_metadata=True)
    assert videos is None and len(images) == 1
    batch = processor(text=[text], images=images, return_tensors='pt', **video_kwargs)
    ids = batch['input_ids'][0]
    visual = (ids == int(processor.image_token_id)).nonzero().flatten().tolist()
    visual_set = set(visual)
    grid = [int(x) for x in batch['image_grid_thw'][0].tolist()]
    mapping = visual_grid_metadata(grid, merge_size=int(processor.image_processor.merge_size),
                                  patch_size=int(processor.image_processor.patch_size))
    assert visual and len(visual) == mapping['visual_token_count']
    assert list(images[0].size) == list(mapping['resized_image_size'])
    with Image.open(source) as image:
        original_size = list(image.size)
    metadata = dict(example_id=row['item_id'], sample_index=row['item_id'], problem_index=row['item_id'],
        question=row['question'], generation_query=row['generation_query'],
        image_reference=str(source), resolved_image_path=str(source.resolve()),
        original_image_size=original_size, ground_truth_answer=row['answer'],
        prompt_token_count=int(ids.numel()), visual_token_indices=visual,
        prompt_nonvisual_token_indices=[i for i in range(ids.numel()) if i not in visual_set],
        visual_mapping=mapping, image_grid_thw=grid, chat_prompt=text,
        preprocessing=dict(min_pixels=MIN_PIXELS, max_pixels=MAX_PIXELS,
            patch_size=int(processor.image_processor.patch_size),
            merge_size=int(processor.image_processor.merge_size),
            resized_image_size=list(images[0].size), path='qwen_process_vision_info_then_HF_processor'),
        prompt_ids_sha256=hashlib.sha256(ids.numpy().tobytes()).hexdigest(),
        pixel_values_sha256=hashlib.sha256(batch['pixel_values'].numpy().tobytes()).hexdigest())
    return {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}, metadata


def generation_parameters():
    # HF has no presence processor by default: this implements penalty zero.
    return dict(do_sample=True, temperature=1.0, top_p=0.95, top_k=20, repetition_penalty=1.0)


def completion_status(text, *, normal_eos, at_length_cap, tokens):
    has_end = '</think>' in text
    if normal_eos and has_end:
        label = 'normal completed'
    elif at_length_cap and not has_end and not normal_eos:
        label = 'capped without final section'
    else:
        label = 'other abnormal stop'
    return dict(completion=label, has_think_end=has_end, normal_eos=bool(normal_eos),
                at_length_cap=bool(at_length_cap), tokens=int(tokens))
