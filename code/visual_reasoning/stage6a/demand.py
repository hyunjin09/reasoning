"""Conservative temporal bookkeeping for independently assigned semantic states."""


def temporal_labels(spans):
    result=[];explicit={};seen_demand=set();unknown_history=False;uncertain_explicit=set()
    previous=None;departed_sources=set();unknown_since_demand=False
    for index,row in enumerate(spans):
        sources=sorted(set(row['demanded_sources']));unresolved=row['unresolved']
        prior={key:True if key in explicit else None if unknown_history or key in uncertain_explicit else False for key in sources}
        evidence={key:explicit[key] for key in sources if key in explicit}
        changed=None if unresolved or previous is None else sources!=previous
        per_source={}
        for key in sources:
            if unresolved:per_source[key]='UNRESOLVED'
            elif key not in seen_demand and not unknown_history:per_source[key]='FIRST_USE'
            elif prior[key] is True and not unknown_since_demand:
                per_source[key]='REFRESH' if key in departed_sources else 'REUSE'
            else:per_source[key]='UNRESOLVED'
        roles=set(per_source.values())
        role='UNRESOLVED' if unresolved else 'NONE' if not sources else next(iter(roles)) if len(roles)==1 else 'MIXED'
        result.append({**row,'previous_demand':previous,'demand_changed':changed,
            'prior_explicit_access':prior,'prior_explicit_evidence':evidence,'first_reuse_refresh':role,
            'source_temporal_roles':per_source,
            'temporal_annotation_basis':'Full ordered semantic-state prefix; positive prior claims retained, uncertainty never treated as absence.'})
        # The current claim becomes available only to later spans.
        for key in row['explicit_visual_claim_sources']:
            explicit.setdefault(key,dict(span_id=row.get('span_id',str(index)),text=row['text']))
        uncertain_explicit.update(row.get('candidate_visual_claim_sources',[]))
        if unresolved:
            previous=None;unknown_history=True;unknown_since_demand=True
        else:
            previous=sources
            if sources:
                # A refresh requires an intervening known demand on another
                # source, excluding this one. Narrowing AT to A keeps A active;
                # arithmetic/no-demand pauses alone do not visit another source.
                departed_sources.update((seen_demand|set(explicit))-set(sources))
                departed_sources.difference_update(sources)
                seen_demand.update(sources);unknown_since_demand=False
    return result
