import argparse,json,os,traceback
from copy import deepcopy
from scripts.stage14e.common import *
from scripts.stage14e.contracts import *
from scripts.stage14e.engine import Engine
from scripts.stage14d1_pilot.interface_v6 import normalize_address,SCHEMAS
LOCATE_SCHEMA=SCHEMAS["locate"]
from scripts.stage14d1.contracts import LOCATE_INSTRUCTION
LOCATE_INSTRUCTION=LOCATE_INSTRUCTION.replace("boxes are normalized [xmin,ymin,xmax,ymax]", "boxes are integer [xmin,ymin,xmax,ymax] coordinates from 0 to 1000")
from scripts.stage14d1.contracts import validate_address
from scripts.stage14d1.views import render_views
from PIL import Image

def parse(g):
 try:return json.loads(g['raw_decoded_response'])
 except (ValueError,TypeError):return None

def run(path):
 m=load(path)
 for p,h in load(m['seal'])['files'].items():assert sha(p)==h,p
 fam={r['item_id']:r for r in rows(P/'inference/diagnostic_families.jsonl')};work=[fam[i] for i in m['families']]
 old=load(P/'inference/original_targets.json');oracle=load(P/'inference/diagnostic_target_identities.json')
 e=Engine(m);root=e.root
 def task(r,name,kind='helper',cap=2048,**kw):return dict(id=r['item_id']+'_'+name,row=r,kind=kind,cap=cap,**kw)
 try:
  runs=[]
  for rep in ['a','b']:
   runs.append(e.calls([task(fam[i],'replay_'+rep,'solver',64) for i in m['technical_ids']],width=1))
  comps=[]
  for i in m['technical_ids']:
   a,b=runs[0][i+'_replay_a'],runs[1][i+'_replay_b'];comps.append({'item_id':i,'tokens_exact':a['generated_token_ids']==b['generated_token_ids'],'inputs_exact':a['prompt_token_ids']==b['prompt_token_ids']})
  save(root/'replay_gate.json',comps);assert all(r['tokens_exact'] and r['inputs_exact'] for r in comps)
  controls=load(m.get('controls',str(P/'inference/controls_v1.json')));ct=[]
  for r in controls:
   s=deepcopy(QUERY_SCHEMA);s['anyOf'][0]['properties']['source_refs']['items']={'enum':[v['id'] for v in build_catalog(r['question'],r['prefix'])]}
   ct.append(task(r,'query',prompt=query_prompt(r),schema=s))
  cg=e.calls(ct);cr=[]
  for r in controls:
   q=parse(cg[r['item_id']+'_query']);ok,why=validate_demand(q,build_catalog(r['question'],r['prefix']))
   cr.append({'id':r['item_id'],'expected':r['expected'],'output':q,'valid':ok,'reason':why,'expected_branch':isinstance(q,dict) and q.get('status')==r['expected']})
  save(root/'controls.json',cr)
  assert all(r['valid'] for r in cr),'Technical control transport failed'
  assert {'QUERY','NONE'}<={r['output']['status'] for r in cr},'Both branches not demonstrated'
  qt=[]
  for r in work:
   s=deepcopy(QUERY_SCHEMA);s['anyOf'][0]['properties']['source_refs']['items']={'enum':[v['id'] for v in build_catalog(r['question'],r['prefix'])]}
   qt.append(task(r,'demand',prompt=query_prompt(r),schema=s))
  qg=e.calls(qt);states={}
  for r in work:
   i=r['item_id'];q=parse(qg[i+'_demand']);cat=build_catalog(r['question'],r['prefix']);ok,why=validate_demand(q,cat)
   states[i]={'item_id':i,'query':q,'valid':ok,'reason':why,'compiled':compile_target(q,cat) if ok else {'status':'NONE','reason':'INVALID'},'generation_path':qg[i+'_demand']['generation_path']}
  save(root/'demand_states.json',states)
  lt=[]
  for r in work:
   i=r['item_id'];prompt=LOCATE_INSTRUCTION+'\n\nOriginal question:\n'+r['question']+'\n\nRequested source:\n'+oracle[i]['query']
   lt.append(task(r,'target_locate',prompt=prompt,images=[r['image']],schema=LOCATE_SCHEMA,oracle=True))
  lg=e.calls(lt);locs={}
  for r in work:
   i=r['item_id'];raw=parse(lg[i+'_target_locate'])
   try:a=normalize_address(raw)
   except ValueError:a=None
   with Image.open(r['image']) as im:w,h=im.size
   ok=validate_address(a,w,h)
   views=render_views(r['image'],a,root/'views'/i) if ok else {'paths':[r['image']],'status':'INVALID_ADDRESS_FALLBACK','transforms':[]}
   locs[i]={'raw':raw,'normalized':a,'valid':ok,'views':views,'generation_path':lg[i+'_target_locate']['generation_path']}
  save(root/'target_locations.json',locs)
  reads=[];logical=[]
  for r in work:
   i=r['item_id']
   for arm in m['conditions']:
    t=old[i] if arm.startswith('O_') else states[i]['compiled'] if arm.startswith('D_') else oracle[i]
    if t.get('status')!='QUERY':logical.append({'item_id':i,'condition':arm,'status':'NOT_ATTEMPTED_QUERY_NONE_OR_INVALID','generation_path':None});continue
    if arm=='T_GL' and len(locs[i]['views']['paths'])<2:
     logical.append({'item_id':i,'condition':arm,'status':'FULL_IMAGE_FALLBACK','alias_of':'T_blind','generation_path':str(root/(i+'_T_blind')/'generation.json')});continue
    images=[] if arm=='T_noimage' else locs[i]['views']['paths'] if arm=='T_GL' else [r['image']]
    reads.append(task(r,arm,prompt=reader_prompt(r,t,with_prefix=arm.endswith('_context'),structured=arm=='D_struct'),images=images,
     schema=STRUCT_SCHEMA if arm=='D_struct' else READ_SCHEMA,condition=arm,oracle=arm.startswith('T_')))
    logical.append({'item_id':i,'condition':arm,'status':'PHYSICAL','generation_path':str(root/(i+'_'+arm)/'generation.json')})
  save(root/'read_execution_manifest.json',{'logical':logical,'physical_count':len(reads),'frozen_before_readout':now()})
  e.calls(reads)
  save(root/'result.json',{'at':now(),'status':'COMPLETED','physical_calls':e.count,'families':len(work),'logical_readouts':len(logical)})
 except BaseException as ex:
  save(root/'failure.json',{'at':now(),'error':repr(ex),'traceback':traceback.format_exc(),'completed':e.count});raise
 finally:
  e.budget_check()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('manifest');run(p.parse_args().manifest)
