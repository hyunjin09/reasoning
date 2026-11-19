"""Finite CPU handoff after all confirmation workers terminate; no launches.

Validate every expected call, then perform only gold-blind Instruct extraction.
Any unresolved/missing call holds; no inference, manual-QC claims, or follow-on.
"""
from collections import Counter
from scripts.stage14b.common import *
from scripts.stage14b.scoring import raw_freeze, extract_arm, final_extraction
from scripts.stage14b.presentation_v2 import apply
from scripts.stage14b.review_v1 import inventory, packet


def main():
    seal=load(ROOT/'audit/confirmation_postprocess_seal_v1.json')
    for path,digest in seal['files'].items():assert sha(path)==digest,path
    assert (ROOT/'audit/secondary_analysis_seal.json').exists()
    assert len(all_tasks('confirmatory'))==9600
    if not (ROOT/'audit/confirmatory_raw_seal.json').exists():raw_freeze('confirmatory')
    extract_arm('confirmatory','I')
    if not (ROOT/'audit/confirmatory_I_presentation_repair_v2.json').exists():apply('confirmatory','I')
    pending=inventory('confirmatory','I','extract')
    packet_path=ROOT/'scoring/review_packets/confirmation_I_extraction_pending_v1.jsonl'
    if not packet_path.exists():write_rows(packet_path,[packet(t,'extract',2200) for t in pending])
    counts=Counter(final_extraction(t['task_id'])['status'] for t in all_tasks('confirmatory') if t['model_key']=='I')
    save(ROOT/'audit/confirmation_extraction_handoff_v1.json',dict(at=now(),status='RESPONSE_REVIEW_REQUIRED',
         raw_calls_validated=9600,instruct_extraction_counts=dict(counts),pending_review=len(pending),
         packet_file=str(packet_path),packet_sha256=sha(packet_path),correctness_used=False,
         thinking_extraction_opened=False,gpu_or_follow_on_launches=0,manual_review_claimed=False))
    print('Validated confirmation raws; Instruct gold-blind extraction ready for review.',dict(counts))

if __name__=='__main__':main()
