"""Gold-free literal final review; source answers are joined only after sealing."""
import argparse
from scripts.stage10ar.common import ROOT,load,save,sha,now
from scripts.stage9a3.literal_review import terminal_option
from visual_reasoning.stage9a3.analysis import extract_option


def packet(stage):
    mp=ROOT/f'audit/{stage}_manifest.json';manifest=load(mp);rows=[]
    for r in manifest['rows']:
        g=load(r['generation_path']);receipt=load(r['result_path'])
        assert receipt['generation_sha256']==sha(r['generation_path'])
        option=terminal_option(g['final_text']) if g['reasoning_closed'] else None
        rows.append(dict(task_id=r['task_id'],query_id=r['query_id'],condition=r['condition'],anchor=r['anchor'],
            final_text=g['final_text'],reasoning_closed=g['reasoning_closed'],closure_count=g['closure_count'],
            continuation_text=g['continuation_text'],tokens=g['tokens'],continuation_tokens=g['continuation_tokens'],
            normal_eos=g['normal_eos'],at_length_cap=g['at_length_cap'],automatic_option=option,
            raw_option=extract_option(g['final_text']) if g['reasoning_closed'] else None,
            requires_manual=option is None,generation_sha256=sha(r['generation_path']),result_sha256=sha(r['result_path'])))
    save(ROOT/f'audit/{stage}_review_packet.json',dict(at=now(),gold_omitted=True,rows=rows,manifest_sha256=sha(mp),
         literal_adapter_sha256=sha('scripts/stage9a3/literal_review.py')))
    print('PACKET',stage,len(rows),'manual',sum(r['requires_manual'] for r in rows),flush=True)


def seal(stage):
    p=ROOT/f'audit/{stage}_review_packet.json';packet=load(p)
    assert packet['literal_adapter_sha256']==sha('scripts/stage9a3/literal_review.py')
    needed={r['task_id'] for r in packet['rows'] if r['requires_manual']}
    manual=load(ROOT/f'audit/{stage}_manual_review.json') if needed else dict(rows=[],sealed=True,gold_opened=False)
    assert manual['sealed'] and not manual['gold_opened']
    if needed:assert manual['packet_sha256']==sha(p)
    decisions={r['task_id']:r for r in manual['rows']};assert set(decisions)==needed
    rows=[]
    for r in packet['rows']:
        d=decisions.get(r['task_id'],dict(option=r['automatic_option'],note='Frozen terminal literal adapter.'))
        assert d['option'] in list('ABCDE')+[None]
        if not r['reasoning_closed']:assert d['option'] is None
        rows.append(dict(r,option=d['option'],review_note=d['note']))
    save(ROOT/f'audit/{stage}_review.json',dict(at=now(),sealed=True,gold_opened=False,rows=rows,packet_sha256=sha(p)))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['packet','seal']);p.add_argument('stage');a=p.parse_args()
    globals()[a.action](a.stage)
