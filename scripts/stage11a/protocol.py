"""Frozen descriptive predicates; ambiguity is preserved, never forced."""
import hashlib
from collections import defaultdict
from scripts.stage11a.common import SEED

def order(value):
    return hashlib.sha256((f'stage11a:{SEED}:'+str(value)).encode()).hexdigest()

def probe_state(labels):
    assert 1<=len(labels)<=4 and set(labels)<= {'CORRECT','WRONG','MISSING','AMBIGUOUS'}
    n=labels.count('CORRECT')
    return 'PROBE_ACCESSIBLE' if n==len(labels) else 'PROBE_PARTIAL' if n else 'PROBE_INACCESSIBLE'

def profile(probe,native,final):
    assert native in ['N0','N1','N2','N3','N4','N5']
    assert final in ['FINAL_CORRECT','FINAL_WRONG','NO_VALID_FINAL']
    failed=final!='FINAL_CORRECT';flags=[]
    if failed and probe in ['PROBE_PARTIAL','PROBE_INACCESSIBLE']:flags.append('P1')
    if failed and probe=='PROBE_ACCESSIBLE' and native in ['N0','N1','N3','N4']:flags.append('P2')
    if failed and native=='N2':flags.append('P3')
    if not failed and native=='N2':flags.append('P4')
    return (flags[0] if len(flags)==1 else 'P5'),flags

def localization(success,failed):
    assert success['final']=='FINAL_CORRECT' and failed['final']!='FINAL_CORRECT'
    flags=[]
    if success['probe']=='PROBE_ACCESSIBLE' and failed['probe'] in ['PROBE_PARTIAL','PROBE_INACCESSIBLE']:flags.append('A')
    if success['probe']==failed['probe']=='PROBE_ACCESSIBLE' and success['native']=='N2' and failed['native'] in ['N0','N1','N3','N4']:flags.append('B')
    if success['native']==failed['native']=='N2':flags.append('C')
    return (flags[0] if len(flags)==1 else 'D'),flags

def select_probes(rows,n=64):
    assert len({r['item_id'] for r in rows})==len(rows)
    if len(rows)<=n:return sorted((r['item_id'] for r in rows),key=order)
    groups=defaultdict(list)
    for r in rows:groups[(r['subject'],r['evidence_type'])].append(r['item_id'])
    quota={k:n*len(v)//len(rows) for k,v in groups.items()}
    fractions=sorted(groups,key=lambda k:(-(n*len(groups[k])%len(rows)),order(k)))
    for k in fractions[:n-sum(quota.values())]:quota[k]+=1
    chosen=[x for k,v in groups.items() for x in sorted(v,key=order)[:quota[k]]]
    assert len(chosen)==n
    return sorted(chosen,key=order)

def feasibility(eligible,discordant,informative,categories,kappa,mixed):
    if eligible<32 or informative<8 or kappa is None or kappa<.6 or mixed>.75:return 'NO_GO'
    if eligible>=48 and discordant>=16 and sum(n>=8 for n in categories)>=2:return 'STRONG_GO'
    return 'LIMITED_GO'
