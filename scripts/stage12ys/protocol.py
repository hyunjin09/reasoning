"""Prospective Stage12Y-S family-level rules; technical missingness stays unknown."""
import hashlib

ARMS=('E_I','E_T','I_img','T_img','I_E','T_E')
CAPS={a:(81920 if a in ('E_T','T_img','T_E','RT_T') else 32768)
      for a in (*ARMS,'RT_T','RT_I','Q_I','SH_I')}

def order(role,family):
    return hashlib.sha256(f'stage12ys-v1|{role}|{family}'.encode()).hexdigest()

def seed(family,condition,replicate,phase):
    assert phase in 'ABC'
    domain={'A':'stage12ys-v1|screen|','B':'stage12ys-v1|','C':'stage12ys-v1|state-transfer|'}[phase]
    return int(hashlib.sha256(f'{domain}{family}|{condition}|{replicate}'.encode()).hexdigest(),16)%(2**31)

def majority(values,n):
    assert len(values)==n and n in (3,5)
    assert all(v is None or type(v) is bool for v in values)
    k=n//2+1;s=sum(v is True for v in values);m=values.count(None)
    return True if s>=k else False if s+m<k else None

def conjunction(*values):
    return False if False in values else None if None in values else True

def neg(x):return None if x is None else not x

def screen(r):
    linked=r['I_img'] is False and r['T_img'] is True
    weak=linked and r['I_E'] is True
    strong=weak and r['E_I'] is False and r['E_T'] is True
    down=r['I_E'] is False and r['T_E'] is True
    return dict(access_strong=strong,access_weak=weak,downstream=down,native_linked=linked,
        transition=None if not linked else 'A_COLLAPSE' if r['I_E'] is True else
        'B_PERSIST' if down else 'C_BOTH_FAIL' if r['I_E'] is False and r['T_E'] is False else 'D_UNRESOLVED')

def select_candidates(rows):
    strong=sorted([r for r in rows if r['access_strong']],key=lambda r:order('ACCESS_SCREEN_STRONG',r['family_id']))
    access=strong[:16]
    if len(strong)<8:
        weak=sorted([r for r in rows if r['access_weak'] and not r['access_strong']],key=lambda r:order('ACCESS_SCREEN_WEAK',r['family_id']))
        access+=weak[:16-len(access)]
    downstream=sorted([r for r in rows if r['downstream']],key=lambda r:(not r['native_linked'],order('DOWNSTREAM_SCREEN',r['family_id'])))[:16]
    return access,downstream

def support(r):
    access=conjunction(neg(r.get('I_img')),r.get('T_img'),r.get('I_E'),neg(r.get('E_I')),r.get('E_T'))
    downstream=conjunction(neg(r.get('I_E')),r.get('T_E'))
    return dict(access=access,downstream=downstream,native_linked_downstream=conjunction(downstream,neg(r.get('I_img')),r.get('T_img')))

def role_signals(access_n,access_yes,down_n,down_yes,c_entered,state_yes,c_resolved):
    a=access_n>=5 and access_yes>=3 and access_yes/access_n>=.6
    d=down_n>=5 and down_yes>=3 and down_yes/down_n>=.6
    s=c_entered>=3 and state_yes>=2 and c_resolved>0 and state_yes/c_resolved>=.6
    decision='MULTI_ROLE_THINKING_SIGNAL' if a and d else 'STATE_CONSTRUCTION_ROLE_SIGNAL' if s else 'VISUAL_ACCESS_ROLE_SIGNAL' if a else 'EQUAL_EVIDENCE_REASONING_SIGNAL' if d else 'ROLE_DECOMPOSITION_UNRESOLVED'
    return dict(access=a,downstream=d,state=s,multi_role=a and d,decision=decision)
