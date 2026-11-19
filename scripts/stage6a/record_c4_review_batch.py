"""Join explicit manual image/assertion decisions to immutable claim IDs."""
import argparse
import json
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write


def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',required=True);a=p.parse_args();assert a.batch.isidentifier()
    packet=json.loads((OUT/f'review/c4_{a.batch}.json').read_text())
    decisions=json.loads((OUT/f'review/c4_{a.batch}_decisions.json').read_text())
    path=OUT/'c4_natural_failure/c4_claim_reviews.jsonl'
    rows=[json.loads(s) for s in path.read_text().splitlines()] if path.exists() else []
    existing={r['claim_id'] for r in rows};added=[]
    statuses={'not_object_claim','nonasserted','visually_supported','hallucination','unresolved_image'}
    for row in packet:
        if row['base_id'] not in decisions:continue
        for claim in row['candidates']:
            if claim['claim_id'] in existing:continue
            base_decision=decisions[row['base_id']]
            decision=base_decision.get('claims',{}).get(claim['claim_id'],base_decision.get(claim['category']))
            if decision is None:continue
            status,reason=decision
            assert status in statuses and reason
            added.append(dict(claim_id=claim['claim_id'],base_id=row['base_id'],category=claim['category'],
                review_status=status,reason=reason,canonical_category_override=None,
                image_review='Source image inspected and candidate assertion contexts read.',
                evidence_packet=f'review/c4_{a.batch}.json',decision_file=f'review/c4_{a.batch}_decisions.json',
                attention_or_causal_data_used=False))
    write(path,rows+added);print('Saved',len(added),'explicit claim reviews')


if __name__=='__main__':main()
