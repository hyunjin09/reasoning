"""Freeze B/C-derived candidates and all nested D combinations before D replay."""
from pathlib import Path
from scripts.stage12ws.common import ROOT,load,save,sha,now
from scripts.stage12ws.advance import families,scored,vector
from scripts.stage12ws.analysis import signature
from scripts.stage12ws.protocol import paired
from scripts.stage12ws.controls import closest

def write_retained(f,removed,label):
    text=''.join(Path(b['path']).read_text() for b in f['blocks'] if b['block_id'] not in removed)
    p=ROOT/'prefixes'/f"{f['item_id']}_{label}.txt"
    with p.open('x') as out:out.write(text)
    # Token sum is only a queue-balancing estimate; actual input IDs are recorded at runtime.
    return dict(prefix_path=str(p),prefix_sha256=sha(p),prefix_tokens=sum(b['token_count'] for b in f['blocks'] if b['block_id'] not in removed),question=f['question'])

def control_for(f,eligible,removed,target):
    count=sum(b['token_count'] for b in f['blocks'] if b['block_id'] in removed)
    ids=closest(f['blocks'],[i for i in eligible if i not in removed],count)
    row=dict(item_id=f['item_id'],target_condition=target,target_removed=removed,target_tokens=count,control_removed=ids)
    if ids is None:return dict(row,status='NO_ELIGIBLE_CONTROL')
    ct=sum(b['token_count'] for b in f['blocks'] if b['block_id'] in ids)
    return dict(row,status='FROZEN',control_tokens=ct,length_ratio=ct/count,adequate_length_match=.8<=ct/count<=1.25,
                condition='CTRL_'+target,material=write_retained(f,ids,'CTRL_'+target))

def main():
    aa=scored('phaseA');bb=scored('phaseB');cc=scored('phaseC');gate=load(ROOT/'audit/replication_gate.json')
    candidates=[];controls=[]
    for f in families():
        item=f['item_id']
        if item not in gate['eligible']:
            candidates.append(dict(item_id=item,status='INELIGIBLE_PHASE_A'));continue
        full=vector(aa,item,'FULL');effects={str(b['block_id']):paired(full,vector(bb,item,f"MINUS_B{b['block_id']}")) for b in f['blocks']}
        ds=signature(full,vector(cc,item,'MINUS_D'),vector(cc,item,'ESTAR_D'),vector(cc,item,'ESTAR'),True)
        support=[b['block_id'] for b in f['blocks'] if effects[str(b['block_id'])]['net_bounds'][0]>=1]
        if ds is True:support=sorted(set(support+f['derived_blocks']))
        interfering=[b['block_id'] for b in f['blocks'] if effects[str(b['block_id'])]['net_bounds'][1]<=-1]
        excluded=set(support+interfering+[b['block_id'] for b in f['blocks'] if b['role']=='REPAIR_OR_RESOLUTION'])
        if item=='750':excluded.update(b['block_id'] for b in f['blocks'] if b['start_step']<=598 and b['end_step']>=300)
        low=[b['block_id'] for b in f['blocks'] if b['block_id'] not in excluded and effects[str(b['block_id'])]['net_bounds']==[0,0]]
        complete=all(e['net_successes'] is not None for e in effects.values())
        order=sorted([b['block_id'] for b in f['blocks']],key=lambda i:(effects[str(i)]['net_successes'],i)) if complete else []
        eligible=len(support)>=2 and complete
        nested=[]
        if eligible:
            for k in range(1,len(order)+1):
                name=f'D_REMOVE_{k}';nested.append(dict(k=k,removed=order[:k],condition=name,material=write_retained(f,order[:k],name)))
        candidates.append(dict(item_id=item,status='D_ELIGIBLE' if eligible else 'D_NOT_ELIGIBLE',supportive=support,interfering=interfering,
                low_importance=low,derived_signature=ds,effects=effects,order=order,nested=nested))
        for b in f['blocks']:
            if effects[str(b['block_id'])]['at_least_3'] is True:
                controls.append(control_for(f,low,[b['block_id']],f"MINUS_B{b['block_id']}"))
        if paired(full,vector(cc,item,'MINUS_D'))['at_least_3'] is True:
            controls.append(control_for(f,low,f['derived_blocks'],'MINUS_D'))
    save(ROOT/'audit/candidate_support_freeze.json',dict(at=now(),families=candidates,controls=controls,
         max_new_D_calls=84,order_frozen_before_D=True,BC_closed=True))
    print([(c['item_id'],c['status'],c.get('supportive')) for c in candidates])

if __name__=='__main__':main()
