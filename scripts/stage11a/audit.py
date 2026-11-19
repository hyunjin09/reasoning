"""Fail closed on incomplete evidence, altered baselines, or resource violations."""
import os
from scripts.stage11a.common import ROOT,load,save,sha,now

def main():
    assert os.environ.get('SLURM_JOB_ID')
    provenance=load(ROOT/'audit/input_provenance.json')
    assert provenance['independent_families']==128 and provenance['existing_trajectories']==384
    assert sha(provenance['source'])==provenance['source_sha256']
    for r in provenance['rows']:
        for p,h in r['source_sha256'].items():assert sha(p)==h,p
    cfg=load(ROOT/'probe_config.json');manifest=load(ROOT/'stage11a_probe_manifest.json')
    for p,h in {**cfg['frozen_artifact_sha256'],**cfg['source_sha256']}.items():assert sha(p)==h,p
    assert len(manifest['selected_item_ids'])<=64 and len(manifest['rows'])==3*len(manifest['selected_item_ids'])
    for r in manifest['rows']:
        d=ROOT/'probes/results'/r['task_id'];receipt=load(d/'result.json')
        assert receipt['preprocessing_matches_native'] and receipt['tokens']<=512
        assert receipt['manifest_sha256']==sha(ROOT/'stage11a_probe_manifest.json')
        assert receipt['generation_sha256']==sha(d/'generation.json') and receipt['input_sha256']==sha(d/'input.json')
    eligibility=load(ROOT/'stage11a_e_star_eligibility.json')
    assert len(eligibility['rows'])==128 and eligibility['model_outcomes_opened'] is False
    n=sum(r['eligibility']=='E_STAR_ELIGIBLE' for r in eligibility['rows'])
    joined=load(ROOT/'audit/census_joined.json')
    assert len(joined['rows'])==3*n and len({(r['family_id'],r['arm']) for r in joined['rows']})==3*n
    assert sum(r['probed'] for r in joined['rows'])==len(manifest['rows'])
    for p,h in joined['sources_sha256'].items():assert sha(p)==h,p
    resource=load(ROOT/'stage11a_resource_accounting.json')
    assert resource['all_gpu_jobs_terminal'] and resource['allocated_gpu_hours']<2.5 and resource['peak_gpus']<=8
    decision=load(ROOT/'stage11a_go_nogo_decision.json');assert decision['stage11b_launched'] is False
    required=['stage11a_bottleneck_census_spec.md','stage11a_e_star_eligibility.json','stage11a_e_star_gold.parquet',
        'stage11a_e_star_sufficiency_review.json','stage11a_native_evidence_states.parquet','stage11a_probe_manifest.json',
        'stage11a_probe_results.parquet','stage11a_bottleneck_profiles.parquet','stage11a_thinking_cot_discordance.json',
        'stage11a_annotation_agreement.json','stage11a_primary_inference.json','stage11a_go_nogo_decision.json',
        'stage11a_resource_accounting.json','stage11a_summary.md']
    for p in required:assert (ROOT/p).stat().st_size>0,p
    figures=list((ROOT/'figures').glob('*.png'));assert len(figures)>=4
    for p in figures:assert p.with_suffix('.pdf').stat().st_size>0
    save(ROOT/'audit/completion_audit.json',dict(at=now(),passed=True,eligible=n,probes=len(manifest['rows']),
        original128_families_and384_traces_unchanged=True,all_gpu_jobs_terminal=True,stage11b_launched=False,
        resource_gpu_hours=resource['allocated_gpu_hours'],required_artifact_sha256={p:sha(ROOT/p) for p in required},
        figure_sha256={str(p):sha(p) for p in list((ROOT/'figures').glob('*.png'))+list((ROOT/'figures').glob('*.pdf'))}))
    print('AUDIT_PASSED',n,'eligible',len(manifest['rows']),'probes')

if __name__=='__main__':main()
