"""Prospective completion/replay gates; no accuracy-dependent repair choice."""
from collections import Counter


def token_comparison(historical, current):
    common=min(len(historical),len(current))
    first=next((i for i in range(common) if historical[i]!=current[i]),None)
    if first is None and len(historical)!=len(current):first=common
    return dict(exact_token_identity=historical==current,first_divergence_token=first,
        common_prefix_tokens=common if first is None else first,
        prefix_128_identical=historical[:128]==current[:128],
        length_ratio=len(current)/len(historical) if historical else None)


def repetition_metrics(ids):
    # Exact repeated blocks, not ordinary mathematical vocabulary/reconsideration.
    # Semantically pathological loops also require output-only review.
    counts=Counter(tuple(ids[i:i+32]) for i in range(max(0,len(ids)-31)))
    maximum=max(counts.values(),default=0)
    repeated_fraction=sum(v for v in counts.values() if v>=4)/max(1,len(ids)-31)
    return dict(max_exact_32gram_repetitions=maximum,repeated_32gram_fraction=repeated_fraction,
        automatic_pathology=maximum>=8 and repeated_fraction>=.25)


def completion_gate(rows, phase):
    expected={'known_good':12,'nonprimary':24,'native':160,'oracle':160}[phase]
    if len(rows)!=expected or len({r['task_id'] for r in rows})!=expected or any(r.get('budget_interrupted') for r in rows):
        return dict(status='INCOMPLETE',pass_gate=False,expected=expected,observed=len(rows))
    assert all(isinstance(r['committed_final'],bool) and isinstance(r['pathological_repetition'],bool) for r in rows)
    arms={}
    for arm in ['thinking','instruct_direct']:
        rr=[r for r in rows if r['arm']==arm];assert len(rr)==expected//2
        arms[arm]=dict(n=len(rr),caps=sum(r['at_length_cap'] for r in rr),
            finals=sum(r['committed_final'] for r in rr),loops=sum(r['pathological_repetition'] for r in rr),
            image_input_failures=sum(r.get('image_input_valid') is False for r in rr))
    n=expected//2;t,d=arms.values();cap=sum(v['caps'] for v in arms.values())
    if phase=='known_good':
        passed=(cap<=1 and sum(v['finals'] for v in arms.values())>=10 and
            sum(v['loops'] for v in arms.values())<=1 and all(v['finals']>=4 for v in arms.values()) and
            all(r['replay_tier_pass'] for r in rows))
    else:
        passed=(all(v['caps']/n<.2 and v['finals']/n>=.75 for v in arms.values()) and
            abs(t['finals']-d['finals'])/n<.2 and abs(t['loops']-d['loops'])/n<.2)
        if phase=='nonprimary':passed=passed and cap/expected<.15
    passed=bool(passed and all(v['image_input_failures']==0 for v in arms.values()))
    return dict(status='PASS' if passed else 'STOP',pass_gate=passed,phase=phase,n=expected,arms=arms,
        total_cap_rate=cap/expected,completion_rate_difference=abs(t['finals']-d['finals'])/n,
        scientific_accuracy_used=False)
