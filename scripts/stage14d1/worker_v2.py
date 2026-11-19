"""Bounded SAVA worker: runtime-only input allowlist, immutable requests and no oracle imports."""
import argparse,os,socket,time,hashlib,traceback,importlib.metadata
from pathlib import Path
from scripts.stage14d1.common import *
from scripts.stage14d1.contracts_v2 import *
from scripts.stage14d1.views import render_views

def run(manifest):
 job=os.environ['SLURM_JOB_ID'];node=socket.gethostname().split('.')[0];assert node in {'node02','node03','node06','node07'}
 started=time.monotonic();m=load(manifest);cfg=load(P/'protocol/runtime_v2.json');mode=m['mode'];assert mode in ['technical','main']
 seal=load(P/'audit/execution_seal_v2.json')
 for path,h in seal['files'].items():assert sha(path)==h,path
 assert sha(manifest)==m['manifest_identity'] if 'manifest_identity' in m else True
 if mode=='main':assert load(P/'audit/technical_gate.json')['pass']
 family={r['family_id']:safe_payload(r) for r in rows(P/'inference/families.jsonl')};work=[family[f] for f in m['families']]
 outroot=P/'raw'/(mode+'_v2');dest=P/'audit/workers'/job
 for r in work:assert sha(r['image'])==r['image_sha256'];assert hashlib.sha256(r['prefix'].encode()).hexdigest()==r['prefix_sha256']
 for name,h in cfg['model']['model']['files_sha256'].items():assert sha(Path(cfg['model']['model']['checkpoint'])/name)==h,name
 import sys,torch
 from vllm import LLM,SamplingParams
 from vllm.sampling_params import StructuredOutputsParams
 from transformers import AutoProcessor
 sys.path.insert(0,str(Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision').resolve()))
 from run_mathv import build_mathv_prompt,prepare_inputs_for_vllm
 assert torch.cuda.device_count()==1
 versions={k:importlib.metadata.version(k) for k in cfg['environment']};assert versions==cfg['environment']
 save(dest/'environment.json',dict(at=now(),job=job,node=node,gpu=torch.cuda.get_device_name(0),packages=versions,manifest=manifest,manifest_sha256=sha(manifest),runtime_sha256=sha(P/'protocol/runtime_v2.json')))
 proc=AutoProcessor.from_pretrained(cfg['model']['model']['checkpoint']);rt=cfg['runtime']
 llm=LLM(model=cfg['model']['model']['checkpoint'],dtype='bfloat16',tensor_parallel_size=1,seed=rt['engine_seed'],gpu_memory_utilization=rt['gpu_memory_utilization'],max_model_len=rt['max_model_len'],max_num_seqs=rt['max_num_seqs'],limit_mm_per_prompt={'image':3},trust_remote_code=True)
 engine=llm.llm_engine;completed=0
 save(dest/'ready.json',dict(at=now(),seconds=time.monotonic()-started,mode=mode,families=[r['item_id'] for r in work],dtype=str(engine.model_config.dtype)))
 def call_batch(jobs):
  nonlocal completed
  answers={};active={};cursor=0;last=0;tick=0
  while cursor<len(jobs) or active:
   while cursor<len(jobs) and len(active)<rt['max_num_seqs']:
    t=jobs[cursor];cursor+=1;rid=t['id'];folder=outroot/rid
    if (folder/'result.json').exists():
     receipt=load(folder/'result.json');assert sha(folder/'generation.json')==receipt['generation_sha256'];answers[rid]=load(folder/'generation.json');continue
    assert not folder.exists(),('partial call requires preserved versioned recovery',rid)
    if time.monotonic()-started>m['wall_seconds']-120:
     save(folder/'failure.json',dict(at=now(),reason='ALLOCATION_ADMISSION_STOP'));answers[rid]=None;continue
    r=t['row'];images=t.get('images',[])
    if t['kind']=='solver':
     inp=prepare_inputs_for_vllm(r['original_messages'],proc);assert inp['prompt']==r['original_chat_prompt']
     sizes=[list(im.size) for im in inp['multi_modal_data']['image']];pixels=[hashlib.sha256(im.tobytes()).hexdigest() for im in inp['multi_modal_data']['image']]
     assert sizes==r['original_image_sizes'] and pixels==r['original_image_pixels'],('source preprocessing parity',r['item_id'])
     base=inp['prompt']+r['prefix'];inp['prompt']=base+t.get('suffix','');messages=r['original_messages']
    else:
     prompt=compact_prompt(t['prompt']);messages=build_mathv_prompt({'question':prompt},lambda _:images,'MathVision') if images else [dict(role='user',content=[dict(type='text',text=prompt)])]
     inp=prepare_inputs_for_vllm(messages,proc) if images else {'prompt':proc.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)}
     base=None
    structured=None
    if t['kind']!='solver':
     assert inp['prompt'].endswith('<think>\n')
     inp['prompt']+='</think>\n\n'
     structured=StructuredOutputsParams(json=SCHEMAS[t['kind']])
    param=SamplingParams(**cfg['helper_recipe'],max_tokens=t['cap'],seed=r['seed'],stop_token_ids=[],ignore_eos=False,structured_outputs=structured)
    image_data=inp.get('multi_modal_data',{}).get('image',[])
    save(folder/'input.json',dict(at=now(),id=rid,kind=t['kind'],family_id=r['family_id'],prefix_sha256=r['prefix_sha256'],solver_base_sha256=hashlib.sha256(base.encode()).hexdigest() if base else None,chat_prompt=inp['prompt'],messages=messages,images=images if t['kind']!='solver' else [r['image']],prepared_image_sizes=[list(im.size) for im in image_data],prepared_image_pixel_sha256=[hashlib.sha256(im.tobytes()).hexdigest() for im in image_data],seed=r['seed'],cap=t['cap'],sampling=cfg['helper_recipe'],job=job))
    engine.add_request(rid,inp,param);active[rid]={'task':t,'started':time.monotonic(),'latest':None}
   if not active:continue
   try:updates=engine.step()
   except Exception as exc:
    for rid,a in active.items():save(outroot/rid/'failure.json',dict(at=now(),reason='ENGINE_FAILURE',error=repr(exc),last_tokens=len(a['latest'].outputs[0].token_ids) if a['latest'] else 0))
    raise
   for out in updates:
    a=active[out.request_id];a['latest']=out
    if not out.finished:continue
    t=a['task'];o=out.outputs[0];folder=outroot/out.request_id
    g=dict(at=now(),id=out.request_id,raw_decoded_response=o.text,generated_token_ids=list(o.token_ids),tokens=len(o.token_ids),prompt_token_ids=list(out.prompt_token_ids),prompt_tokens=len(out.prompt_token_ids),visual_tokens=sum(x==151655 for x in out.prompt_token_ids),finish_reason=o.finish_reason,stop_reason=o.stop_reason,cap_hit=o.finish_reason=='length',latency_seconds=time.monotonic()-a['started'],job=job,node=node,seed=t['row']['seed'])
    save(folder/'generation.json',g);save(folder/'result.json',dict(at=now(),generation_sha256=sha(folder/'generation.json'),input_sha256=sha(folder/'input.json')));answers[out.request_id]=g;del active[out.request_id];completed+=1
    print('COMPLETE',out.request_id,g['tokens'],g['finish_reason'],flush=True)
   expired=[rid for rid,a in active.items() if time.monotonic()-a['started']>cfg['timeout_seconds'] or time.monotonic()-started>m['wall_seconds']-30]
   if expired:
    engine.abort_request(expired)
    for rid in expired:
     a=active.pop(rid);o=a['latest'].outputs[0] if a['latest'] else None
     save(outroot/rid/'failure.json',dict(at=now(),reason='SAFE_DEADLINE_OR_TIMEOUT',partial=o.text if o else '',partial_ids=list(o.token_ids) if o else []));answers[rid]=None
   if time.monotonic()-last>60:
    save(dest/f'heartbeat_{completed}_{tick}.json',dict(at=now(),completed=completed,active={rid:len(a['latest'].outputs[0].token_ids) if a['latest'] else 0 for rid,a in active.items()},seconds=time.monotonic()-started));last=time.monotonic();tick+=1
  return answers
 def task(r,name,kind,cap,**kwargs):return dict(id=f"{r['item_id']}_{name}",row=r,kind=kind,cap=cap,**kwargs)
 cap=cfg['caps'];state={r['item_id']:{'family_id':r['family_id'],'item_id':r['item_id'],'prefix_sha256':r['prefix_sha256']} for r in work}
 try:
  if mode=='technical':
   replay=[]
   for name in ['replay_a','replay_b']:
    outputs=call_batch([task(r,name,'solver',cap['replay']) for r in work]);replay.append(outputs)
   for r in work:
    x,y=replay[0][r['item_id']+'_replay_a'],replay[1][r['item_id']+'_replay_b'];state[r['item_id']]['replay_exact']=bool(x and y and x['generated_token_ids']==y['generated_token_ids'])
  qout=call_batch([task(r,'query','query',cap['query'],prompt=helper_prompt(r,'query')) for r in work if r['eligible']])
  queries={};qlabels={}
  for r in work:
   g=qout.get(r['item_id']+'_query');q=parse_record(g['raw_decoded_response']) if g else None;ok,reason=validate_query(q,r['question'],r['prefix']);qlabels[r['item_id']]=(ok,reason);state[r['item_id']].update(query=q,query_contract_valid=ok,query_contract_reason=reason)
   if ok and q['status']=='QUERY':queries[r['item_id']]=q
  loc=call_batch([task(r,'locate','locate',cap['locate'],prompt=helper_prompt(r,'locate',queries[r['item_id']]),images=[r['image']]) for r in work if r['item_id'] in queries])
  addresses={};views={}
  from PIL import Image
  for r in work:
   g=loc.get(r['item_id']+'_locate');a=parse_record(g['raw_decoded_response']) if g else None;w,h=Image.open(r['image']).size;ok=validate_address(a,w,h);state[r['item_id']].update(address=a,address_contract_valid=ok)
   if ok:
    addresses[r['item_id']]=a;views[r['item_id']]=render_views(r['image'],a,P/'data/views'/(mode+'_v2')/r['item_id']);state[r['item_id']]['views']=views[r['item_id']]
  readjobs=[];aliases={}
  for r in work:
   item=r['item_id'];readjobs.append(task(r,'G_read','read',cap['read'],prompt=helper_prompt(r,'G'),images=[r['image']]))
   if item not in queries:continue
   q=queries[item]
   for arm,images in [('Q',[]),('QI',[r['image']])]:readjobs.append(task(r,arm+'_read','read',cap['read'],prompt=helper_prompt(r,arm,q),images=images))
   if item not in addresses:aliases[item+'_QIA_read']=item+'_QI_read';aliases[item+'_QGL_read']=item+'_QI_read';continue
   a=addresses[item];readjobs.append(task(r,'QIA_read','read',cap['read'],prompt=helper_prompt(r,'QIA',q,a),images=[r['image']]))
   if len(views[item]['paths'])==1:aliases[item+'_QGL_read']=item+'_QIA_read'
   else:readjobs.append(task(r,'QGL_read','read',cap['read'],prompt=helper_prompt(r,'QGL',q,a),images=views[item]['paths']))
  reads=call_batch(readjobs)
  for to,fr in aliases.items():reads[to]=reads.get(fr)
  continuations=[];c_aliases={};cap_c=cap['technical_continuation' if mode=='technical' else 'main_continuation']
  for r in work:
   item=r['item_id'];state[item]['readouts']={};state[item]['read_aliases']={k:v for k,v in aliases.items() if k.startswith(item+'_')};seen={'':item+'_N'}
   continuations.append(task(r,'N','solver',cap_c))
   for arm in ARMS[1:]:
    g=reads.get(item+'_'+arm+'_read');v=parse_record(g['raw_decoded_response']) if g else None;ok=valid_readout(v);state[item]['readouts'][arm]={'value':v,'contract_valid':ok,'generation_id':g['id'] if g else None};suffix=solver_suffix(v) if ok else ''
    if suffix in seen:c_aliases[item+'_'+arm]=seen[suffix]
    else:seen[suffix]=item+'_'+arm;continuations.append(task(r,arm,'solver',cap_c,suffix=suffix))
  cout=call_batch(continuations)
  for r in work:
   item=r['item_id'];state[item]['continuation_aliases']={k:v for k,v in c_aliases.items() if k.startswith(item+'_')};state[item]['continuations']={arm:c_aliases.get(item+'_'+arm,item+'_'+arm) for arm in ARMS}
   save(P/'data'/f'{mode}_v2_state'/f'{item}.json',state[item])
  save(dest/'exit.json',dict(at=now(),status='COMPLETE',completed=completed,seconds=time.monotonic()-started,mode=mode,families=[r['item_id'] for r in work]))
 except BaseException as e:
  save(dest/'error.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc(),seconds=time.monotonic()-started,completed=completed));raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('manifest');a=p.parse_args();run(a.manifest)
