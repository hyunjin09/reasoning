"""Independent artifact-chain and literal-count verification before final reporting."""
from itertools import product
from scripts.stage12ws.common import ROOT,load,save,sha,now
from scripts.stage12ws.advance import identity

def bounds(a,b):
    low=high=0
    for x,y in zip(a,b):
        choices=[int(i)-int(j) for i,j in product([False,True] if x is None else [x],
                                                  [False,True] if y is None else [y])]
        low+=min(choices);high+=max(choices)
    return [low,high]

def main():
    phases={p.name.removesuffix('_execution.json'):load(p) for p in (ROOT/'audit').glob('*_execution.json')}
    tasks={t['task_id']:t for ex in phases.values() for t in ex['tasks']}
    assert len(tasks)==sum(len(ex['tasks']) for ex in phases.values())
    assert len({identity(t) for t in tasks.values()})==len(tasks), 'Unnecessary identical execution'
    aliases=0;qc=0
    for phase,ex in phases.items():
        closed=load(ROOT/'audit'/f'{phase}_scoring_closed.json');assert closed['pass_all']
        qc+=len(closed['reviews'])
        if ex['tasks']:
            for p,h in load(ROOT/'audit'/f'{phase}_score_seal.json')['hashes'].items():assert sha(p)==h
        groups={}
        for t in ex.get('logical_tasks',ex['tasks']):
            canonical=t.get('canonical_task_id',t['task_id'])
            assert identity(t)==identity(tasks[canonical])
            aliases+=canonical!=t['task_id']
            groups.setdefault((t['item_id'],t['condition']),[]).append(t['replicate'])
        assert all(sorted(reps)==list(range(7)) for reps in groups.values())
    for tid,t in tasks.items():
        score=load(ROOT/'audit/first_scores'/f'{tid}.json')
        technical=load(ROOT/'audit/technical_decisions'/f'{tid}.json')
        packet=load(ROOT/'audit/review_packets'/f'{tid}.json')
        assert score['technical_decision_sha256']==sha(ROOT/'audit/technical_decisions'/f'{tid}.json')
        assert technical['packet_sha256']==sha(ROOT/'audit/review_packets'/f'{tid}.json')
        assert (score['correct'] is None)==(not technical['scoreable'])
        if packet.get('technical_missing'):
            assert not (ROOT/'generations'/tid/'generation.json').exists()
            assert packet['tokens'] is None and packet['cap_hit'] is None
        else:
            g=load(ROOT/'generations'/tid/'generation.json')
            assert packet['raw']==g['raw_decoded_response'] and packet['tokens']==g['tokens']
    result=load(ROOT/'stage12ws_primary_inference.json')
    for family in result['families']:
        c=family['conditions'];vectors={k:v['seed_correctness'] for k,v in c.items()}
        for k,v in c.items():
            assert v['correct']==vectors[k].count(True) and v['missing']==vectors[k].count(None)
            assert v['correct']+v['incorrect']+v['missing']==7
        for a,b,report in [('FULL','Q',family['portability']),('ESTAR_D','ESTAR',family['derived_contrasts']['addition']),
                            ('FULL','MINUS_D',family['derived_contrasts']['deletion']),('FULL','ORDER',family['order_effect'])]:
            assert bounds(vectors[a],vectors[b])==report['net_bounds']
    natural=result['interference_repair']
    for a,b,name in [('Pa','Pb','interference'),('Pc','Pb','repair')]:
        assert bounds(natural[a]['seed_correctness'],natural[b]['seed_correctness'])==natural[name]['net_bounds']
    d_calls=sum(len(ex['tasks']) for p,ex in phases.items() if p.startswith('phaseD'))
    assert d_calls<=84 and len(phases['phaseE']['tasks'])<=28 and len(phases['phaseF']['tasks'])==21
    save(ROOT/'audit/independent_final_verification.json',dict(at=now(),unique_task_slots=len(tasks),
        exact_aliases_reused=aliases,second_pass_agreements=qc,new_D_calls=d_calls,
        artifact_chains_verified=True,literal_missing_bounds_verified=True,full_seed_panels_verified=True,
        decision=result['decision'],independent_method='Literal enumeration of missing Boolean values; same-agent verification, not an independent rater.'))
    print('Independent artifact verification passed',len(tasks),'slots',qc,'QC agreements')

if __name__=='__main__':main()
