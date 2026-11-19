"""Prospective prompt and output contracts; no gold used for formatting."""
import re
from visual_reasoning.stage8b.scoring import safe_number

D_MC='Respond only with the correct option letter. Do not provide an explanation or intermediate reasoning.'
D_OPEN='Respond only with the final value or expression. Do not provide an explanation or intermediate reasoning.'
C_MC='Think step by step. End your response with Final answer: X, where X is the correct option letter.'
C_OPEN='Think step by step. End your response with Final answer: X, where X is the final value or expression.'

def build_prompt(row,arm):
    if arm=='E':
        requests='\n'.join(f'E{i}: {f["probe_request"]}' for i,f in enumerate(row['facts'],1))
        schema='\n'.join(f'E{i}: [value]' for i in range(1,len(row['facts'])+1))
        return ('Inspect the image and report only the requested visual facts.\n'
            'Do not solve the original problem.\nDo not explain or show reasoning.\n'
            f'Requested facts:\n{requests}\nReturn exactly:\n{schema}')
    assert arm in ['D','C']
    mc=row['answer_type']=='multiple_choice'
    suffix=(D_MC if mc else D_OPEN) if arm=='D' else (C_MC if mc else C_OPEN)
    return row['question']+'\n\nSolve the original problem.\n'+suffix

def unwrap(value):
    s=value.strip().strip('*').strip().rstrip('.').strip()
    if s.startswith('\\(') and s.endswith('\\)'):s=s[2:-2].strip()
    if s.startswith('\\[') and s.endswith('\\]'):s=s[2:-2].strip()
    s=s.strip('$').strip()
    if s.startswith('\\boxed{') and s.endswith('}'):s=s[7:-1].strip()
    return s

def parse_task(text,arm,answer_type):
    assert arm in ['D','C']
    candidate=text.strip();marker=False
    if arm=='C':
        matches=list(re.finditer(r'final\s+answer\s*:\s*',candidate,re.I))
        if not matches:return dict(answer=None,format_valid=False,has_final_marker=False)
        candidate=candidate[matches[-1].end():].strip();marker=True
    s=unwrap(candidate)
    if answer_type=='multiple_choice':
        matched=re.fullmatch(r'\(?([A-Ea-e])\)?',s)
        answer=matched.group(1).upper() if matched else None
    else:
        answer=s if '\n' not in s and '=' not in s and safe_number(s) is not None else None
    return dict(answer=answer,format_valid=answer is not None,has_final_marker=marker)

def parse_evidence(text,n_facts):
    lines=[x.strip() for x in text.strip().splitlines() if x.strip()]
    values={};valid=len(lines)==n_facts
    for line in lines:
        match=re.fullmatch(r'E([1-4]):\s*(.+)',line)
        if not match:valid=False;continue
        k=int(match.group(1));v=match.group(2).strip()
        if k in values or not 1<=k<=n_facts or v.lower() in ['[value]','[value/expression]']:valid=False
        values[k]=v
    valid=valid and set(values)==set(range(1,n_facts+1))
    return dict(format_valid=bool(valid),values={str(k):v for k,v in values.items()})

def technical_gate(rows):
    assert set(rows)==set('EDC') and all(len(rows[a])==12 for a in rows)
    s={a:dict(n=12,format_valid=sum(r['format_valid'] for r in rr),
        severe_reasoning=sum(r['severe_reasoning'] for r in rr),
        intermediate_reasoning=sum(r['intermediate_reasoning'] for r in rr),
        repetitions=sum(r['repetition_pathology'] for r in rr),
        committed_finals=sum(r['committed_final'] for r in rr),caps=sum(r['cap_hit'] for r in rr)) for a,rr in rows.items()}
    e=s['E'];d=s['D'];c=s['C']
    passed=dict(E=e['format_valid']>=10 and e['severe_reasoning']<=1,
        D=d['format_valid']>=10 and d['intermediate_reasoning']<=1 and d['repetitions']==0,
        C=c['committed_finals']>=10 and c['caps']<=2 and c['repetitions']<=1)
    return dict(pass_by_arm=passed,**{'pass':all(passed.values())},summaries=s)

def phenotype(e,d,c):
    return dict(L=e and not d,F1=not e and not d,F2=e and not d,
        F3=e and not d and c,F4=e and not d and not c)
