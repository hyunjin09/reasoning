"""Post-outcome descriptive transport audit; no rejected record is executed or rescored."""
from collections import Counter
from scripts.stage14e.common import P, load, rows, save, sha, now
from scripts.stage14e.contracts_v2 import build_catalog, validate_demand, numeric_lexemes


def main():
    states=load(P/'raw/evaluation_acquisition_a6000_v2/acquisition_states.json')
    families={r['item_id']:r for r in rows(P/'inference/evaluation_families.jsonl')}
    labels=load(P/'annotations/evaluation_source_review_v1.json')['records']
    qc={r['item_id']:r for r in load(P/'annotations/evaluation_source_QC_v1.json')['rows']}
    details=[]
    for i,s in states.items():
        cat=build_catalog(families[i]['question'],families[i]['prefix']);index={r['id']:r for r in cat}
        obligations=s['M']['query'].get('obligations',[]);entries=[]
        for j,o in enumerate(obligations):
            q=dict(status='QUERY',need='REINSPECT' if o['coverage']=='TENTATIVE' else 'NEW_VISUAL',target=o['source_object'],property=o['property'],frame=o['source_frame'],source_refs=o['source_refs'],answer_value=None)
            ok,reason=validate_demand(q,cat)
            sources=[index[k] for k in o['source_refs']]
            origins={v['source'] for v in sources}
            if ok and o['coverage']=='ASSERTED_IN_PREFIX' and 'prefix' not in origins:ok,reason=False,'NO_ASSERTION_PROVENANCE'
            if ok and o['coverage']=='GIVEN_IN_QUESTION' and 'question' not in origins:ok,reason=False,'NO_GIVEN_PROVENANCE'
            text=' '.join(v['text'] for v in sources)
            unsupported=numeric_lexemes(q['target']+' '+q['frame'])-numeric_lexemes(text)
            entries.append(dict(index=j,obligation=o,entry_valid=ok,reason=reason,
                unsupported_in_cited_spans=sorted(unsupported),source_spans=sources,
                unsupported_also_absent_from_entire_catalog=sorted(unsupported-numeric_lexemes(' '.join(v['text'] for v in cat)))))
        first=next((j for j,o in enumerate(obligations) if o['coverage'] in ['UNKNOWN','TENTATIVE']),None)
        details.append(dict(item_id=i,entries=entries,actual_transport_valid=s['M']['transport_valid'],actual_target=s['M']['target'],
            first_eligible_index=first,first_eligible_entry_valid=entries[first]['entry_valid'] if first is not None else None,
            discarded_due_other_entry=not s['M']['transport_valid'] and first is not None and entries[first]['entry_valid'],
            interpretation='Descriptive host-contract decomposition only. No alternative target was run and no scientific label changed.'))
    out=dict(at=now(),records=details,discarded_due_other_entry=[r['item_id'] for r in details if r['discarded_due_other_entry']],
        source_review_sha256=sha(P/'annotations/evaluation_source_review_v1.json'),arms={})
    for arm in ['S','M']:
        actual=[(i,s[arm]) for i,s in states.items()]
        valid_none=[i for i,v in actual if v['transport_valid'] and v['target']['status']=='NONE']
        useful_none=[i for i in valid_none if qc[i]['prefix_state']=='established']
        rs=[r for r in labels if r['condition']==arm]
        out['arms'][arm]=dict(assigned=32,accepted_query=sum(v['transport_valid'] and v['target']['status']=='QUERY' for i,v in actual),
            invalid_target_ids=[i for i,v in actual if not v['transport_valid']],
            invalid_reasons=dict(Counter(v['validation_reason'] for i,v in actual if not v['transport_valid'])),
            legitimate_none=valid_none,useful_none=useful_none,
            genuine_none_with_unsettled_premise=[i for i in valid_none if qc[i]['prefix_state']!='established'],
            accepted_target_relevance=dict(Counter(r['target_relevance'] for r in rs if states[r['item_id']][arm]['transport_valid'] and states[r['item_id']][arm]['target']['status']=='QUERY')),
            by_prefix_state={status:dict(n=sum(qc[r['item_id']]['prefix_state']==status for r in rs),useful=sum(qc[r['item_id']]['prefix_state']==status and r['label'] in ['U','R'] for r in rs)) for status in ['established','tentative','unresolved']})
    out['zero_event_uncertainty_note']='Bootstrap[0,0] at0/32 is degenerate, not evidence true rate is exactlyzero. Unstratified two-sided95%ClopperPearson upper bound1-.025**(1/32), descriptive only.'
    out['zero_of32_binomial_upper95_descriptive']=1-.025**(1/32)
    save(P/'analysis/evaluation_transport_diagnostics_v1.json',out)
    print({k:v for k,v in out.items() if k not in ['records']})

if __name__=='__main__':main()
