"""Single-GPU local checkpoint runtime and common inference inputs."""
import hashlib,os,socket,time
from pathlib import Path
import torch
from PIL import Image
from transformers import AutoProcessor,Qwen2_5_VLForConditionalGeneration,Qwen3VLForConditionalGeneration
from scripts.stage9a3.prepare import ROOT,load,sha
from visual_reasoning.stage9a_dynamics.generation import start,resume


def load_runtime(key):
    assert os.environ.get('SLURM_JOB_ID') and torch.cuda.device_count()==1
    cfg=load(ROOT/'config.json');assert socket.gethostname().split('.')[0] in cfg['allowed_nodes']
    if key=='qwen3':assert load(ROOT/'stage9a3_qwen25_positive_control.json')['pass'], 'Phase A must pass before Qwen3 compute'
    for filename,expected in cfg['models'][key]['files_sha256'].items():
        assert sha(Path(cfg['models'][key]['checkpoint'])/filename)==expected
    assert sha('plan/stage9a3_execution_protocol_v1.md')==cfg['protocol_sha256']
    assert sha(ROOT/'audit/inference_tasks.json')==cfg['tasks_sha256']
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    checkpoint=cfg['models'][key]['checkpoint']
    processor=AutoProcessor.from_pretrained(checkpoint,local_files_only=True,min_pixels=cfg['min_pixels'],max_pixels=cfg['max_pixels'])
    cls=Qwen2_5_VLForConditionalGeneration if key=='qwen25' else Qwen3VLForConditionalGeneration
    model=cls.from_pretrained(checkpoint,local_files_only=True,dtype=torch.bfloat16,
         attn_implementation={'vision_config':'sdpa','text_config':'eager'},low_cpu_mem_usage=True).to('cuda:0').eval()
    assert model.config.text_config._attn_implementation=='eager' and model.config.vision_config._attn_implementation=='sdpa'
    return cfg,processor,model


def inputs(processor,model,row):
    assert 'answer' not in row and 'count' not in row
    assert sha(row['image_path'])==row['image_sha256']
    with Image.open(row['image_path']) as source:im=source.convert('RGB')
    messages=[dict(role='user',content=[dict(type='image',image=im),dict(type='text',text=row['prompt'])])]
    prepared=processor.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_dict=True,return_tensors='pt')
    prepared={k:v.to('cuda:0') if isinstance(v,torch.Tensor) else v for k,v in prepared.items()}
    ids=prepared['input_ids'][0];p=len(ids);visual=torch.where(ids==model.config.image_token_id)[0].tolist();assert visual
    meta=dict(query_id=row['query_id'],prompt_length=p,visual=visual,input_ids=ids.tolist(),
        image_grid_thw=prepared['image_grid_thw'].cpu().tolist(),image_sha256=row['image_sha256'],
        pixel_values_sha256=hashlib.sha256(prepared['pixel_values'].cpu().float().numpy().tobytes()).hexdigest())
    return prepared,meta


@torch.inference_mode()
def generate(model,processor,prepared,cap,seed):
    began=time.perf_counter();state,out=start(model,prepared,seed,cap,sample=False)
    ids=state.sequences[0,prepared['input_ids'].shape[1]:].tolist()
    eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
    result=dict(generated_token_ids=ids,text=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False),
                normal_eos=bool(ids and ids[-1] in eos),tokens=len(ids),runtime_seconds=time.perf_counter()-began)
    result['at_length_cap']=len(ids)>=cap and not result['normal_eos']
    return result
