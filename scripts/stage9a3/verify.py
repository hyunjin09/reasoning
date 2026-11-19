"""Read-only provenance/completeness audit, independent of scientific gate values."""
import argparse,subprocess
from pathlib import Path
from scripts.stage9a3.prepare import ROOT,load,save,sha,now


def verify(key,stage,split='primary'):
    cfg=load(ROOT/'config.json');assert sha('plan/stage9a3_execution_protocol_v1.md')==cfg['protocol_sha256']
    assert sha(ROOT/'audit/inference_tasks.json')==cfg['tasks_sha256']
    gate=load(ROOT/f'stage9a3_mask_validation_{key}.json');assert gate['pass_all'] and gate['examples']==8
    for p,h in gate['source_sha256'].items():assert sha(p)==h
    for p,h in gate['checks_sha256'].items():assert sha(p)==h
    tasks={r['query_id']:r for r in load(ROOT/'audit/inference_tasks.json')['rows'] if r['split']==split}
    for r in tasks.values():assert sha(r['image_path'])==r['image_sha256']
    mpath=ROOT/f'audit/{key}_{stage}_{split}_manifest.json';m=load(mpath)
    assert m['frozen'] and m['config_sha256']==sha(ROOT/'config.json')
    for p,h in m['source_sha256'].items():assert sha(p)==h
    receipts={};workers=set();runs=[]
    for r in m['rows']:
        q=r['query_id'];p=Path(r['result_path']);result=load(p);g=load(r['generation_path'])
        assert result['query_id']==q and result['generation_sha256']==sha(r['generation_path'])
        assert result['config_sha256']==sha(ROOT/'config.json')
        assert result['input']['image_sha256']==tasks[q]['image_sha256']
        assert result['tokens']==len(g['generated_token_ids'])==g['tokens']
        assert result['tokens']<=gate['scientific_cap']
        if r['execution']=='run':
            assert result['policy']=={k:v for k,v in r.items()}
            runs.append(r);workers.add(result['worker'])
        else:assert sha(p)==r['reuse_result_sha256']
        receipts[str(p)]=sha(p)
    assert len({(r['query_id'],r['policy_id']) for r in m['rows']})==len(m['rows'])
    assert len(list((ROOT/key/f'{stage}_{split}/results').glob('*/*/result.json')))==len(runs)
    live=subprocess.check_output(['squeue','-u','hyunjin','-h','-o','%A %T %N'],text=True)
    terminal={}
    for w in workers:
        p=ROOT/key/f'{stage}_{split}/workers'/w/'complete.json';terminal[w]=dict(path=str(p),sha256=sha(p))
        assert w.removeprefix('slurm_') not in live
    suffix='' if split=='primary' else '_'+split
    out=ROOT/f'audit/{key}_{stage}{suffix}_completion_validation.json'
    save(out,dict(at=now(),pass_all=True,model=key,stage=stage,split=split,n_images=len({r['image_id'] for r in tasks.values()}),n_queries=len(tasks),canonical_rows=len(m['rows']),
        new_runs=len(runs),logical_rows=len(m['logical_rows']),receipt_sha256=receipts,terminal=terminal,
        source_and_input_hashes_verified=True,workers_released=True,live_slurm=live))
    print(out,'PASS',len(runs),'new runs',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--model',choices=['qwen25','qwen3'],required=True);ap.add_argument('--stage',choices=['grid','sink'],required=True)
    ap.add_argument('--split',choices=['primary','reserve'],default='primary')
    a=ap.parse_args();verify(a.model,a.stage,a.split)
