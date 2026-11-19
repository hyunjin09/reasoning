"""Metadata-only progress; never opens generated text or scores."""
import json
from collections import Counter
from scripts.stage11b.common import ROOT,load,now

rows=[load(p) for p in (ROOT/'discovery/results').glob('*/result.json')]
out=dict(at=now(),total=256,complete=len(rows),by_mode={})
for arm in ['instruct_cot','thinking']:
    rr=[r for r in rows if r['arm']==arm]
    seconds=sum(r['batch_seconds']/4 for r in rr)
    out['by_mode'][arm]=dict(n=len(rr),tokens=sum(r['tokens'] for r in rr),generation_gpu_seconds=seconds,
        estimated_generation_seconds_remaining=(128-len(rr))*seconds/len(rr) if rr else None,
        capped=sum(r['at_length_cap'] for r in rr),budget_interrupted=sum(r['budget_interrupted'] for r in rr))
print(json.dumps(out,indent=2))
