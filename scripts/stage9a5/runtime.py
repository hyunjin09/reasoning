"""Stage-local4B loader; share immutable input/generation code with9A.3."""
import os,socket
from pathlib import Path
import torch
from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
from scripts.stage9a5.common import ROOT,verify_config,sha,save,now
from scripts.stage9a3.runtime import inputs as base_inputs,generate as base_generate,start,resume
from scripts.stage9a5.native import sections


def inputs(processor,model,row):
    prepared,meta=base_inputs(processor,model,row)
    suffix=processor.tokenizer.decode(meta['input_ids'][-12:],skip_special_tokens=False)
    assert suffix.endswith('<think>\n'),'Native Thinking prefix missing'
    meta.update(native_thinking_prefix=True,prompt_suffix=suffix)
    return prepared,meta


def generate(model,processor,prepared,cap,seed):
    g=base_generate(model,processor,prepared,cap,seed)
    assert processor.tokenizer.convert_tokens_to_ids('</think>')==151668
    g.update(sections(g['generated_token_ids'],151668,
        lambda ids:processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)))
    return g


def load_runtime():
    assert os.environ.get('SLURM_JOB_ID') and torch.cuda.device_count()==1
    cfg=verify_config();assert socket.gethostname().split('.')[0] in cfg['allowed_nodes']
    for name,digest in cfg['files_sha256'].items():assert sha(Path(cfg['checkpoint'])/name)==digest,name
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    processor=AutoProcessor.from_pretrained(cfg['checkpoint'],local_files_only=True,min_pixels=cfg['min_pixels'],max_pixels=cfg['max_pixels'])
    model=Qwen3VLForConditionalGeneration.from_pretrained(cfg['checkpoint'],local_files_only=True,dtype=torch.bfloat16,
        attn_implementation={'vision_config':'sdpa','text_config':'eager'},low_cpu_mem_usage=True).to('cuda:0').eval()
    assert model.config.text_config.num_hidden_layers==cfg['layers']==36
    assert model.config.text_config._attn_implementation=='eager'
    assert model.config.vision_config._attn_implementation=='sdpa'
    return cfg,processor,model


def environment(model):
    import transformers
    return dict(at=now(),slurm_job_id=os.environ['SLURM_JOB_ID'],node=socket.gethostname(),
        gpu=torch.cuda.get_device_name(0),torch_version=torch.__version__,transformers_version=transformers.__version__,
        dtype=str(next(model.parameters()).dtype),layers=model.config.text_config.num_hidden_layers,
        config_sha256=sha(ROOT/'config.json'))
