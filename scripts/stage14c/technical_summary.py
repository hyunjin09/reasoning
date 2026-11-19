"""Technical output accounting from sealed generations; no correctness grading."""
from collections import Counter,defaultdict
import numpy as np
from scripts.stage14c.common import *
from scripts.stage14c.preflight import checked
from scripts.stage14c.response_protocol import repetition


def describe(values):
    if not values:return dict(n=0,median=None,IQR=None,max=None,total=0)
    return dict(n=len(values),median=float(np.median(values)),IQR=np.quantile(values,[.25,.75]).tolist(),max=max(values),total=sum(values))


def main():
    for name in ['main_raw_seal.json','D1_raw_seal.json']:
        assert (ROOT/'audit'/name).exists(),name
    groups=defaultdict(list)
    for mode in ['main','D1']:
        for t in all_tasks(mode):
            c=checked(t)
            r=dict(task_id=t['task_id'],technical_missing=c is None)
            if c:
                g=c[2];r.update(tokens=g['tokens'],seconds=g['request_latency_seconds'],cap_hit=g['cap_hit'],
                    finish_reason=g['finish_reason'],stop_reason=g['stop_reason'],strict_repetition_flag=repetition(g['generated_token_ids'])['flag'],
                    native_think_closed=t['model_key']!='T' or '</think>' in g['raw_decoded_response'])
            groups[(mode,t['benchmark'],t['model_key'],t['condition'])].append(r)
    panels=[]
    for (mode,b,m,cond),rr in sorted(groups.items()):
        complete=[r for r in rr if not r['technical_missing']]
        panels.append(dict(mode=mode,benchmark=b,model=m,condition=cond,expected=len(rr),completed=len(complete),technical_missing=len(rr)-len(complete),
            cap_hits=sum(r['cap_hit'] for r in complete),official_stop_count=sum(r['finish_reason']=='stop' for r in complete),
            native_think_close_count=sum(r['native_think_closed'] for r in complete),
            strict_repetition_flag_count=sum(r['strict_repetition_flag'] for r in complete),
            tokens=describe([r['tokens'] for r in complete]),request_seconds=describe([r['seconds'] for r in complete]),
            stop_reasons=dict(Counter(str(r['stop_reason']) for r in complete))))
    synthetic=[]
    for p in sorted((ROOT/'raw/seed_replay').glob('*/attempt_*/generation.json')):
        g=load(p);synthetic.append(dict(path=str(p),sha256=sha(p),tokens=g['tokens'],cap_hit=g['cap_hit']))
    save(ROOT/'audit/technical_output_summary.json',dict(at=now(),panels=panels,synthetic_replays=synthetic,
        note='42 G2 scientific calls are reused within main; do not count them twice. Six short synthetic replay calls are technical only. Request latencies overlap within engines and must not be summed as GPU-hours. Repetition is a strict token-pattern flag, not an automatic scientific error label. Cap hits are separate from final-answer scorable status.',
        expected_main_unique=4588,expected_D1_unique=600,correctness_used=False))


if __name__=='__main__':main()
