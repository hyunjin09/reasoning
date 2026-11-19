"""Frozen-prefix local greedy branches and exact-token teacher-forced scores."""
import os,socket,time,hashlib
from pathlib import Path
import torch
from scripts.stage10c.common import ROOT,load,sha,save,now
from scripts.stage10c.access import LocalAccessMask
from visual_reasoning.stage0.modeling import load_runtime as load_model,runtime_environment
from visual_reasoning.stage3c9.streaming import prefill_streaming_state,advance_streaming_state,clone_streaming_state
from visual_reasoning.stage8b.v2_protocol import prepared_input
from scripts.stage10b.passive_repair import inputs as verse_inputs
CONDITIONS=('NATIVE','PRE_ALL_OFF','POST_ALL_OFF','POST_TARGET_OFF','POST_IRRELEVANT_OFF')

def load_runtime():
 assert os.environ.get('SLURM_JOB_ID') and torch.cuda.device_count()==1
 assert socket.gethostname().split('.')[0] in ('node02','node03','node06','node07')
 cfg=load(ROOT/'config.json')
 for p,h in cfg['source_sha256'].items():assert sha(p)==h,p
 for p,h in cfg['frozen_artifact_sha256'].items():assert sha(p)==h,p
 info=cfg['model']
 for p,h in info['files_sha256'].items():assert sha(Path(info['checkpoint'])/p)==h,p
 torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
 proc,model=load_model(Path(info['checkpoint']),'cuda:0');env=runtime_environment(Path(info['checkpoint']),model,88)
 assert (env['language_layers'],env['attention_heads'],env['kv_heads'])==(28,16,8)
 assert str(next(model.parameters()).dtype)=='torch.bfloat16'
 assert env['language_attention_implementation']=='eager' and env['vision_attention_implementation']=='sdpa'
 env.update(at=now(),slurm_job_id=os.environ['SLURM_JOB_ID'],hostname=socket.gethostname(),tf32=False,
            model_revision=info['revision'],config_sha256=sha(ROOT/'config.json'),greedy=True)
 return proc,model,env

def inputs(proc,row):
 r=row['corpus'];native=Path(r['native_directory']);old=load(native/'input.json')
 assert sha(r['image'])==r['image_sha256']
 for p,h in r['source_sha256'].items():assert sha(p)==h,p
 if r['dataset']=='MathVerse':prepared,meta,evidence=verse_inputs(proc,r)
 else:
  manifest=load(native/'manifest_row.json');prepared,meta=prepared_input(proc,dict(manifest,answer=None))
  assert meta['pixel_values_sha256']==old['pixel_values_sha256'] and meta['prompt_ids_sha256']==old['prompt_ids_sha256']
  evidence=dict(prompt_ids_sha256=meta['prompt_ids_sha256'],pixel_values_sha256=meta['pixel_values_sha256'])
 assert meta['visual_token_indices']==old['visual_token_indices'] and meta['image_grid_thw']==old['image_grid_thw']
 assert prepared['input_ids'].shape[1]==old['prompt_token_count']
 generation=load(native/'generation.json');ids=generation['generated_token_ids']
 evidence.update(historical_input_sha256=sha(native/'input.json'),image_sha256=r['image_sha256'],prefix_native_sha256=sha(native/'generation.json'))
 return prepared,old,ids,generation['seed'],evidence

@torch.inference_mode()
def base_state(model,prepared,ids,seed,row):
 state,audit=prefill_streaming_state(model=model,prepared=prepared,seed=seed)
 # Leave the query immediately before PRE unprocessed so PRE's first predicted
 # token receives the intervention; all conditions share this exact native state.
 stop=row['pre_window'][0]-1
 advance_streaming_state(model=model,state=state,token_ids=ids[:stop],seed=seed,chunk_size=64)
 assert state.generated_length==stop and state.cache.get_seq_length()==state.prompt_length+stop
 return state,dict(audit,prefix_token_count=stop,prefix_ids_sha256=hashlib.sha256(str(ids[:stop]).encode()).hexdigest(),prefix_chunk=64)

def mask_args(row,meta,control,condition,audit=False):
 visual=meta['visual_token_indices']
 if condition=='POST_TARGET_OFF':visual=control['target_absolute']
 if condition=='POST_IRRELEVANT_OFF':visual=control['control_absolute']
 windows=[] if condition=='NATIVE' else [row['pre_window'] if condition=='PRE_ALL_OFF' else row['post_window']]
 return dict(visual=visual,prompt_length=meta['prompt_token_count'],intervals=windows,audit=audit)

@torch.inference_mode()
def free(model,proc,base,ids,seed,row,args,*,hook=True,logits=False):
 from contextlib import nullcontext
 state=clone_streaming_state(base);start=row['pre_window'][0];end=row['local_score_window'][1]
 next_input=ids[start-1];generated=[];raw=[];began=time.perf_counter()
 eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else eos
 cm=LocalAccessMask(**args) if hook else nullcontext()
 with cm as mask:
  for i in range(start,end):
   advance_streaming_state(model=model,state=state,token_ids=[next_input],seed=seed,chunk_size=1)
   assert state.generated_length==i
   if logits:raw.append(state.last_logits.detach().cpu())
   token=int(state.last_logits.argmax());generated.append(token);next_input=token
   if token in eos:break
 decode=lambda x:proc.tokenizer.decode(x,skip_special_tokens=True,clean_up_tokenization_spaces=False)
 local=generated[24:88];result=dict(generated_token_ids=generated,local_token_ids=local,text=decode(generated),local_text=decode(local),
  first_generated_index=start,local_start_offset=24,normal_eos=bool(generated and generated[-1] in eos),local_tokens=len(local),
  reached_local_cap=len(local)==64,seconds=time.perf_counter()-began,mask_records=mask.records if hook and args.get('audit') else None)
 del state
 return result,raw

@torch.inference_mode()
def teacher(model,base,ids,seed,row,args):
 state=clone_streaming_state(base);start=row['pre_window'][0];span=row['observation_span'];end=span['token_end'];lp=[];positions=[]
 assert span['token_start']>=row['onset'] and end>span['token_start']
 begin=time.perf_counter()
 with LocalAccessMask(**args) as mask:
  for i in range(start,end):
   advance_streaming_state(model=model,state=state,token_ids=[ids[i-1]],seed=seed,chunk_size=1)
   if i>=span['token_start']:
    lp.append(float(state.last_logits.float().log_softmax(-1)[ids[i]]));positions.append(i)
 assert positions==list(range(span['token_start'],end)) and torch.isfinite(torch.tensor(lp)).all()
 result=dict(evidence_token_ids=ids[span['token_start']:end],positions=positions,token_log_probabilities=lp,
  mean_nll=-sum(lp)/len(lp),sum_nll=-sum(lp),tokens=len(lp),seconds=time.perf_counter()-begin,
  mask_records=mask.records if args.get('audit') else None,exact_frozen_native_tokens=True)
 del state
 return result
