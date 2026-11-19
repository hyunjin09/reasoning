"""One frozen backward-elimination step per active family and round; <=84 new calls."""
import argparse
from scripts.stage12ws.common import ROOT,load,save,now
from scripts.stage12ws.advance import families,scored,vector,queue
from scripts.stage12ws.protocol import paired
from scripts.stage12ws.controls import elimination_status
from scripts.stage12ws.candidates import control_for

def next_round(shards):
    freeze=load(ROOT/'audit/candidate_support_freeze.json');ff={f['item_id']:f for f in families()}
    aa=scored('phaseA');bb=scored('phaseB');states=[];controls=[]
    executed=sorted((ROOT/'audit').glob('phaseD[0-9][0-9]_execution.json'))
    used=sum(len(load(p)['tasks']) for p in executed);assert used<=84
    past=[]
    for p in executed:past+=scored(p.name.removesuffix('_execution.json'))
    conditions=[]
    for c in sorted(freeze['families'],key=lambda c:int(c['item_id'])):
        item=c['item_id'];f=ff[item]
        if c['status']!='D_ELIGIBLE':states.append(dict(item_id=item,status=c['status']));continue
        full=vector(aa,item,'FULL');accepted=[];tested=[];status='ACTIVE';next_condition=None
        for spec in c['nested']:
            k=spec['k'];name=spec['condition']
            if k==1:values=vector(bb,item,f"MINUS_B{spec['removed'][0]}");reuse=True
            elif any(r['item_id']==item and r['condition']==name for r in past):values=vector(past,item,name);reuse=False
            else:next_condition=spec;break
            effect=paired(full,values);action=elimination_status(effect['net_bounds'])
            tested.append(dict(**spec,correct=values,effect=effect,action=action,reused_B=reuse))
            if action=='ACCEPT':accepted=spec['removed']
            else:status=action;break
        if status=='ACTIVE' and next_condition is None:status='ALL_TESTED'
        if status=='ACTIVE':
            # At most one new condition per family each round, numerical family order.
            if used+7*len(conditions)+7<=84:
                conditions.append((f,next_condition['condition'],next_condition['material']))
            else:status='MAX_D_CALLS'
        states.append(dict(item_id=item,status=status,accepted_removed=accepted,
                    candidate_retained=[b['block_id'] for b in f['blocks'] if b['block_id'] not in accepted],tested=tested))
    round_no=len(executed)+1;label=f'phaseD{round_no:02d}'
    # Freeze each newly observed high-impact composite's matching control once.
    old_targets={r['target_condition']+'|'+r['item_id'] for p in (ROOT/'audit').glob('phaseD*_planning.json') for r in load(p)['controls']}
    for s in states:
        for t in s.get('tested',[]):
            key=t['condition']+'|'+s['item_id']
            if t['k']>=2 and t['effect']['at_least_3'] is True and key not in old_targets:
                c=next(c for c in freeze['families'] if c['item_id']==s['item_id'])
                controls.append(control_for(ff[s['item_id']],c['low_importance'],t['removed'],t['condition']));old_targets.add(key)
    save(ROOT/'audit'/f'{label}_planning.json',dict(at=now(),states=states,controls=controls,new_calls_used=used,proposed_conditions=len(conditions)))
    if conditions:return queue(label,conditions,shards)
    save(ROOT/'audit/phaseD_closed.json',dict(at=now(),complete=True,activated=any(c['status']=='D_ELIGIBLE' for c in freeze['families']),new_calls=used,states=states))
    print('PhaseD closed',[(s['item_id'],s['status']) for s in states])

def controls(shards):
    assert load(ROOT/'audit/phaseF_scoring_closed.json')['pass_all']
    freeze=load(ROOT/'audit/candidate_support_freeze.json');rows=list(freeze['controls'])
    for p in sorted((ROOT/'audit').glob('phaseD*_planning.json')):rows+=load(p)['controls']
    ff={f['item_id']:f for f in families()}
    natural=scored('phaseF')
    effects={'F1_INTERFERE':paired(vector(natural,'750','P299'),vector(natural,'750','P448')),
             'F4_REPAIR':paired(vector(natural,'750','P598'),vector(natural,'750','P448'))}
    for r in load(ROOT/'audit/natural_controls_freeze.json')['rows']:
        if effects[r['target_condition']]['at_least_3'] is True:rows.append(r)
    save(ROOT/'audit/matched_controls_execution_map.json',dict(at=now(),rows=rows))
    return queue('matched',[(ff[r['item_id']],r['condition'],r['material']) for r in rows if r['status']=='FROZEN'],shards)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['next','controls']);p.add_argument('--shards',type=int,default=4);a=p.parse_args()
    next_round(a.shards) if a.action=='next' else controls(a.shards)
