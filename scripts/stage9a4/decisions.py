"""Prospective Stage9A.4 gates; no model inference or outcome-dependent tuning."""
def baseline_gates(rows,noop):
    n=len(rows);assert n==64
    capped=[r for r in rows if r['at_length_cap']]
    g=dict(G1_accuracy=sum(r['correct'] for r in rows)/n>=.60,
           G2_cot=sum(r['cot'] for r in rows)/n>=.90,
           G3_final=sum(r['option'] is not None for r in rows)/n>=.90,
           G4_completion=len(capped)/n<=.10 or all(r['option'] is not None for r in capped),
           G5_noop=bool(noop))
    g['pass']=all(g.values());return g


def next_cutoff(zero,finite):
    if zero<=.05+1e-12:return 'stop_no_necessity',None
    for t in (64,128,256):
        if t not in finite:return 'run',t
        if finite[t]<=.05+1e-12:return 'selected',t
    return 'stop_no_finite',None


def reserve_eligible(selected,damage,ci):
    return bool(selected is not None and abs(damage)<=.1+1e-12 and ci[0]<.05<ci[1])
