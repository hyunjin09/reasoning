"""Pinned Slurm-only generation with full-cap admission and allocation accounting."""
import hashlib,importlib.metadata,os,socket,subprocess,time,json
from pathlib import Path
from scripts.stage14e.common import *
from scripts.stage14e.resource_guard import allowance
class Engine:
 def __init__(self,m):
  assert os.environ.get('SLURM_JOB_ID') and os.environ.get('VLLM_ENABLE_V1_MULTIPROCESSING')=='0'
  self.m=m;self.root=P/'raw'/m['id'];assert not self.root.exists(),'Use an immutable new attempt'
  self.job=os.environ['SLURM_JOB_ID'];self.start=time.monotonic();self.cfg=load(m['runtime']);self.count=0;self.last_budget=0;self.last_heartbeat=0
  import torch
  from transformers import AutoProcessor
  from vllm import LLM
  import sys
  sys.path.insert(0,str(Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision').resolve()))
  from run_mathv import prepare_inputs_for_vllm,build_mathv_prompt
  self.prepare=prepare_inputs_for_vllm;self.build=build_mathv_prompt
  assert torch.cuda.device_count()==self.m['gpus']
  versions={k:importlib.metadata.version(k) for k in self.cfg['environment']};assert versions==self.cfg['environment']
  self.processor=AutoProcessor.from_pretrained(self.cfg['model']['model']['checkpoint'])
  self.llm=LLM(model=self.cfg['model']['model']['checkpoint'],dtype='bfloat16',tensor_parallel_size=self.m['gpus'],seed=42,
   gpu_memory_utilization=self.cfg['runtime']['gpu_memory_utilization'],max_model_len=self.cfg['runtime']['max_model_len'],max_num_seqs=self.cfg['runtime']['max_num_seqs'],limit_mm_per_prompt={'image':3},enable_prefix_caching=False,trust_remote_code=True)
  self.engine=self.llm.llm_engine;cache=self.engine.vllm_config.cache_config
  self.block=cache.block_size;self.capacity=cache.num_gpu_blocks*self.block-4096
  save(self.root/'environment.json',{'at':now(),'job':self.job,'node':socket.gethostname(),'gpu':torch.cuda.get_device_name(0),'versions':versions,
   'engine_config':str(self.engine.vllm_config),'runtime_sha256':sha(m['runtime']),'manifest':m,'ready_seconds':time.monotonic()-self.start,'usable_token_capacity':self.capacity})
 def budget_check(self):
  if time.monotonic()-self.last_budget<30:return
  self.last_budget=time.monotonic()
  r=subprocess.run(['sacct','-X','-n','-P','-j',self.job,'--format=JobIDRaw,ElapsedRaw,AllocTRES'],capture_output=True,text=True,check=True,timeout=10)
  lines=[l.split('|') for l in r.stdout.splitlines() if l.split('|')[0]==self.job]
  if not lines:raise RuntimeError('Cannot verify allocation budget')
  elapsed=int(lines[0][1])*self.m['gpus'];self.elapsed=elapsed
  update(self.root/'allocation_progress.json',{'at':now(),'job':self.job,'elapsed_gpu_seconds':elapsed,'reserved_seconds':allowance(self.m)})
  # This explicit reservation enforces the user ceiling, not an arbitrary rollout timeout.
  if elapsed>=allowance(self.m)-60:raise RuntimeError('EXPLICIT_GPU_BUDGET_RESERVATION_EXHAUSTED')
 def calls(self,tasks,width=4):
  from vllm import SamplingParams
  from vllm.sampling_params import StructuredOutputsParams
  active={};answers={};cursor=0;pending=None
  while cursor<len(tasks) or active:
   try:self.budget_check()
   except BaseException as exc:
    for rid,a in active.items():
     out=a['latest'].outputs[0] if a['latest'] else None
     save(self.root/rid/'interrupted.json',{'at':now(),'reason':'BUDGET_OR_ACCOUNTING','error':repr(exc),'raw':out.text if out else '', 'tokens':list(out.token_ids) if out else []})
    raise
   while cursor<len(tasks) and len(active)<width:
    t=tasks[cursor];r=t['row'];rid=t['id'];folder=self.root/rid
    if pending is None:
     tick=time.monotonic();images=t.get('images',[])
     if t['kind']=='solver':
      assert sha(r['image'])==r['image_sha256']
      inp=self.prepare(r['original_messages'],self.processor);assert inp['prompt']==r['original_chat_prompt']
      inp['prompt']+=r['prefix']+t.get('suffix','');images=[r['image']]
     else:
      msgs=self.build({'question':t['prompt']},lambda _:images,'MathVision') if images else [{'role':'user','content':[{'type':'text','text':t['prompt']}]}]
      inp=self.prepare(msgs,self.processor) if images else {'prompt':self.processor.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)}
      assert inp['prompt'].endswith('<think>\n');inp['prompt']+='</think>\n\n'
     ims=inp.get('multi_modal_data',{}).get('image',[])
     pixels=[hashlib.sha256(im.tobytes()).hexdigest() for im in ims];sizes=[list(im.size) for im in ims]
     if t['kind']=='solver':assert pixels==r['original_image_pixels'] and sizes==r['original_image_sizes']
     bound=len(self.processor.tokenizer.encode(inp['prompt']))+sum(w*h//1024 for w,h in sizes)+256
     reserve=((bound+t['cap']+self.block-1)//self.block)*self.block
     assert reserve<=self.capacity,'One request exceeds full-cap KV capacity'
     pending=(inp,pixels,sizes,reserve,images,time.monotonic()-tick)
    inp,pixels,sizes,reserve,images,prep=pending
    if sum(a['reserve'] for a in active.values())+reserve>self.capacity:break
    assert not folder.exists(),rid
    save(folder/'input.json',{'at':now(),'id':rid,'item_id':r['item_id'],'family_id':r['family_id'],'kind':t['kind'],
      'condition':t.get('condition'),'prompt':inp['prompt'],'images':images,'pixels':pixels,'sizes':sizes,'preprocessing_seconds':prep,
      'prefix_sha256':r['prefix_sha256'],'seed':t.get('seed',r['seed']),'sampling':self.cfg['helper_recipe'],'cap':t['cap'],'schema':t.get('schema'),'job':self.job,
      'full_cap_token_reservation':reserve,'diagnostic_oracle_target':t.get('oracle',False)})
    pars=SamplingParams(**self.cfg['helper_recipe'],max_tokens=t['cap'],seed=t.get('seed',r['seed']),stop_token_ids=[],ignore_eos=False,
     structured_outputs=StructuredOutputsParams(json=t['schema']) if t.get('schema') else None)
    self.engine.add_request(rid,inp,pars);active[rid]={'task':t,'started':time.monotonic(),'reserve':reserve,'latest':None};cursor+=1;pending=None
   if not active:raise RuntimeError('No admissible task')
   try:updates=self.engine.step()
   except BaseException as exc:
    for rid,a in active.items():
     out=a['latest'].outputs[0] if a['latest'] else None
     save(self.root/rid/'interrupted.json',{'at':now(),'error':repr(exc),'raw':out.text if out else '', 'tokens':list(out.token_ids) if out else []})
    raise
   for out in updates:
    a=active[out.request_id];a['latest']=out
    if not out.finished:continue
    g=out.outputs[0];rid=out.request_id;folder=self.root/rid
    receipt={'at':now(),'id':rid,'tokens':len(g.token_ids),'generated_token_ids':list(g.token_ids),'raw_decoded_response':g.text,
      'prompt_token_ids':list(out.prompt_token_ids),'prompt_tokens':len(out.prompt_token_ids),'visual_tokens':sum(v==151655 for v in out.prompt_token_ids),
      'finish_reason':g.finish_reason,'stop_reason':g.stop_reason,'cap_hit':g.finish_reason=='length','latency_seconds':time.monotonic()-a['started'],
      'job':self.job,'node':socket.gethostname(),'seed':a['task'].get('seed',a['task']['row']['seed'])}
    save(folder/'generation.json',receipt);save(folder/'result.json',{'input_sha256':sha(folder/'input.json'),'generation_sha256':sha(folder/'generation.json')})
    answers[rid]=dict(receipt,generation_path=str(folder/'generation.json'));del active[rid];self.count+=1
    print('COMPLETE',rid,receipt['tokens'],receipt['finish_reason'],flush=True)
   if time.monotonic()-self.last_heartbeat>60:
    update(self.root/'progress.json',{'at':now(),'completed':self.count,'pending_in_phase':len(tasks)-cursor,'active':{k:len(a['latest'].outputs[0].token_ids) if a['latest'] else 0 for k,a in active.items()}})
    self.last_heartbeat=time.monotonic()
  return answers
