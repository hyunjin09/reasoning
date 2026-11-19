"""Seal literal extraction before scoring the frozen coarse grid."""
import argparse,os
from pathlib import Path
import numpy as np
import pandas as pd
from scripts.stage9a3.prepare import ROOT,load,save,sha,now
from scripts.stage9a3.literal_review import terminal_option
from visual_reasoning.stage9a3.analysis import extract_option,image_surface,calibration


def packet(key,stage='grid',split='primary'):
    manifest_path=ROOT/f'audit/{key}_{stage}_{split}_manifest.json';manifest=load(manifest_path)
    base_name=f'{key}_full_review.json' if split=='primary' else f'{key}_reserve_full_review.json'
    base_reviews={r['query_id']:r for r in load(ROOT/'audit'/base_name)['rows']}
    rows=[]
    for r in manifest['rows']:
        path=Path(r['generation_path']);g=load(path);receipt=load(r['result_path'])
        assert sha(path)==receipt['generation_sha256']
        if r['execution']=='reuse_full':
            assert sha(r['result_path'])==r['reuse_result_sha256'];auto=base_reviews[r['query_id']]['option'];method='sealed FULL review reused'
        else:auto=terminal_option(g['text']);method='deterministic terminal explicit label' if auto else 'manual review required'
        rows.append(dict(query_id=r['query_id'],policy_id=r['policy_id'],text=g['text'],tokens=g['tokens'],normal_eos=g['normal_eos'],
            at_length_cap=g['at_length_cap'],raw_option=extract_option(g['text']),automatic_option=auto,method=method,
            result_path=r['result_path'],generation_path=str(path),generation_sha256=sha(path),result_sha256=sha(r['result_path'])))
    save(ROOT/f'audit/{key}_{stage}_{split}_review_packet.json',dict(at=now(),manifest_sha256=sha(manifest_path),
        literal_rule_sha256=sha('scripts/stage9a3/literal_review.py'),rows=rows,blinding='Gold answers and accuracy omitted.'))
    print(dict(rows=len(rows),manual_exceptions=sum(r['method']=='manual review required' for r in rows)),flush=True)


def seal(key,stage='grid',split='primary'):
    path=ROOT/f'audit/{key}_{stage}_{split}_review_packet.json';p=load(path)
    assert p['literal_rule_sha256']==sha('scripts/stage9a3/literal_review.py')
    needed=[r for r in p['rows'] if r['method']=='manual review required']
    manual_path=ROOT/f'audit/{key}_{stage}_{split}_manual_review.json'
    manual=load(manual_path) if needed else dict(rows=[],sealed=True,gold_opened=False)
    assert manual['sealed'] and not manual['gold_opened']
    decisions={(r['query_id'],r['policy_id']):r for r in manual['rows']}
    assert set(decisions)=={(r['query_id'],r['policy_id']) for r in needed}
    rows=[]
    for r in p['rows']:
        d=decisions.get((r['query_id'],r['policy_id']))
        option=d['option'] if d else r['automatic_option'];assert option in list('ABCDE')+[None]
        rows.append(dict(query_id=r['query_id'],policy_id=r['policy_id'],option=option,
            note=d['note'] if d else r['method'],generation_sha256=r['generation_sha256']))
    save(ROOT/f'audit/{key}_{stage}_{split}_review.json',dict(at=now(),sealed=True,gold_opened=False,packet_sha256=sha(path),
         manual_sha256=sha(manual_path) if needed else None,rows=rows))
    print('SEALED',len(rows),flush=True)


def score(key,stage='grid',split='primary'):
    assert os.environ.get('SLURM_JOB_ID'),'Statistical scoring runs as a bounded scheduled CPU job'
    mpath=ROOT/f'audit/{key}_{stage}_{split}_manifest.json';m=load(mpath)
    ppath=ROOT/f'audit/{key}_{stage}_{split}_review_packet.json';packet=load(ppath)
    rpath=ROOT/f'audit/{key}_{stage}_{split}_review.json';review=load(rpath)
    assert review['sealed'] and review['packet_sha256']==sha(ppath) and packet['manifest_sha256']==sha(mpath)
    decisions={(r['query_id'],r['policy_id']):r for r in review['rows']}
    prows={(r['query_id'],r['policy_id']):r for r in packet['rows']}
    gold={r['query_id']:r for r in load(ROOT/'stage9a3_synthetic_dataset_manifest.json')['queries']}
    canonical=[]
    for r in m['rows']:
        q,p=r['query_id'],r['policy_id'];d=decisions[q,p];pr=prows[q,p]
        assert sha(pr['generation_path'])==d['generation_sha256']==pr['generation_sha256']
        assert sha(pr['result_path'])==pr['result_sha256']
        canonical.append(dict(query_id=q,image_id=gold[q]['image_id'],attribute=gold[q]['attribute'],policy=p,
            fraction=r['fraction'],token_cutoff=r['token_cutoff'],mode=r['mode'],option=d['option'],raw_option=pr['raw_option'],
            answer=gold[q]['answer'],correct=d['option']==gold[q]['answer'],raw_correct=pr['raw_option']==gold[q]['answer'],
            tokens=pr['tokens'],normal_eos=pr['normal_eos'],at_length_cap=pr['at_length_cap'],
            unscorable=d['option'] is None,execution=r['execution'],generation_path=pr['generation_path'],generation_sha256=pr['generation_sha256']))
    lookup={(r['query_id'],r['policy']):r for r in canonical}
    logical=[dict(lookup[r['query_id'],r['policy_id']],logical_fraction=r['fraction'],logical_token_cutoff=r['token_cutoff']) for r in m['logical_rows']]
    assert len(logical)==64*16 if stage=='grid' and split=='primary' else True
    out=ROOT/(f'stage9a3_{key}_coarse_grid.parquet' if stage=='grid' and split=='primary' else f'audit/{key}_{stage}_{split}_scored.parquet')
    assert not out.exists();pd.DataFrame(logical).to_parquet(out,index=False)
    save(ROOT/f'audit/{key}_{stage}_{split}_canonical_scored.json',dict(at=now(),rows=canonical,review_sha256=sha(rpath),parquet_sha256=sha(out)))
    if stage=='grid':
        images,policies,values=image_surface(canonical);meta={r['policy']:(r['fraction'],r['token_cutoff']) for r in canonical}
        baseline=load(ROOT/f'stage9a3_{key}_full_access.json');assert baseline['gates']['pass']
        result=calibration(policies,values,meta,baseline['length_summary']['median'])
        _,_,rawvalues=image_surface([dict(r,correct=r['raw_correct']) for r in canonical])
        result.update(at=now(),model=key,split=split,images=images,source_review_sha256=sha(rpath),parquet_sha256=sha(out),
            technical_pass=True,baseline_valid=True,raw_sensitivity=calibration(policies,rawvalues,meta,baseline['length_summary']['median']),
            completion_by_policy={p:dict(n=sum(r['policy']==p for r in canonical),capped=sum(r['policy']==p and r['at_length_cap'] for r in canonical),
                unscorable=sum(r['policy']==p and r['unscorable'] for r in canonical)) for p in policies},slurm_job_id=os.environ['SLURM_JOB_ID'])
        save(ROOT/f'audit/{key}_{split}_calibration_result.json',result)
        print({k:result[k] for k in ['pass','reserve_eligible','clear_restriction_damage','selected_policy','bootstrap_joint_stability']},flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['packet','seal','score']);ap.add_argument('--model',choices=['qwen25','qwen3'],required=True)
    ap.add_argument('--stage',choices=['grid','sink'],default='grid');ap.add_argument('--split',choices=['primary','reserve'],default='primary')
    a=ap.parse_args();globals()[a.action](a.model,a.stage,a.split)
