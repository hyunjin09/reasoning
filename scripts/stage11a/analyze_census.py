"""Bounded descriptive inference, after every annotation stage is sealed."""
import os
from collections import Counter
import numpy as np
from scripts.stage11a.common import ROOT,ARMS,SEED,load,save,sha,now
from scripts.stage11a.protocol import feasibility
from scripts.stage11a.census_statistics import rate,paired_summary,coarse_state
from scripts.stage10b.protocol import agreement

def summarize(rows):
    modes={}
    for arm in ARMS:
        rr=[r for r in rows if r['arm']==arm];n2=[r for r in rr if r['native']=='N2'];pp=[r for r in rr if r['probed']]
        modes[arm]=dict(n=len(rr),probe_n=len(pp),probe_accessible=rate([r['probe']=='PROBE_ACCESSIBLE' for r in pp]),
            native_sufficient=rate([r['native']=='N2' for r in rr]),final_correct=rate([r['final']=='FINAL_CORRECT' for r in rr]),
            downstream_failure=rate([r['final']!='FINAL_CORRECT' for r in n2]),downstream_wrong_only=rate([r['final']=='FINAL_WRONG' for r in n2]),
            downstream_no_valid_final=rate([r['final']=='NO_VALID_FINAL' for r in n2]),native_states=dict(Counter(r['native'] for r in rr)),
            final_states=dict(Counter(r['final'] for r in rr)),profiles=dict(Counter(r['profile'] for r in pp)))
    by={arm:{r['item_id']:r for r in rows if r['arm']==arm} for arm in ARMS};contrasts={}
    for field,state in [('probe','PROBE_ACCESSIBLE'),('native','N2'),('final','FINAL_CORRECT')]:
        ids=sorted(by['thinking'].keys()&by['instruct_cot'].keys())
        if field=='probe':ids=[i for i in ids if by['thinking'][i]['probed'] and by['instruct_cot'][i]['probed']]
        contrasts[field]=paired_summary([by['thinking'][i][field]==state for i in ids],[by['instruct_cot'][i][field]==state for i in ids])
    return dict(modes=modes,thinking_minus_cot=contrasts)

def categories(rows):
    return dict(n=len(rows),counts=dict(Counter(r['category'] for r in rows)),rates={c:rate([r['category']==c for r in rows]) for c in ['A','B','C','D']})

def descriptive(values):
    values=[v for v in values if v is not None]
    return dict(n=len(values),median=float(np.median(values)) if values else None,
        range=[min(values),max(values)] if values else None)

def main():
    assert os.environ.get('SLURM_JOB_ID')
    data=load(ROOT/'audit/census_joined.json');assert data['sealed'];rows=data['rows'];disc=data['discordances']
    key=load(ROOT/'audit/native_key.json');agreeids=set(key['agreement_item_ids'])
    native={w:{r['packet_id']:r for r in load(ROOT/'annotations'/f'native_{w}.json')['rows']} for w in ['a','b']}
    keys=[r for r in key['rows'] if r['agreement']]
    na=[native['a'][r['packet_id']]['state'] for r in keys];nb=[native['b'][r['packet_id']]['state'] for r in keys]
    fine=agreement(na,nb);coarse=agreement([coarse_state(x) for x in na],[coarse_state(x) for x in nb])
    used=fine if fine['kappa'] is not None and fine['kappa']>=.6 else coarse
    loc={w:load(ROOT/'annotations'/f'localization_{w}.json') for w in ['a','b']}
    lp=ROOT/'packets/localization_agreement.json'
    for v in loc.values():assert v['sealed'] and v['packet_sha256']==sha(lp) and {r['item_id'] for r in v['rows']}==agreeids
    lr={w:{r['item_id']:r for r in v['rows']} for w,v in loc.items()}
    from scripts.stage11a.protocol import localization
    for p in load(lp)['rows']:
        t,c=p['thinking'],p['cot']
        direction='THINKING_GAIN' if t['final']=='FINAL_CORRECT' and c['final']!='FINAL_CORRECT' else 'COT_GAIN' if c['final']=='FINAL_CORRECT' and t['final']!='FINAL_CORRECT' else 'CONCORDANT'
        expected=localization(t,c)[0] if direction=='THINKING_GAIN' else localization(c,t)[0] if direction=='COT_GAIN' else 'NOT_DISCORDANT'
        for w in lr:
            assert lr[w][p['item_id']]['direction']==direction and lr[w][p['item_id']]['category']==expected,(w,p['item_id'],'localization needs adjudication')
    suff={w:{r['item_id']:r for r in load(ROOT/'annotations'/f'sufficiency_{w}.json')['rows']} for w in ['a','b']}
    construction={w:{r['item_id']:r for r in load(ROOT/'annotations'/f'e_star_{w}.json')['rows']} for w in ['a','b']}
    eligibility=load(ROOT/'stage11a_e_star_eligibility.json')['rows'];allids=sorted(r['item_id'] for r in eligibility)
    agreement_result=dict(at=now(),independent_families=len(agreeids),native_ratings=len(keys),native_fine=fine,native_coarse=coarse,
        native_gate_kappa=used['kappa'],fine_proportions_promotable=fine['kappa'] is not None and fine['kappa']>=.6,
        eligibility_all128=agreement([construction['a'][i]['eligibility'] for i in allids],[construction['b'][i]['eligibility'] for i in allids]),
        sufficiency_fixed32=agreement([suff['a'][i]['sufficiency'] for i in sorted(agreeids)],[suff['b'][i]['sufficiency'] for i in sorted(agreeids)]),
        localization_fixed32=agreement([lr['a'][i]['direction']+':'+lr['a'][i]['category'] for i in sorted(agreeids)],[lr['b'][i]['direction']+':'+lr['b'][i]['category'] for i in sorted(agreeids)]),
        native_disagreements=[dict(packet_id=k['packet_id'],a=native['a'][k['packet_id']],b=native['b'][k['packet_id']]) for k in keys if native['a'][k['packet_id']]['state']!=native['b'][k['packet_id']]['state']],
        limitations='Independent model-agent passes, not human reliability. Same models/project history can induce correlated errors. Styles can reveal modes. Localization agreement checks frozen rule application after semantic reviews.')
    save(ROOT/'stage11a_annotation_agreement.json',agreement_result)
    eligible=len({r['item_id'] for r in rows});probed=[r for r in rows if r['probed']]
    forward=[r for r in disc if r['direction']=='THINKING_GAIN'];reverse=[r for r in disc if r['direction']=='COT_GAIN']
    E5=categories(forward);rev=categories(reverse)
    save(ROOT/'stage11a_thinking_cot_discordance.json',dict(at=now(),primary=E5,reverse=rev,rows=disc,
        denominator='Fully probed eligible independent families; primary Thinking correct/CoT wrong or no-valid-final, reverse swapped.',
        by_evidence_type={t:categories([r for r in forward if r['evidence_type']==t]) for t in sorted({r['evidence_type'] for r in forward})},
        by_subject={t:categories([r for r in forward if r['subject']==t]) for t in sorted({r['subject'] for r in forward})},
        by_atom_count={str(t):categories([r for r in forward if r['n_facts']==t]) for t in sorted({r['n_facts'] for r in forward})}))
    counts=Counter(r['profile'] for r in probed if r['arm']=='instruct_cot')
    informative=sum(r['category']!='D' for r in forward);mixed=E5['counts'].get('D',0)/len(forward) if forward else 1.
    decision=feasibility(eligible,len(forward),informative,[counts[c] for c in ['P1','P2','P3']],used['kappa'],mixed)
    recommendations={'STRONG_GO':'Freeze the E*-eligible cohort and run a preregistered Equal-Evidence Oracle to causally localize the Thinking–CoT performance gap.',
        'LIMITED_GO':'Run only a small Equal-Evidence Oracle pilot and keep Claim 3 secondary.',
        'NO_GO':'Stop the bottleneck branch and finalize the paper around the already-established causal retrieval and visual-to-text lifecycle claims.'}
    save(ROOT/'stage11a_go_nogo_decision.json',dict(at=now(),decision=decision,eligible=eligible,discordant=len(forward),informative_discordant=informative,
        cot_failure_profile_unique_counts={p:counts[p] for p in ['P1','P2','P3']},native_agreement_kappa=used['kappa'],mixed_fraction=mixed,
        optional_pilot_eligible=decision!='NO_GO',exactly_one_recommendation=recommendations[decision],stage11b_launched=False))
    save(ROOT/'stage11a_primary_inference.json',dict(at=now(),independent_unit='problem/image family',bootstrap_draws=4000,seed=SEED,
        all128_eligibility=rate([r['eligibility']=='E_STAR_ELIGIBLE' for r in eligibility]),eligibility_counts=dict(Counter(r['eligibility'] for r in eligibility)),
        all_eligible=summarize(rows),matched_probed_subset=summarize(probed),E5=E5,reverse=rev,
        secondary_by_mode={arm:dict(reasoning_tokens=descriptive([r['reasoning_tokens'] for r in rows if r['arm']==arm]),
            first_evidence_token=descriptive([r.get('first_evidence_token') for r in rows if r['arm']==arm]),
            first_sufficient_token=descriptive([r.get('first_sufficient_token') for r in rows if r['arm']==arm]),
            first_evidence_normalized=descriptive([r['first_evidence_token']/r['reasoning_tokens'] for r in rows if r['arm']==arm and r.get('first_evidence_token') is not None and r['reasoning_tokens']]),
            single_fact=summarize([r for r in rows if r['n_facts']==1])['modes'][arm],
            multi_fact=summarize([r for r in rows if r['n_facts']>1])['modes'][arm]) for arm in ARMS},
        agreement=agreement_result,decision=decision,causal_claim=False,joined_sha256=sha(ROOT/'audit/census_joined.json')))
    print('CENSUS',decision,'eligible',eligible,'discordant',len(forward),'informative',informative,flush=True)

if __name__=='__main__':main()
