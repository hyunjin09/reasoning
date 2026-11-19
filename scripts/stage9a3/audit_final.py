"""Independent arithmetic, paired-bootstrap and immutability checks."""
import os,subprocess
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scripts.stage9a3.prepare import ROOT,load,save,sha,now


def main():
    assert os.environ.get('SLURM_JOB_ID')
    checks=[];gold={r['query_id']:r['answer'] for r in load(ROOT/'stage9a3_synthetic_dataset_manifest.json')['queries']}
    for key in ['qwen25','qwen3']:
        b=load(ROOT/f'stage9a3_{key}_full_access.json')
        assert len(b['rows'])==64 and len({r['image_id'] for r in b['rows']})==32
        assert sum(r['option']==gold[r['query_id']] for r in b['rows'])==b['counts']['correct']
        assert sum(r['cot'] for r in b['rows'])==b['counts']['cot']
        gate=load(ROOT/f'stage9a3_mask_validation_{key}.json');assert gate['pass_all'] and gate['examples']==8
        for p,h in gate['source_sha256'].items():assert sha(p)==h
        for p,h in gate['checks_sha256'].items():assert sha(p)==h
        review=load(ROOT/f'audit/{key}_full_review.json');assert review['sealed'] and not review['gold_opened']
        checks.append(key+' baseline counts, sealed review,8 technical checks and source hashes')
    p=load(ROOT/'stage9a3_qwen25_positive_control.json');assert p['n_images']==48 and p['pass']
    frames=pd.read_parquet(ROOT/'stage9a3_qwen25_coarse_grid_extended.parquet');assert len(frames)==1536
    assert frames['image_id'].nunique()==48 and frames['query_id'].nunique()==96
    canonical=frames.drop_duplicates(['query_id','policy']);assert len(canonical)==960
    assert canonical.groupby(['image_id','policy']).size().eq(2).all()
    table=canonical.groupby(['image_id','policy'])['correct'].mean().unstack()
    assert len(table)==48 and table.shape[1]==10 and table.notna().all().all()
    rng=np.random.default_rng(920260927);indices=rng.integers(0,48,size=(4000,48))
    zero=table['l100_tFULL'].to_numpy()-table['l000_t0'].to_numpy()
    selected=table['l100_tFULL'].to_numpy()-table[p['selected_policy']].to_numpy()
    zboot=zero[indices].mean(axis=1);sboot=selected[indices].mean(axis=1)
    for policy in table:
        diff=table['l100_tFULL'].to_numpy()-table[policy].to_numpy()
        assert abs(float(table[policy].mean())-p['surface'][policy]['accuracy'])<1e-12
        assert abs(float(diff.mean())-p['surface'][policy]['damage'])<1e-12
        assert np.allclose(np.quantile(diff[indices].mean(axis=1),[.025,.975]),p['surface'][policy]['ci95'],atol=1e-12)
    assert abs(np.mean((zboot>0)&(sboot<=.05+1e-12))-p['bootstrap_joint_stability'])<1e-12
    checks.append('Independent image-equal counts,10 canonical/16 logical cells,4000 paired bootstrap intervals and gate stability')
    for split,n in [('primary',571),('reserve',287)]:
        m=load(ROOT/f'audit/qwen25_grid_{split}_manifest.json');assert sum(r['execution']=='run' for r in m['rows'])==n
        for path,h in m['source_sha256'].items():assert sha(path)==h
        for r in m['rows']:
            result=load(r['result_path']);assert sha(r['generation_path'])==result['generation_sha256']
            if r['execution']=='reuse_full':assert sha(r['result_path'])==r['reuse_result_sha256']
    checks.append('858 new standard grid receipts and all exact FULL aliases unchanged')
    sink=load(ROOT/'stage9a3_bounded_null_sink_control.json');assert sink['qwen25_new_continuations']==125
    assert sink['qwen25']['conditions']['l000_t0']['sink_ci95'][0]>0
    assert sink['qwen25']['conditions']['l100_t64']['sink_damage']<=.05
    q3=load(ROOT/'stage9a3_qwen3_full_access.json');assert not q3['gates']['pass']
    assert (q3['counts']['correct']+64-q3['counts']['valid_option'])/64==.59375
    assert not list((ROOT/'qwen3/grid_primary/results').glob('*/*/result.json'))
    assert pq.read_table(ROOT/'stage9a3_qwen3_coarse_grid.parquet').num_rows==0
    assert b'NOT RUN' in pq.read_schema(ROOT/'stage9a3_qwen3_coarse_grid.parquet').metadata[b'execution_status']
    assert load(ROOT/'stage9a3_generation_comparison.json')['C2_gamma'] is None
    checks.append('Qwen3 mandatory validity stop, arithmetic cap bound and explicitly unmeasured comparison')
    prior=load('outputs/stage9a_dynamics/amendment_v1/controls_v1/audit/stage9a3_transition_complete.json')
    assert sha('outputs/stage9a_dynamics/amendment_v1/stage9a_summary.md')==prior['prior_main_report_sha256']
    for cid,h in prior['receipt_sha256'].items():assert sha(Path('outputs/stage9a_dynamics/amendment_v1/controls_v1/rollouts/results')/cid/'result.json')==h
    for cid,h in prior['generation_sha256'].items():assert sha(Path('outputs/stage9a_dynamics/amendment_v1/controls_v1/rollouts/results')/cid/'generation.json')==h
    checks.append('Prior main report and all74 completed controls remain byte-identical')
    cfg=load(ROOT/'config.json');assert sha('plan/stage9a3_execution_protocol_v1.md')==cfg['protocol_sha256']
    for r in load(ROOT/'stage9a3_synthetic_dataset_manifest.json')['rows']:assert sha(r['image_path'])==r['image_sha256']
    live=subprocess.check_output(['squeue','-u','hyunjin','-h','-o','%A %T %N'],text=True)
    for j in load('state/gpu_experiment_queue.json')['jobs']:
        if j['id'].startswith('stage9a3_') and j['gpus']:assert str(j['slurm_job_id']) not in live
    checks.append('Frozen52-image corpus/protocol unchanged; all Stage9A.3 GPUs released')
    save(ROOT/'audit/final_validation.json',dict(at=now(),pass_all=True,checks=checks,numerical_tolerance=1e-12,
        qwen25_positive_control_sha256=sha(ROOT/'stage9a3_qwen25_positive_control.json'),live_slurm=live))
    print('PASS',len(checks),'independent final audit groups',flush=True)


if __name__=='__main__':main()
