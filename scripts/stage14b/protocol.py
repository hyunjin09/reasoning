"""Prospective Stage14B inputs and conservative answer-only grading adapter."""
import hashlib
import re
from visual_reasoning.stage8b.v2_scoring import extract_answer, equivalent

VERSIONS=('Text Dominant','Text Lite','Text Only','Vision Intensive','Vision Dominant','Vision Only')
CLEAN_FIELDS=('same_task','gold_consistency','text_only_sufficient','visual_versions_sufficient','answer_safe')

def native_prompt(row):
    return row['question']+('' if not row['options'] else '\n\nOptions:\n'+'\n'.join(f'{chr(65+i)}. {v}' for i,v in enumerate(row['options'])))

def clean_verse(row):
    return all(row['consistency_checks'][k]=='PASS' for k in CLEAN_FIELDS)

def seed(identity,replicate):
    return int(hashlib.sha256(f'stage14b-v1|{identity}|r{replicate}'.encode()).hexdigest(),16)%(2**31)

def extract(raw,options,model,finish_reason):
    """No gold access; cap-before-final and unsupported prose go to review."""
    result=dict(answer=None,status='NEEDS_RESPONSE_REVIEW',method=None)
    if model=='T' and '</think>' not in raw:
        return dict(result,status='UNSCORABLE_NO_THINK_CLOSE')
    body=raw.rsplit('</think>',1)[-1].replace('<|im_end|>','').strip()
    if not body:return dict(result,status='UNSCORABLE_EMPTY_FINAL')
    # Explicit terminal commitment outranks incidental option letters in reasoning.
    explicit=extract_answer(body,[])
    if explicit['extracted'] is not None:
        value=explicit['extracted'].strip()
        if options:
            match=re.fullmatch(r'\s*\(?([A-Z])\)?[.\s]*',value)
            if match:value=match[1]
        if finish_reason=='length':
            # Keep only a completed final with no subsequent reasoning at the boundary.
            span=explicit['span'];tail=body[span[1]:].strip('}$. \n\t')
            if tail:return dict(result,status='NEEDS_CAP_COMMITMENT_REVIEW')
        return dict(answer=value,status='EXTRACTED',method=explicit['method'])
    # Whole final must be a sole letter or option text; no early incidental matches.
    if options:
        plain=body.strip('().*$ \n')
        letters=[chr(65+i) for i in range(len(options))]
        if plain in letters:return dict(answer=plain,status='EXTRACTED',method='sole_option_letter')
        matches=[letters[i] for i,v in enumerate(options) if plain.casefold()==str(v).strip().casefold()]
        if len(matches)==1:return dict(answer=matches[0],status='EXTRACTED',method='sole_option_text')
    return result

def grade(answer,row):
    result=dict(correct=None,status='UNSCORABLE',grader='inherited_exact_or_bounded_numeric_1e-6')
    if answer is None:return result
    if answer=='__NO_ANSWER__':return dict(result,correct=False,status='WRONG')
    if row['options']:
        letters=[chr(65+i) for i in range(len(row['options']))]
        if answer in letters:correct=answer==row['gold_answer']
        else:
            matches=[letters[i] for i,v in enumerate(row['options']) if equivalent(answer,v) is True]
            correct=matches[0]==row['gold_answer'] if len(matches)==1 else None
    else:correct=equivalent(answer,row['gold_answer'])
    return dict(result,correct=correct,status='CORRECT' if correct is True else 'WRONG' if correct is False else 'NEEDS_EQUIVALENCE_REVIEW')

def verse_options(row,reference):
    if row['answer_type']!='multi-choice':return []
    pattern=r'(?:^|\n)\s*[A-Z]\s*[:.]\s*(.*?)(?=\n\s*[A-Z]\s*[:.]|\Z)'
    own=re.findall(pattern,row['question'],re.S)
    return [v.strip() for v in (own or re.findall(pattern,reference['question'],re.S))]
