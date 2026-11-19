"""Ordinary batched native/oracle generation; no interventions or scoring."""
import copy, hashlib, time
from pathlib import Path
import torch
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
from qwen_vl_utils import process_vision_info
from visual_reasoning.stage8b.v2_protocol import MIN_PIXELS,MAX_PIXELS
from visual_reasoning.stage9a.protocol import prompt
from scripts.stage11b.protocol import trim_generated

def runtime(info):
    proc=AutoProcessor.from_pretrained(info['checkpoint'],local_files_only=True)
    proc.tokenizer.padding_side='left'
    model=Qwen3VLForConditionalGeneration.from_pretrained(info['checkpoint'],dtype=torch.bfloat16,
        attn_implementation={'vision_config':'sdpa','text_config':'sdpa'},local_files_only=True).to('cuda:0').eval()
    assert next(model.parameters()).dtype==torch.bfloat16
    return proc,model

def prepare(proc,rows,device='cuda:0'):
    texts=[];images=[];metas=[]
    native=rows[0]['condition']=='native'
    assert all((r['condition']=='native')==native for r in rows)
    for r in rows:
        query=prompt(r['generation_query'],r['arm'])
        content=[dict(type='text',text=query)]
        if native:
            content.insert(0,dict(type='image',image=r['image'],min_pixels=MIN_PIXELS,max_pixels=MAX_PIXELS))
        messages=[dict(role='user',content=content)]
        text=proc.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        expected='<|im_start|>assistant\n<think>\n' if r['arm']=='thinking' else '<|im_start|>assistant\n'
        assert text.endswith(expected)
        if native:
            ims,vids,kwargs=process_vision_info(messages,image_patch_size=proc.image_processor.patch_size,
                return_video_kwargs=True,return_video_metadata=True)
            assert vids is None and len(ims)==1
            images.extend(ims)
        texts.append(text)
        metas.append(dict(task_id=r['task_id'],chat_prompt=text,generation_query=query,image_present=native,
            image_sha256=r.get('image_sha256') if native else None,oracle_evidence_sha256=r.get('oracle_evidence_sha256')))
    batch=proc(text=texts,images=images if native else None,padding=True,return_tensors='pt')
    assert ('pixel_values' in batch)==native
    for i,m in enumerate(metas):
        ids=batch['input_ids'][i][batch['attention_mask'][i].bool()]
        visual=(ids==proc.image_token_id).sum().item()
        assert (visual>0)==native
        m.update(prompt_token_count=len(ids),visual_token_count=visual,input_ids_sha256=hashlib.sha256(ids.numpy().tobytes()).hexdigest(),
            batch_left_padding=int((batch['attention_mask'][i]==0).sum()),image_grid_thw=batch['image_grid_thw'][i].tolist() if native else None)
    return {k:v.to(device) if isinstance(v,torch.Tensor) else v for k,v in batch.items()},metas

def generate(proc,model,batch,cap,max_time=None):
    cfg=copy.deepcopy(model.generation_config)
    cfg.do_sample=False;cfg.temperature=None;cfg.top_p=None;cfg.top_k=None
    cfg.repetition_penalty=1.;cfg.max_new_tokens=cap;cfg.use_cache=True
    cfg.pad_token_id=proc.tokenizer.pad_token_id
    eos=cfg.eos_token_id;eos={eos} if isinstance(eos,int) else set(eos)
    torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();start=time.monotonic()
    with torch.inference_mode():
        output=model.generate(**batch,generation_config=cfg,return_dict_in_generate=False,
            max_time=max_time,output_scores=False,output_logits=False)
    torch.cuda.synchronize();elapsed=time.monotonic()-start
    records=[]
    for raw in output[:,batch['input_ids'].shape[1]:].tolist():
        ids,eos_stop,capped=trim_generated(raw,eos,cap)
        text=proc.tokenizer.decode(ids,skip_special_tokens=False)
        records.append(dict(generated_token_ids=ids,raw_decoded_response=text,tokens=len(ids),normal_eos=eos_stop,
            at_length_cap=capped,budget_interrupted=not eos_stop and not capped,has_think_end='</think>' in text,
            batch_seconds=elapsed,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
            peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved()))
    return records
