"""Frozen missing-call authorization and scientific decision thresholds."""
from scripts.stage12ts.common import ROOT,load

def authorize_manifest(m,frozen=None):
    frozen=load(ROOT/'stage12ts_remaining37_manifest.json') if frozen is None else frozen
    assert m['frozen'] and m['phase']=='remaining' and m['arm']=='T'
    assert m['config_sha256']==frozen['config_sha256']
    expected={t['task_id']:t for t in frozen['rows']}
    assert 0<len(m['rows'])<=37 and len({t['task_id'] for t in m['rows']})==len(m['rows'])
    for t in m['rows']:
        assert t==expected.get(t['task_id']) and t['arm']=='T' and t['cap']==81920

def scientific_decision(b1,b4,t_only,evidence_linked,technical_pass=True):
    assert 0<=evidence_linked<=t_only<=b1
    if not technical_pass:return ['THINKING_TECHNICAL_BREAKDOWN']
    states=[]
    if b1>=5:
        states.append('THINKING_VISUAL_RECOVERY_SIGNAL' if t_only>=3 and evidence_linked>=3
                      else 'THINKING_RESCUE_WITHOUT_CLEAR_EVIDENCE_LINK')
    if b4>=5:states.append('THINKING_DOWNSTREAM_SIGNAL')
    return states or ['THINKING_RESCUE_SPARSE']
