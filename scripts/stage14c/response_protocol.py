"""Conservative response-only extraction and technical repetition flags."""
import re
from scripts.stage14c.design_core import _canonical


def extract(raw,model,kind,finish_reason):
    if model=='T' and '</think>' not in raw:
        return dict(answer=None,status='UNSCORABLE',reason='No native thinking close',committed=False,needs_review=False)
    body=raw.rsplit('</think>',1)[-1].replace('<|im_end|>','').strip()
    if not body:return dict(answer=None,status='UNSCORABLE',reason='Empty final',committed=False,needs_review=False)
    def norm(x):return x.strip().strip('$*').strip().rstrip('.').strip()
    candidates=[]
    if _canonical(norm(body),kind,['A','B','C','D']) is not None:
        candidates.append((0,len(body),norm(body),'sole_final'))
    for pat,method in [(r'\\boxed\{([^{}]+)\}','boxed'),(r'\{([^{}\n]+)\}','native_braces'),
                       (r'(?im)(?:final answer|answer)\s*[:=]\s*([^\n]+)','explicit_final')]:
        for m in re.finditer(pat,body):
            a=norm(m[1])
            if _canonical(a,kind,['A','B','C','D']) is not None:candidates.append((m.start(),m.end(),a,method))
    if candidates:
        start,end,answer,method=max(candidates,key=lambda v:(v[1],v[0]))
        # A terminal source-format answer is safe; any subsequent prose is reviewed.
        tail=body[end:].strip(' \n\t.$*')
        if not tail:
            return dict(answer=answer,status='EXTRACTED',method=method,span=[start,end],committed=True,
                        needs_review=finish_reason=='length',reason='Terminal response-only commitment')
    return dict(answer=None,status='NEEDS_RESPONSE_REVIEW',reason='No unambiguous terminal source-format answer',committed=False,needs_review=True)


def repetition(tokens):
    n=len(tokens)
    for width in range(8,129):
        if n<max(1024,8*width):continue
        block=tokens[-width:];repeats=1
        while (repeats+1)*width<=n and tokens[n-(repeats+1)*width:n-repeats*width]==block:
            repeats+=1
        if repeats>=8 and repeats*width>=1024:
            return dict(flag=True,block_tokens=width,repeats=repeats,span=[n-repeats*width,n],manual_review_required=True)
    return dict(flag=False,manual_review_required=False)
