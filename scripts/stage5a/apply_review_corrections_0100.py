"""Corrections from the second source-crop review; no scores available."""
from scripts.stage5a.prepare import OUT,read_json,write_json
fixes={'202':{'B':[182,228,227,261]},'205':{'C':[150,227,186,259]},
 '210':{'A':[88,1092,191,1177],'B':[296,455,395,534]},
 '218':{'A':[112,127,201,168],'B':[224,168,284,211]},'242':{'B':[333,73,552,130]}}
audit=[]
for path in sorted((OUT/'cohort/review').glob('manual_[0-9][0-9][0-9][0-9].json')):
 rows=read_json(path)
 for r in rows:
  b=r['base']
  for key,box in fixes.get(b,{}).items():
   old=r['facts'][key]['roi'];r['facts'][key]['roi']=box;audit.append({'base':b,'source':key,'old_roi':old,'corrected_roi':box})
  if b=='205':r['events'][0]['quote']="There's a right angle marked with a red square, so that's a 90-degree angle"
  if b=='180':r['facts']['A']['edit_roi']=[532,167,584,239]
  if b=='218':r['facts']['A']['render_suffix']=' m'
  if b=='246':r['facts']['A']['render_suffix']=' cm'
  if b=='222':
   for k,suffix in [('A',' in.'),('B',' in²'),('C',' in²')]:r['facts'][k]['render_suffix']=suffix
  for e in r['events']:
   e.setdefault('semantic_role','VISUAL_CLAIM' if e['correctness']!='UNDECIDABLE' else 'CURRENTLY_DEMANDED')
   e.setdefault('has_explicit_visual_claim',e['correctness']!='UNDECIDABLE')
  if path.stem>='manual_0060':r['roi_review_status']='needs_corrected_crop_check' if b in fixes else 'source_numeric_or_relational_content_reviewed'
  if b in ('28','247'):r['roi_review_status']='ground_truth_ambiguous_atlas_unavailable'
 write_json(path,rows)
write_json(OUT/'cohort/review/roi_correction_audit_0100.json',{'before_causal_scoring':True,'corrections':audit,
 'review_sheets':['roi_0100.png','roi_0148.png'],'last_8_source_crops_pending':True,
 'units_preserved_for':['218A','222A','222B','222C','246A'],
 'compound_pixel_masks':['233B'],'atlas_identity_uncertainties':['28','247']})
