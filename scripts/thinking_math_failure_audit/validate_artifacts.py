"""Independent arithmetic/coverage and exact-export checks; never rescores answers."""
import collections
import csv
import json
from pathlib import Path

from scripts.thinking_math_failure_audit.analyze import ROOT, OUT, read_json, read_rows, sha, save_json


def csv_rows(path):
    with Path(path).open() as f:return list(csv.DictReader(f))


def main():
    checks={}
    records=csv_rows(OUT/'all_thinking_records.csv')
    assert len(records)==13568 and len({r['task_id'] for r in records})==13568
    checks['all_thinking_records']=len(records)
    main=[r for r in records if r['replicate']=='0' and r['condition']!='evidence']
    assert len(main)==7768
    c=collections.Counter((r['dataset'],r['status']) for r in main)
    assert c['MATH-Vision','CORRECT']==1917 and c['MATH-Vision','WRONG']==1097 and c['MATH-Vision','UNSCORABLE']==26
    assert c['MathVerse','CORRECT']==3522 and c['MathVerse','WRONG']==1206
    failures=csv_rows(OUT/'main_native_failure_cases.csv')
    assert len(failures)==2329 and len({r['task_id'] for r in failures})==2329
    assert {r['task_id'] for r in failures}=={r['task_id'] for r in main if r['status']!='CORRECT'}
    checks['complete_primary_failure_inventory']=2329
    bysubject=collections.Counter()
    for r in csv_rows(OUT/'question_type_failure_rates.csv'):
        if r['dataset']=='MATH-Vision' and r['dimension']=='subject':
            assert int(r['n'])==int(r['correct'])+int(r['wrong'])+int(r['unscorable'])
            assert abs(float(r['wrong_rate'])-int(r['wrong'])/int(r['scored']))<1e-12
            bysubject['n']+=int(r['n']);bysubject['wrong']+=int(r['wrong'])
    assert bysubject=={'n':3040,'wrong':1097}
    checks['subject_partition_correct']=True
    profiles=csv_rows(OUT/'mathverse_family_profiles.csv')
    assert len(profiles)==788
    assert all(int(r['correct_versions'])+int(r['wrong_versions'])+int(r['unscorable_versions'])==6 for r in profiles)
    checks['six_versions_nested_in_788_families']=True
    followups=[r for r in csv_rows(OUT/'evidence_followups.csv') if r['replicate']=='0']
    counts=collections.Counter((r['native_status'],r['evidence_status']) for r in followups)
    assert counts['WRONG','CORRECT']==306 and counts['WRONG','WRONG']==110 and counts['WRONG','UNSCORABLE']==4
    assert len(followups)==1000
    checks['evidence_transitions_correct']=True
    inputs=read_json(OUT/'image_denial_input_receipt_check.json')
    assert inputs['n']==884 and inputs['all_saved_inputs_image_present']
    assert all(r['prepared_image_sizes'] for r in inputs['records'])
    checks['884_claims_have_present_processed_image_receipts']=True
    casebook=read_json(OUT/'casebook_provenance.json')
    for r in casebook:
        p=ROOT/r['generation_path'];assert sha(p)==r['generation_sha256']
        raw=read_json(p)['raw_decoded_response']
        assert raw[r['excerpt_start']:r['excerpt_end']]==r['quote']
        export=(OUT/'case_traces'/f"{r['task_id']}.md").read_text()
        assert export.split('````text\n',1)[1].rsplit('\n````',1)[0]==raw
    checks['exact_casebook_excerpts_and_complete_raw_exports']=len(casebook)
    validation=read_json(OUT/'validation.json')
    for path,digest in validation['source_hashes_unchanged'].items():assert sha(ROOT/path)==digest,path
    checks['original_input_tables_and_manifests_unchanged']=True
    # The evidence-status supplement is authoritative for R/F; never substitute CSV answer-parser values for reviewed correctness.
    source_audits=[r for r in csv_rows(ROOT/'outputs/stage14d0_answer_evidence_supplement_v1/family_evidence_status.csv') if r['model']=='T']
    ac=collections.Counter((r['panel'],r['native_status'],r['last_state']) for r in source_audits)
    assert ac['R','WRONG','2']==50 and ac['R','WRONG','1']==5 and ac['R','WRONG','3']==14
    assert ac['F','WRONG','2']==50 and ac['F','WRONG','1']==15 and ac['F','WRONG','3']==22
    checks['historical_R_F_evidence_denominators_preserved']=True
    save_json(OUT/'independent_validation.json',dict(passed=True,checks=checks,new_model_calls=0,new_gpu_hours=0))
    print(json.dumps(checks,indent=2))


if __name__=='__main__':main()
