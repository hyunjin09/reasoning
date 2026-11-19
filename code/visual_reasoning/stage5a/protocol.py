"""Prospective cohort selection and attention-independent causal labels."""


def select_natural(rows,target=200):
    selected=[];seen=set()
    for row in rows:
        if row['base'] in seen or not row['eligible']:continue
        selected.append(row);seen.add(row['base'])
        if len(selected)==target:break
    return selected


def select_atlas(natural,target=128):
    eligible=[r for r in natural if r['atlas_eligible']]
    chosen=set()
    for incorrect in (False,True):
        group=[r for r in eligible if bool(r['local_incorrect'])==incorrect]
        chosen.update(r['base'] for r in group[:target//2])
    for row in eligible:
        if len(chosen)>=target:break
        chosen.add(row['base'])
    return [r for r in eligible if r['base'] in chosen]


def classify_event(*,local_correctness,final_correct,vsd,w8_t,ce_minus_sham,
                   temporal,integration_error_reviewed=False,mention_differs=False,
                   has_explicit_claim=True,floor=.05,ce_effect=None,sham_effect=None,
                   alternative_ce_minus_sham=None,alternative_ce_roi=None,previous_source_roi=None):
    """Freeze causal/semantic axes without accepting any attention feature.

    Missing counterfactual evidence lowers confidence; it cannot count as a null.
    Wrong final answers alone never establish a visual or integration diagnosis.
    """
    t=vsd.get('T');alternatives=[vsd[x] for x in ('X','M') if x in vsd]
    x=max(alternatives) if alternatives else None;i=vsd.get('I')
    substantial=t is not None and t>floor
    weak=t is not None and abs(t)<=floor and w8_t is not None and abs(w8_t)<=floor
    semantic_positive=ce_minus_sham is not None and ce_minus_sham>floor
    semantic_weak=(ce_effect is not None and sham_effect is not None
                   and abs(ce_effect)<=floor and abs(sham_effect)<=floor)
    semantic_conflict=(ce_effect is not None and sham_effect is not None
                       and ce_effect < -floor and abs(sham_effect)<=floor)
    demanded=substantial and (x is None or t>x) and (i is None or t>i)
    alternative=x is not None and t is not None and x>floor and x>t
    mixed=substantial and x is not None and x>floor
    tied=x is not None and t==x and t>floor
    unsupported=has_explicit_claim and weak and semantic_weak and not alternative
    profiles=[]
    if demanded:profiles.append('DEMANDED_ROI_DOMINANT')
    if alternative:profiles.append('ALTERNATIVE_ROI_DOMINANT')
    if mixed:profiles.append('MIXED_VISUAL_SUPPORT')
    if weak:profiles.append('LOCAL_VISUAL_INSENSITIVE')
    if t is not None and t<=floor and w8_t is not None and w8_t>floor:profiles.append('BROADER_LOCAL_SOURCE_DEPENDENCE')
    if not profiles or tied or semantic_conflict:profiles.append('UNRESOLVED')
    wrong=local_correctness=='INCORRECT';hallucinations=[]
    previous=vsd.get(previous_source_roi) if previous_source_roi in ('X','M') else None
    stale=(temporal=='REFRESH_AFTER_OTHER_SOURCE' and previous is not None
           and t is not None and previous>floor and previous>t)
    if wrong and has_explicit_claim:
        if unsupported:hallucinations.append('H-NR')
        if alternative:hallucinations.append('H-MR')
        if substantial and semantic_positive:hallucinations.append('H-SC')
        if stale:hallucinations.append('H-ST')
    target_confirmed=substantial and semantic_positive and i is not None and t>i
    alternative_confirmed=(alternative and alternative_ce_minus_sham is not None
                           and alternative_ce_minus_sham>floor and i is not None and x>i
                           and alternative_ce_roi in ('X','M') and vsd.get(alternative_ce_roi)==x)
    stale_confirmed=(stale and alternative_ce_roi==previous_source_roi
                     and alternative_ce_minus_sham is not None and alternative_ce_minus_sham>floor
                     and i is not None and previous>i)
    weak_confirmed=unsupported and i is not None and abs(i)<=floor
    tiers={name:('Tier1' if {'H-NR':weak_confirmed,'H-MR':alternative_confirmed,
                            'H-SC':target_confirmed,'H-ST':stale_confirmed}[name]
                 else 'Tier2') for name in hallucinations}
    confidence=('Tier1' if target_confirmed or alternative_confirmed or weak_confirmed
                else 'Tier2' if t is not None else 'Tier3')
    # A confirmed demanded source cannot upgrade a different, unconfirmed failure mechanism.
    if tiers:confidence='Tier1' if all(v=='Tier1' for v in tiers.values()) else 'Tier2'
    return {'causal_profiles':profiles,'demanded_dominant':demanded,'alternative_dominant':alternative,
        'mixed_support':mixed,'source_tie':tied,'local_insensitive':weak,
        'semantic_control':semantic_positive,'semantic_conflict':semantic_conflict,
        'semantic_null_with_sham_control':semantic_weak,'unsupported_grounding':unsupported,
        'unsupported_candidate_without_CE':has_explicit_claim and weak and ce_minus_sham is None and not alternative,
        'genuine_retrieval':demanded,'retrieval_semantically_confirmed':demanded and semantic_positive,
        'alignment_only_candidate':mention_differs and vsd.get('M') is not None and abs(vsd['M'])<=floor and substantial,
        'verification':demanded and temporal=='REUSE_WITHOUT_INTERVENING_SOURCE',
        'refresh':demanded and temporal=='REFRESH_AFTER_OTHER_SOURCE',
        'hallucination_subtypes':hallucinations,'subtype_confidence_tiers':tiers,
        'stale_previous_source_dominant':stale,'local_visual_hallucination':wrong and has_explicit_claim,
        'grounded_local_globally_wrong':local_correctness=='CORRECT' and demanded and not final_correct,
        'integration_failure':local_correctness=='CORRECT' and demanded and not final_correct and integration_error_reviewed,
        'confidence_tier':confidence}
