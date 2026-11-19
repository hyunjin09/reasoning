"""Validate final cohort contracts and publication joins, independently of assembly."""
import re
from collections import Counter
from scripts.stage14a.common import *
from scripts.stage14a.review import rendering
from scripts.stage14a.review_v2 import validate
from scripts.stage14a.sampling import confirm

def main():
 checks={}
 def passed(name,condition):
  assert condition,name
  checks[name]=True
 plan=Path('plan/stage14a_large_scale_math_cohort_construction_plan.md').read_text().split('## 31. Required artifacts')[1].split('## 32.')[0]
 required=re.findall(r'`(stage14a_[^`]+)`',plan)
 passed('21_required_artifacts',len(required)==21 and all((ROOT/n).is_file() for n in required))
 mv0=load(ROOT/'audit/mathvision_census_source_snapshot.json')['rows'];mv=load(ROOT/'stage14a_mathvision3040_manifest.json')['rows'];by={r['item_id']:r for r in mv0}
 passed('3040_native_ids',len(mv)==3040 and {r['item_id'] for r in mv}==set(by))
 passed('native_mv_source_fields_unchanged',all(all(r[k]==by[r['item_id']][k] for k in ['question','question_hash','options','gold_answer','image','image_hash','answer_type','subject','difficulty']) for r in mv))
 a=load(ROOT/'stage14a_mathvision_e_star_annotations.json')['rows'];am={r['family_id']:r for r in a}
 passed('1000_unique_final_families',len(a)==len(am)==1000)
 passed('qc_rejection_replaced',not any(r['item_id']=='1174' for r in a) and any(r['item_id']=='879' and r['rank']==1727 for r in a))
 for r in a:validate(by[r['item_id']],r)
 passed('all_1000_schema_and_second_review',True)
 rr={r['family_id']:r for r in load(ROOT/'stage14a_mathvision_equal_evidence_renderings.json')['rows']};probes={r['family_id']:r for r in load(ROOT/'stage14a_mathvision_evidence_probe_requests.json')['rows']}
 passed('exact_rendering_and_hashes',set(rr)==set(am) and all(rr[f]['text']==rendering(by[r['item_id']],r['e_star_atoms']) and digest(rr[f]['text'])==rr[f]['sha256'] for f,r in am.items()))
 passed('one_probe_per_atom',set(probes)==set(am) and all(probes[f]['requests']==r['evidence_request_per_atom'] and len(probes[f]['requests'])==r['num_e_star_atoms'] for f,r in am.items()))
 qc=load(ROOT/'stage14a_mathvision_qc_records.json');want=sorted(am,key=lambda f:digest('stage14a-v1|mv-qc|'+f))[:250]
 passed('250_final_hash_selected_rereads',qc['final_selected_family_ids']==want and sum(r['final_250_selected'] for r in qc['rows'])==250 and all(r['complete_reread'] and r['complete_reread']['eligibility']=='PASS' for r in qc['rows'] if r['final_250_selected']))
 passed('all_review_receipts_immutable',all(sha(r['primary_receipt'])==r['primary_receipt_sha256'] for r in qc['rows']))
 c=load(ROOT/'stage14a_mathvision_confirm300_manifest.json');expected=confirm(a,300,c['strata'],'stage14a-v1|mv-confirm|')
 passed('mv_confirm300_deterministic',len(c['rows'])==300 and [r['family_id'] for r in c['rows']]==[r['family_id'] for r in expected])
 v0=load(ROOT/'audit/mathverse_mapping_source_snapshot.json');families=load(ROOT/'stage14a_mathverse788_family_manifest.json')['rows'];versions=load(ROOT/'stage14a_mathverse_variant_mapping.json')['rows']
 passed('788_native_families_4728_versions',len(families)==788 and len(versions)==4728 and len({r['family_id'] for r in families})==788)
 vd={(r['family_id'],r['version']):r for r in versions}
 passed('six_versions_each',len(vd)==4728 and set(Counter(r['family_id'] for r in versions).values())=={6})
 passed('all_native_version_inputs_unchanged',all(all(vd[(r['family_id'],r['version'])][k]==r[k] for k in r if k!='semantic_source_review') for r in v0['versions']))
 vq=load(ROOT/'stage14a_mathverse_qc_records.json')['rows'];chosen={r['family_id'] for r in vq if r['second_review']}
 passed('197_prospective_mathverse_rereads',len(chosen)==197 and chosen==set(load(ROOT/'audit/mathverse_prospective_qc197.json')['family_ids']))
 passed('source_ambiguities_explicit_review_disagreements_resolved',all(r['review_disagreements_resolved'] for r in vq) and all(r['semantic_source_review']=='COMPLETE' for r in families))
 cv=load(ROOT/'stage14a_mathverse_confirm300_manifest.json');ev=confirm(v0['families'],300,cv['strata'],'stage14a-v1|mathverse-confirm|')
 passed('mathverse_confirm300_unchanged',len(cv['rows'])==300 and [r['family_id'] for r in cv['rows']]==[r['family_id'] for r in ev])
 passed('all_4728_source_metadata_rows',len(load(ROOT/'stage14a_mathverse_source_metadata.json')['rows'])==4728)
 scan=load(ROOT/'audit/historical_identity_scan_final.json')
 for ds,n in [('mathvision',2104),('mathverse',788)]:
  hist=load(ROOT/f'stage14a_{ds}_historical_exposure.json')['rows']
  passed(ds+'_history_family_joins',len(hist)==n and all(all(0<=i<len(scan['records']) for i in r['artifact_indices']) for r in hist))
 passed('original_source_prior_and_code_hashes_match',load(ROOT/'audit/final_input_preservation_verification.json')['all_match'])
 figure=load(ROOT/'audit/source_figure_manifest.json')
 passed('five_png_five_pdf_figures_match',len(figure['files'])==10 and all(sha(p)==h for p,h in figure['files'].items()))
 stats=load(ROOT/'stage14a_source_statistics.json');m=stats['mathvision'];passed('screening_conservation',m['screened']==1727==m['accepted']+sum(m['exclusions'].values())+m['duplicate_accepted_source_receipts'])
 passed('zero_model_calls_and_gpu_hours',stats['new_evaluated_model_calls']==stats['external_annotator_calls']==stats['gpu_hours']==0)
 acc=load(ROOT/'stage14a_resource_accounting.json');passed('stage_cpu_jobs_complete',all(j['status']=='succeeded' and j['gpus']==0 for j in acc['jobs']))
 preserved=load(ROOT/'stage14a_preservation_manifest.json')
 passed('final_artifact_and_receipt_hashes',all(sha(p)==h for p,h in preserved['final_files'].items()))
 save(ROOT/'audit/final_validation.json',dict(at=now(),checks=checks,passed=len(checks),failed=0,scope='Structural,identity,hash and rendering contracts; actual semantic review comes from preserved manual receipts, not these assertions.'))
 print('FINAL_VALIDATION',len(checks),'PASS')

if __name__=='__main__':main()
