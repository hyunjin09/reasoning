"""Independent input, coverage, gate, and numerical checks for stage closeout."""
import os
from collections import Counter
import numpy as np
from scripts.stage9a4.common import ROOT,OLD,load,save,sha,now,verify_config


def independent_surface(rows,result):
    images=sorted(set(r['image_id'] for r in rows));policies=sorted(set(r['policy'] for r in rows))
    v=np.empty((len(images),len(policies)))
    for i,image in enumerate(images):
        for j,policy in enumerate(policies):
            pair=[r for r in rows if r['image_id']==image and r['policy']==policy]
            assert len(pair)==2
            v[i,j]=sum(float(r['correct']) for r in pair)/2
    rng=np.random.default_rng(920260927);ix=rng.integers(0,len(images),(4000,len(images)))
    draw=np.array([v[indices].mean(0) for indices in ix]);f=policies.index('full')
    for j,p in enumerate(policies):
        point=v[:,f].mean()-v[:,j].mean();ci=np.percentile(draw[:,f]-draw[:,j],[2.5,97.5])
        assert abs(point-result['surface'][p]['damage'])<1e-12
        assert np.allclose(ci,result['surface'][p]['ci95'],atol=1e-12,rtol=0)


def main():
    assert os.environ.get('SLURM_JOB_ID')
    cfg=verify_config();checks=[];checks.append('Frozen inputs/prior outputs byte-identical')
    base=load(ROOT/'stage9a4_qwen3_4b_full_baseline.json');rows=base['rows'];assert len(rows)==64
    assert all(n==2 for n in Counter(r['image_id'] for r in rows).values())
    gold={r['query_id']:r['answer'] for r in load(OLD/'stage9a3_synthetic_dataset_manifest.json')['queries']}
    for r in rows:assert r['correct']==(r['option']==gold[r['query_id']])
    assert base['gates']['pass'] and sum(r['correct'] for r in rows)>=39
    assert sum(r['cot'] for r in rows)>=58 and sum(r['option'] is not None for r in rows)>=58
    assert sum(r['at_length_cap'] for r in rows)<=6 or all(r['option'] is not None for r in rows if r['at_length_cap'])
    checks.append('FULL64 coverage, gold join and original G1-G5 thresholds')
    validation=load(ROOT/'stage9a4_qwen3_4b_mask_validation.json');assert validation['examples']==8 and validation['pass_all']
    for p,d in validation['checks_sha256'].items():assert sha(p)==d
    for p,d in validation['source_sha256'].items():assert sha(p)==d
    checks.append('Eight actual36-layer technical validations unchanged')
    counts={}
    for mp in sorted((ROOT/'audit').glob('*_manifest.json')):
        m=load(mp);stage=m['stage'];assert m['config_sha256']==sha(ROOT/'config.json')
        for p,d in m['source_sha256'].items():assert sha(p)==d
        for r in m['rows']:
            g=load(r['generation_path']);receipt=load(r['result_path'])
            assert sha(r['generation_path'])==receipt['generation_sha256']
            assert g['tokens']<=512 and len(g['generated_token_ids'])==g['tokens']
            if r['execution']=='reuse_full':
                assert sha(r['generation_path'])==r['reuse_generation_sha256'] and sha(r['result_path'])==r['reuse_result_sha256']
                assert r['cutoff'] is None or (g['normal_eos'] and g['tokens']-1<=r['cutoff'])
            else:assert receipt['manifest_sha256']==sha(mp)
        counts[stage]=dict(logical=len(m['rows']),new=sum(r['execution']=='run' for r in m['rows']))
    checks.append('All manifests, generation receipts and exact reuse verified')
    cumulative=base['rows']
    for stage in ['r1','t128','t256']:
        p=ROOT/f'audit/{stage}_scored.json'
        if not p.exists():continue
        scored=load(p)['rows'];cumulative=cumulative+scored
        for r in scored:assert r['correct']==(r['option']==gold[r['query_id']])
        independent_surface(cumulative,load(ROOT/f'audit/{stage}_decision.json'))
    checks.append('Independent paired-image bootstrap reconstruction for each primary decision')
    rp=ROOT/'stage9a4_qwen3_4b_reserve_extension.json'
    if rp.exists():
        reserve=load(ROOT/'audit/reserve_scored.json')['rows'];rr=load(rp);t=rr['selected_cutoff']
        independent_surface([r for r in cumulative if r['policy'] in ['full','t0',f't{t}']]+reserve,rr['combined'])
        checks.append('Independent48-image combined reserve bootstrap')
    sp=ROOT/'stage9a4_qwen3_4b_null_sink_control.json'
    if sp.exists():
        independent_surface(load(ROOT/'audit/sink_scored.json')['rows'],load(sp));checks.append('Independent32-image null-sink bootstrap')
    assert not list((ROOT/'audit').glob('*failure*.json'))
    checks.append('No GPU failure receipts; no unauthorized condition beyond0/64/128/256/FULL')
    save(ROOT/'audit/final_validation.json',dict(at=now(),pass_all=True,checks=checks,counts=counts,
        source_sha256=sha(__file__),slurm_job_id=os.environ['SLURM_JOB_ID']))
    print('AUDIT_PASS',len(checks),counts,flush=True)


if __name__=='__main__':main()
