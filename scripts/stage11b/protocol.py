"""Prospective Stage11B gates and serialization; no outcome-dependent defaults."""
import hashlib

CANDIDATES = [
    dict(id='hard_all',levels=[3,4,5],subject_rule='all'),
    dict(id='upper_all',levels=[4,5],subject_rule='all'),
    dict(id='middle_all',levels=[3,4],subject_rule='all'),
    dict(id='hard_geometry',levels=[3,4,5],subject_rule='geometry'),
    dict(id='hard_other',levels=[3,4,5],subject_rule='other'),
    dict(id='upper_geometry',levels=[4,5],subject_rule='geometry'),
]

def in_stratum(row, rule):
    geo='geometry' in row['subject']
    return row['level'] in rule['levels'] and (rule['subject_rule']=='all' or geo==(rule['subject_rule']=='geometry'))

def hash_order(row, seed, purpose='sample'):
    return hashlib.sha256(f"stage11b:{seed}:{purpose}:{row['family_id']}".encode()).hexdigest()

def discovery_gate(n, eligible, t_correct, c_correct, forward):
    checks=dict(eligible_rate=n>0 and eligible/n>=.4,
        forward_rate=eligible>0 and forward/eligible>=.2,
        thinking_accuracy=eligible>0 and .2<=t_correct/eligible<=.75,
        cot_accuracy=eligible>0 and .1<=c_correct/eligible<=.65,
        forward_count=forward>=12)
    return {'pass':all(checks.values()),'checks':checks}

def oracle_text(question, facts):
    if not 1<=len(facts)<=4 or not all(isinstance(x,str) and x.strip() for x in facts):
        raise ValueError('Oracle requires one to four nonempty frozen atomic facts')
    return ('Task-relevant visual evidence:\n'+
        '\n'.join(f'Fact {i+1}: {fact}' for i,fact in enumerate(facts))+
        '\n\nQuestion:\n'+question)

def trim_generated(ids,eos,cap):
    end=next((i+1 for i,t in enumerate(ids) if t in eos),len(ids))
    tokens=ids[:end]
    normal=bool(tokens and tokens[-1] in eos)
    return tokens,normal,len(tokens)>=cap and not normal
