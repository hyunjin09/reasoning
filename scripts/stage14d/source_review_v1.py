"""Save manual original-image judgments, never infer source labels from outcomes."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from PIL import Image
from scripts.stage14d.prepare_technical_v1 import ROOT,save,sha,lines
from scripts.stage14d.design import render_directive


def record(reviews):
    source={r['item_id']:r for r in lines(ROOT/'cohorts/source_only_target_review_worklist_v1.jsonl') if not r['technical']}
    for review in reviews:
        item=review['item_id'];s=source[item]
        assert review['original_image_directly_inspected'] is True
        assert review['judgment_method']=='manual_source_image_and_question_review'
        assert sha(s['source_image'])==s['source_image_sha256']
        width,height=Image.open(s['source_image']).size
        out=dict(at=dt.datetime.now(dt.timezone.utc).isoformat(),family_id=s['family_id'],
            original_source=s,source_image_dimensions=[width,height],source_receipt_sha256=sha(s['source_receipt']),
            scientific_outcomes_seen=False,reviewer='main agent; no independent inter-rater claim',**review)
        if review['status']=='SOURCE_VALID_VALUE_FREE':
            x0,y0,x1,y1=review['ROI_pixels'];assert 0<=x0<x1<=width and 0<=y0<y1<=height
            assert review['request'] and review['evaluator_only_reference'] and review['source_observation']
            assert review['answer_safe_reason'] and review['selection_reason']
            target=dict(request=review['request'],source_request_sha256=hashlib.sha256(review['request'].encode()).hexdigest(),
                review_status='SOURCE_VALID_VALUE_FREE',ROI_id=f'source_{item}_target')
            out['model_visible_target']=target;out['target_directive']=render_directive('LOOK_TARGET',target)
            out['normalized_ROI']=[x0/width,y0/height,x1/width,y1/height]
            if review.get('irrelevant_status')=='SOURCE_VALID_VALUE_FREE':
                x0,y0,x1,y1=review['irrelevant_ROI_pixels'];assert 0<=x0<x1<=width and 0<=y0<y1<=height
                request=review['irrelevant_request']
                target=dict(request=request,source_request_sha256=hashlib.sha256(request.encode()).hexdigest(),
                    review_status='SOURCE_VALID_VALUE_FREE',ROI_id=f'source_{item}_irrelevant')
                out['irrelevant_model_visible_target']=target
                out['irrelevant_directive']=render_directive('LOOK_IRRELEVANT',target)
        else:
            assert review['status'] in {'SOURCE_AMBIGUOUS','SOURCE_INVALID','ALREADY_TEXT_SUPPLIED','STRUCTURED_COMPLEX','ANSWER_LEAKING_TARGET'}
            assert review['reason'];out['model_visible_target']=None
        save(ROOT/'annotation/source_review_v1'/f'{item}.json',out)
    print('Saved source records:',len(reviews),'total:',len(list((ROOT/'annotation/source_review_v1').glob('*.json'))))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('file');record(json.loads(Path(p.parse_args().file).read_text()))
