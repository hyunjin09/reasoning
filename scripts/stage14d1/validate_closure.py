"""Verify preservation, source identity and honest missingness at technical closure."""
import csv
import subprocess
from scripts.stage14d1.common import *
from scripts.stage14d1.contracts import safe_payload

def validate():
    counts={}
    for seal in ['outputs/stage14d0_visual_difficulty/v2/audit/final_package_seal.json',
                 'outputs/stage14d0/audit/output_package_seal_v1.json']:
        files=load(seal)['package_files']
        for path,h in files.items():
            assert sha(path)==h, path
        counts[seal]=len(files)
    for name in ['execution_seal_v1.json','execution_seal_v2.json','execution_seal_v3.json']:
        seal=load(P/'audit'/name)
        for path,h in seal['files'].items():
            assert sha(path)==h, path
        counts[name]=len(seal['files'])
    original=(P/'provenance/original_plan_v1.md').read_text()
    assert Path('plan/stage14d1_sava_method_feasibility_plan.md').read_text().endswith(original)
    provenance=rows(P/'provenance/source_inputs_manifest.jsonl')
    families=rows(P/'inference/families.jsonl')
    selected=rows(P/'data/selected_family_target_manifest.jsonl')
    assert len(families)==len(provenance)==len(selected)==72
    assert len({r['family_id'] for r in families})==72
    for r in provenance:
        for field in ['image','native_input','native_raw']:
            assert sha(r[field])==r[field+'_sha256'],r[field]
    for r in families:
        safe_payload(r)
        assert hashlib.sha256(r['prefix'].encode()).hexdigest()==r['prefix_sha256']
    counts['upstream_source_files_verified']=len(provenance)*3
    physical=rows(P/'data/physical_request_inventory.jsonl')
    assert len(physical)==93
    for r in physical:
        assert sha(r['input_path'])==r['input_sha256']
        if r['generation_path']:
            assert sha(r['generation_path'])==r['generation_sha256']
            receipt=load(Path(r['generation_path']).parent/'result.json')
            assert receipt['input_sha256']==r['input_sha256']
            assert receipt['generation_sha256']==r['generation_sha256']
    completed=sum(r['generation_path'] is not None for r in physical)
    assert completed==85
    answers=list(csv.DictReader((P/'analysis/answer_transitions_and_costs.csv').open()))
    assert len(answers)==432 and all(r['intervention_correct']==r['native_correct']=='' for r in answers)
    bootstrap=load(P/'analysis/paired_bootstrap.json')
    assert bootstrap['estimates'] is None and bootstrap['confidence_intervals'] is None
    assert bootstrap['independent_families_analyzed']==0
    resource=load(P/'audit/resource_accounting_final.json')
    ids=','.join(r['job_id'] for r in resource['jobs'])
    active=subprocess.run(['squeue','-h','-j',ids,'-o','%i %T'],check=True,capture_output=True,text=True).stdout.strip()
    assert not active,active
    assert resource['total_allocated_GPU_hours']<2
    result=dict(at=now(),status='PASS',preservation_counts=counts,
                physical_inputs_verified=len(physical),completed_generations_verified=completed,
                original_plan_body_preserved=True,no_scientific_outcomes_fabricated=True,
                source_families=72,main_outcome_rows_not_run=432,
                active_stage_jobs=active,allocated_GPU_hours=resource['total_allocated_GPU_hours'])
    save(P/'audit/final_validation.json',result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    validate()
