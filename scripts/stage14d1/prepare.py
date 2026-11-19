"""CPU source selection and inference-only payload materialization; no outcome selection."""
import json,hashlib,datetime,collections
from pathlib import Path
from tokenizers import Tokenizer
from scripts.stage14d1.contracts import *
P=Path('outputs/stage14d1_sava');V=Path('outputs/stage14d0_visual_difficulty/v2');D=Path('outputs/stage14d0')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def j(p):return json.loads(Path(p).read_text())
def jl(p):return [json.loads(x) for x in Path(p).read_text().splitlines()]
def save(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,indent=2,ensure_ascii=False)
def rows(p,v):
 with Path(p).open('x') as f:
  for r in v:f.write(json.dumps(r,ensure_ascii=False)+'\n')
def rank(x):return hashlib.sha256(('sava-dev-v2-20261019|'+x).encode()).hexdigest()
def main():
 assert not (P/'protocol/sampler_and_seeds.json').exists()
 seals={V/'audit/final_package_seal.json':'package_files',D/'audit/output_package_seal_v1.json':'package_files'}
 verified={}
 for path,key in seals.items():
  a=j(path)
  for f,h in a[key].items():assert sha(f)==h,f
  verified[str(path)]={'sha256':sha(path),'files_verified':len(a[key])}
 source=jl(V/'source_difficulty_subfacts_v2.jsonl');allnative=jl(D/'inventory/source_and_raw_output_manifest.jsonl');native={x['family_id']:x for x in allnative}
 # Original family identities retained; known duplicate construction 1744 excluded by source metadata only.
 options=collections.defaultdict(lambda:collections.defaultdict(list))
 for r in source:
  if r['primary_acquisition_eligible'] and r['item_id']!='1744':options[r['G']['context_need']][r['family_id']].append(r)
 quota={'global_required':36,'local_sufficient':18,'local_plus_global':18}
 # Deterministic bipartite matching; handles overlapping family opportunities without quota relaxation.
 slots=[(cat,k) for cat in ['local_sufficient','local_plus_global','global_required'] for k in range(quota[cat])];owners={};chosen={}
 def assign(slot,seen):
  cat=slot[0]
  for fam in sorted(options[cat],key=lambda f:rank(cat+'|'+f)):
   if fam in seen:continue
   seen.add(fam)
   if fam not in owners or assign(owners[fam],seen):owners[fam]=slot;chosen[slot]=fam;return True
  return False
 for slot in slots:assert assign(slot,set()),('source quota infeasible',slot)
 selected=[]
 for slot,fam in chosen.items():
  cat=slot[0];fact=min(options[cat][fam],key=lambda r:rank(r['subfact_id']))
  selected.append(dict(family_id=fam,item_id=fact['item_id'],audit_target_subfact_id=fact['subfact_id'],audit_source_fact=fact['source_fact'],audit_context_stratum=cat,source_annotation=fact,selection_hash=rank(fam)))
 selected.sort(key=lambda r:r['selection_hash']);assert len(selected)==len({r['family_id'] for r in selected})==72
 technical=[]
 for cat,n in [('global_required',4),('local_sufficient',2),('local_plus_global',2)]:technical.extend([r['family_id'] for r in sorted(selected,key=lambda r:rank('technical|'+r['family_id'])) if r['audit_context_stratum']==cat][:n])
 cfg=j('outputs/stage14b/spec/frozen_run_config.json');model=cfg['models']['T'];tok=Tokenizer.from_file(str(Path(model['model']['checkpoint'])/'tokenizer.json'))
 run=[];provenance=[];manifest=[]
 for r in selected:
  m=native[r['family_id']];n=m['native']['T'];ip=n['input'];gp=n['generation'];assert sha(ip)==n['input_sha256'] and sha(gp)==n['generation_sha256'];assert sha(m['image'])==m['image_sha256']
  inp=j(ip);g=j(gp);ids=g['generated_token_ids'][:512]
  text=tok.decode(ids,skip_special_tokens=True)
  # Stop-token IDs are retained in generation receipts but omitted by vLLM's text decoder.
  # Back off only an incomplete UTF-8 token boundary; never reconstruct future text.
  while ids and not g['raw_decoded_response'].startswith(text) and text.endswith('\ufffd'):
   ids=ids[:-1];text=tok.decode(ids,skip_special_tokens=True)
  assert g['raw_decoded_response'].startswith(text),(m['item_id'],'token decode parity')
  prefix=choose_checkpoint(text,len(text));active=len(tok.encode(prefix,add_special_tokens=False).ids)>=64
  row=dict(item_id=m['item_id'],family_id=m['family_id'],question=m['native_question'],image=m['image'],image_sha256=m['image_sha256'],prefix=prefix,prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),seed=int(rank('seed|'+m['family_id'])[:8],16)%(2**31),eligible=active,original_chat_prompt=inp['chat_prompt'],original_messages=inp['messages'],original_image_pixels=inp['prepared_image_pixel_sha256'],original_image_sizes=inp['prepared_image_sizes'])
  assert ''.join(c.get('text','') for msg in row['original_messages'] for c in msg['content'])==row['question']
  safe_payload(row);run.append(row)
  r['technical']=m['family_id'] in technical;r['source_stratum']=next(x['stratum'] for x in jl(D/'samples/panel_R_source_selected.jsonl') if x['family_id']==m['family_id'])
  provenance.append(dict(family_id=m['family_id'],item_id=m['item_id'],image=m['image'],image_sha256=m['image_sha256'],native_input=ip,native_input_sha256=n['input_sha256'],native_raw=gp,native_raw_sha256=n['generation_sha256'],prefix_sha256=row['prefix_sha256'],prefix_token_count=len(tok.encode(prefix,add_special_tokens=False).ids),prefix_rule='First512 generated tokens, cut before first final/boxed boundary; <64tokens => no eligible checkpoint; no replacement',offline_annotation_sha256=sha(V/'source_difficulty_subfacts_v2.jsonl')))
  for arm in ARMS:manifest.append(dict(family_id=m['family_id'],item_id=m['item_id'],arm=arm,prefix_sha256=row['prefix_sha256'],seed=row['seed'],technical=r['technical'],runtime_record_sha256=fingerprint(row),status='FROZEN_NOT_RUN'))
 rows(P/'data/selected_family_target_manifest.jsonl',selected);rows(P/'inference/families.jsonl',run);rows(P/'provenance/source_inputs_manifest.jsonl',provenance);rows(P/'protocol/arm_manifest.jsonl',manifest)
 runtime=dict(model=model,environment=cfg['environment'],precision=cfg['precision'],runtime=dict(engine_seed=42,tensor_parallel_size=1,gpu_memory_utilization=.85,max_model_len=128000,max_num_seqs=8,max_images_per_prompt=3),pixels=cfg['image_preprocessing'],caps=dict(query=4096,locate=2048,read=4096,technical_continuation=256,replay=64,main_continuation=81920),stage_gpu_hour_ceiling=16,technical_gpu_hour_ceiling=2,max_concurrent_gpus=8,helper_recipe=model['recipe'],source_protocol='Original source preprocessing; text-only query/Q helpers; solver retains original image. All helpers are interrupted restarted requests.',timeout_seconds=3000,stage_seed=20261019)
 save(P/'protocol/runtime.json',runtime)
 save(P/'protocol/sampler_and_seeds.json',dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),seed='sava-dev-v2-20261019',source_rule='SHA256 deterministic bipartite matching from source-only eligible R facts; no outcome selection',quotas=quota,families=72,technical_families=technical,technical_count=8,source_only_exclusion='1744 known same-construction alias of751; preserve original cohort and source records',no_replacements_after_generation=True,verified_seals=verified))
 save(P/'audit/p0_inventory.json',dict(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),families=72,arms=len(manifest),technical_families=8,eligible_checkpoints=sum(r['eligible'] for r in run),source_only_selection=True,model_outputs_used_for_selection=False,native_prefixes_reused=True,source_dimensions_are_offline_only=True,new_model_calls=0,verified_seals=verified,plan_original_sha256=sha(P/'provenance/original_plan_v1.md'),amendment_sha256=sha('plan/stage14d1_sava_execution_amendment_v2.md')))
 print(json.dumps(dict(selected=72,arms=len(manifest),technical=[r['item_id'] for r in selected if r['technical']],eligible_checkpoints=sum(r['eligible'] for r in run))))
if __name__=='__main__':main()
