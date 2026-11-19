"""Join only sealed continuation scores; retain every replicate and family."""
import json
import pandas as pd
from scipy.stats import beta
from scripts.stage12us.common import ROOT,load,save,sha,now
from scripts.stage12us.review import tasks,checked
from scripts.stage12us.inference import interpret,decision


RECOMMENDATIONS={
 'STATE_PRODUCTION_SIGNAL':'Localize which Thinking-derived intermediate deductions make the state portable to Instruct using prefix-position and content ablations.',
 'STATE_UTILIZATION_SIGNAL':'Hold the transferred reasoning state fixed and causally compare downstream computation between Instruct and Thinking.',
 'STATE_REPAIR_SIGNAL':'Identify which flawed Instruct reasoning components Thinking corrects using counterfactual repair/edit interventions.',
 'MIXED_STATE_SIGNAL':'Decompose production and utilization separately with prefix-localization and fixed-state downstream interventions.',
 'TEXT_STATE_INSUFFICIENT':'Test whether non-textual cached/hidden state is required before making further production-vs-utilization claims.',
 'UNRESOLVED':'Review the unresolved transfer and control pattern before authorizing another mechanism intervention.',
}


def interval(values):
    observed=[v for v in values if v is not None];k=sum(v is True for v in observed);n=len(observed);total=len(values)
    ci=[float(beta.ppf(.025,k,n-k+1)) if k else 0,
        float(beta.ppf(.975,k+1,n-k)) if k<n else 1] if n else [None,None]
    return dict(successes=k,observed=n,frozen=total,missing=total-n,
                rate=k/n if n else None,clopper_pearson_95=ci,
                missingness_bounds=[k/total,(k+total-n)/total] if total else [None,None])


def main():
    assert load(ROOT/'stage12us_technical_validation.json')['pass']
    assert load(ROOT/'stage12us_scoring_review.json')['all_agree']
    for p,h in load(ROOT/'audit/source_prefix_seal.json')['hashes'].items():assert sha(p)==h
    for p,h in load(ROOT/'audit/first_score_seal.json')['hashes'].items():assert sha(p)==h
    for p,h in load(ROOT/'audit/analysis_rules.json')['analysis_source_hashes'].items():assert sha(p)==h
    rows=[]
    for t in tasks('science'):
        g,checks=checked(t);s=load(ROOT/'audit/first_scores'/f"{t['task_id']}.json")
        a=load(ROOT/'audit/technical_decisions'/f"{t['task_id']}.json")
        assert s['technical_decision_sha256']==sha(ROOT/'audit/technical_decisions'/f"{t['task_id']}.json")
        rows.append(dict(**t,correct=s['correct'],label=s['label'],outcome=a['outcome'],scoreable=a['scoreable'],
             tokens=g['tokens'],cap_hit=g['cap_hit'],finish_reason=g['finish_reason'],
             latency_seconds=g['request_latency_seconds'],job=g['job'],node=g['node'],
             generation_path=str(ROOT/'generations'/t['task_id']/'generation.json'),
             generation_sha256=sha(ROOT/'generations'/t['task_id']/'generation.json'),input_valid=all(checks.values())))
    assert len(rows)==156
    for kind,prefix,n in [('transfer_results','R',84),('question_only_controls','Q',42),('shuffled_trace_controls','S',30)]:
        selected=[r for r in rows if r['condition'].startswith(prefix)];assert len(selected)==n
        pd.DataFrame(selected).to_parquet(ROOT/f'stage12us_{kind}.parquet',index=False)
    content=load(ROOT/'stage12us_prefix_content_audit.json')['rows']
    families=load(ROOT/'audit/cohorts.json')['cohorts'];items=[]
    for cohort in ['primary','secondary']:
        for r in families[cohort]:
            conditions=['RT_T','RT_I','RC_I','RC_T','Q_I','Q_T']+(['ST_I','SC_T'] if cohort=='primary' else [])
            outcomes={c:[x['correct'] for x in sorted(rows,key=lambda x:x['replicate']) if x['family_id']==r['family_id'] and x['condition']==c] for c in conditions}
            source=next(x for x in content if x['item_id']==r['item_id'] and x['source']=='C')
            result=interpret(outcomes,source['evidence_state'],source['derivation_state'])
            items.append(dict(**r,cohort=cohort,**result,run_outcomes=outcomes,
                 C_evidence_state=source['evidence_state'],C_derivation_state=source['derivation_state']))
    flat=[]
    for item in items:
        r={k:v for k,v in item.items() if k not in ['majority','run_outcomes']}
        r.update(item['majority']);r['run_outcomes_json']=json.dumps(item['run_outcomes']);flat.append(r)
    pd.DataFrame(flat).to_parquet(ROOT/'stage12us_item_interpretations.parquet',index=False)
    primary=[r for r in items if r['cohort']=='primary'];secondary=[r for r in items if r['cohort']=='secondary']
    inference=dict(at=now(),independent_unit='conservative visual family',primary=primary,secondary=secondary,
        endpoints=dict(U_P1_S_TT=interval([r['majority']['RT_T'] for r in primary]),
            U_P2_S_TI_given_TT=interval([r['majority']['RT_I'] for r in primary if r['majority']['RT_T'] is True]),
            U_P3_S_CT=interval([r['majority']['RC_T'] for r in primary]),
            U_P3_S_CI=interval([r['majority']['RC_I'] for r in primary]),
            U_P4_production_trace_dependence=interval([r['production_trace_dependence'] for r in primary]),
            U_P4_utilization_repair_trace_dependence=interval([r['utilization_repair_trace_dependence'] for r in primary])),
        supports={k:interval([r[k] for r in primary]) for k in ['PRODUCTION_SUPPORT','UTILIZATION_SUPPORT','REPAIR_SUPPORT','TEXT_NOT_SUFFICIENT']},
        controls={k:interval([r['majority'][k] for r in primary]) for k in ['Q_I','Q_T','ST_I','SC_T']},
        interval_note='Exact binomial intervals describe resolved-family proportions only; n5 is targeted localization, not prevalence estimation. Missingness bounds retain frozen families.',
        source_audit_sha256=sha(ROOT/'stage12us_prefix_content_audit.json'),
        limitations=['Cohort selected on prior C−T+ outcomes; historical native/oracle trials not repeated.',
                    'Targets differ in checkpoint, intended decoding and cap; this does not isolate a hidden Thinking switch.',
                    'Prefixes stop before first candidate, potentially before later useful deductions; same-model sufficiency gate is mandatory.',
                    'Source audit uses whole-prefix lexical scanning and targeted semantic reading, not independent exhaustive review.',
                    'Q-only or shuffled success weakens trace-specific/content-specific interpretation; report all controls.',
                    'No explanation of text insufficiency is chosen without a further authorized intervention.'])
    save(ROOT/'stage12us_primary_inference.json',inference)
    result=decision(primary);result.update(at=now(),recommendation=RECOMMENDATIONS[result['decision']],
         next_experiment_launched=False,stage_complete=True,stop=True,scope='Externalized textual-state transfer under intended checkpoint-specific recipes')
    save(ROOT/'stage12us_decision.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
