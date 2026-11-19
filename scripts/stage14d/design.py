"""Pure CPU Stage14D design safeguards. No inference or scheduler entry point."""
import hashlib
import json
from collections import Counter, defaultdict
import numpy as np

ARMS=('B0','THINK_MORE','LOOK_GENERIC','LOOK_TARGET','LOOK_IRRELEVANT')
TEMPLATES={
 'B0':'',
 'THINK_MORE':'Reconsider the solution. Check the reasoning and calculations for an error. Then continue solving the original problem.',
 'LOOK_GENERIC':'Re-examine the original image. Check its task-relevant visible details directly, without assuming details from earlier reasoning. Then continue solving the original problem.',
 'LOOK_TARGET':'Re-examine the original image. {request} Read this directly from the image; do not infer or assume its value from earlier reasoning. Then continue solving the original problem.',
 'LOOK_IRRELEVANT':'Re-examine the original image. {request} Read this directly from the image; do not infer or assume its value from earlier reasoning. Then continue solving the original problem.'}
WRAPPER='\n\n[Verification instruction]\n{directive}\n[Continue the original solution]\n'

def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def hash_order(seed,family):return hashlib.sha256((seed+'|'+family).encode()).hexdigest()
def classify(native,evidence):
    if native=='WRONG' and evidence=='CORRECT':return 'S1'
    if native=='WRONG' and evidence=='WRONG':return 'S2'
    if native=='CORRECT':return 'S3'
    return None

def features(row):
    return {'subject':str(row['subject']),'difficulty':str(row['difficulty']),
            'atoms':str(row['num_e_star_atoms']),
            'evidence_type':json.dumps(row['evidence_types'],sort_keys=True)}

def select_panel(rows,n,seed):
    """Exact format×structure quotas, marginal metadata balance, hash tie breaks."""
    if n>len(rows) or n<0:raise ValueError('Source shortfall; no substitution')
    identities=set();aliases=set()
    for row in rows:
        if row['family_id'] in identities:raise ValueError('Duplicate family')
        identities.add(row['family_id'])
        current=set(row['alias_member_item_ids'])
        if current & aliases:raise ValueError('Shared conservative source alias')
        aliases |= current
    cells=defaultdict(list)
    for row in rows:cells[str(row['answer_type'])+'|'+str(row['has_structured_atom'])].append(row)
    if not rows:return []
    exact={k:n*len(v)/len(rows) for k,v in cells.items()};quota={k:int(v) for k,v in exact.items()}
    for k in sorted(cells,key=lambda k:(-(exact[k]-quota[k]),hash_order(seed,k)))[:n-sum(quota.values())]:quota[k]+=1
    selected=[]
    for key,pool in sorted(cells.items()):
        ordered=sorted(pool,key=lambda r:hash_order(seed,r['family_id']));totals=Counter((k,v) for r in ordered for k,v in features(r).items());used=Counter()
        for step in range(quota[key]):
            def deficit(r):
                # Most underrepresented source metadata at the next selected size.
                return sum(((step+1)*totals[k,v]/len(pool)-used[k,v])/max(1,quota[key]*totals[k,v]/len(pool)) for k,v in features(r).items())
            chosen=min(ordered,key=lambda r:(-deficit(r),hash_order(seed,r['family_id'])))
            ordered.remove(chosen);selected.append(chosen);used.update(features(chosen).items())
    return sorted(selected,key=lambda r:hash_order(seed,r['family_id']))

def arm_order(rank):
    k=rank%len(ARMS);return list(ARMS[k:]+ARMS[:k])

def render_directive(arm,target):
    if arm not in ARMS:raise ValueError('Unknown arm')
    if arm=='B0':return ''
    if arm in ['LOOK_TARGET','LOOK_IRRELEVANT']:
        forbidden={'value','gold','answer','evidence','oracle_value','true_value'}
        if any(target.get(k) not in (None,'') for k in forbidden):raise ValueError('Evaluator value must not enter model input')
        if target.get('review_status')!='SOURCE_VALID_VALUE_FREE' or not target.get('source_request_sha256'):raise ValueError('Target is not source-reviewed and sealed')
        request=target.get('request','')
        if not request.strip():raise ValueError('Missing source-only request')
        if hashlib.sha256(request.encode()).hexdigest()!=target['source_request_sha256']:raise ValueError('Source request differs from sealed bytes')
        directive=TEMPLATES[arm].format(request=request)
    else:directive=TEMPLATES[arm]
    return WRAPPER.format(directive=directive)

def enforce_release(state):
    if not state.get('user_approved') or not isinstance(state.get('gpu_hours'),(int,float)) or state['gpu_hours']<=0:raise ValueError('Explicit numeric G0 approval required')
    if not(state.get('cv_closed') or state.get('cv_waiver_explicit')):raise ValueError('Stage14C-V closure or explicit waiver required')
    if not state.get('calibration_pass'):raise ValueError('Technical calibration gate required')
    if not all(state.get(k) for k in ['source_qc_sealed','anchors_sealed','scientific_manifest_sealed']):raise ValueError('G1/G2/G4 seals required')

def pair_effect(pairs,draws=10000,seed=20261011):
    """A minus B. All planned families contribute to missing-outcome bounds."""
    def value(x):
        if x in ['CORRECT','EXPLICIT_CORRECT']:return 1
        if x in ['WRONG','EXPLICIT_INCORRECT','PARTIAL_OR_APPROXIMATE','CONTRADICTORY','NOT_DEMONSTRATED']:return 0
        return None
    complete=[];lo=hi=0
    for a,b in pairs:
        a,b=value(a),value(b)
        if a is not None and b is not None:complete.append(a-b)
        lo+=(0 if a is None else a)-(1 if b is None else b)
        hi+=(1 if a is None else a)-(0 if b is None else b)
    n=len(pairs)
    if complete:
        x=np.array(complete,dtype=float);rng=np.random.default_rng(seed)
        means=np.mean(rng.choice(x,(draws,len(x)),replace=True),axis=1)
        estimate=float(x.mean());ci=np.quantile(means,[.025,.975]).tolist()
    else:estimate=ci=None
    return dict(planned_families=n,complete_pairs=len(complete),effect=estimate,ci95_unadjusted=ci,
                bounds=[lo/n,hi/n] if n else None,draws=draws,seed=seed)

def paired_exact_p(pairs):
    """Exact two-sided discordance test, excluding explicit missing endpoints."""
    import math
    one={'CORRECT','EXPLICIT_CORRECT'}
    zero={'WRONG','EXPLICIT_INCORRECT','PARTIAL_OR_APPROXIMATE','CONTRADICTORY','NOT_DEMONSTRATED'}
    b=c=n=0
    for a,z in pairs:
        if a not in one|zero or z not in one|zero:continue
        n+=1;b+=a in one and z in zero;c+=a in zero and z in one
    d=b+c
    p=min(1.,2*sum(math.comb(d,k) for k in range(min(b,c)+1))/(2**d)) if d else (1. if n else None)
    return dict(complete_pairs=n,target_only=b,control_only=c,p_two_sided=p)

def holm_two(pvalues):
    if set(pvalues)!={'P1','P2'}:raise ValueError('Frozen family is exactly P1/P2')
    if any(v is None for v in pvalues.values()):return {k:None for k in pvalues}
    order=sorted(pvalues,key=lambda k:(pvalues[k],k));result={};previous=0
    for i,k in enumerate(order):
        if not 0<=pvalues[k]<=1:raise ValueError('Invalid p value')
        previous=max(previous,min(1,(2-i)*pvalues[k]));result[k]=previous
    return result
