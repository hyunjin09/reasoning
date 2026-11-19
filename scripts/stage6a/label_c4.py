"""Join raw claims with explicit image review; retain unknown and missing data."""
import argparse
import json
from collections import defaultdict, Counter
from datetime import datetime, timezone
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write
from visual_reasoning.stage6a.labels import aggregate_object_label


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--allow-partial',action='store_true');args=parser.parse_args()
    dest=OUT/'c4_natural_failure'
    generations=load(dest/'generations.jsonl');claims=load(dest/'object_claims.jsonl')
    reviews={r['claim_id']:r for r in load(dest/'c4_claim_reviews.jsonl')}
    groups=defaultdict(list);adjudicated=[]
    for claim in claims:
        review=reviews.get(claim['claim_id'])
        status=review['review_status'] if review else claim['label']
        # The first immutable review packet used these earlier names. Its eight
        # uncertain records explicitly concern hedged assertion wording.
        status={'supported':'visually_supported','uncertain':'nonasserted'}.get(status,status)
        row={**claim,'adjudicated_label':status,'manual_review':review,
             'support_scope':'COCO80 presence under frozen normalization; reference support does not prove every attribute, relation or count'}
        adjudicated.append(row);groups[claim['base_id']].append(row)
    labels=[]
    for generation in generations:
        base=generation['base_id'];rows=groups[base]
        all_label=aggregate_object_label([r['adjudicated_label'] for r in rows],generation['complete'])
        final_label=aggregate_object_label([r['adjudicated_label'] for r in rows if r['section']=='final'],generation['complete'])
        labels.append(dict(base_id=base,event_id=generation['event_id'],image_id=generation['image_id'],
            cohort='C4',complete_native_trace=generation['complete'],
            object_hallucination_presence=all_label,final_caption_object_hallucination=final_label,
            confirmed_hallucination_claim_ids=[r['claim_id'] for r in rows if r['adjudicated_label']=='hallucination'],
            unresolved_claim_ids=[r['claim_id'] for r in rows if r['adjudicated_label'] in ('unresolved_image','pending_image_review')],
            assertion_context_reviewed=any(r['manual_review'] for r in rows),
            non_object_error_labels='not exhaustively annotated; explicit attribute errors retained in manual review reasons',
            metric_scope='Frozen COCO80 conservative presence normalization, full thinking plus final; final-caption scope separate',
            attention_or_causal_data_used=False))
    planned=[]
    for name in ['c4_primary','c4_extension']:
        path=OUT/f'cohort/{name}_manifest.jsonl'
        if path.exists():planned.extend(load(path))
    counts=Counter(r['object_hallucination_presence'] for r in labels)
    pending=sum(r['adjudicated_label']=='pending_image_review' for r in adjudicated)
    missing=len(planned)-len(generations)
    if (pending or missing) and not args.allow_partial:raise RuntimeError(f'{pending} claims and {missing} generations pending')
    total=len(planned);confirmed=counts['hallucination'];unknown=counts['UNRESOLVED']+missing
    report=dict(status='PROVISIONAL' if pending or missing else 'COMPLETE_ANNOTATION_WITH_EXPLICIT_UNRESOLVED',
        created_at=datetime.now(timezone.utc).isoformat(),planned_images=total,completed_generation_records=len(generations),
        missing_generation_records=missing,complete_native_traces=sum(g['complete'] for g in generations),
        pending_claim_reviews=pending,whole_trace_label_counts=dict(counts),
        final_caption_label_counts=dict(Counter(r['final_caption_object_hallucination'] for r in labels)),
        confirmed_positive_fraction=confirmed/total if total else None,
        annotation_protocol_uncertainty_interval=[confirmed/total,(confirmed+unknown)/total] if total else None,
        interval_meaning='Identification range from unresolved/missing cases under this lexicon and reference-support protocol; not a statistical confidence interval or universal upper bound on all hallucinations.',
        unbiased_sample='All prospectively ordered initial600 and, if activated, next400 retained regardless of outcomes.',
        selection_of_case_control_atlas_used_for_prevalence=False,
        limitations=['Reference-supported category presence is not an exhaustive manual check of every claim.',
          'Frozen vocabulary can miss non-COCO objects; object counts, attributes, relations and nonvisual reasoning errors are separate.',
          'No-detected label denotes this conservative metric, not proof of a completely error-free caption.',
          'Generic phone, van, table and monitor aliases are contextually adjudicated; this is CHAIR-compatible normalization, not an unmodified official CHAIR score.'])
    write(dest/'adjudicated_object_claims.jsonl',adjudicated);write(dest/'hallucination_labels.jsonl',labels)
    (dest/'unbiased_prevalence.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','planned_images','completed_generation_records','missing_generation_records','pending_claim_reviews','whole_trace_label_counts','final_caption_label_counts']},indent=2))


if __name__=='__main__':main()
