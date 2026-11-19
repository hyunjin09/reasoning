"""Independent scientific and completion branches; frozen selection and gates."""
import hashlib
from scripts.stage12cr.common import ROOT,load

def select_fresh(rows,exclude):
    pool=sorted((r for r in rows if r['item_id'] not in set(exclude)),
        key=lambda r:(hashlib.sha256(('stage12tr-fresh-validation-v1|'+r['family_id']).encode()).hexdigest(),r['family_id']))
    mc=[r for r in pool if r['answer_type']=='multiple_choice'][:5]
    oe=[r for r in pool if r['answer_type']!='multiple_choice'][:7]
    selected={r['item_id'] for r in mc+oe}
    for r in pool:
        if len(selected)==12:break
        selected.add(r['item_id'])
    assert len(selected)==12
    return [r['item_id'] for r in pool if r['item_id'] in selected]

def thinking_gate(rows,phase):
    assert phase in ['same12','fresh12'] and len(rows)==12
    counts={k:sum(r[k] for r in rows) for k in ['INPUT_VALID','SCOREABLE','TRUNCATED_BEFORE_OUTCOME']}
    passed=counts['INPUT_VALID']==12 and counts['SCOREABLE']>=(11 if phase=='same12' else 10) and counts['TRUNCATED_BEFORE_OUTCOME']<=1
    decision=('CAP_EXTENSION_PROMISING' if passed else 'THINKING_COMPLETION_UNSTABLE') if phase=='same12' else ('THINKING_REGIME_VALIDATED' if passed else 'THINKING_REGIME_UNSTABLE')
    return dict(phase=phase,counts=counts,decision=decision,**{'pass':passed})

def authorize_manifest(m,frozen=None,phase1_pass=None):
    if frozen is None:frozen=load(ROOT/'audit/execution_manifest.json')
    assert m['frozen'] and m['phase'] in ['cot','same12','fresh12']
    assert m['config_sha256']==frozen['config_sha256']
    assert m['arm']==('C' if m['phase']=='cot' else 'T')
    if m['phase']=='fresh12':
        if phase1_pass is None:phase1_pass=load(ROOT/'stage12tr_same12_decision.json')['pass']
        assert phase1_pass,'Fresh Thinking requires the frozen same12 completion gate'
    permitted=set(frozen[m['phase']+'_ids']);expected={t['task_id']:t for t in frozen['tasks']}
    assert 0<len(m['rows'])<=49 and len({t['task_id'] for t in m['rows']})==len(m['rows'])
    for t in m['rows']:
        assert t==expected.get(t['task_id']) and t['arm']==m['arm'] and t['item_id'] in permitted
