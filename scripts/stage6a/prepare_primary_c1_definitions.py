"""Materialize reviewed C1 construction definitions before native generation."""
import json
import argparse
import numpy as np
from scripts.stage6a.inventory import OUT
from scripts.stage6a.review_candidates import open_image


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-label',default='primary_c1')
    args=parser.parse_args();assert args.output_label.isidentifier()
    authored=json.loads((OUT/'config/primary_c1_authored_semantics.json').read_text())
    queue={r['base_id']:r for r in map(json.loads,(OUT/'cohort/primary_c1_review_queue.jsonl').read_text().splitlines())}
    audits={r['base_id']:r for dataset in ['MathVerse','MathVision','MathVista']
        for r in json.loads((OUT/f'audit/primary_{dataset}_edit_review.json').read_text())}
    c1=[];overrides={};shams=[]
    for key,review in authored.items():
        if review.get('status','').startswith(('deferred','excluded')) or not review.get('crop_review','').startswith('pass'):continue
        row=queue[key];edit=audits[key];assert edit['status']=='pending_visual_review'
        im=open_image(row);pixels=np.asarray(im).astype(float);w,h=im.size
        x,y,x1,y1=edit['edit_roi'];bw,bh=x1-x,y1-y
        candidates=[]
        for sy in np.unique(np.linspace(2,h-bh-2,40).astype(int)):
            for sx in np.unique(np.linspace(2,w-bw-2,40).astype(int)):
                if not(sx+bw<=x or sx>=x1 or sy+bh<=y or sy>=y1):continue
                patch=pixels[sy:sy+bh,sx:sx+bw]
                # Uniform pale/background patch: avoid editing another label/edge.
                spread=patch.std(axis=(0,1)).mean()
                if spread>6 or patch.mean(2).min()<180:continue
                color_distance=float(np.linalg.norm(patch.mean(axis=(0,1))-edit['background_color']))
                candidates.append((color_distance+spread,int(sx),int(sy)))
        if not candidates:raise ValueError('No clean sham patch for '+key)
        score,sx,sy=min(candidates);sham=[sx,sy,sx+bw,sy+bh]
        target=row['proposed_target'];roi=edit['roi']
        c1.append([key,roi,sham,target['value'],target['counterfactual'],target['entity'],review['answer'],review['counterfactual_answer']])
        overrides[key]=dict(prompt=row['proposed_prompt'],answer_audit=review['answer_audit'],
            answer_format_normalization='Original mathematical task retained; fixed multiple-choice options omitted to allow numerical counterfactual values.',
            original_question=row['question'],source_semantic_review=review,
            selection_inputs=['source image','source question','objective local truth','localized editability'],
            primary_membership_status='pre-generation semantic candidate; intact completion/interpretability review pending')
        shams.append(dict(base_id=key,roi=sham,area=bw*bh,selection='uniform background, disjoint from target',background_distance_plus_spread=score))
    dest=OUT/f'config/{args.output_label}_construction_definitions.json'
    if dest.exists():raise FileExistsError(dest)
    dest.write_text(json.dumps(dict(c1=c1,c1_overrides=overrides,c2=[]),indent=2)+'\n')
    (OUT/f'audit/{args.output_label}_sham_selection.json').write_text(json.dumps(shams,indent=2)+'\n')
    print('C1 reviewed candidates',len(c1))


if __name__=='__main__':main()
