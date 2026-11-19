"""Score available finals and audit against manual review without changing labels."""
import hashlib
import json
from collections import Counter
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write
from visual_reasoning.stage6a.answers import score_condition_answer


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    index=load(OUT/'traces/controlled_native_index.jsonl')
    originals={r['base_id']:r['answer'] for r in load(OUT/'cohort/c1_primary_v2_manifest.jsonl') if r['condition']=='intact'}
    reviews={r['event_id']:r for path in [OUT/'c1_diagram_stress/intact_local_claim_review.jsonl',OUT/'traces/controlled_manual_reviews.jsonl'] if path.exists() for r in load(path)}
    output=[];checks=[]
    for row in index:
        if row['cohort']=='C1':row={**row,'source_answer':originals[row['base_id']]}
        score=score_condition_answer(row)
        output.append(dict(event_id=row['event_id'],base_id=row['base_id'],cohort=row['cohort'],condition=row['condition'],
            raw_generation_artifact=row['generation_artifact'],**score))
        review=reviews.get(row['event_id'])
        if review:
            automatic=score['final_answer_correctness'];manual=review['final_answer_correctness']
            disagreement=automatic in ['CORRECT','INCORRECT'] and manual in ['CORRECT','INCORRECT'] and automatic!=manual
            checks.append(dict(event_id=row['event_id'],cohort=row['cohort'],manual_label=manual,
                manual_readout=review['final_readout'],automatic_label=automatic,automatic_readout=score['final_readout'],
                resolved_disagreement=disagreement,manual_review_preserved=True))
    diagnostic=dict(status='PASS' if not any(r['resolved_disagreement'] for r in checks) else 'FAIL_RESOLVED_DISAGREEMENT',
        reviewed_events=len(checks),resolved_agreement=sum(r['automatic_label']==r['manual_label'] for r in checks),
        unresolved_automatic=sum(r['automatic_label']=='UNRESOLVED' for r in checks),
        checks=checks,scorer_code_sha256=hashlib.sha256((OUT.parents[1]/'code/visual_reasoning/stage6a/answers.py').read_bytes()).hexdigest(),
        note='Manual reviews remain authoritative; this is format/label validation, not independent evidence of parser generalization.')
    (OUT/'audit/final_scorer_manual_comparison.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
    assert diagnostic['status']=='PASS','Review the saved resolved disagreement before exporting automatic scores'
    write(OUT/'traces/controlled_automatic_final_reviews.jsonl',output)
    print(json.dumps(dict(events=len(output),manual_validation=diagnostic['status'],
        final_labels=dict(Counter(r['final_answer_correctness'] for r in output)),
        source_consistency=dict(Counter(r['source_answer_consistency'] for r in output))),indent=2))


if __name__=='__main__':main()
