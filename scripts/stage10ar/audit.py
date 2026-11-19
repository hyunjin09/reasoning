"""Separate artifact/arithmetical audit; never changes frozen scientific outputs."""
import os
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
from scripts.stage10ar.common import ROOT,load,save,sha,now,verify_config
from scripts.stage9a3.literal_review import terminal_option


def main():
    assert os.environ.get('SLURM_JOB_ID')
    cfg=verify_config();cohort=load(ROOT/'stage10ar_primary_cohort.json');ann=load(ROOT/'stage10ar_anchor_annotations.json')
    assert cfg['annotations_sha256']==sha(ROOT/'stage10ar_anchor_annotations.json')
    assert cfg['cohort_sha256']==sha(ROOT/'stage10ar_primary_cohort.json')
    assert ann['frozen'] and not ann['intervention_outcomes_used']
    events={e['query_id']:e for e in ann['rows']};selected=cohort['primary_ids'];reserve=cohort['reserve_ids']
    assert len(selected)==24 and len(reserve)==8 and not(set(selected)&set(reserve))
    assert len({events[q]['image_id'] for q in selected+reserve})==32
    assert Counter(events[q]['attribute'] for q in selected)=={'color':12,'shape':12}
    for q in selected+reserve:
        e=events[q];g=load(e['generation_path']);a=e['anchors']
        assert g['reasoning_closed'] and terminal_option(g['final_text'])==e['source_answer']
        assert 0==a['A0']['native_tokens']<a['A1']['native_tokens']<a['A3']['native_tokens']<=a['A4']['native_tokens']
        if a['A2']:assert a['A1']['native_tokens']<a['A2']['native_tokens']<a['A3']['native_tokens']
        for point in a.values():
            if point is None:continue
            n=point['native_tokens'];assert len(point['prefix_ids'])==n and point['prefix_ids']==g['generated_token_ids'][:n]
    checks={};new_paths=set()
    for stage in ('primary','optional'):
        mp=ROOT/f'audit/{stage}_manifest.json';m=load(mp);pp=ROOT/f'audit/{stage}_review_packet.json'
        review=load(ROOT/f'audit/{stage}_review.json');reviewed={r['task_id']:r for r in review['rows']}
        assert review['sealed'] and review['packet_sha256']==sha(pp) and load(pp)['manifest_sha256']==sha(mp)
        assert m['config_sha256']==sha(ROOT/'config.json')
        for p,d in m['source_sha256'].items():assert sha(p)==d,p
        for r in m['rows']:
            g=load(r['generation_path']);receipt=load(r['result_path']);d=reviewed[r['task_id']]
            assert sha(r['generation_path'])==receipt['generation_sha256']==d['generation_sha256']
            assert sha(r['result_path'])==d['result_sha256']
            n=r['prefix_tokens'];assert g['generated_token_ids'][:n]==r['prefix_ids']
            assert g['tokens']<=512 and g['tokens']==n+g['continuation_tokens']
            if r['execution']=='run':
                new_paths.add(r['generation_path']);assert receipt['manifest_sha256']==sha(mp)
                assert receipt['prefix_tokens']==n and receipt['remaining_tokens']==512-n
                meta=receipt['input']
                if r['condition']!='image_off':
                    assert meta['mode']=='fresh_text_only' and not meta['image_present'] and not meta['original_cache_copied'] and not meta['image_derived_state_copied']
                else:
                    assert meta['original_cache_preserved'] and meta['prior_prefix_exact']
                    assert meta['mask_cutoff']==max(0,n-1) and meta['first_masked_absolute_query']==meta['input']['prompt_length']+max(1,n)-1
            if receipt.get('reused'):
                for name in ('generation','result','manifest'):
                    assert sha(receipt[f'source_{name}_path'])==receipt[f'source_{name}_sha256']
            if stage=='optional' and r['execution']=='reuse':
                assert sha(r['generation_path'])==r['source_generation_sha256'] and sha(r['result_path'])==r['source_result_sha256']
        checks[stage]=dict(logical_rows=len(m['rows']),unique_generation_paths=len({r['generation_path'] for r in m['rows']}),
            execution_counts=dict(Counter(r['execution'] for r in m['rows'])))
    assert len(new_paths)==190
    scored=load(ROOT/'audit/primary_scored.json')['rows'];result=load(ROOT/'stage10ar_primary_inference.json')
    images=sorted({r['image_id'] for r in scored});by={(r['image_id'],r['condition'],r['anchor']):r for r in scored}
    contrasts=[('image_off','A4','A0'),('text_only','A4','A0'),('image_off','A3','A1'),('text_only','A3','A1')]
    ix=np.random.default_rng(920260927).integers(0,24,size=(4000,24))
    for j,(condition,late,early) in enumerate(contrasts,1):
        d=np.array([int(by[i,condition,late]['correct'])-int(by[i,condition,early]['correct']) for i in images])
        expected=result['primary'][f'P{j}'];assert abs(d.mean()-expected['point'])<1e-12
        assert np.allclose(np.quantile(d[ix].mean(1),[.00625,.99375]),expected['familywise95_ci'])
        assert expected['positive']==int((d>0).sum()) and expected['negative']==int((d<0).sum())
    for assay,file in [('image_off','stage10ar_visual_necessity.parquet'),('text_only','stage10ar_text_sufficiency.parquet')]:
        frame=pd.read_parquet(ROOT/file);expected=[r for r in scored if r['condition']==assay]
        assert len(frame)==118 and set(frame.task_id)=={r['task_id'] for r in expected}
        assert int(frame.correct.sum())==sum(r['correct'] for r in expected)
    assert result['main_gate_pass'] and all(result['gate_components'].values()) and not result['reserve_gate_pass']
    assert not load(ROOT/'stage10ar_reserve_extension.json')['executed'] and load(ROOT/'stage10ar_a3_text_edit.json')['executed']
    states=load(ROOT/'stage10ar_item_transition_states.json')
    for r in states['rows']:
        good=[]
        for j in range(5):
            key=(r['image_id'],'image_off',f'A{j}')
            if key in by and by[key]['correct'] and by[r['image_id'],'text_only',f'A{j}']['correct']:good.append(f'A{j}')
        assert r['H']==(good[0] if good else None)
    account=load(ROOT/'stage10ar_resource_accounting.json')
    assert account['all_gpu_jobs_terminal'] and account['scientific_generations']==190 and account['allocated_gpu_hours']<3
    assert account['observed_peak_gpus']<=8
    failures=list((ROOT/'audit').glob('*worker_failure_*.json'))
    assert {p.name for p in failures}=={'optional_worker_failure_125017.json','optional_worker_failure_125018.json'}
    repair=load(ROOT/'audit/optional_resume_manifest.json')
    assert repair['parent_manifest_sha256']==sha(ROOT/'audit/optional_manifest.json')
    assert repair['diagnostic_sha256']==sha(ROOT/'audit/optional_display_diagnostic.json')
    for p,d in repair['source_sha256'].items():assert sha(p)==d,p
    for row in repair['rows']:
        receipt=load(row['result_path']);assert receipt['resume_manifest_sha256']==sha(ROOT/'audit/optional_resume_manifest.json')
    for p in sorted((ROOT/'figures').glob('*')):assert p.stat().st_size>1000
    assert len(list((ROOT/'figures').glob('*.png')))==len(list((ROOT/'figures').glob('*.pdf')))==4
    artifacts=['stage10ar_phase_localization_spec.md','stage10ar_anchor_annotations.json','stage10ar_primary_cohort.json',
        'stage10ar_visual_necessity.parquet','stage10ar_text_sufficiency.parquet','stage10ar_primary_inference.json',
        'stage10ar_item_transition_states.json','stage10ar_a3_text_edit.json','stage10ar_reserve_extension.json',
        'stage10ar_resource_accounting.json','stage10ar_summary.md']
    hashes={str(ROOT/p):sha(ROOT/p) for p in artifacts}
    hashes.update({str(p):sha(p) for p in (ROOT/'figures').glob('*')})
    save(ROOT/'audit/final_audit.json',dict(at=now(),pass_all=True,checks=checks,artifact_sha256=hashes,
        methods='Main-agent separate arithmetic/provenance audit, not an independent human or agent review.',
        primary_contrasts_recomputed=True,masked_prefix_and_fresh_text_receipts_verified=True,
        prior_evidence_hashes_unchanged=True,source_hashes_unchanged=True,all_gpu_jobs_terminal=True))
    print('AUDIT PASS',checks,'190 new scientific generations;11 artifacts;4 PNG/PDF figures',flush=True)


if __name__=='__main__':main()
