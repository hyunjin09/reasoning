"""Read-only scientific progress, caching immutable receipt metadata for cheap polls."""
import argparse
from collections import Counter
from scripts.stage14c.common import *
from scripts.stage14c.oom_policy import missing_path

def main(mode):
    cache_path=Path('state/stage14c_progress_cache.json')
    cache=load(cache_path) if cache_path.exists() else {};counts=Counter();tokens=Counter()
    for t in all_tasks(mode):
        k=t['model_key'];tid=t['task_id'];counts[k+'_total']+=1
        if tid not in cache:
            pp=list((ROOT/'raw'/t['collection']/tid).glob('attempt_*/result.json'))
            assert len(pp)<=1
            if pp:
                receipt=load(pp[0]);assert receipt['task_sha256']==fingerprint(t)
                g=load(pp[0].parent/'generation.json')
                cache[tid]=dict(tokens=g['tokens'],result=str(pp[0]),receipt_sha256=sha(pp[0]))
        if tid in cache:counts[k+'_complete']+=1;tokens[k]+=cache[tid]['tokens']
        elif missing_path(t).exists():counts[k+'_technical_missing']+=1
    tmp=cache_path.with_suffix('.tmp');tmp.write_text(json.dumps(cache));tmp.replace(cache_path)
    print(json.dumps(dict(at=now(),counts=dict(counts),generated_tokens=dict(tokens)),indent=2))
    for folder in sorted((ROOT/'audit/workers').glob('*')):
        if (folder/'exit.json').exists():continue
        if (folder/'failure.json').exists():continue
        beats=sorted(folder.glob('heartbeat_*.json'))
        if beats:
            h=load(beats[-1]);print(folder.name,'completed',h['completed'],'/',h['total'],'active',len(h['active']),
                'max_seconds',round(max((r['seconds'] for r in h['active']),default=0)),
                'max_tokens',max((r['tokens'] for r in h['active']),default=0))
        else:print(folder.name,'startup or no heartbeat yet')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['preflight','main','D1']);a=p.parse_args();main(a.mode)
