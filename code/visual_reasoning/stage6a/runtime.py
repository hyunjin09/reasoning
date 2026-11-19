"""General single-image/text-only adapter for the unchanged native model path."""
import hashlib
import torch
from PIL import Image
from visual_reasoning.stage0.attention import visual_grid_metadata


def prepare_condition(processor, row, device):
    no_image=bool(row.get('no_image'))
    content=[];image=None;image_sha=None
    if not no_image:
        if not row.get('image_path'):raise ValueError('Image condition is missing its image')
        image=Image.open(row['image_path']).convert('RGB')
        image_sha=hashlib.sha256(image.tobytes()).hexdigest()
        content.append({'type':'image','image':image})
    content.append({'type':'text','text':row['prompt']})
    batch=processor.apply_chat_template([{'role':'user','content':content}],tokenize=True,
        add_generation_prompt=True,return_dict=True,return_tensors='pt')
    ids=batch['input_ids'][0];visual=(ids==int(processor.image_token_id)).nonzero().flatten().tolist()
    if no_image:
        if visual or 'pixel_values' in batch or 'image_grid_thw' in batch:
            raise RuntimeError('No-image prompt contains image state')
        grid=None;mapping=None
    else:
        if not visual or batch['image_grid_thw'].shape[0]!=1:raise RuntimeError('Expected one image')
        grid=list(map(int,batch['image_grid_thw'][0].tolist()))
        mapping=visual_grid_metadata(grid,merge_size=int(processor.image_processor.merge_size),patch_size=int(processor.image_processor.patch_size))
        if len(visual)!=mapping['visual_token_count']:raise RuntimeError('Visual token mapping mismatch')
    metadata=dict(event_id=row['event_id'],condition=row['condition'],image_path=row.get('image_path'),
        decoded_image_sha256=image_sha,image_size=list(image.size) if image else None,
        prompt=row['prompt'],prompt_token_count=len(ids),prompt_token_ids=ids.tolist(),
        visual_token_indices=visual,image_grid_thw=grid,visual_mapping=mapping,no_image=no_image,
        image_state_policy='fresh prepare and generation reset for each condition; no donor cache supplied')
    return {k:v.to(device) if isinstance(v,torch.Tensor) else v for k,v in batch.items()},metadata
