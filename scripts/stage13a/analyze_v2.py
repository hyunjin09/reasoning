"""Seal primary inference before any Stage12Y comparison or conditional calls."""
import pandas as pd
from scripts.stage13a.execution import ROOT,load,save,sha,now,cohort,shards
from scripts.stage13a.review import tasks,technical
from scripts.stage13a.scoring import final_score
from scripts.stage13a.inference_v2 import estimate,bounds,majority,transitions,decision,optional_needed

def parquet(path,rows):
    assert not path.exists();pd.DataFrame(rows).to_parquet(path,index=False)

def results(phase,arm):
    assert (ROOT/'audit'/f'{arm}_scoring_closed.json').exists()
    rows=[]
    for t in tasks(phase):
        if t['arm']!=arm:continue
        tid=t['task_id'];s=final_score(tid);a=technical(tid);p=ROOT/'generations'/tid/'generation.json';g=load(p)
        before=None
        if t['model_key']=='T' and s['correct'] is not None:
            if g['tokens']<32768:before=True
            else:
                budget=load(ROOT/'audit/token_budget'/f'{tid}.json')
                assert budget['generation_sha256']==sha(p) and type(budget['scoreable_before32k']) is bool
                before=budget['scoreable_before32k']
        rows.append(dict(task_id=tid,item_id=t['item_id'],family_id=t['family_id'],arm=arm,replicate=t['replicate'],
            label=s['label'],correct=s['correct'],outcome=a['outcome'],**a['validity'],cap_hit=g['cap_hit'],tokens=g['tokens'],
            scoreable_before32k=before,finish_reason=g['finish_reason'],latency_seconds=g['request_latency_seconds'],
            seed=t['seed'],generation_path=str(p),generation_sha256=sha(p)))
    return rows

def primary():
    ins,think=results('P','I_EQ'),results('P','T_EQ');assert len(ins)==len(think)==288
    families=[];flat=[]
    for source in cohort():
        item=source['item_id'];i=sorted([r for r in ins if r['item_id']==item],key=lambda r:r['replicate']);t=sorted([r for r in think if r['item_id']==item],key=lambda r:r['replicate'])
        ii=[r['correct'] for r in i];tt=[r['correct'] for r in t];assert len(ii)==len(tt)==3
        complete=all(v is not None for v in ii+tt);comparable=complete and all(r['scoreable_before32k'] for r in t)
        im=sum(v is True for v in ii)/sum(v is not None for v in ii) if any(v is not None for v in ii) else None
        tm=sum(v is True for v in tt)/sum(v is not None for v in tt) if any(v is not None for v in tt) else None
        f=dict(item_id=item,family_id=source['family_id'],I=ii,T=tt,complete=complete,comparable32k=comparable,
            I_mean=im,T_mean=tm,difference=(tt.count(True)-ii.count(True))/3 if complete else None,I_majority=majority(ii),T_majority=majority(tt))
        families.append(f);flat.append(f)
    main=estimate([f['difference'] for f in families if f['complete']]);sensitivity=estimate([f['difference'] for f in families if f['comparable32k']]);bound=bounds(families)
    scoreability={a:sum(r['correct'] is not None for r in rr)/288 for a,rr in [('I',ins),('T',think)]}
    gap=100*(scoreability['T']-scoreability['I'])
    state=decision(main['n'],main['effect_pp'],main['ci95_pp'],gap,bound['preserves_positive_gate'])
    optional=optional_needed(state=='EQUAL_EVIDENCE_THINKING_ADVANTAGE_CONFIRMED',sensitivity)
    parquet(ROOT/'stage13a_instruct_equal_evidence_results.parquet',ins)
    parquet(ROOT/'stage13a_thinking_equal_evidence_results.parquet',think)
    parquet(ROOT/'stage13a_family_level_results.parquet',flat)
    save(ROOT/'stage13a_missingness_bounds.json',dict(at=now(),**bound))
    save(ROOT/'stage13a_32k_comparable_sensitivity.json',dict(at=now(),**sensitivity,selected_ids=[f['item_id'] for f in families if f['comparable32k']],optional_triggered=optional,
        rule='Prospective n>=80, effect>=5pp, CI lower>0; not decoding matched.'))
    save(ROOT/'stage13a_scoring_audit.json',dict(at=now(),I=load(ROOT/'audit/I_EQ_scoring_closed.json'),T=load(ROOT/'audit/T_EQ_scoring_closed.json'),
        order='All Instruct first scores and QC closed before Thinking outputs opened.',scope='Same-agent second pass; not independent human reliability.'))
    inference=dict(at=now(),primary=main,scoreability=scoreability,scoreability_difference_pp=gap,missingness_bounds=bound,
        majority_transitions=transitions(families),decision=state,optional_capmatched_triggered=optional,
        independent_unit='Conservative visual family; repeats within family, not independent population samples.',
        estimand='Deployed Thinking-variant advantage with identical image-free task-critical evidence.',
        historical_comparison_opened=False)
    save(ROOT/'stage13a_primary_inference.json',inference)
    save(ROOT/'audit/primary_inference_seal.json',dict(at=now(),files={str(p):sha(p) for p in ROOT.glob('stage13a_*') if p.is_file()},historical_comparison_opened=False))
    print('PRIMARY SEALED',state,main,'OPTIONAL',optional)

if __name__=='__main__':primary()
