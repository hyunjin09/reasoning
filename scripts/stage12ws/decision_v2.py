"""Apply the frozen specification's explicit mixed/missingness qualification."""
def select(gate, counts, natural, families):
    if gate['status']=='STOP_WEAK':return 'PORTABILITY_WEAK_UNDER_PAIRED_SEEDS'
    if not gate['continue']:return 'UNRESOLVED'
    if counts['derived_state_support']>=3 and counts['distributed_necessity']>=2:return 'DISTRIBUTED_DERIVED_STATE_SIGNAL'
    if counts['derived_state_support']>=3:return 'DERIVED_STATE_ONLY'
    if natural['joint']:return 'INTERFERENCE_REPAIR_SIGNAL'
    signals=[]
    for family in families:
        if not family['eligible']:continue
        signals += [family.get('derived_state_support'),family.get('order_sensitive')]
        signals += [e['at_least_3'] for e in family.get('derived_contrasts',{}).values()]
        signals += [e['at_least_3'] for e in family.get('block_effects',{}).values()]
    for key in ['interference','repair']:
        if key in natural:signals.append(natural[key]['at_least_3'])
    # Do not describe a robust local effect or an unidentified contrast as a clean null.
    if any(v is True or v is None for v in signals):return 'UNRESOLVED'
    return 'PORTABILITY_CONTENT_UNRESOLVED'
