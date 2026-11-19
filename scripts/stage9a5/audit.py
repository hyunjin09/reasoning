"""Reconstruct coverage, extraction, paired statistics, and frozen inputs."""
import os
from collections import Counter
import numpy as np
from scripts.stage9a5.common import ROOT, OLD, COT, load, save, sha, now, verify_config
from scripts.stage9a4.audit import independent_surface


def check_contrast(thinking, cot, result):
    policy=result['policy']; values=[]
    images=sorted({r['image_id'] for r in thinking})
    for image in images:
        damages=[]
        for rows in (thinking,cot):
            cells={p:[float(r['correct']) for r in rows if r['image_id']==image and r['policy']==p]
                   for p in ('full',policy)}
            assert all(len(v)==2 for v in cells.values())
            damages.append(sum(cells['full'])/2-sum(cells[policy])/2)
        values.append(damages[0]-damages[1])
    values=np.asarray(values)
    rng=np.random.default_rng(920260927)
    draws=[np.mean(values[rng.integers(0,len(values),size=len(values))]) for _ in range(4000)]
    assert abs(values.mean()-result['difference'])<1e-12
    assert np.allclose(np.percentile(draws,[2.5,97.5]),result['ci95'],atol=1e-12,rtol=0)


def main():
    assert os.environ.get('SLURM_JOB_ID')
    verify_config();checks=['All pinned checkpoints, images, native tasks, protocol and CoT reference hashes unchanged']
    base=load(ROOT/'stage9a5_thinking_full_baseline.json');rows=base['rows'];assert len(rows)==64
    assert len(set(r['query_id'] for r in rows))==64
    assert all(n==2 for n in Counter(r['image_id'] for r in rows).values())
    gold={r['query_id']:r['answer'] for r in load(OLD/'stage9a3_synthetic_dataset_manifest.json')['queries']}
    assert base['gates']['pass'] and sum(r['correct'] for r in rows)>=39
    assert sum(r['native_reasoning'] for r in rows)>=58 and sum(r['option'] is not None for r in rows)>=58
    assert sum(r['at_length_cap'] for r in rows)<=6 or all(r['option'] is not None for r in rows if r['at_length_cap'])
    assert load(ROOT/'audit/full_noop_validation.json')['pass_all']
    checks.append('64 FULL rows and original G1-G5 thresholds reconstructed')
    validation=load(ROOT/'stage9a5_thinking_mask_validation.json')
    assert validation['examples']==8 and validation['pass_all']
    for p,d in validation['checks_sha256'].items():assert sha(p)==d
    for p,d in validation['source_sha256'].items():assert sha(p)==d
    checks.append('Eight actual-model V1-V6 receipts and source hashes unchanged')
    counts={};all_scored=rows[:]
    for mp in sorted((ROOT/'audit').glob('*_manifest.json')):
        m=load(mp);stage=m['stage'];assert m['config_sha256']==sha(ROOT/'config.json')
        for p,d in m['source_sha256'].items():assert sha(p)==d,p
        assert len({(r['query_id'],r['policy']) for r in m['rows']})==len(m['rows'])
        review=load(ROOT/f'audit/{stage}_review.json');packet=ROOT/f'audit/{stage}_review_packet.json'
        assert review['sealed'] and not review['gold_opened'] and review['packet_sha256']==sha(packet)
        reviewed={(r['query_id'],r['policy']):r for r in review['rows']}
        for r in m['rows']:
            g=load(r['generation_path']);receipt=load(r['result_path']);d=reviewed[r['query_id'],r['policy']]
            assert sha(r['generation_path'])==receipt['generation_sha256']==d['generation_sha256']
            assert sha(r['result_path'])==d['result_sha256']
            assert g['tokens']<=512 and len(g['generated_token_ids'])==g['tokens']
            assert receipt['input']['native_thinking_prefix']
            ids=g['generated_token_ids'];closed=ids.count(151668)==1
            assert g['reasoning_closed']==closed
            if not closed:assert d['option'] is None
            if 151668 not in ids:assert g['final_text']==''
            assert g['reasoning_tokens']==(ids.index(151668) if 151668 in ids else len(ids))
            if r['execution']=='reuse_full':
                assert sha(r['generation_path'])==r['reuse_generation_sha256']
                assert sha(r['result_path'])==r['reuse_result_sha256']
                assert r['cutoff'] is None or (g['normal_eos'] and g['tokens']-1<=r['cutoff'])
            else:assert receipt['manifest_sha256']==sha(mp)
        counts[stage]=dict(logical=len(m['rows']),new=sum(r['execution']=='run' for r in m['rows']))
    checks.append('Manifest coverage, immutable receipts, native channel boundaries and exact aliases verified')
    for stage in ('t1','t256'):
        p=ROOT/f'audit/{stage}_scored.json'
        if not p.exists():continue
        scored=load(p)['rows'];all_scored+=scored
        independent_surface(all_scored,load(ROOT/f'audit/{stage}_decision.json'))
    for r in all_scored:assert r['correct']==(r['option']==gold[r['query_id']])
    checks.append('Gold scoring and independent paired-image bootstrap reconstruction')
    cot=load(COT/'stage9a4_qwen3_4b_full_baseline.json')['rows']+load(COT/'audit/r1_scored.json')['rows']+load(COT/'audit/t128_scored.json')['rows']
    comparison=load(ROOT/'stage9a5_absolute_access_comparison.json')
    for r in comparison['contrasts'].values():check_contrast(all_scored,cot,r)
    checks.append('Independent cross-arm damage contrast bootstrap at0/64/128')
    sink=load(ROOT/'stage9a5_null_sink_control.json')
    if sink['status']=='complete':
        sr=load(ROOT/'audit/sink_scored.json')['rows'];independent_surface(sr,sink)
        for r in sr:assert r['correct']==(r['option']==gold[r['query_id']])
        checks.append('Independent bounded null-sink bootstrap and gold reconstruction')
    # Optional assays require their own explicit verified receipts before closeout.
    for name in ('relative_time_intervention','reserve_extension'):
        p=ROOT/f'stage9a5_{name}.json'
        if p.exists() and load(p)['status']=='complete':
            assert load(p)['independent_audit_pass']
    assert not list((ROOT/'audit').glob('*failure*.json'))
    checks.append('No unhandled failure receipt or unaudited optional assay')
    save(ROOT/'audit/final_validation.json',dict(at=now(),pass_all=True,checks=checks,counts=counts,
         source_sha256=sha(__file__),slurm_job_id=os.environ['SLURM_JOB_ID']))
    print('AUDIT_PASS',len(checks),counts,flush=True)


if __name__=='__main__':main()
