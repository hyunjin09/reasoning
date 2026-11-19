"""Preserve v3 extraction, but send destructive-format normalization to review."""
import re
from scripts.stage14c.response_protocol_v3 import extract as previous,repetition
from scripts.stage14c.design_core import _canonical


def unwrap(text):
    text=text.strip()
    if text.endswith('.'):text=text[:-1].strip()
    changed=True
    while changed:
        changed=False
        for mark in ['**','$$','*','$']:
            if len(text)>2*len(mark) and text.startswith(mark) and text.endswith(mark):
                text=text[len(mark):-len(mark)].strip();changed=True;break
    return text


def extract(raw,model,kind,finish_reason,question=''):
    value=previous(raw,model,kind,finish_reason,question)
    if value['status']!='EXTRACTED' or 'span' not in value:return value
    body=raw.rsplit('</think>',1)[-1].replace('<|im_end|>','').strip()
    start,end=value['span'];component=body[start:end];method=value['method']
    if method=='native_braces':component=component[1:-1]
    elif method=='boxed':component=component[len('\\boxed{'):-1]
    elif method=='explicit_final':component=re.split(r'[:=]',component,maxsplit=1)[1]
    candidate=_canonical(unwrap(component),kind,['A','B','C','D'])
    expected=_canonical(value['answer'],kind,['A','B','C','D'])
    tail=body[end:].strip();safe_tail=tail in {'','.'}
    if not safe_tail:
        last=body.splitlines()[-1].strip()
        if last.endswith('.'):last=last[:-1].strip()
        clean_tail=tail[:-1].strip() if tail.endswith('.') else tail
        # Only a paired terminal Markdown/math enclosure can explain these
        # trailing symbols. Any unclear inline form remains semantic review.
        safe_tail=clean_tail in {'**','$$','*','$'} and last.startswith(clean_tail) and last.endswith(clean_tail)
    if candidate!=expected or candidate is None or not safe_tail:
        return dict(answer=None,status='NEEDS_RESPONSE_REVIEW',committed=False,needs_review=True,
             reason='Legacy formatter removed unbalanced syntax/operator characters; no automatic value interpretation',
             previous_candidate=value)
    return value
