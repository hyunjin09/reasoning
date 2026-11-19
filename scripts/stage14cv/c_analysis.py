"""Separate old/new source strata, frozen mode and fidelity endpoints."""
from collections import Counter
from scripts.stage14cv.common import *
from scripts.stage14cv.analysis_core import paired_binary


def summarize(rr):
    scored=[r for r in rr if r['status']=='SCORED'];n=len(scored)
    claims=sum((Counter(r['claim_classes']) for r in scored),Counter())
    asserted=sum(r['asserted_visual_facts'] for r in scored)
    precision=[r['targeted_precision'] for r in scored if r['targeted_precision'] is not None]
    units=sum((Counter(r['bound_source_units']) for r in scored),Counter())
    return dict(planned=len(rr),mode_counts=dict(Counter(r['mode'] for r in rr)),
         fidelity_statuses=dict(Counter(r['status'] for r in rr)),scored=n,
         full_recovery=sum(r['full_E_star_recovery'] for r in scored),
         partial_recovery=sum(0<r['recovered_subfacts']<r['subfacts'] for r in scored),
         no_recovery=sum(r['recovered_subfacts']==0 for r in scored),
         recovered_subfacts=sum(r['recovered_subfacts'] for r in scored),required_subfacts=sum(r['subfacts'] for r in scored),
         subfact_recall_macro=sum(r['subfact_recall'] for r in scored)/n if n else None,
         full_atom_recall_macro=sum(r['full_E_star_recovery'] for r in scored)/n if n else None,
         targeted_precision_macro=sum(precision)/len(precision) if precision else None,precision_defined_families=len(precision),
         targeted_precision_micro=sum(r['required_visual_facts'] for r in scored)/asserted if asserted else None,
         required_visual_facts=sum(r['required_visual_facts'] for r in scored),asserted_visual_facts=asserted,claim_classes=dict(claims),
         bound_subfact_recovery_counts=dict(units),bound_subfact_denominator=n,
         binding_definition='Unit credit requires correct source identity and left/middle/right order; this is bound-subfact recall, not an independent binding-only assay')


def main():
    for name in ['analysis_adapter_seal_v1.json','R_primary_seal_v1.json','C_contract_modes_seal_v1.json','C_fidelity_scoring_seal_v1.json','C_fixed_QC_seal_v1.json']:
        for p,h in load(ROOT/'audit'/name)['files'].items():assert sha(p)==h,p
    data=rows(ROOT/'scoring/C_scored_outcomes.jsonl');assert len(data)==800
    strata=sorted({r['stratum'] for r in data});assert len(strata)==2
    primary={};fidelity={};marginal={};pooled={};mode_transitions={}
    for model in 'IT':
        for stratum in strata+['pooled200_secondary']:
            rr=[r for r in data if r['model']==model and (stratum=='pooled200_secondary' or r['stratum']==stratum)]
            pairs={}
            for r in rr:
                pairs.setdefault(r['family_id'],{})[r['condition']]=r
            assert all(set(p)=={'C0','C1'} for p in pairs.values())
            key=model+'|'+stratum
            def compare(getter,label):
                obs=[dict(family_id=f,a=getter(p['C0']),b=getter(p['C1'])) for f,p in pairs.items()]
                return paired_binary(obs,'a','b',key+'|'+label)
            evidence=lambda r:None if r['mode']=='UNRESOLVED' else int(r['mode'] in {'EVIDENCE_ONLY','MIXED'})
            strict=lambda r:None if r['mode']=='UNRESOLVED' else int(r['mode']=='EVIDENCE_ONLY')
            full=lambda r:int(r['full_E_star_recovery']) if r['status']=='SCORED' else None
            result=dict(evidence_output_C1_minus_C0=compare(evidence,'evidence-output'),strict_evidence_only_C1_minus_C0=compare(strict,'strict-evidence-only'))
            if stratum=='pooled200_secondary':pooled[key]=result
            else:primary[key]=result
            def state(r):
                return ('FULL' if r['full_E_star_recovery'] else 'NOT_FULL') if r['status']=='SCORED' else r['status']
            states=['FULL','NOT_FULL','UNRESOLVED','TECHNICAL_MISSING']
            counts=Counter(state(p['C0'])+'__'+state(p['C1']) for p in pairs.values())
            fidelity[key]=dict(full_source_atom_C1_minus_C0=compare(full,'full-atom'),
                 full_atom_transitions={a+'__'+b:counts[a+'__'+b] for a in states for b in states},
                 C0=summarize([r for r in rr if r['condition']=='C0']),C1=summarize([r for r in rr if r['condition']=='C1']))
            mode_transitions[key]=dict(Counter(p['C0']['mode']+'__'+p['C1']['mode'] for p in pairs.values()))
    save(ROOT/'analysis/contract_primary.json',dict(at=now(),primary=primary,pooled_secondary=pooled,
         mode_transitions=mode_transitions,definition='Evidence-output = EVIDENCE_ONLY or MIXED; strict compliance shown separately',
         inference='10000 paired-family draws; seed20261009; unadjusted95% intervals, estimation only'))
    save(ROOT/'analysis/d1_fidelity_companions.json',dict(at=now(),panels=fidelity,
         target='Original one structured atom, five unchanged bound source subfacts',
         precision='Required direct-image assertions / (required + accurate unmatched + unsupported + contradictory assertions); derived and uncertain excluded',
         caveat='A separate elicitation prompt; cannot establish native internal knowledge or mediation of R performance'))
    paths=[ROOT/'analysis/contract_primary.json',ROOT/'analysis/d1_fidelity_companions.json']
    save(ROOT/'audit/C_primary_seal_v1.json',dict(at=now(),files={str(p):sha(p) for p in paths},
         separate_strata_primary=True,no_case_selection_before_seal=True))


if __name__=='__main__':main()
