"""Source-only deterministic held-out METHOD evaluation selection, before interventions."""
import hashlib,json,math,collections
from pathlib import Path
from scripts.stage14e2.common import *
seed='stage14e2-evaluation-20261023-v1'
def rank(f):return hashlib.sha256((seed+'|'+f).encode()).hexdigest()
inv=rows('outputs/stage14d0/inventory/source_and_raw_output_manifest.jsonl')
exclude={r['family_id'] for f in ['outputs/stage14d0/samples/panel_R_source_selected.jsonl','outputs/stage14d0/samples/panel_F_outcome_enriched.jsonl'] for r in rows(f)}
exclude.update(r['family_id'] for r in load(PREVIOUS/'manifests/evaluation_family_selection_v1.json')['rows'])
source=[]
for r in inv:
 if r['family_id'] in exclude:continue
 # Deliberately whitelist source metadata; never read native correctness/outcome fields.
 source.append({k:r[k] for k in ['family_id','item_id','image','image_sha256','native_question_sha256','answer_type','subject','difficulty','has_structured_atom','source_receipt','source_receipt_sha256']})
assert len(source)==668
strata=collections.defaultdict(list)
for r in source:
 r['stratum']=r['answer_type']+'|structured='+str(r['has_structured_atom']);r['selection_hash']=rank(r['family_id']);strata[r['stratum']].append(r)
quotas={s:32*len(v)/len(source) for s,v in strata.items()};alloc={s:math.floor(q) for s,q in quotas.items()}
for s in sorted(quotas,key=lambda s:(-(quotas[s]-alloc[s]),s))[:32-sum(alloc.values())]:alloc[s]+=1
chosen=[]
for s in sorted(strata):chosen+=sorted(strata[s],key=lambda r:r['selection_hash'])[:alloc[s]]
chosen=sorted(chosen,key=lambda r:r['selection_hash']);assert len(chosen)==32
save(P/'manifests/evaluation_family_selection_v1.json',{'at':now(),'seed':seed,'selection':'SHA256(seed|family); proportional largest-remainder32 across answer format x structured; excludes all originalD0R/F300 plus previous32method-evaluation families',
 'native_outcomes_used':False,'intervention_outcomes_exist':False,'pool_n':700,'stratum_population':{s:len(v) for s,v in strata.items()},'stratum_n':alloc,'rows':chosen,
 'excluded_family_ids':sorted(exclude),'historical_benchmark_exposure':'Previously benchmark-evaluated source cohort; fresh only for method development/evaluation; not independent large-scale confirmation'})
print('FROZEN',[(r['item_id'],r['stratum']) for r in chosen]);print(alloc)
