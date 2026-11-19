"""Exactly three frozen reserve-compatible validation cases; no primary scoring."""
import os,time,gc,traceback
import torch
from scripts.stage10c.common import ROOT,load,save,sha,now
from scripts.stage10c.runtime import load_runtime,inputs,base_state,free,teacher,mask_args,CONDITIONS,clone_streaming_state,advance_streaming_state

def audit_records(records,row,condition,prompt):
 expected=set(range(*(row['pre_window'] if condition=='PRE_ALL_OFF' else row['post_window']))) if condition!='NATIVE' else set()
 for layer in range(28):
  own=[r for r in records if r['layer']==layer]
  observed={q-prompt+1 for r in own for q in r['blocked_absolute_queries']}
  assert observed==expected,(condition,layer,observed,expected)
  assert all(r['masked_probability_max']==0 for r in own if r['blocked_absolute_queries'])
  if expected:
   after=[r for r in own if r['query_start']-prompt+1>=max(expected)+1]
   assert after and all(not r['blocked_absolute_queries'] for r in after)
   assert any(r['image_probability_max']>0 for r in after)
 return dict(all28_layers=True,exact_masked_prediction_indices=sorted(expected),restored_after_window=True,masked_probability_zero=True)

@torch.inference_mode()
def main():
 started=time.monotonic();proc,model,env=load_runtime();save(ROOT/'technical/environment.json',env)
 split=load(ROOT/'stage10c_frozen_candidate_split.json');controls={r['trajectory_id']:r for r in load(ROOT/'stage10c_roi_controls.json')['rows']};rows=[]
 for row in [r for r in split['rows'] if r['technical']]:
  tid=row['trajectory_id'];prepared,meta,ids,seed,inputaudit=inputs(proc,row);base,prefix=base_state(model,prepared,ids,seed,row)
  snapshot=clone_streaming_state(base);args=mask_args(row,meta,controls[tid],'NATIVE',True)
  native,log0=free(model,proc,base,ids,seed,row,args,hook=False,logits=True)
  noop,log1=free(model,proc,base,ids,seed,row,args,hook=True,logits=True)
  assert native['generated_token_ids']==noop['generated_token_ids'] and all(torch.equal(a,b) for a,b in zip(log0,log1))
  assert len(log0)==len(log1)==88
  assert all(torch.equal(x.keys,y.keys) and torch.equal(x.values,y.values) for x,y in zip(base.cache.layers,snapshot.cache.layers))
  # Split/resume versus uninterrupted one-token native advancement.
  a=clone_streaming_state(base);b=clone_streaming_state(base);lo=base.generated_length
  advance_streaming_state(model=model,state=a,token_ids=ids[lo:lo+4],seed=seed,chunk_size=1)
  advance_streaming_state(model=model,state=b,token_ids=ids[lo:lo+2],seed=seed,chunk_size=1);b=clone_streaming_state(b)
  advance_streaming_state(model=model,state=b,token_ids=ids[lo+2:lo+4],seed=seed,chunk_size=1)
  assert torch.equal(a.last_logits,b.last_logits)
  assert all(torch.equal(x.keys,y.keys) and torch.equal(x.values,y.values) for x,y in zip(a.cache.layers,b.cache.layers))
  data=[];audits=[]
  for condition in CONDITIONS:
   args=mask_args(row,meta,controls[tid],condition,True)
   generation=noop if condition=='NATIVE' else free(model,proc,base,ids,seed,row,args)[0]
   audits.append(dict(condition=condition,**audit_records(generation['mask_records'],row,condition,meta['prompt_token_count'])))
   nll=teacher(model,base,ids,seed,row,dict(args,audit=False))
   assert nll['evidence_token_ids']==ids[row['observation_span']['token_start']:row['observation_span']['token_end']]
   generation.pop('mask_records',None);data.append(dict(condition=condition,free=generation,nll=nll))
  c=controls[tid];assert len(c['target_absolute'])==len(c['control_absolute']) and not(set(c['target_absolute'])&set(c['control_absolute']))
  dest=ROOT/'technical/cases'/tid/'result.json'
  save(dest,dict(at=now(),trajectory_id=tid,rows=data,input=inputaudit,prefix=prefix,slurm_job_id=os.environ['SLURM_JOB_ID'],
                config_sha256=sha(ROOT/'config.json'),source='technical reserve-compatible',peak_allocated_bytes=torch.cuda.max_memory_allocated()))
  rows.append(dict(trajectory_id=tid,pass_all=True,prefix_ids_exact=True,no_op_logits_tokens_bitwise_equal=True,validation_span_tokens=88,
   mask_checks=audits,roi_disjoint=True,matched_token_counts=len(c['target_absolute']),teacher_forced_ids_exact=True,
   image_preprocessing_verified=True,cache_resume_bitwise_equal=True,original_cache_unchanged=True,result_path=str(dest),result_sha256=sha(dest)))
  print('TECHNICAL_PASS',tid,flush=True)
  del prepared,base,snapshot,a,b,log0,log1;gc.collect();torch.cuda.empty_cache()
 assert len(rows)==3 and {r['trajectory_id'] for r in rows}==set(split['technical_ids'])
 save(ROOT/'stage10c_technical_validation.json',dict(at=now(),pass_all=True,examples=3,rows=rows,environment=env,
  config_sha256=sha(ROOT/'config.json'),seconds=time.monotonic()-started,scientific_primary_outputs_opened=False,
  source_sha256=load(ROOT/'config.json')['source_sha256'],baseline='Unmasked versus no-op greedy continuation from unchanged sampled native prefix; historical sampled suffix is not a greedy alias.'))
if __name__=='__main__':
 try:main()
 except Exception as e:
  save(ROOT/f'audit/validation_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc()));raise
