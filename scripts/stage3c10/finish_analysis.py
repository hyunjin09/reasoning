#!/usr/bin/env python3
"""Assess supported claims and paper value after every authorized gate finishes."""
import statistics
from scripts.stage3c10.freeze_inputs import ROOT,OUT,read_json,read_jsonl,write_json
from scripts.stage3c10.analyze import load_phase,TARGETS
from visual_reasoning.stage3c10.analysis import secondary
from visual_reasoning.stage3c10.protocol import vsd
from visual_reasoning.stage3c8.analysis import summarize_effect


def main():
    p=read_json(OUT/'phase_b_primary/primary_statistics.json')
    e=read_json(OUT/'phase_e_mediation/mediation_statistics.json')
    h=read_json(OUT/'phase_e_mediation/hpre_statistics.json')['targets']
    k=read_json(OUT/'phase_c_temporal/k80.json')
    rows=load_phase('primary');med=load_phase('mediation');results={};generic={}
    for t in TARGETS:
        gate=p['gates'][t]['passed'];ss=e[t]['primary_family_with_rescue']
        rescue_r=ss['q_rescue_rds']['robust_positive'];rescue_v=ss['q_rescue_vsd']['robust_positive']
        if gate and rescue_r and rescue_v:outcome='O2 — Query-Mediated Retrieval Trigger';mediator='M1 — Q-mediated trigger'
        elif gate:
            outcome='O1 — Reasoning-State Retrieval Trigger'
            mediator='M2 — Routing mediation only' if rescue_r else 'M4 — No clean mediation'
            if isinstance(h[t].get('vsd'),dict) and h[t]['vsd']['robust_positive']:mediator='M3 — Broad-state mediation'
        elif ss['rds_T']['robust_positive'] and not ss['vsd_T']['robust_positive']:
            outcome='O4 — Routing-Only Trigger';mediator='not established'
        else:outcome='O5 — Distributed / No Clean Trigger';mediator='not established'
        qvals={b:v['q_vsd_T'] for b,v in p['paired_effects_by_base'][t].items()};qstats=secondary(qvals,8)
        neg={b:-v for b,v in ss['r16_minus_q']['values_by_base'].items()};qminus=secondary(neg,1)
        qminus['holm_p']=ss['r16_minus_q']['holm_p']
        prompt_dominant=qstats['robust_positive'] and qminus['bootstrap_mean_ci95'][0]>0 and qminus['positive_fraction']>=.75 and qminus['holm_p']<.05 and (ss['vsd_T']['median']<=0 or qstats['median']>=1.5*ss['vsd_T']['median'])
        if prompt_dominant:outcome='O3 — Prompt-Dominant Trigger'
        # Rescue gains and ratios remain unclipped; zero denominators explicit.
        ratios={};native_vsd={};kd_vsd={};rescued_vsd={};selected_vsd={};exact_rds=[]
        for r in med:
            if r['target_id']!=t:continue
            b=r['base_problem_id'];a=r['arms'];loss=vsd(a,'N')-vsd(a,'R16');gain=vsd(a,'Q_all')-vsd(a,'R16')
            if loss!=0:ratios[b]=gain/loss
            native_vsd[b]=vsd(a,'N');kd_vsd[b]=vsd(a,'R16');rescued_vsd[b]=vsd(a,'Q_all');selected_vsd[b]=vsd(a,'Q_selected')
            exact_rds.append(a['Q_all']['none']['rds']==a['N']['none']['rds'])
        results[t]={'outcome':outcome,'mediation':mediator,'primary_trigger_gate':p['gates'][t],
            'statistics':ss,'k80':k[t],'Q_control':qstats,'Q_minus_R16':qminus,'prompt_dominant':prompt_dominant,
            'native_VSD':summarize_effect(native_vsd),'R16KD_VSD':summarize_effect(kd_vsd),
            'Q_all_VSD':summarize_effect(rescued_vsd),'Q_selected_VSD':summarize_effect(selected_vsd),
            'Q_VSD_recovery_ratio_unclipped':summarize_effect(ratios),'Q_VSD_recovery_ratios_by_base':ratios,
            'native_Q_exact_RDS_restoration_count':sum(exact_rds),
            'Q_routing_restoration_interpretation':'Native Q with unchanged visual K reconstructs visual QK routing by design; behavioral VSD rescue is the nontrivial mediation readout.'}
        generic[t]={}
        for state in ['M','T']:
            rrs=[r for r in rows if r['target_id']==t and r['state']==state]
            generic[t][state]={}
            for name in ['R16','E16','Q']:
                vals={key:{} for key in ['original_NLL_change','counterfactual_NLL_change','residual_norm_change','entropy_change','attention_output_norm_change','noncausal_RDS_drop','causal_RDS_drop','TE_VSD']}
                for r in rrs:
                    a=r['arms'];b=r['base_problem_id']
                    if name not in a:continue
                    n,x=a['N']['none'],a[name]['none']
                    vals['original_NLL_change'][b]=x['candidate_nll']['original']-n['candidate_nll']['original']
                    vals['counterfactual_NLL_change'][b]=x['candidate_nll']['counterfactual']-n['candidate_nll']['counterfactual']
                    vals['residual_norm_change'][b]=x['current_query_residual_norm']-n['current_query_residual_norm']
                    vals['entropy_change'][b]=x['current_query_entropy']-n['current_query_entropy']
                    vals['attention_output_norm_change'][b]=statistics.mean(v['attention_output_norm'] for v in x['layer_norms'])-statistics.mean(v['attention_output_norm'] for v in n['layer_norms'])
                    vals['noncausal_RDS_drop'][b]=n['routing']['noncausal']['RDS_T_vs_M']-x['routing']['noncausal']['RDS_T_vs_M']
                    vals['causal_RDS_drop'][b]=n['rds']-x['rds'];vals['TE_VSD'][b]=vsd(a,'N')-vsd(a,name)
                generic[t][state][name]={key:{**summarize_effect(v),'values_by_base':v} for key,v in vals.items()}
    strong=all(r['outcome'].startswith('O2') for r in results.values())
    recommendation='GO — Stage 4 Multi-Evidence Retrieval/Refresh' if any(r['primary_trigger_gate']['passed'] for r in results.values()) else 'REVIEW — Broader Current-State Trigger Mediation'
    assessment={'new_causal_link': 'Recent reasoning input changes target-specific current-query visual dependence at both frozen retrieval coordinates; the tested late Q/h_pre rescues do not establish its behavioral mediator.' if all(r['primary_trigger_gate']['passed'] for r in results.values()) else 'Target-specific conclusions are in retrieval_trigger_summary.json.',
        'lifecycle_strengthened':True if any(r['primary_trigger_gate']['passed'] for r in results.values()) else False,
        'Q_mediation_both_targets':strong,
        'remaining_central_ambiguity':'The behavioral mediator remains unresolved: late Q rescue restores routing but not VSD, and the optional late h_pre rescue is also nonrobust. Prior stages already document local redundancy and late-state insufficiency. k80=16 is limited to tested windows; natural-generation sufficiency and generality beyond this historical cohort remain open.',
        'sink_value':'Sink release remains observational. These interventions already test the upstream recent-input link; sink manipulation is not necessary to establish the supported link and was not performed.',
        'paper_priority':'Test whether the local mechanism extends to selecting and refreshing multiple visual facts, subject to a new approved Stage4 plan.' if recommendation.startswith('GO — Stage 4') else 'Review the unresolved upstream-state mechanism before another intervention.',
        'recommendation':recommendation,'follow_on_started':False,
        'limitations':['Fixed O-image teacher-forced local evidence contrast; no free-generation or global reasoning-performance claim.',
            'Early M R16 windows contain fewer than16 tokens on two primary bases; retained and reported without prompt spill.',
            'E16 controls available on22/24 T bases; unavailable windows were not shifted.',
            'Broad source deletion changes generic language quantities too; target/M/E16/I/Q specificity and same-state Q rescue support the bounded retrieval interpretation, not exclusively retrieval-only computation.',
            'Historical A5000 full-path values are not numerical denominators; every causal contrast uses the same A6000 cached path.',
            'Noncausal heads also change, especially at Target A; the trigger effect is not confined to the historical four-head set.',
            'h_pre donors contain native upstream visual information and can bypass some all-layer source suppression; its VSD rescue is not a guaranteed upper bound or a pure routing intervention.',
            'Position/type results are descriptive and distance-controlled; no universal trigger token is claimed.']}
    write_json(OUT/'analysis/retrieval_trigger_summary.json',results)
    write_json(OUT/'analysis/generic_language_damage.json',generic)
    write_json(OUT/'analysis/routing_vs_behavior.json',{'targets':{t:{'routing_drop':p['statistics'][t]['rds_T'],'VSD_drop':p['statistics'][t]['vsd_T'],'paired_by_base':p['paired_effects_by_base'][t]} for t in TARGETS}})
    write_json(OUT/'analysis/target_heterogeneity.json',{'targets':{t:{'outcome':results[t]['outcome'],'mediation':results[t]['mediation'],'k80':k[t]} for t in TARGETS},'unit':'base_problem_id; targets kept separate'})
    write_json(OUT/'analysis/paper_claim_assessment.json',assessment)
    print({t:{k:v[k] for k in ['outcome','mediation','native_Q_exact_RDS_restoration_count']} for t,v in results.items()})

if __name__=='__main__':main()
