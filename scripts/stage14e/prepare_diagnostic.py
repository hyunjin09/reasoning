import json,hashlib
from pathlib import Path
from scripts.stage14e.common import *
from scripts.stage14e.contracts import *
OLD=Path('outputs/stage14d1_sava_pilot/v1')
ids=[Path(f).stem for f in load(OLD/'annotations/fixed_readout_review_complete.json')['files']]
allrows={r['item_id']:r for r in rows(OLD/'inference/families.jsonl')}
tech=['317','760','2577','107','2274','33','1477','737']
selected=list(dict.fromkeys(sorted(ids,key=int)+tech))
(P/'inference/diagnostic_families.jsonl').write_text(''.join(json.dumps(allrows[i],ensure_ascii=False)+'\n' for i in selected))
source=load(OLD/'manifests/resumption_v8_design.json')['source_states'];targets={}
for i in ids:
 s=load(source[i]);c=s.get('compiled_query')
 targets[i]={'status':'NONE','reason':'ORIGINAL_INVALID_OR_NONE'} if not(s['query_valid'] and s['query']['status']=='QUERY') else {k:c[k] for k in ['status','target','property','scope','query']}
save(P/'inference/original_targets.json',targets)
t=load(P/'offline/diagnostic_targets_v1.json')['targets'];assert set(t)==set(ids)
save(P/'inference/diagnostic_target_identities.json',{i:{'status':'QUERY','query':q,'diagnostic_oracle_target':True} for i,q in t.items()})
cfg=load(OLD/'protocol/runtime_v6.json');cfg['stage_gpu_hour_ceiling']=24;cfg['historical_sava_gpu_hours']=21.365278;cfg['protocol_version']='stage14e_diagnostic_v1';cfg['stage_seed']=20261022;cfg['technical_gpu_hour_ceiling']=None
save(P/'protocol/runtime_v1.json',cfg)
controls=[
 ('label','The image shows a labeled point. What value is printed beside it?','I need to read the printed value before computing.','QUERY'),
 ('layout','A diagram shows blocks. Find its perimeter.','I do not yet know how the rows are aligned. I need the relative row positions.','QUERY'),
 ('bridge','A map shows named islands connected by bridges. Find a route.','The adjacency of the central island is unresolved; read its connected neighbors.','QUERY'),
 ('recheck','A plot shows a marked point. Find the area.','I guessed its coordinate, but have not read it. I need to check the plotted position.','QUERY'),
 ('given','There are six objects, each costing two dollars. What is their cost?','All quantities are supplied in the question. Multiply six by two.','NONE'),
 ('algebra','Solve x plus three equals seven.','The unknown x must be calculated; no visual source exists.','NONE'),
 ('known','Use a bar chart to compute a mean.','I have transcribed all bar values and checked the correspondence. The only next step is adding the recorded values.','NONE'),
 ('future','A tank initially has five litres, then three are added. Find the final amount.','The final amount is not drawn; it is a mathematical sum of the given amounts.','NONE')]
synthetic=[]
for k,(i,q,p,e) in enumerate(controls):synthetic.append({'item_id':'control_'+i,'family_id':'synthetic_'+i,'question':q,'prefix':p,'prefix_sha256':hashlib.sha256(p.encode()).hexdigest(),'seed':202610220+k,'expected':e})
save(P/'inference/controls_v1.json',synthetic)
manifest={'id':'diagnostic_v1','mode':'diagnostic','families':sorted(ids,key=int),'technical_ids':tech,'wall_seconds':172800,
 'budget_reservation_seconds':43200,'expected_gpu_hours':[.5,2],'hard_total_cycle_gpu_seconds':86400,
 'conditions':['O_context','O_blind','D_context','D_blind','D_struct','T_context','T_blind','T_noimage','T_GL'],
 'runtime':str(P/'protocol/runtime_v1.json'),'seal':str(P/'audit/diagnostic_execution_seal_v1.json')}
save(P/'manifests/diagnostic_v1.json',manifest)
print('families',len(ids),'runtime_rows',len(selected),'maxcalls',24+24+216+8+16)
