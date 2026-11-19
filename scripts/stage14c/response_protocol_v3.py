"""Versioned terminal option-format support; source text only, never gold-aware."""
import re
from scripts.stage14c.response_protocol import extract as original_extract,repetition


def clean(text):
    text=re.sub(r'(?<!\w)\*\*(.+?)\*\*(?!\w)',r'\1',text)
    return re.sub(r'\s+',' ',text.replace('✅','').strip(' \n\t>#')).strip().rstrip('.').strip()


def option_texts(question):
    pieces=re.split(r'(?i)\b(?:Options|Choices)\s*:',question)
    if len(pieces)<2:return {}
    text=pieces[-1]
    matches=list(re.finditer(r'(?:^|[,\n])\s*(?:\(([A-D])\)|([A-D])\s*[:.)])\s*',text))
    if [m[1] or m[2] for m in matches]!=list('ABCD'):return {}
    return {(m[1] or m[2]):clean(text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)]) for i,m in enumerate(matches)}


def extract(raw,model,kind,finish_reason,question=''):
    old=original_extract(raw,model,kind,finish_reason)
    if old['status']!='NEEDS_RESPONSE_REVIEW' or kind!='choice':return old
    body=raw.rsplit('</think>',1)[-1].replace('<|im_end|>','').strip()
    lines=[clean(x) for x in body.splitlines() if clean(x)];last=lines[-1]
    # A sole terminal letter is the native requested response format.
    if re.fullmatch('[A-D]',last):
        return dict(answer=last,status='EXTRACTED',method='terminal_native_option_letter',committed=True,
                    needs_review=finish_reason=='length',reason='Literal last-line option label; no gold consulted')
    if len(lines)>1 and re.fullmatch(r'(?i)(?:final|correct)?\s*answer\s*:?',lines[-2]):
        last=lines[-2]+' '+last
    match=re.fullmatch(r'(?i)(?:the\s+)?(?:(?:final|correct|best)\s+)?(?:answer|option)(?:\s+is)?\s*:?\s*([A-D])(?:\s*[:.)-]\s*(.+))?',last)
    if not match:return old
    letter=match[1].upper();tail=match[2]
    if tail:
        options=option_texts(question)
        if letter not in options or clean(tail).casefold()!=options[letter].casefold():return old
    return dict(answer=letter,status='EXTRACTED',method='terminal_explicit_option_with_source_text_check',committed=True,
                needs_review=finish_reason=='length',reason='Explicit terminal answer marker; any following option text exactly matches that source option; no gold consulted')
