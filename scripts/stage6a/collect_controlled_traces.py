"""Extract exact native spans and source ROI maps without model-state features."""
import argparse
import hashlib
import json
from collections import Counter
import numpy as np
from PIL import Image
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write
from visual_reasoning.stage6a.segmentation import segment_native
from visual_reasoning.stage6a.stimuli import rect_mask
from visual_reasoning.stage3b7.roi import map_changed_pixels_to_tokens
from scripts.stage6a.source_annotations import secondary_sources


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--runs',nargs='+',default=['controlled_intact','controlled_stress','c3_stress']);args=parser.parse_args()
    index=[];spans=[];roi_maps=[];checks=[];seen=set();secondary=secondary_sources()
    for run in args.runs:
        for path in sorted((OUT/'native'/run).glob('shard_*/examples/*/result.json')):
            result=json.loads(path.read_text());eid=result['event_id']
            assert eid not in seen,eid;seen.add(eid)
            row=json.loads((path.parent/'manifest_row.json').read_text())
            row['annotation_sources']=secondary.get(row['base_id'],[])
            data=json.loads((path.parent/'input.json').read_text())
            generation=json.loads((path.parent/'generation.json').read_text())
            tokens=load(path.parent/'tokens.jsonl');raw=generation['raw_decoded_response']
            assert raw==''.join(t['decoded_token'] for t in tokens)
            assert generation['generated_token_ids']==[t['token_id'] for t in tokens]
            assert data['prompt']==row['prompt'] and data['condition']==row['condition']
            segmented=segment_native(tokens)
            for span in segmented:
                left,right=span['token_start'],span['token_end']
                assert span['text']==''.join(t['decoded_token'] for t in tokens[left:right])
                assert span['text']==raw[span['char_start']:span['char_end']]
                spans.append(dict(event_id=eid,base_id=row['base_id'],cohort=row['cohort'],
                    dataset=row['dataset'],condition=row['condition'],run=run,**span))
            if data['no_image']:
                assert not data['visual_token_indices'] and data['image_grid_thw'] is None
                assert data['image_path'] is None
            else:
                image=Image.open(data['image_path']).convert('RGB')
                assert hashlib.sha256(image.tobytes()).hexdigest()==data['decoded_image_sha256']
                visual=data['visual_token_indices'];_,height,width=data['visual_mapping']['merged_grid_shape']
                assert len(visual)==height*width and len(set(visual))==len(visual)
                sources=([row['target']] if row.get('target') else [])+row.get('other_sources',[])+row['annotation_sources']
                for source in sources:
                    # A queried COCO object's actual polygon, not its enclosing box,
                    # defines its primary token footprint. Diagram/DocVQA facts use
                    # independently reviewed semantic rectangles.
                    polygon=(row['cohort']=='C3' and source['source_id']=='T' and row.get('present'))
                    mask=np.asarray(Image.open(row['roi_mask_paths']['target']))>0 if polygon else rect_mask(image.size,source['roi'])
                    local=map_changed_pixels_to_tokens(mask,merged_rows=height,merged_cols=width)
                    yy,xx=np.nonzero(mask)
                    direct=sorted(set((yy*height//image.height*width+xx*width//image.width).tolist()))
                    assert local==direct and local
                    roi_maps.append(dict(event_id=eid,base_id=row['base_id'],cohort=row['cohort'],source_id=source['source_id'],
                        roi=source['roi'],local_token_indices=local,absolute_token_indices=[visual[i] for i in local],
                        grid=[1,height,width],image_size=list(image.size),image_grid_thw=data['image_grid_thw'],
                        pixel_mask_kind='reviewed_COCO_polygon' if polygon else 'reviewed_semantic_rectangle',
                        pixel_mask_path=row['roi_mask_paths']['target'] if polygon else None,
                        mapping_rule='Original pixel floor projection into merged row-major visual cells; independently enumerated',
                        condition=row['condition'],semantic_applicability='original-coordinate placebo only; original source absent' if row['condition']=='unrelated' else 'condition-specific source location',
                        retained_context_warning='Opaque masks do not prove absence of all category information' if polygon and row['condition']=='mask' else None))
            index.append({**row,**result,'run':run,'span_count':len(segmented),
                'reasoning_span_count':sum(s['section']=='reasoning' for s in segmented),
                'raw_decoded_response':raw,'generation_artifact':str(path.parent/'generation.json'),
                'input_metadata_artifact':str(path.parent/'input.json'),'tokens_artifact':str(path.parent/'tokens.jsonl'),
                'future_replay_context':dict(prompt_token_count=data['prompt_token_count'],native_token_count=len(tokens),
                    processor_grid=data['image_grid_thw'],visual_prompt_indices=data['visual_token_indices'],
                    cache_policy=data['image_state_policy'],stored_kv_tensors=False,
                    native_cache_reconstructable_from_prompt_tokens_image_and_continuation=True),
                'semantic_membership_review':'pending explicit intact local-claim review' if row['cohort']=='C1' and row['condition']=='intact' else 'not assigned by this mechanical parser'})
            checks.append(dict(event_id=eid,status='PASS',routing_and_image_sha_exact=True,
                native_decode_and_token_ids_exact=True,span_token_and_character_indices_exact=True,
                roi_projection_independently_checked=True,no_image_metadata_checked=data['no_image']))
    write(OUT/'traces/controlled_native_index.jsonl',index)
    write(OUT/'traces/controlled_reasoning_spans.jsonl',spans)
    write(OUT/'regions/controlled_roi_maps.jsonl',roi_maps)
    write(OUT/'audit/controlled_native_checks.jsonl',checks)
    summary=dict(status='SNAPSHOT',events=len(index),complete_native_traces=sum(r['complete'] for r in index),
        reasoning_spans=sum(s['section']=='reasoning' for s in spans),all_spans=len(spans),roi_maps=len(roi_maps),
        cohort_events=dict(Counter(r['cohort'] for r in index)),semantic_annotations_complete=False,
        no_model_or_attention_or_causal_computation=True)
    (OUT/'audit/controlled_native_snapshot.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
