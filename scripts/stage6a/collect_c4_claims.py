"""Parse frozen native C4 outputs and queue annotation-absent claims for review.

No image membership changes; annotation absence is only a review candidate.
The fixed lexicon defines coverage of the COCO80 object-presence metric.
"""
import bisect
import json
from collections import defaultdict
from pathlib import Path
from scripts.stage6a.inventory import OUT, allowed
from scripts.stage6a.prepare_candidates import write
from visual_reasoning.stage6a.objects import extract_object_claims
from visual_reasoning.stage6a.segmentation import segment_native


def main():
    ontology=json.loads((OUT/'config/object_synonyms.json').read_text())
    aliases=ontology['aliases']
    inventory=json.loads((OUT/'cohort/dataset_inventory.json').read_text())
    coco=next(row for row in inventory['datasets'] if row['dataset']=='COCO2014')
    instance_path=allowed(Path(coco['instance_annotations']))
    caption_path=allowed(Path(coco['caption_annotations']))
    instances=json.loads(instance_path.read_text());captions=json.loads(caption_path.read_text())
    cats={r['id']:r['name'] for r in instances['categories']}
    anns=defaultdict(list);refs=defaultdict(list)
    for row in instances['annotations']:anns[row['image_id']].append(row)
    for row in captions['annotations']:refs[row['image_id']].append(row['caption'])
    manifests=[]
    for name in ['c4_primary','c4_extension']:
        path=OUT/f'cohort/{name}_manifest.jsonl'
        if path.exists():manifests.extend(json.loads(s) for s in path.read_text().splitlines())
    by_id={r['event_id']:r for r in manifests}
    paths=[]
    for name in ['c4_primary','c4_extension']:
        paths.extend((OUT/f'native/{name}').glob('shard_*/examples/*/result.json'))
    generations=[];all_claims=[];review=[];span_rows=[];inventories=[]
    for path in sorted(paths):
        result=json.loads(path.read_text());eid=result['event_id'];row=by_id[eid];iid=row['image_id']
        generation=json.loads((path.parent/'generation.json').read_text())
        tokens=[json.loads(s) for s in (path.parent/'tokens.jsonl').read_text().splitlines()]
        raw=generation['raw_decoded_response'];assert raw==''.join(t['decoded_token'] for t in tokens)
        offsets=[0]
        for token in tokens:offsets.append(offsets[-1]+len(token['decoded_token']))
        spans=segment_native(tokens)
        span_rows.extend(dict(event_id=eid,base_id=row['base_id'],cohort='C4',**s) for s in spans)
        instance_cats={cats[a['category_id']] for a in anns[iid]}
        reference_cats={c['category'] for ref in refs[iid] for c in extract_object_claims(ref,aliases)}
        inventory=instance_cats|reference_cats
        inventories.append(dict(base_id=row['base_id'],image_id=iid,instance_categories=sorted(instance_cats),
            reference_caption_categories=sorted(reference_cats),reference_captions=refs[iid],
            category_union=sorted(inventory),instance_count=len(anns[iid]),source_annotations=[str(instance_path),str(caption_path)]))
        marker=raw.find('</think>');candidates=[]
        claims=extract_object_claims(raw,aliases)
        for i,claim in enumerate(claims):
            a,b=claim['char_start'],claim['char_end'];left=max(0,bisect.bisect_right(offsets,a)-1)
            right=bisect.bisect_left(offsets,b)
            assert offsets[left]<=a<b<=offsets[right]
            span=next((s for s in spans if s['char_start']<=a<s['char_end']),None)
            assertion=claim['assertion'];present=claim['category'] in inventory
            item=dict(event_id=eid,base_id=row['base_id'],claim_id=f'{eid}__O{i:04}',**claim,
                section='final' if marker>=0 and a>marker else 'reasoning',
                token_start=left,token_end=right,native_token_ids=[t['token_id'] for t in tokens[left:right]],
                span_id=span['span_id'] if span else None,span_text=span['text'] if span else raw[max(0,a-160):b+160],
                category_in_reference_inventory=present,
                label='reference_supported' if present else 'pending_image_review' if assertion=='asserted' else 'nonasserted',
                metric_scope='COCO80 frozen conservative object normalization')
            all_claims.append(item)
            if not present and assertion=='asserted':candidates.append(item)
        if candidates:
            review.append(dict(base_id=row['base_id'],image_id=iid,image_path=row['image_path'],
                candidates=candidates,reference_inventory=sorted(inventory),
                status='pending_independent_image_and_assertion_review'))
        generations.append({**row,**result,'raw_decoded_response':raw,'artifact_result':str(path),
            'normalized_claim_count':len(claims),'candidate_absent_assertions':len(candidates)})
    dest=OUT/'c4_natural_failure'
    for name,data in [('generations',generations),('object_claims',all_claims),('candidate_hallucination_review',review),('reference_inventory',inventories)]:
        write(dest/f'{name}.jsonl',data)
    write(OUT/'traces/c4_native_reasoning_spans.jsonl',span_rows)
    print(json.dumps(dict(completed_images=len(generations),planned_images=len(manifests),
        claims=len(all_claims),candidate_images_requiring_review=len(review),
        candidate_claims=sum(len(r['candidates']) for r in review),final_labels='not yet assigned'),indent=2))


if __name__=='__main__':main()
