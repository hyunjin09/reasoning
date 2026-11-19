"""One-shot disjoint evaluation. Source references/scoring never enter this worker."""
import argparse,hashlib,json,traceback
from copy import deepcopy
from scripts.stage14e.common import *
from scripts.stage14e.engine import Engine
from scripts.stage14e.contracts import QUERY_SCHEMA,query_prompt,validate_demand,compile_target,build_catalog
from scripts.stage14e.evaluation_contracts import acquisition_plan,continuation_plan
from scripts.stage14d1.contracts import safe_payload
from scripts.stage14d1_pilot.interface_v6 import QUERY_SCHEMA as OLD_SCHEMA,query_prompt as old_prompt,validate_query,compile_query

def parse(record):
 try:return json.loads(record['raw_decoded_response'])
 except (ValueError,TypeError):return None

def run(path):
 m=load(path)
 for p,h in load(m['seal'])['files'].items():assert sha(p)==h,p
 families={r['item_id']:safe_payload(r) for r in rows(m['families_path'])}
 work=[families[i] for i in m['families']];assert all(r['eligible'] for r in work)
 e=Engine(m);root=e.root
 def task(r,name,kind='helper',cap=2048,**kw):return dict(id=r['item_id']+'_'+name,row=r,kind=kind,cap=cap,**kw)
 try:
  checks=[];reps=[]
  for rep in ['a','b']:
   reps.append(e.calls([task(r,'check_'+rep,'solver',64) for r in work[:2]],width=1))
  for r in work[:2]:
   i=r['item_id'];a,b=reps[0][i+'_check_a'],reps[1][i+'_check_b']
   checks.append({'item_id':i,'same_tokens':a['generated_token_ids']==b['generated_token_ids'],'same_input':a['prompt_token_ids']==b['prompt_token_ids']})
  save(root/'technical_gate.json',checks);assert all(r['same_tokens'] and r['same_input'] for r in checks)
  qt=[]
  for r in work:
   cat=build_catalog(r['question'],r['prefix'])
   for name,template,prompt in [('S_query',OLD_SCHEMA,old_prompt(r)),('M_query',QUERY_SCHEMA,query_prompt(r))]:
    schema=deepcopy(template);schema['anyOf'][0]['properties']['source_refs']['items']={'enum':[s['id'] for s in cat]}
    qt.append(task(r,name,prompt=prompt,schema=schema))
  qg=e.calls(qt);states={};reads=[]
  for r in work:
   i=r['item_id'];cat=build_catalog(r['question'],r['prefix']);state={}
   for arm,validator,compiler in [('S',validate_query,compile_query),('M',validate_demand,compile_target)]:
    q=parse(qg[i+'_'+arm+'_query']);ok,why=validator(q,cat)
    state[arm]={'query':q,'transport_valid':ok,'validation_reason':why,'target':compiler(q,cat) if ok else {'status':'NONE','reason':'INVALID_QUERY'},'query_generation_path':qg[i+'_'+arm+'_query']['generation_path']}
   plan=acquisition_plan(r,state['S']['target'],state['M']['target'],m['candidate'])
   state['read_plan']={name:dict(v,generation_path=str(root/(i+'_'+name+'_read')/'generation.json')) for name,v in plan.items()}
   for name,t in plan.items():reads.append(task(r,name+'_read',condition=name,**t))
   states[i]=state
  save(root/'query_states.json',states)
  rg=e.calls(reads);solvers=[];logical=[]
  for r in work:
   i=r['item_id'];state=states[i];readouts={}
   for arm in ['S','M','M_noimage']:
    g=rg.get(i+'_'+arm+'_read');readouts[arm]=parse(g) if g else None
   state['readouts']=readouts
   physical,assignments=continuation_plan(i,readouts)
   # Fixed hash arm order within family; no outcome-dependent allocation.
   order=sorted(physical,key=lambda k:hashlib.sha256(('stage14e-arm-order-v1|'+k).encode()).hexdigest())
   for rid in order:solvers.append(task(r,rid.split('_',1)[1],'solver',81920,suffix=physical[rid],condition=rid.split('_',1)[1]))
   for arm,a in assignments.items():
    logical.append({'item_id':i,'family_id':r['family_id'],'arm':arm,**a,'generation_path':str(root/a['physical_id']/'generation.json'),'suffix_sha256':hashlib.sha256(physical[a['physical_id']].encode()).hexdigest(),'seed':r['seed']})
  save(root/'acquisition_states.json',states)
  save(root/'solver_execution_manifest.json',{'at':now(),'rows':logical,'physical_count':len(solvers),'solver_width':1,'all_suffixes_frozen_before_any_solver_final':True})
  e.calls(solvers,width=1)
  save(root/'result.json',{'at':now(),'status':'COMPLETED','families':len(work),'logical_solvers':len(logical),'physical_solvers':len(solvers),'total_physical_calls':e.count})
 except BaseException as exc:
  save(root/'failure.json',{'at':now(),'error':repr(exc),'traceback':traceback.format_exc(),'completed':e.count});raise
 finally:e.budget_check()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('manifest');run(p.parse_args().manifest)
