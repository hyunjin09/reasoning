import json,collections,hashlib,re
from pathlib import Path
import numpy as np
from scripts.stage14e.postmortem import NEW,OLD,load,save,sha
x=load(NEW/'analysis/sava72_joined.json');manual={}
for l in (NEW/'annotations/prefix_review_v1.tsv').read_text().splitlines():
 i,s,n=l.split('\t');manual[i]={'observable_prefix_state':s,'rationale':n}
assert set(manual)=={r['item_id'] for r in x}
fixed={Path(p).stem for p in load(OLD/'annotations/fixed_readout_review_complete.json')['files']}
rows=[];flags=[]
for r in x:
 i=r['item_id'];q=r['query_review'];a=r['acquisition'];rout=r['readout_review']
 qi=next((v for v in (rout or {}).get('records',[]) if v['arm']=='QI'),None)
 scores={s['arm']:s for s in r['solver_rows']}
 row=dict(item_id=i,family_id=r['family_id'],**manual[i],image=r['image'],image_sha256=r['image_sha256'],prefix_sha256=r['prefix_sha256'],
  query=a['query'],query_valid=a['query_valid'],query_label=q['label'],query_relevance=q['task_relevance'],query_notes=q['notes'],
  address_label=r['address_review']['label'],address_notes=r['address_review']['notes'],crop_generated=len(a.get('views',{}).get('paths',[]))>1,
  qi_readout=a.get('readouts',{}).get('QI'),qi_existing_source_review=qi,
  native_status=scores['N']['final_status'],QI_status=scores['QI']['final_status'],
  any_regression=any(s['correct'] is False and scores['N']['correct'] is True for s in scores.values()),
  QI_rescue=scores['QI']['correct'] is True and scores['N']['correct'] is False,
  fixed24=i in fixed,annotation_scope='retrospective source/observable-text; not latent acquisition or causal diagnosis',
  provenance={'joined_record':'analysis/sava72_joined.json','acquisition':r['acquisition_path'],'query_review':str(OLD/f'annotations/query_only/{i}.json'),
              'address_review':str(OLD/f'annotations/address_only/{i}.json'),'solver_generations':{a:s['generation_path'] for a,s in scores.items()}},
  reviewer='main_AI',independent_review=False,source_display='analysis/source_sheet_'+str(x.index(r)//12)+'.jpg')
 rows.append(row)
 for arm,v in a.get('readouts',{}).items():
  raw=json.dumps(v.get('value'),ensure_ascii=False)
  if re.search(r'cannot.*(?:see|visual)|can.t.*(?:see|visual)|unavailable|no.*(?:visual|image).*provided|not.*(?:visual|image).*provided',raw,re.I):
   flags.append({'item_id':i,'arm':arm,'raw_record':v.get('value'),'generation':v.get('generation_path'),'heuristic_flag_only':True})
save(NEW/'analysis/postmortem_family_taxonomy_v1.json',rows)
rng=np.random.default_rng(20261022)
def estimate(vals):
 v=np.array(vals,dtype=float);b=np.mean(v[rng.integers(0,len(v),(4000,len(v)))],axis=1)
 return {'numerator':int(sum(v)),'denominator':len(v),'rate':float(v.mean()),'bootstrap_ci95':np.quantile(b,[.025,.975]).tolist(),'descriptive_previously_observed_families':True}
summary={'n':72,'observable_prefix_states':dict(collections.Counter(r['observable_prefix_state'] for r in rows)),
 'accepted_query_relevant':estimate([r['query_relevance']=='yes' for r in rows if r['query_valid'] and r['query']['status']=='QUERY']),
 'local_crop_correct_target':estimate([r['address_label']=='correct_for_requested_target' for r in rows if r['crop_generated']]),
 'any_regression_ids':[r['item_id'] for r in rows if r['any_regression']], 'QI_rescue_ids':[r['item_id'] for r in rows if r['QI_rescue']],
 'fixed24_ids':sorted(fixed,key=int),'annotation_limit':'One AI reviewer, source sheets plus existing detailed original-image reviews; retrospective and nonindependent. Unmentioned/ambiguous evidence never imputed error.'}
save(NEW/'analysis/postmortem_summary_v1.json',summary);save(NEW/'analysis/image_unavailable_claim_flags_v1.json',flags)
casebook=[]
for r in x:
 rr=next(v for v in rows if v['item_id']==r['item_id'])
 if rr['any_regression'] or rr['QI_rescue']:
  casebook.append({'item_id':r['item_id'],'image':r['image'],'image_sha256':r['image_sha256'],'prefix':r['prefix'],'query':r['acquisition']['query'],
   'address':r['acquisition'].get('address'),'readouts':r['acquisition'].get('readouts'), 'source_judgments':r['readout_review'],
   'solver_rows':r['solver_rows'],'causal_mediation':'NOT_IDENTIFIED: output changes may reflect evidence, prompting, stochastic trajectory changes or integration; no selective mediation intervention.'})
assert len(casebook)==12
save(NEW/'analysis/all_regressions_and_primary_rescues_v1.json',casebook)
print(json.dumps(summary,indent=2))
