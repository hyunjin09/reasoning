"""Prospective technical and rescue gates; missingness is never a wrong answer."""
import math
from scripts.stage12c.common import ROOT, load


def technical_gate(rows):
    assert set(rows)==set('CT')
    n=len(rows['C']);assert n in [12,61] and len(rows['T'])==n
    summary={a:{k:sum(r[k] for r in rr) for k in ['INPUT_VALID','SCOREABLE','TRUNCATED_BEFORE_OUTCOME']} for a,rr in rows.items()}
    passed={a:s['INPUT_VALID']==n and s['SCOREABLE']>=math.ceil(n*10/12) and s['TRUNCATED_BEFORE_OUTCOME']<=math.floor(n/12) for a,s in summary.items()}
    return dict(n=n,summaries=summary,pass_by_arm=passed,**{'pass':all(passed.values())},
                rule='12/12 valid,>=10/12 scoreable,<=1/12 pre-outcome caps; rate-preserving full61 extension51/5; no repetition threshold')


def transition(c,t):
    if c is None or t is None:return 'UNSCOREABLE_TECHNICAL'
    if c and t:return 'BOTH_SUCCEED'
    if c:return 'C_ONLY'
    if t:return 'T_ONLY'
    return 'BOTH_FAIL'


def rescue_decision(rows,technical_pass):
    if not technical_pass:return 'TECHNICAL_STOP'
    selected=[r for r in rows if r['bottleneck'] in ['B1','B4']]
    five=any(sum(r[a] is True for r in selected if r['bottleneck']==b)>=5 for a in ['c','t'] for b in ['B1','B4'])
    four=sum(transition(r['c'],r['t'])=='T_ONLY' for r in selected)>=4
    return 'RESCUE_INFORMATIVE' if five or four else 'RESCUE_SPARSE'


def authorize_manifest(manifest,frozen=None,sanity_pass=None):
    if frozen is None:frozen=load(ROOT/'stage12c_frozen_bottleneck_manifest.json')
    assert manifest['frozen'] and manifest['phase'] in ['sanity','remaining']
    assert manifest['arm'] in 'CT' and manifest['config_sha256']==frozen['config_sha256']
    if manifest['phase']=='remaining':
        if sanity_pass is None:sanity_pass=load(ROOT/'stage12c_technical_sanity.json')['pass']
        assert sanity_pass, 'Remaining49 cannot run before both sanity arms pass'
    permitted=set(frozen[manifest['phase']+'_ids'])
    expected={t['task_id']:t for t in frozen['tasks']}
    assert 0<len(manifest['rows'])<=61
    assert len({t['task_id'] for t in manifest['rows']})==len(manifest['rows'])
    for t in manifest['rows']:
        assert t==expected.get(t['task_id']) and t['arm']==manifest['arm'] and t['item_id'] in permitted
