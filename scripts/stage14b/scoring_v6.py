"""Immutable second adjudications; retain original scoring code and all records.

Only explicit reviewed decisions create adjudications. This does not change the
grading criterion or perform outcome-dependent automatic corrections.
"""
import argparse
from scripts.stage14b.common import *
from scripts.stage14b import scoring

_original = scoring.final_score


def final_score(tid):
    previous = _original(tid)
    path = ROOT/'scoring/score_adjudications_v6'/f'{tid}.json'
    if not path.exists():
        return previous
    result = load(path)
    assert result['supersedes_sha256'] == fingerprint(previous), tid
    return result


def install():
    scoring.final_score = final_score
    # Existing packet helper may already be imported in a review process.
    from scripts.stage14b import review_v1
    review_v1.final_score = final_score


def commit_adjudication(packet_path, decision, mode, model):
    scoring.guard(mode, model)
    assert not (ROOT/'audit'/f'{mode}_{model}_scoring_seal.json').exists(), 'Arm already sealed'
    matches=[p for p in rows(packet_path) if p['task_id']==decision['task_id']]
    assert len(matches)==1
    p=matches[0];tid=p['task_id']
    assert p['model']==model and p['review_kind']!='extract'
    assert decision['reason'].strip()
    before=final_score(tid)
    assert fingerprint(before)==fingerprint(p['score'])
    label=decision['status'];correct={'CORRECT':True,'WRONG':False,'UNSCORABLE':None,'TECHNICAL_MISSING':None}[label]
    assert label!=before['status']
    save(ROOT/'scoring/score_adjudications_v6'/f'{tid}.json',dict(before,at=now(),
         correct=correct,status=label,grader='same_agent_semantic_adjudication_v6',
         supersedes_sha256=fingerprint(before),reason=decision['reason'],
         review_packet_sha256=fingerprint(p),review_packet_file=str(packet_path)))
    save(ROOT/'scoring/qc'/f'{tid}.json',dict(at=now(),task_id=tid,resolved=True,
         final_score_sha256=fingerprint(final_score(tid)),review_packet_sha256=fingerprint(p),
         review_packet_file=str(packet_path),reason=decision['reason'],
         scope='Same-agent arm-separated response-context adjudication; not independent human QC'))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('action',choices=['close','primary','secondary','confirmation'])
    p.add_argument('--mode',default='main');p.add_argument('--model',default='T')
    a=p.parse_args();install()
    if a.action=='close':
        scoring.close_arm(a.mode,a.model)
    else:
        from scripts.stage14b import analyze
        getattr(analyze,a.action)()

if __name__=='__main__':main()
