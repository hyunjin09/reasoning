"""Prospective segmentation, replay identity and conservative transition rules."""
import hashlib
import math
import re
from scripts.stage12vs.common import ROOT,load,sha
from scripts.stage12us.protocol import render,majority


def seed(family,phase,step,replicate):
    return int(hashlib.sha256(f'stage12vs-v1|{family}|{phase}|{step}|{replicate}'.encode()).hexdigest(),16)%(2**31)


def segment(text):
    protected=[]
    for pattern in [r'\\\[.*?\\\]',r'\$\$.*?\$\$',r'```.*?```']:
        protected.extend((m.start(),m.end()) for m in re.finditer(pattern,text,re.S))
    boundaries=[0]+[m.end() for m in re.finditer(r'\n[ \t]*\n+',text)
                     if not any(a<m.start()<b for a,b in protected)]+[len(text)]
    out=[]
    for a,b in zip(boundaries,boundaries[1:]):
        if a==b:continue
        cuts=[a]
        if b-a>600:
            cuts.extend(a+m.end() for m in re.finditer(r'(?<=[.!?]) +(?=[A-Z])',text[a:b])
                        if not any(x<a+m.start()<y for x,y in protected))
        cuts.append(b)
        out.extend(text[x:y] for x,y in zip(cuts,cuts[1:]) if x<y)
    assert ''.join(out)==text
    return out


def anchors(n):return sorted({int(math.floor(n*f/5+.5)) for f in range(6)})


def localization(observed):
    rows=sorted(observed.items());known=[(k,v) for k,v in rows if v is not None]
    bits=[v for k,v in known]
    if any(bits[i] is True and bits[i+1] is False for i in range(len(bits)-1)):
        return dict(status='NONMONOTONIC_PORTABILITY')
    for i,(b,v) in enumerate(rows):
        if v is not True or i==0:continue
        a,previous=rows[i-1]
        if previous is None:return dict(status='MISSING_BOUNDARY',a=a,b=b)
        if previous is False:
            if b-a>1:return dict(status='BISECT',a=a,b=b,next=(a+b)//2)
            return dict(status='STABLE' if any(k>b and w is True for k,w in rows) else 'NO_LATER_SUPPORT',a=a,b=b)
    return dict(status='NO_TRANSITION')


def authorize(manifest):
    expected={t['task_id']:t for t in load(ROOT/'audit'/f"{manifest['phase']}_execution.json")['tasks']}
    assert manifest['frozen'] and manifest['config_sha256']==sha(ROOT/'config.json')
    assert len({t['task_id'] for t in manifest['rows']})==len(manifest['rows'])
    assert all(t==expected.get(t['task_id']) for t in manifest['rows'])
    for p,h in load(ROOT/'audit/source_seal.json')['hashes'].items():assert sha(p)==h,p
    if manifest['phase']!='phaseA':assert load(ROOT/'audit/replication_gate.json')['continue']
