"""Stage12B-S authorization and prospective full-cohort operational rules."""
import math
from scripts.stage12bs.common import ROOT,load
from scripts.stage12br.protocol import validity


def authorize_manifest(manifest,frozen=None):
    if frozen is None:frozen=load(ROOT/'stage12bs_remaining_generation_manifest.json')
    assert manifest['frozen'] and manifest['phase']=='remaining'
    assert manifest['config_sha256']==frozen['config_sha256']
    expected={t['task_id']:t for t in frozen['tasks']}
    assert len(expected)==111
    rows=manifest['rows'];assert 0<len(rows)<=30 and len({r['task_id'] for r in rows})==len(rows)
    assert all(t==expected.get(t['task_id']) for t in rows),'Only exact111 new calls; never replace reused calls'


def full_gate(rows):
    assert set(rows)==set('ENO') and all(len(v)==61 for v in rows.values())
    summaries={a:{k:sum(r[k] for r in rr) for k in ['INPUT_VALID','SCOREABLE','TRUNCATED_BEFORE_OUTCOME']} for a,rr in rows.items()}
    passed={a:s['INPUT_VALID']==61 and s['SCOREABLE']>=51 and s['TRUNCATED_BEFORE_OUTCOME']<=5 for a,s in summaries.items()}
    return dict(summaries=summaries,pass_by_arm=passed,**{'pass':all(passed.values())},
                rule='Prospective rate-preserving extension of12-case gate:61valid,ceil(61*10/12)=51scoreable,floor(61/12)=5pre-outcome caps,per arm. No repetition threshold.')


def audit_selection(frozen_order,ambiguous_families):
    eligible=[f for f in frozen_order if f not in ambiguous_families]
    return eligible[:math.ceil(.2*len(eligible))]


def failure_type(labels):
    if labels['R1'] or labels['R2']:return 'LOOP_OR_REOPEN'
    if labels['R3']:return 'NONCONVERGENT'
    return 'WRONG_CONVERGED'


def persistence(native_types,oracle_types,oracle_valid):
    assert native_types
    if not oracle_valid:return 'UNSCOREABLE'
    if not oracle_types:return 'RESOLVED'
    return 'PERSISTED_SAME_TYPE' if native_types&oracle_types else 'PERSISTED_DIFFERENT_TYPE'
