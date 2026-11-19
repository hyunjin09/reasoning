"""After recovery, prepare response-only review; never launch C or grade golds."""
from scripts.stage14cv.common import *
from scripts.stage14cv.r_scoring import extract_available, freeze_raw, review_packet


def main():
    for p,h in load(ROOT/'audit/analysis_adapter_seal_v1.json')['files'].items():assert sha(p)==h,p
    completed=sum(checked(t) is not None for t in tasks('R'))
    if completed!=1800:
        save(ROOT/'audit/R_post_recovery_hold_v1.json',dict(at=now(),completed=completed,
             reason='Recovery checkpoint/incomplete: inspect before resubmission.',C_launched=False))
        return
    extract_available()
    freeze_raw()
    review_packet(ROOT/'scoring/R_review_packet_v2.json')
    save(ROOT/'audit/R_ready_for_final_response_review_v1.json',dict(at=now(),completed=1800,
         gold_scoring_performed=False,C_launched=False))


if __name__=='__main__':main()
