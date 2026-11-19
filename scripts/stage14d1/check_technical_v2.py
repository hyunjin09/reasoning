"""CPU-only technical audit; no answer correctness or protocol selection."""
from scripts.stage14d1.common import *
from scripts.stage14d1.contracts import ARMS

def check():
 sample=load(P/'protocol/sampler_and_seeds.json');selected=[r for r in rows(P/'data/selected_family_target_manifest.jsonl') if r['family_id'] in sample['technical_families']]
 states=[];missing=[]
 for r in selected:
  path=P/'data/technical_v2_state'/f"{r['item_id']}.json"
  if path.exists():states.append(load(path))
  else:missing.append(r['item_id'])
 if missing:return dict(at=now(),complete=False,completed_families=len(states),missing=missing)
 ids={r['item_id'] for r in selected};read=[];locator=[];query=[];physical=[];hash_ok=True;prefix_ok=True
 for p in (P/'raw/technical_v2').glob('*/result.json'):
  inp=load(p.parent/'input.json');g=load(p.parent/'generation.json');r=load(p);hash_ok &= sha(p.parent/'input.json')==r['input_sha256'] and sha(p.parent/'generation.json')==r['generation_sha256'];physical.append(g)
 for s in states:
  query.append(s['query_contract_valid']);locator.append(s['address_contract_valid']) if s['query_contract_valid'] and s['query'].get('status')=='QUERY' else None
  expected=next(r for r in rows(P/'inference/families.jsonl') if r['item_id']==s['item_id']);base=hashlib.sha256((expected['original_chat_prompt']+expected['prefix']).encode()).hexdigest()
  for arm in ARMS:
   cid=s['continuations'][arm];p=P/'raw/technical_v2'/cid/'input.json'
   prefix_ok &= p.exists() and load(p)['solver_base_sha256']==base
  for p in (P/'raw/technical_v2').glob(s['item_id']+'_*_read'):
   from scripts.stage14d1.contracts_v2 import parse_record,valid_readout
   read.append(valid_readout(parse_record(load(p/'generation.json')['raw_decoded_response'])) if (p/'generation.json').exists() else False)
 actionable=sum(s['query_contract_valid'] and s['query'].get('status')=='QUERY' for s in states)
 replay=all(s.get('replay_exact',False) for s in states)
 gates=dict(all_source_receipts=True,receipt_hashes=bool(hash_ok),same_solver_prefix=bool(prefix_ok),replay_exact=replay,query_contract_at_least6=sum(query)>=6,actionable_queries_at_least4=actionable>=4,read_contract_at_least80pct=bool(read) and sum(read)/len(read)>=.8,locator_contract_at_least75pct=bool(locator) and sum(locator)/len(locator)>=.75)
 return dict(at=now(),complete=True,**{'pass':all(gates.values())},gates=gates,families=len(states),query_schema_valid=sum(query),actionable_queries=actionable,none=sum(s['query_contract_valid'] and s['query'].get('status')=='NONE' for s in states),read_schema_valid=sum(read),physical_read_attempts=len(read),locator_schema_valid=sum(locator),physical_locator_attempts=len(locator),physical_completed_calls=len(physical),generated_tokens=sum(g['tokens'] for g in physical),cap_hits=sum(g['cap_hit'] for g in physical),semantic_source_review='PENDING; no claim that schema-valid means relevant/value-free/source-correct',accuracy='NOT_MEASURED: technical continuations256 tokens only')
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--seal',action='store_true');args=a.parse_args();r=check();print(json.dumps(r,indent=2))
 if args.seal:
  assert r['complete'];save(P/'audit/technical_gate_v2.json',r)
