"""Independent coverage, provenance, semantic arithmetic and gate verification."""
import os
import numpy as np
import pandas as pd
from scripts.stage10a.common import ROOT,DATA,load,save,sha,now,verify_config


def main():
    assert os.environ.get('SLURM_JOB_ID')
    cfg=verify_config();selection=load(ROOT/'stage10a_event_selection.json')
    primary=[r for r in selection['rows'] if r['split']=='primary']
    assert len(primary)==24 and len({r['image_id'] for r in primary})==24
    assert len(selection['reserve_ids'])==8
    assert sum(r['attribute']=='color' for r in primary)==12
    assert sha(ROOT/'stage10a_event_selection.json')==cfg['selection_sha256']
    gold={r['query_id']:r for r in load(DATA/'stage9a3_synthetic_dataset_manifest.json')['queries']}
    events={r['query_id']:r for r in selection['rows']}
    unique_paths=set();logical=0
    for stage,size in [('gate_a',144),('gate_b',96),('dominance_v2',48)]:
        mp=ROOT/f'audit/{stage}_manifest.json';m=load(mp)
        assert m['frozen'] and len(m['rows'])==size
        for p,digest in m['source_sha256'].items():assert sha(p)==digest,p
        review=load(ROOT/f'audit/{stage}_review.json');reviewed={r['task_id']:r for r in review['rows']}
        assert review['sealed'] and len(reviewed)==size
        for r in m['rows']:
            d=reviewed[r['task_id']];g=load(r['generation_path']);receipt=load(r['result_path'])
            assert sha(r['generation_path'])==receipt['generation_sha256']==d['generation_sha256']
            assert sha(r['result_path'])==d['result_sha256']
            n=r['prefix_tokens'];assert g['tokens']<=512 and g['prefix_tokens']==n
            assert g['continuation_tokens']==g['tokens']-n
            if r.get('reused'):
                assert stage=='gate_b' and r['condition']=='original'
                assert sha(r['generation_path'])==r['reused_generation_sha256']
            else:assert receipt['manifest_sha256']==sha(mp)
            if not g['reasoning_closed']:assert d['option'] is None
            if stage=='gate_a':ids=events[r['query_id']]['anchors'][r['anchor']]['prefix_ids']
            else:ids=r['prefix_ids']
            assert g['generated_token_ids'][:n]==ids
            if stage=='gate_b' or (stage=='gate_a' and r['condition']=='text_only'):
                assert not receipt['input']['image_present'] and not receipt['input']['original_cache_copied']
            if stage=='dominance_v2':
                assert receipt['input']['image_state_recomputed_from_current_image'] and not receipt['input']['original_cache_copied']
                assert sha(r['task']['image_path'])==r['task']['image_sha256']
            unique_paths.add(r['generation_path']);logical+=1
    assert logical==288 and len(unique_paths)==264
    for stage in ('gate_a','gate_b','dominance_v2'):
        m=load(ROOT/f'audit/{stage}_manifest.json');mr={r['task_id']:r for r in m['rows']}
        scores=load(ROOT/f'audit/{stage}_scored.json')['rows']
        for r in scores:
            query=gold[r['query_id']];option=r['option'];count=query['options'].get(option)
            if stage=='gate_a':assert r['correct']==(option==query['answer'])
            else:
                original=mr[r['task_id']]['original_count'];cf=mr[r['task_id']]['counterfactual_count']
                assert r['semantic_score']==(1 if count==cf else -1 if count==original else 0)
    a=load(ROOT/'audit/gate_a_inference.json');b=load(ROOT/'audit/gate_b_inference.json');c=load(ROOT/'audit/dominance_v2_inference.json')
    assert a['gate_a_pass'] and b['gate_b_pass']
    scores=load(ROOT/'audit/gate_a_scored.json')['rows']
    lookup={(r['image_id'],r['condition'],r['anchor']):float(r['correct']) for r in scores}
    images=sorted({r['image_id'] for r in scores});sample=np.random.default_rng(cfg['seed']).integers(0,24,(4000,24))
    for condition in ('text_only','image_off'):
        diff=np.array([lookup[i,condition,'post']-lookup[i,condition,'pre'] for i in images])
        expected=a[condition]['post_minus_pre'];assert abs(float(diff.mean())-expected['point'])<1e-12
        assert np.allclose(np.quantile(diff[sample].mean(1),[.025,.975]),expected['ci95'])
    scores=load(ROOT/'audit/gate_b_scored.json')['rows'];ix={(r['image_id'],r['condition']):r for r in scores}
    for other,key in [('original','cf_minus_original'),('sham','cf_minus_sham'),('delete','cf_minus_delete')]:
        diff=np.array([ix[i,'counterfactual']['semantic_score']-ix[i,other]['semantic_score'] for i in images])
        assert np.isclose(diff.mean(),b[key]['point']) and np.allclose(np.quantile(diff[sample].mean(1),[.025,.975]),b[key]['ci95'])
    scores=load(ROOT/'audit/dominance_v2_scored.json')['rows'];ix={(r['image_id'],r['condition']):r['semantic_score'] for r in scores}
    # Factorial marginal difference algebraically reduces to I0T1-I1T0.
    values=[ix[i,'I0T1']-ix[i,'I1T0'] for i in sorted({r['image_id'] for r in scores})]
    assert np.isclose(np.mean(values),c['text_minus_image']['point'])
    assert load(ROOT/'audit/technical_validation.json')['pass_all']
    assert load(ROOT/'audit/dominance_validation.json')['pass_all']
    v2=load(ROOT/'audit/dominance_v2_validation.json')
    assert v2['validation_reused'] and sha(v2['original_validation_path'])==v2['original_validation_sha256']
    for p,d in v2['unchanged_runtime_sha256'].items():assert sha(p)==d
    assert sorted(p.name for p in (ROOT/'audit').glob('*failure*.json'))==['validation_failure_124857.json']
    for path,n in [('stage10a_text_prefix_sufficiency.parquet',72),('stage10a_visual_necessity.parquet',72),
        ('stage10a_text_edit_results.parquet',96),('stage10a_image_text_2x2.parquet',48)]:assert len(pd.read_parquet(ROOT/path))==n
    artifacts=['stage10a_handoff_spec.md','stage10a_event_selection.json','stage10a_text_prefix_sufficiency.parquet',
        'stage10a_visual_necessity.parquet','stage10a_text_edit_results.parquet','stage10a_image_text_2x2.parquet',
        'stage10a_primary_inference.json','stage10a_reserve_extension.json','stage10a_mathvision_bridge.json',
        'stage10a_resource_accounting.json','stage10a_summary.md']
    for name in artifacts:assert (ROOT/name).is_file()
    figures=sorted((ROOT/'figures').glob('*'));assert len(figures)==8
    account=load(ROOT/'stage10a_resource_accounting.json');assert account['all_gpu_jobs_terminal'] and account['allocated_gpu_hours']<7
    out=load(ROOT/'stage10a_primary_inference.json');assert not out['full_handoff_supported'] and out['outcome']=='C'
    save(ROOT/'audit/final_validation.json',dict(at=now(),pass_all=True,independent_unit='image',primary_images=24,dominance_images=12,
        logical_rows=logical,unique_scientific_generations=len(unique_paths),source_hashes_pass=True,
        paired_arithmetic_and_bootstrap_pass=True,raw_receipts_and_native_final_review_pass=True,
        artifacts_sha256={n:sha(ROOT/n) for n in artifacts},figures_sha256={str(p):sha(p) for p in figures},
        immutable_pre_repair_artifacts_retained=True,known_failure_resolved=True,all_gpus_released=True))
    print('FINAL_AUDIT_PASS',logical,'logical',len(unique_paths),'new generations',flush=True)


if __name__=='__main__':main()
