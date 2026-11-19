"""Consolidate reviewed paired outcomes; never launches scientific work."""
import pandas as pd
from scripts.stage12ws.common import ROOT,load,save,now
from scripts.stage12ws.advance import families,scored,vector
from scripts.stage12ws.protocol import paired
from scripts.stage12ws.analysis import signature,distributed

TABLES={'phaseA':'full_state','phaseB':'block_deletion','phaseC':'derived_state','phaseE':'order_control','phaseF':'interference_repair','matched':'matched_controls'}
def summary(values):
    s=values.count(True);m=values.count(None)
    return dict(correct=s,incorrect=values.count(False),missing=m,n=7,seed_correctness=values,probability=s/7 if m==0 else None,probability_bounds=[s/7,(s+m)/7])
def any_signal(values):return True if True in values else None if None in values else False

def main():
    gate=load(ROOT/'audit/replication_gate.json');cont=gate['continue'];data={}
    for phase,name in TABLES.items():
        exists=(ROOT/'audit'/f'{phase}_scoring_closed.json').exists()
        assert exists or not cont,('Required phase incomplete',phase)
        data[phase]=scored(phase) if exists else []
        if phase!='phaseA':
            table=list(data[phase])
            if phase=='phaseF':
                for alias,source in [('F1','P299'),('F2','P448'),('F3','P598'),('F4','P448')]:
                    table += [dict(r,condition=alias,canonical_task_id=r.get('canonical_task_id',r['task_id']),exact_execution_alias=True) for r in data[phase] if r['condition']==source]
            frame=pd.DataFrame(table) if table else pd.DataFrame(columns=['task_id','item_id','family_id','condition','replicate','seed','correct','outcome','label'])
            frame.to_parquet(ROOT/('stage12ws_matched_controls.parquet' if phase=='matched' else f'stage12ws_{name}_results.parquet'),index=False)
    dd=[]
    if cont:
        for p in sorted((ROOT/'audit').glob('phaseD[0-9][0-9]_execution.json')):dd+=scored(p.name.removesuffix('_execution.json'))
        dclose=load(ROOT/'audit/phaseD_closed.json')
        if dclose['activated']:
            dtable=list(dd)
            for state in dclose['states']:
                for t in state.get('tested',[]):
                    if t.get('reused_B'):
                        source='MINUS_B'+str(t['removed'][0])
                        dtable += [dict(r,condition=t['condition'],canonical_task_id=r.get('canonical_task_id',r['task_id']),exact_execution_alias=True) for r in data['phaseB'] if r['item_id']==state['item_id'] and r['condition']==source]
            pd.DataFrame(dtable,columns=list(dtable[0]) if dtable else ['task_id','item_id','condition','correct']).to_parquet(ROOT/'stage12ws_minimal_blockset_results.parquet',index=False)
    controlmap=load(ROOT/'audit/matched_controls_execution_map.json')['rows'] if cont else []
    out=[]
    for f in families():
        item=f['item_id'];full=vector(data['phaseA'],item,'FULL');q=vector(data['phaseA'],item,'Q');elig=item in gate['eligible']
        r=dict(item_id=item,family_id=f['family_id'],eligible=elig,conditions={'FULL':summary(full),'Q':summary(q)},portability=paired(full,q),block_effects={},derived_state_support=None,distributed_necessity=None,order_sensitive=None)
        if cont:
            for phase in ['phaseB','phaseC','phaseE','phaseF','matched']:
                for condition in sorted({a['condition'] for a in data[phase] if a['item_id']==item}):r['conditions'][condition]=summary(vector(data[phase],item,condition))
            if elig:
                for b in f['blocks']:
                    name=f"MINUS_B{b['block_id']}";r['block_effects'][name]=paired(full,vector(data['phaseB'],item,name))
            r['derived_state_support']=signature(full,vector(data['phaseC'],item,'MINUS_D'),vector(data['phaseC'],item,'ESTAR_D'),vector(data['phaseC'],item,'ESTAR'),elig)
            r['derived_contrasts']=dict(addition=paired(vector(data['phaseC'],item,'ESTAR_D'),vector(data['phaseC'],item,'ESTAR')),deletion=paired(full,vector(data['phaseC'],item,'MINUS_D')))
            r['order_effect']=paired(full,vector(data['phaseE'],item,'ORDER'));r['order_sensitive']=r['order_effect']['at_least_3'] if elig else False
            r['distributed_tests']=[]
            if elig:
                dc=next(s for s in dclose['states'] if s['item_id']==item)
                composites=[dict(condition='MINUS_D',removed=f['derived_blocks'],correct=vector(data['phaseC'],item,'MINUS_D'))]+[t for t in dc.get('tested',[]) if t['k']>=2]
                for t in composites:
                    loss=paired(full,t['correct']);cm=next((c for c in controlmap if c['item_id']==item and c['target_condition']==t['condition']),None)
                    ctrl=None;ratio=None
                    if cm and cm['status']=='FROZEN':
                        ctrl=paired(full,vector(data['matched'],item,cm['condition']));ratio=cm['length_ratio']
                    hit=distributed([e['net_bounds'] for e in r['block_effects'].values()],loss['net_bounds'],ctrl['net_bounds'] if ctrl else None,ratio) if len(t['removed'])>=2 else False
                    r['distributed_tests'].append(dict(condition=t['condition'],removed=t['removed'],effect=loss,control=ctrl,length_ratio=ratio,signature=hit))
                r['distributed_necessity']=any_signal([t['signature'] for t in r['distributed_tests']])
                r['greedy']=dc
        out.append(r)
    natural=None
    if cont:
        pa=vector(data['phaseF'],'750','P299');pb=vector(data['phaseF'],'750','P448');pc=vector(data['phaseF'],'750','P598')
        ie=paired(pa,pb);re=paired(pc,pb)
        natural=dict(item_id='750',phaseA_eligible='750' in gate['eligible'],Pa=summary(pa),Pb=summary(pb),Pc=summary(pc),interference=ie,repair=re,
             joint=ie['at_least_3'] is True and re['at_least_3'] is True,
             aliases={'F1':'Pa','F2':'Pb','F3':'Pc','F4':'Pb'},unique_calls=21,independent_fourfold_confirmation=False)
    if natural:
        natural['matched_controls']=[]
        for c in controlmap:
            if not c.get('natural'):continue
            effect=None
            if c['status']=='FROZEN':
                v=vector(data['matched'],'750',c['condition'])
                effect=paired(v,pb) if c['target_condition']=='F1_INTERFERE' else paired(pc,v)
            natural['matched_controls'].append(dict(target=c['target_condition'],status=c['status'],effect=effect,length_ratio=c.get('length_ratio')))
    counts={k:sum(r[k] is True for r in out) for k in ['eligible','derived_state_support','distributed_necessity','order_sensitive']}
    if gate['status']=='STOP_WEAK':decision='PORTABILITY_WEAK_UNDER_PAIRED_SEEDS'
    elif not cont:decision='UNRESOLVED'
    elif counts['derived_state_support']>=3 and counts['distributed_necessity']>=2:decision='DISTRIBUTED_DERIVED_STATE_SIGNAL'
    elif counts['derived_state_support']>=3:decision='DERIVED_STATE_ONLY'
    elif natural['joint']:decision='INTERFERENCE_REPAIR_SIGNAL'
    else:decision='PORTABILITY_CONTENT_UNRESOLVED'
    result=dict(at=now(),families=out,counts=counts,interference_repair=natural,decision=decision,
                caveat='Four selected independent families; seven paired seeds. Source mixtures and alias identities remain limitations. Sparse mixed block effects are reported even when the cross-family mechanism is unresolved.')
    save(ROOT/'stage12ws_primary_inference.json',result);print(decision,counts)

if __name__=='__main__':main()
