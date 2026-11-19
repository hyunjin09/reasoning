"""Prospective five-seed held-out replication rules; missing is never incorrect."""
import hashlib
from scripts.stage12b.protocol import build_prompt

def seed(family,condition,replicate):
    assert 0<=replicate<5
    return int(hashlib.sha256(f'stage12xs-v1|{family}|{condition}|{replicate}'.encode()).hexdigest(),16)%(2**31)

def prompt(row,arm):
    if arm=='C':return row['question']+" Let's think step by step."
    if arm=='T':return row['question']
    return build_prompt(row,arm)

def majority(values):
    assert len(values)==5 and all(v is None or type(v) is bool for v in values)
    wins=values.count(True);missing=values.count(None)
    return True if wins>=3 else False if wins+missing<=2 else None

def support(panels,strict=False):
    predicates=[majority(panels[k]) for k in ['RT_T','RT_I']]
    for key in ['Q_I','SH_I']:
        v=panels[key];limit=1 if strict else 2
        predicates.append(True if v.count(True)+v.count(None)<=limit else False if v.count(True)>limit else None)
    return False if False in predicates else None if None in predicates else True

def decision(n_selected,sufficiency,production):
    assert len(sufficiency)==len(production)==n_selected
    if n_selected<3:return 'HELDOUT_CANDIDATE_SPARSE'
    s=sufficiency.count(True);p=production.count(True)
    if n_selected>=5 and 5*s>=4*n_selected and p>=3 and 5*p>=3*n_selected:return 'HELDOUT_STATE_PRODUCTION_REPLICATED'
    if p>=2:return 'HELDOUT_PORTABILITY_PARTIAL'
    if n_selected>=5 and p+production.count(None)<2:return 'HELDOUT_STATE_PRODUCTION_NOT_REPLICATED'
    if None in production or None in sufficiency:return 'UNRESOLVED_TECHNICAL'
    return 'UNRESOLVED_LOW_YIELD'
