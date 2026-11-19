import argparse,json,traceback
from scripts.stage14e.common import *
from scripts.stage14e.engine import Engine
from scripts.stage14e.contracts import reader_prompt,READ_SCHEMA,build_catalog
from scripts.stage14e.ledger import ledger_prompt,ledger_schema,compile_ledger
def parse(g):
 try:return json.loads(g['raw_decoded_response'])
 except (ValueError,TypeError):return None
def compile_record(g,row):
 q=parse(g)
 try:out=compile_ledger(q,build_catalog(row['question'],row['prefix']))
 except ValueError as ex:out={'target':{'status':'NONE','reason':'INVALID_LEDGER'},'transport_valid':False,'error':str(ex)}
 return dict(out,ledger=q,generation_path=g['generation_path'])
def run(path):
 m=load(path)
 for p,h in load(m['seal'])['files'].items():assert sha(p)==h,p
 fam={r['item_id']:r for r in rows(P/'inference/diagnostic_families.jsonl')};work=[fam[i] for i in m['families']]
 e=Engine(m);root=e.root
 def task(r,name,kind='helper',cap=2048,**kw):return dict(id=r['item_id']+'_'+name,row=r,kind=kind,cap=cap,**kw)
 try:
  reps=[]
  for rep in ['a','b']:reps.append(e.calls([task(fam[i],'replay_'+rep,'solver',64) for i in ['107','33']],width=1))
  gate=[{'item_id':i,'same_tokens':reps[0][i+'_replay_a']['generated_token_ids']==reps[1][i+'_replay_b']['generated_token_ids'],'same_input':reps[0][i+'_replay_a']['prompt_token_ids']==reps[1][i+'_replay_b']['prompt_token_ids']} for i in ['107','33']]
  save(root/'replay_gate.json',gate);assert all(r['same_tokens'] and r['same_input'] for r in gate)
  controls=load(P/'inference/controls_v1c.json')
  cg=e.calls([task(r,'ledger',prompt=ledger_prompt(r),schema=ledger_schema(build_catalog(r['question'],r['prefix']))) for r in controls])
  cr=[{'item_id':r['item_id'],'expected':r['expected'],**compile_record(cg[r['item_id']+'_ledger'],r)} for r in controls]
  save(root/'controls.json',cr)
  # Bad coverage decisions and rejected fabricated claims are model data; the host fallback is unit-tested.
  assert all(parse(cg[r['item_id']+'_ledger']) is not None for r in controls),'Unparseable synthetic transport'
  qg=e.calls([task(r,'ledger',prompt=ledger_prompt(r),schema=ledger_schema(build_catalog(r['question'],r['prefix']))) for r in work]);states={};reads=[];logical=[]
  for r in work:
   i=r['item_id'];state=compile_record(qg[i+'_ledger'],r);states[i]=state;t=state['target']
   for arm in ['R_context','R_blind','R_noimage']:
    if t['status']!='QUERY':logical.append({'item_id':i,'condition':arm,'status':'NONE_OR_INVALID','generation_path':None});continue
    reads.append(task(r,arm,prompt=reader_prompt(r,t,with_prefix=arm!='R_blind'),images=[] if arm=='R_noimage' else [r['image']],schema=READ_SCHEMA,condition=arm))
    logical.append({'item_id':i,'condition':arm,'status':'PHYSICAL','generation_path':str(root/(i+'_'+arm)/'generation.json')})
  save(root/'ledger_states.json',states);save(root/'read_execution_manifest.json',{'logical':logical,'physical_count':len(reads),'at':now()})
  e.calls(reads)
  save(root/'result.json',{'at':now(),'status':'COMPLETED','physical_calls':e.count,'families':len(work),'logical_readouts':len(logical)})
 except BaseException as ex:
  save(root/'failure.json',{'at':now(),'error':repr(ex),'traceback':traceback.format_exc(),'completed':e.count});raise
 finally:e.budget_check()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('manifest');run(p.parse_args().manifest)
