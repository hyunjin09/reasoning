"""Prospective corrections from full-resolution source/candidate review, no causal data."""
from scripts.stage5a.prepare import OUT,read_json,write_json
fixes={
'17':{'B':[90,128,129,150]},'32':{'A':[150,108,183,128]},'34':{'A':[130,121,174,144]},
'40':{'A':[257,22,290,42]},'41':{'A':[12,32,50,51],'B':[10,114,49,133],'C':[205,47,244,67]},
'42':{'A':[198,62,248,84]},'44':{'A':[8,173,40,199],'B':[68,185,103,214],'C':[53,102,90,126]},
'169':{'A':[92,123,112,146]}}
audit=[]
for path in sorted((OUT/'cohort/review').glob('manual_[0-9][0-9][0-9][0-9].json')):
 rows=read_json(path)
 for r in rows:
  b=r['base']
  for key,box in fixes.get(b,{}).items():
   old=r['facts'][key]['roi'];r['facts'][key]['roi']=box;audit.append({'base':b,'source':key,'old_roi':old,'corrected_roi':box,'reason':'Full-resolution coordinate/crop review found clipping or blank/misaligned initial box.'})
  if b=='135':r['events'][1]['quote']='angle AOM = 140°, so arc AM is 140°'
  if b=='87':
   r['events'][1].update(quote='the central angle for arc DE is angle EOD, which is 50°',readout='50',truth='50',correctness='CORRECT',readout_kind='numeric_fact')
   r['events'][1].pop('claim_note',None)
  if b=='5':
   # Derived angle2 is not an independently seen image fact.
   r['events'][2].update(has_explicit_visual_claim=False,semantic_role='CURRENTLY_DEMANDED',readout_kind='derived_visual_demand')
   r['events'][2]['claim_note']+=' Derived angle2 error is excluded from visual-hallucination eligibility.'
  if b=='56':r.pop('derived_event_ids',None)
  for e in r['events']:
   e.setdefault('semantic_role','VISUAL_CLAIM' if e['correctness']!='UNDECIDABLE' else 'CURRENTLY_DEMANDED')
   e.setdefault('has_explicit_visual_claim',e['correctness']!='UNDECIDABLE')
  r['roi_review_status']='needs_corrected_crop_check' if b in fixes else 'source_numeric_or_relational_content_reviewed'
  if b=='28':r['roi_review_status']='ground_truth_unreadable_atlas_unavailable'
 write_json(path,rows)
write_json(OUT/'cohort/review/roi_correction_audit_0060.json',{'before_causal_scoring':True,'corrections':audit,'review_sheets':['roi_0000.png','roi_0048.png','roi_0096.png'],'unresolved_semantic_source':['28']})
