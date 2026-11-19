"""Frozen absolute decision and optional-assay gates."""
def absolute_decision(surface):
    if surface['t0']['damage']<=.05+1e-12:return 'stop_zero',None
    if surface['t128']['damage']<=.05+1e-12:
        return 'selected',64 if surface['t64']['damage']<=.05+1e-12 else 128
    if 't256' not in surface:return 'run',256
    if surface['t256']['damage']<=.05+1e-12:return 'selected',256
    return 'stop_no_finite',256


def relative_gate(surface,contrast,relative):
    a=relative['arms'];longer=a['thinking']['median_observed_tokens']>a['cot']['median_observed_tokens']
    lower=a['thinking']['cutoffs']['128']['median_item_fraction']<a['cot']['cutoffs']['128']['median_item_fraction']
    return bool(surface['t0']['damage']>.05 and surface['t128']['damage']>.05 and contrast['difference']>0 and (longer or lower))


def reserve_gate(surface,contrast,control_ok):
    return bool(control_ok and surface['t0']['damage']>.05 and surface['t128']['damage']>.05 and contrast['difference']>.05 and
        (contrast['ci95'][0]<=0<=contrast['ci95'][1] or surface['t128']['ci95'][0]<.05<surface['t128']['ci95'][1]))
