"""Fresh image-free replay and native-cache branches with explicit state identity."""
import time
import torch
from scripts.stage10a.common import verify_config,sha
from scripts.stage9a5.runtime import load_runtime as previous_load,inputs,environment
from scripts.stage9a5.native import sections
from visual_reasoning.stage9a_dynamics.generation import start,resume


def load_runtime():
    cfg=verify_config();old,processor,model=previous_load()
    assert cfg['checkpoint']==old['checkpoint'] and old['max_new_tokens']==cfg['max_total_tokens']==512
    return cfg,processor,model


def text_inputs(processor,model,task,prefix_ids):
    messages=[dict(role='user',content=[dict(type='text',text=task['prompt'])])]
    prepared=processor.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,
        return_dict=True,return_tensors='pt')
    assert set(prepared)<=set(['input_ids','attention_mask','mm_token_type_ids'])
    modality=prepared.get('mm_token_type_ids')
    if modality is not None:
        assert modality.shape==prepared['input_ids'].shape and bool((modality==0).all())
    prompt=prepared['input_ids'][0].tolist()
    assert model.config.image_token_id not in prompt and model.config.video_token_id not in prompt
    assert processor.tokenizer.decode(prompt[-12:],skip_special_tokens=False).endswith('<think>\n')
    ids=torch.tensor([prompt+prefix_ids],device='cuda:0')
    prepared=dict(input_ids=ids,attention_mask=torch.ones_like(ids))
    if modality is not None:prepared['mm_token_type_ids']=torch.zeros_like(ids)
    return prepared,dict(mode='fresh_text_only',image_present=False,original_cache_copied=False,
        image_derived_state_copied=False,prompt_length=len(prompt),prefix_tokens=len(prefix_ids),
        total_prefill_tokens=ids.shape[1],input_ids=ids[0].tolist())


def record(processor,model,all_ids,prefix_ids,runtime):
    assert all_ids[:len(prefix_ids)]==prefix_ids
    eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
    normal=bool(all_ids and all_ids[-1] in eos)
    decode=lambda ids:processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
    out=dict(generated_token_ids=all_ids,tokens=len(all_ids),prefix_tokens=len(prefix_ids),
        continuation_token_ids=all_ids[len(prefix_ids):],continuation_tokens=len(all_ids)-len(prefix_ids),
        text=decode(all_ids),continuation_text=decode(all_ids[len(prefix_ids):]),
        normal_eos=normal,at_length_cap=len(all_ids)>=512 and not normal,runtime_seconds=runtime)
    out.update(sections(all_ids,151668,decode));return out


@torch.inference_mode()
def fresh(processor,model,task,prefix_ids,seed):
    prepared,meta=text_inputs(processor,model,task,prefix_ids)
    begin=time.perf_counter();state,_=start(model,prepared,seed,512-len(prefix_ids),sample=False)
    ids=state.sequences[0,meta['prompt_length']:].tolist()
    return record(processor,model,ids,prefix_ids,time.perf_counter()-begin),meta


@torch.inference_mode()
def cached(processor,model,state,prompt_length,prefix_ids):
    assert state.cache.get_seq_length()==prompt_length+len(prefix_ids)-1
    assert state.sequences[0,prompt_length:].tolist()==prefix_ids
    begin=time.perf_counter();branch,_=resume(model,state,512-len(prefix_ids),sample=False)
    ids=branch.sequences[0,prompt_length:].tolist()
    return record(processor,model,ids,prefix_ids,time.perf_counter()-begin)
