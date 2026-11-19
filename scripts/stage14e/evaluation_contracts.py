"""Frozen evaluation transport; never uses reference values or final outcomes."""
from scripts.stage14e.contracts import reader_prompt,READ_SCHEMA,STRUCT_SCHEMA
from scripts.stage14d1.contracts import valid_readout,solver_suffix
from scripts.stage14d1_pilot.interface_v6 import helper_prompt

def readout_valid(r):
 if valid_readout(r):return True
 if not isinstance(r,dict) or set(r)!={'status','source_frame','observations','unresolved'}:return False
 if r['status'] not in ['OBSERVED','PARTIAL','UNRESOLVABLE'] or not all(isinstance(r[k],str) for k in ['source_frame','unresolved']):return False
 return isinstance(r['observations'],list) and all(isinstance(o,dict) and set(o)=={'entity','property','value','visual_support'} and all(isinstance(v,str) for v in o.values()) for o in r['observations'])

def acquisition_plan(row,original,selected,candidate):
 assert candidate in ['A','B']
 result={}
 if original.get('status')=='QUERY':
  result['S']={'prompt':helper_prompt(row,'QI',original),'images':[row['image']],'schema':READ_SCHEMA}
 if selected.get('status')=='QUERY':
  prompt=reader_prompt(row,selected,structured=candidate=='B')
  for name,images in [('M',[row['image']]),('M_noimage',[])]:
   result[name]={'prompt':prompt,'images':images,'schema':STRUCT_SCHEMA if candidate=='B' else READ_SCHEMA}
 return result

def continuation_plan(item,readouts):
 physical={item+'_N':''};seen={'':item+'_N'};logical={'N':{'physical_id':item+'_N','status':'PHYSICAL'}}
 for arm in ['S','M']:
  value=readouts.get(arm);valid=readout_valid(value);suffix=solver_suffix(value) if valid else ''
  if suffix not in seen:
   seen[suffix]=item+'_'+arm;physical[seen[suffix]]=suffix;status='PHYSICAL'
  else:status='IDENTICAL_INPUT_ALIAS' if valid else 'NO_VALID_READOUT_NATIVE_ALIAS'
  logical[arm]={'physical_id':seen[suffix],'status':status}
 return physical,logical
