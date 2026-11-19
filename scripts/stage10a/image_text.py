"""Fresh multimodal prefill with a forced native/edited reasoning prefix."""
import time
import torch
from scripts.stage10a.runtime import inputs,start,record


@torch.inference_mode()
def fresh_image(processor,model,task,prefix_ids,seed,count=None):
    prepared,meta=inputs(processor,model,task);prompt=meta['prompt_length']
    assert set(prepared)<=set(['input_ids','attention_mask','mm_token_type_ids','pixel_values','image_grid_thw'])
    prepared['input_ids']=torch.cat([prepared['input_ids'],torch.tensor([prefix_ids],device='cuda:0')],dim=1)
    prepared['attention_mask']=torch.ones_like(prepared['input_ids'])
    if 'mm_token_type_ids' in prepared:
        prepared['mm_token_type_ids']=torch.cat([prepared['mm_token_type_ids'],torch.zeros((1,len(prefix_ids)),device='cuda:0',dtype=prepared['mm_token_type_ids'].dtype)],dim=1)
    begin=time.perf_counter();state,_=start(model,prepared,seed,512-len(prefix_ids) if count is None else count,sample=False)
    ids=state.sequences[0,prompt:].tolist()
    assert ids[:len(prefix_ids)]==prefix_ids
    details=dict(mode='fresh_image_text',image_present=True,original_cache_copied=False,image_derived_state_copied=False,
        image_state_recomputed_from_current_image=True,prefix_tokens=len(prefix_ids),total_prefill_tokens=prompt+len(prefix_ids),input=meta)
    return record(processor,model,ids,prefix_ids,time.perf_counter()-begin),details
