"""Deterministic source/semantic/trigger parsing and create-once A–D freeze."""
from collections import Counter
from datetime import datetime,timezone
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,write_jsonl,sha
from scripts.stage5a.run_scores import verify_freeze
from visual_reasoning.stage5a.protocol import classify_event


def main():
    flag=OUT/'annotations/causal_label_freeze.json'
    if flag.exists():raise FileExistsError('Labels are create-once')
    verify_freeze()
    gates={p:read_json(OUT/d) for p,d in [('causal','phase_b_causal/causal_run_complete.json'),('semantic','phase_c_counterfactual/semantic_run_complete.json')]}
    assert all(g['passed'] for g in gates.values())
    for g in gates.values():
        assert all(sha(ROOT/p)==h for p,h in g['raw_sha256'].items())
    raw={phase:{(r['base_problem_id'],r['condition'],r['event']):r for p in (OUT/'raw'/g['run_id']).glob('shard_*/*/*/*.json') for r in [read_json(p)]} for phase,g in gates.items()}
    annotations=read_jsonl(OUT/'annotations/events.jsonl');labels=[];w2=[];w8=[];mixed=[];semantic=[];shams=[];factorials=[];triggers=[]
    for e in annotations:
        if e['split']=='natural_only':continue
        key=e['base_problem_id'],'O',e['event'];arms=raw['causal'][key]['arms'];d=arms['N']['D']
        vsd={r:d-arms[r+'_W2']['D'] for r in ('T','M','X','I','joint') if r+'_W2' in arms}
        # Overlapping alternatives remain raw descriptive observations only.
        strict={r:v for r,v in vsd.items() if r not in ('M','X') or e['independent_source_contrasts'].get(r,False)}
        w8_t=d-arms['T_W8']['D'];ce=sham=ces=None
        ident={k:e[k] for k in ('base_problem_id','event_id','event','split','template_family','source_class','evidence_type','local_correctness','final_correct','temporal_role','temporal_unresolved','readout_kind','reasoning_progress')}
        if e['cf_validated']:
            source=e['joint_source_ids'][0]
            scores={c:raw['semantic'][e['base_problem_id'],c,e['event']]['arms']['N']['D'] for c in e['cf_conditions']}
            assert d==scores['O']
            ce=d-scores['C_'+source];sham=d-scores['S_'+source];ces=ce-abs(sham)
            semantic.append({**ident,'edited_source':source,'CE':ce,'CE_minus_abs_sham':ces,'condition_D':scores,'direction':'ground-truth original fact minus edited fact'})
            shams.append({**ident,'sham_shift':sham,'absolute_sham_shift':abs(sham)})
            for c in scores:
                if not c.startswith('J_'):continue
                sources=c[2:].split('_');other=next(s for s in sources if s!=source)
                other_ce=d-scores['C_'+other]
                factorials.append({**ident,'target_source':source,'other_source':other,'CE_target':ce,'CE_other_on_target_readout':other_ce,
                    'target_minus_other':ce-other_ce,'joint_CE':d-scores[c],
                    'factorial_interaction':d-scores['C_'+source]-scores['C_'+other]+scores[c],
                    'scope':'Other-source edit on target readout is cross-source control, not a validated alternative-fact semantic readout.'})
        te={}
        if 'R16' in arms:
            for role in ('T','X','M'):
                name='R16_'+role+'_W2'
                if name in arms:te[role]=vsd[role]-(arms['R16']['D']-arms[name]['D'])
            alt=next((r for r in ('X','M') if r in te),None)
            triggers.append({**ident,'TE_VSD':te,'target_specific_trigger_difference':te['T']-te[alt] if alt else None,
                             'alternative_role':alt,'D_native':d,'D_R16_removed':arms['R16']['D']})
        later_error=(e['integration_error_reviewed'] and bool(e['next_downstream_use'])
                     and e['next_downstream_use'] not in e['history_before_ed_text'])
        label=classify_event(local_correctness=e['local_correctness'],final_correct=e['final_correct'],vsd=strict,w8_t=w8_t,
            ce_minus_sham=ces,temporal=e['temporal_role'],integration_error_reviewed=later_error,
            mention_differs=e['independent_source_contrasts'].get('M',False),has_explicit_claim=e['has_explicit_visual_claim'],
            ce_effect=ce,sham_effect=sham,previous_source_roi=e['previous_source_roi'])
        labels.append({**ident,**label,'VSD':vsd,'classification_VSD':strict,'W8_T':w8_t,'CE':ce,'sham_shift':sham,'CE_minus_abs_sham':ces,
            'TE_VSD':te,'D_native':d,'correct_candidate_NLL':-arms['N']['L_o'],
            'actual_generated_candidate_direction':e['actual_candidate_direction'],'has_explicit_visual_claim':e['has_explicit_visual_claim'],
            'semantic_role':e['semantic_role'],'previous_source_roi':e['previous_source_roi'],
            'integration_error_reviewed':e['integration_error_reviewed'],'reviewed_error_after_event':later_error,'next_downstream_use':e['next_downstream_use'],
            'alternative_semantic_readout_available':False,'attention_features_used':False})
        w2.append({**ident,'VSD':vsd,'classification_VSD':strict,'D_native':d,'target_minus_irrelevant':vsd['T']-vsd['I'] if 'I' in vsd else None,
            'target_minus_alternative':vsd['T']-strict['X'] if 'X' in strict else None,'mentioned_minus_target':vsd['M']-vsd['T'] if 'M' in vsd else None})
        w8.append({**ident,'VSD_T_W8':w8_t,'VSD_T_W2':vsd['T']})
        if 'joint' in vsd:mixed.append({**ident,'joint_VSD':vsd['joint'],'joint_minus_demanded':vsd['joint']-vsd['T'],'information_fractions_inferred':False})
    products={'phase_b_causal/w2_source_profiles.jsonl':w2,'phase_b_causal/w8_source_profiles.jsonl':w8,
              'phase_b_causal/mixed_support_controls.jsonl':mixed,'phase_c_counterfactual/semantic_effects.jsonl':semantic,
              'phase_c_counterfactual/sham_effects.jsonl':shams,'phase_c_counterfactual/factorial_source_controls.jsonl':factorials,
              'phase_d_trigger/trigger_effects.jsonl':triggers,'annotations/causal_labels.jsonl':labels,
              'phase_h_failure/hallucination_events.jsonl':[r for r in labels if r['local_visual_hallucination']],
              'phase_h_failure/failure_decision_tree.jsonl':labels,'phase_h_failure/integration_failures.jsonl':[r for r in labels if r['integration_failure']]}
    for p,rows in products.items():write_jsonl(OUT/p,rows)
    summary={'events':len(labels),'bases':len({r['base_problem_id'] for r in labels}),'causal_profiles':dict(Counter(s for r in labels for s in r['causal_profiles'])),
             'hallucination_subtypes':dict(Counter(s for r in labels for s in r['hallucination_subtypes'])),
             'integration_events':sum(r['integration_failure'] for r in labels),'semantic_events':len(semantic),'trigger_events':len(triggers),
             'attention_used':False,'overlapping_labels':True,'alternative_CE_missing_is_not_null':True}
    write_json(OUT/'phase_b_causal/causal_state_classification.json',summary)
    write_json(flag,{'frozen_at':datetime.now(timezone.utc).isoformat(),'attention_extraction_started':False,'summary':summary,
        'sha256':{str((OUT/p).relative_to(ROOT)):sha(OUT/p) for p in products},
        'cohort_freeze_sha256':sha(OUT/'cohort/cohort_freeze_complete.json'),'script_sha256':sha(__file__),
        'protocol_sha256':sha(ROOT/'code/visual_reasoning/stage5a/protocol.py'),
        'causal_gate_sha256':sha(OUT/'phase_b_causal/causal_run_complete.json'),'semantic_gate_sha256':sha(OUT/'phase_c_counterfactual/semantic_run_complete.json')})
    print(summary)


if __name__=='__main__':main()
