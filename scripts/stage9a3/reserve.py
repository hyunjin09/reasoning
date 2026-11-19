"""Execute the one predeclared, already-frozen sixteen-image extension."""
import argparse,os
import pandas as pd
from scripts.stage9a3.prepare import ROOT,load,save,sha,now
from scripts.stage9a3.baseline import gates_and_lengths
from scripts.stage9a3.grid import unique_policies,canonical,policy_id,baseline_alias
from visual_reasoning.stage9a3.analysis import extract_option,image_surface,calibration


def packet_full():
    assert load(ROOT/'audit/qwen25_primary_calibration_result.json')['reserve_eligible']
    tasks=[r for r in load(ROOT/'audit/inference_tasks.json')['rows'] if r['split']=='reserve'];assert len(tasks)==32
    rows=[]
    for t in tasks:
        p=ROOT/'qwen25/full_reserve/results'/t['query_id']/'full';g=load(p/'generation.json');r=load(p/'result.json')
        assert sha(p/'generation.json')==r['generation_sha256']
        rows.append(dict(query_id=t['query_id'],prompt=t['prompt'],text=g['text'],tokens=g['tokens'],normal_eos=g['normal_eos'],
            raw_option=extract_option(g['text']),generation_sha256=sha(p/'generation.json'),result_sha256=sha(p/'result.json')))
    save(ROOT/'audit/qwen25_reserve_full_review_packet.json',dict(at=now(),rows=rows,blinding='No gold answers or counts.'))


def score_full():
    pp=ROOT/'audit/qwen25_reserve_full_review_packet.json';rp=ROOT/'audit/qwen25_reserve_full_review.json';rev=load(rp)
    assert rev['sealed'] and not rev['gold_opened'] and rev['packet_sha256']==sha(pp)
    decisions={r['query_id']:r for r in rev['rows']};packet=load(pp)
    assert set(decisions)=={r['query_id'] for r in packet['rows']}
    gold={r['query_id']:r for r in load(ROOT/'stage9a3_synthetic_dataset_manifest.json')['queries']};rows=[]
    for r in packet['rows']:
        q=r['query_id'];d=decisions[q];p=ROOT/'qwen25/full_reserve/results'/q/'full'
        assert sha(p/'generation.json')==r['generation_sha256'] and sha(p/'result.json')==r['result_sha256']
        rows.append(dict(query_id=q,image_id=gold[q]['image_id'],attribute=gold[q]['attribute'],cot=d['cot'],option=d['option'],
            raw_option=r['raw_option'],answer=gold[q]['answer'],correct=d['option']==gold[q]['answer'],raw_correct=r['raw_option']==gold[q]['answer'],
            normal_eos=r['normal_eos'],tokens=r['tokens'],note=d['note']))
    combined=load(ROOT/'stage9a3_qwen25_full_access.json')['rows']+rows
    result=dict(at=now(),rows=rows,**gates_and_lengths(rows),combined_baseline=gates_and_lengths(combined),review_sha256=sha(rp),
        cap_unchanged=256,token_grid_unchanged=load(ROOT/'stage9a3_qwen25_full_access.json')['token_grid'])
    save(ROOT/'audit/qwen25_reserve_full_access.json',result)
    print({k:result[k] for k in ['counts','accuracy','gates','combined_baseline']},flush=True)


def freeze_grid():
    assert load(ROOT/'audit/qwen25_primary_calibration_result.json')['reserve_eligible']
    b=load(ROOT/'audit/qwen25_reserve_full_access.json')
    assert load(ROOT/'stage9a3_qwen25_full_access.json')['gates']['pass']
    primary=load(ROOT/'audit/qwen25_grid_primary_manifest.json');times=primary['token_grid'];rows=[];logical=[]
    for q in b['rows']:
        for f,t in unique_policies(times):
            pid=policy_id(f,t);reuse=(f==1 and t is None) or baseline_alias(f,t,q['tokens'],q['normal_eos'])
            dest=ROOT/'qwen25'/('full_reserve/results' if reuse else 'grid_reserve/results')/q['query_id']/('full' if reuse else pid)
            rows.append(dict(query_id=q['query_id'],image_id=q['image_id'],policy_id=pid,fraction=f,token_cutoff=t,mode='standard',
                execution='reuse_full' if reuse else 'run',result_path=str(dest/'result.json'),generation_path=str(dest/'generation.json'),
                reuse_result_sha256=sha(dest/'result.json') if reuse else None,
                proof='FULL wrapper is identical, or no mask activates before native EOS at full depth.' if reuse else None))
        for f in primary['fractions']:
            for t in times:logical.append(dict(query_id=q['query_id'],image_id=q['image_id'],fraction=f,token_cutoff=t,policy_id=policy_id(*canonical(f,t))))
    paths=dict(primary['source_sha256']);paths['scripts/stage9a3/reserve.py']=sha('scripts/stage9a3/reserve.py')
    save(ROOT/'audit/qwen25_grid_reserve_manifest.json',dict(at=now(),frozen=True,model='qwen25',token_grid=times,fractions=primary['fractions'],
        rows=rows,logical_rows=logical,source_sha256=paths,config_sha256=sha(ROOT/'config.json'),
        baseline_sha256=sha(ROOT/'audit/qwen25_reserve_full_access.json'),primary_manifest_sha256=sha(ROOT/'audit/qwen25_grid_primary_manifest.json'),
        fixed_reserve=True,no_retuning=True,scientific_cap=256))
    n=sum(r['execution']=='run' for r in rows)
    gen=[load(ROOT/'qwen25/full_reserve/results'/r['query_id']/'full/generation.json') for r in b['rows']]
    mean_seconds=sum(r['runtime_seconds'] for r in gen)/32
    save(ROOT/'audit/qwen25_reserve_resource_estimate.json',dict(at=now(),logical_rows=len(logical),canonical_rows=len(rows),new_grid_continuations=n,
        full_already_generated=32,expected_grid_gpu_hours=n*mean_seconds/3600,unchanged_cap=256,phase_a_remains_below_25gpu_hours=True))
    print('FROZEN',n,'new reserve continuations',flush=True)


def combine():
    assert os.environ.get('SLURM_JOB_ID')
    paths=[ROOT/f'audit/qwen25_grid_{split}_canonical_scored.json' for split in ['primary','reserve']]
    rows=[r for p in paths for r in load(p)['rows']];images,policies,values=image_surface(rows);assert len(images)==48
    meta={r['policy']:(r['fraction'],r['token_cutoff']) for r in rows};median=load(ROOT/'stage9a3_qwen25_full_access.json')['length_summary']['median']
    result=calibration(policies,values,meta,median)
    _,_,raw=image_surface([dict(r,correct=r['raw_correct']) for r in rows])
    b=load(ROOT/'audit/qwen25_reserve_full_access.json')
    assert load(ROOT/'stage9a3_qwen25_full_access.json')['gates']['pass']
    result.update(at=now(),model='qwen25',split='combined',images=images,technical_pass=True,baseline_valid=True,
        reserve_used=True,reserve_exhausted=True,raw_sensitivity=calibration(policies,raw,meta,median),
        primary_result_sha256=sha(ROOT/'audit/qwen25_primary_calibration_result.json'),source_scored_sha256={str(p):sha(p) for p in paths},
        completion_by_policy={p:dict(n=sum(r['policy']==p for r in rows),capped=sum(r['policy']==p and r['at_length_cap'] for r in rows),
           unscorable=sum(r['policy']==p and r['unscorable'] for r in rows)) for p in policies})
    save(ROOT/'audit/qwen25_combined_calibration_result.json',result)
    save(ROOT/'stage9a3_qwen25_positive_control.json',result)
    frames=[pd.read_parquet(ROOT/'stage9a3_qwen25_coarse_grid.parquet'),pd.read_parquet(ROOT/'audit/qwen25_grid_reserve_scored.parquet')]
    out=ROOT/'stage9a3_qwen25_coarse_grid_extended.parquet';assert not out.exists();pd.concat(frames,ignore_index=True).to_parquet(out,index=False)
    save(ROOT/'stage9a3_qwen25_reserve_extension.json',dict(at=now(),activated=True,images=[f'image{i:03d}' for i in range(32,48)],
        activation_sha256=sha(ROOT/'audit/reserve_activation.json'),primary_queries=64,reserve_queries=32,combined_images=48,
        no_prompt_grid_cap_changes=True,combined_full_access=b['combined_baseline'],final_positive_control_sha256=sha(ROOT/'stage9a3_qwen25_positive_control.json'),
        extended_parquet_sha256=sha(out),further_extension_authorized=False))
    print({k:result[k] for k in ['pass','full_accuracy','selected_policy','bootstrap_joint_stability','clear_restriction_damage']},flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['packet_full','score_full','freeze_grid','combine']);a=ap.parse_args();globals()[a.action]()
