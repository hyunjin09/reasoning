"""Freeze R3 completion result; no task accuracy or scientific launch."""
from scripts.stage11cr.common import ROOT,load,save,sha,now


def main():
    review=load(ROOT/'annotations/nonprimary40960_technical_review.json')
    assert review['frozen'] and review['gate']['status'] in ['PASS','STOP']
    save(ROOT/'stage11cr_nonprimary_validation.json',dict(at=now(),frozen=True,**{'pass':review['gate']['pass_gate']},
        gate=review['gate'],common_cap=40960,cap_source='Recovered historical common budget, approved plan section12',
        cases_sha256=sha(ROOT/'nonprimary_cases.json'),review_sha256=sha(ROOT/'annotations/nonprimary40960_technical_review.json'),
        repaired_protocol_sha256=sha(ROOT/'stage11cr_repaired_protocol.json'),
        n_calls=24,rows=review['rows'],accuracy_used=False,
        next_action='Rerun unchanged primary80 T/D only within remaining hard budget' if review['gate']['pass_gate'] else
                    'STOP before primary/oracle; close technical branch, no new protocol/cap/model/benchmark.'))
    print(review['gate'])


if __name__=='__main__':main()
