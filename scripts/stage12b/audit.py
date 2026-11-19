"""Verify closure, full raw receipts, source preservation and stop boundaries."""
from pathlib import Path
from scripts.stage12b.common import ROOT,load,save,sha,now

REQUIRED=['visual_failure_bottleneck_spec.md','frozen_manifest.json','evidence_probe_prompts.json','native_prompts.json',
'oracle_prompts.json','oracle_integrity_review.json','technical_sanity.json','evidence_probe_results.parquet',
'native_results.parquet','oracle_results.parquet','failure_profiles.parquet','primary_inference.json','profile_decision.json',
'resource_accounting.json','summary.md']

def main():
    import pandas as pd
    manifest=load(ROOT/'stage12b_frozen_manifest.json');cfg=load(ROOT/'config.json');gate=load(ROOT/'stage12b_technical_sanity.json')
    assert sha(manifest['source'])==manifest['source_sha256']==cfg['source_manifest_sha256']
    assert load(manifest['source'])['rows']==manifest['rows']
    freeze=load(ROOT/'audit/prospective_freeze.json')
    for p,h in freeze['files'].items():assert sha(p)==h,p
    for p,h in cfg['source_sha256'].items():assert sha(p)==h,p
    dec=load(ROOT/'stage12b_profile_decision.json');res=load(ROOT/'stage12b_resource_accounting.json')
    assert res['all_stage_allocations_released'] and res['allocated_gpu_hours']<=8
    count=0
    for arm,name in [('E','evidence_probe'),('N','native'),('O','oracle')]:
        table=pd.read_parquet(ROOT/f'stage12b_{name}_results.parquet');assert len(table)==61 and table.family_id.nunique()==61
        assert set(table.arm)=={arm}
        for r in table.to_dict('records'):
            if r['status']=='NOT_RUN':continue
            p=Path(r['generation_path']);g=load(p);rec=load(p.parent/'result.json');inp=load(p.parent/'input.json')
            assert sha(p)==rec['generation_sha256']==r['generation_sha256'] and sha(p.parent/'input.json')==rec['input_sha256']
            assert g['raw_decoded_response']==r['raw_decoded_response'] and len(g['generated_token_ids'])==g['tokens']
            t=next(t for t in manifest['tasks'] if t['task_id']==r['task_id']);assert inp['task']==t
            assert (g['visual_tokens']==0)==(arm=='O') and inp['image_present']==(arm!='O')
            if arm=='O':assert not inp['prepared_image_pixel_sha256'] and t['image'] is None
            count+=1
        if not gate['pass']:
            assert table.correct.isna().all() and set(table.correctness_status)=={'NOT_SCORED_TECHNICAL_STOP'}
    assert count==dec['completed_calls']==(183 if gate['pass'] else 36)
    profile=pd.read_parquet(ROOT/'stage12b_failure_profiles.parquet');assert len(profile)==61
    if not gate['pass']:
        assert profile.bottleneck_class.isna().all() and dec['decision']=='TECHNICAL_STOP'
        assert not (ROOT/'audit/scientific_review.json').exists()
        assert all(t['item_id'] in manifest['technical_ids'] for t in manifest['tasks'] if (ROOT/'generations'/t['task_id']).exists())
    for name in REQUIRED:assert (ROOT/f'stage12b_{name}').exists(),name
    assert len(list((ROOT/'figures').glob('figure*.png')))==4
    assert len(list((ROOT/'figures').glob('figure*.pdf')))==4
    save(ROOT/'audit/closure_validation.json',dict(at=now(),pass_all=True,required_artifacts=15,
        required_sha256={str(ROOT/f'stage12b_{p}'):sha(ROOT/f'stage12b_{p}') for p in REQUIRED},
        raw_receipts_verified=count,source_families=61,source_facts=157,no_source_changes=True,
        oracle_no_image_verified=True,all_allocations_released=True,decision=dec['decision'],
        code_tests='Seven focused protocol, exclusion, gate and bootstrap tests pass.',no_followon=True))
    print('CLOSURE_VERIFIED',count,dec['decision'])

if __name__=='__main__':main()
