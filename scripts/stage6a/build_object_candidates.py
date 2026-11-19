"""Freeze POPE/COCO object families by annotation and mask feasibility only."""
from collections import defaultdict
from pathlib import Path
import json
import random
import re
import numpy as np
from PIL import Image, ImageDraw
from scripts.stage6a.prepare_candidates import OUT, read_arrow, write
from visual_reasoning.stage6a.stimuli import translate_mask


def polygon_mask(size, annotations):
    im=Image.new('1',size)
    draw=ImageDraw.Draw(im)
    for annotation in annotations:
        if not isinstance(annotation['segmentation'],list):raise ValueError('RLE needs separate validation')
        for poly in annotation['segmentation']:
            draw.polygon(list(zip(poly[::2],poly[1::2])),fill=1)
    return np.asarray(im,dtype=bool)


def find_sham(mask, occupied):
    y,x=np.nonzero(mask);h,w=mask.shape
    # Deterministic nearest valid translation with <1% annotated foreground overlap.
    candidates=[]
    for dy in range(-h+1,h,16):
        for dx in range(-w+1,w,16):
            if x.min()+dx<0 or x.max()+dx>=w or y.min()+dy<0 or y.max()+dy>=h:continue
            if not dx and not dy:continue
            overlap=float(occupied[y+dy,x+dx].mean())
            if overlap<=.01 and not mask[y+dy,x+dx].any():candidates.append((dx*dx+dy*dy,dx,dy,overlap))
    if not candidates:return None
    _,dx,dy,overlap=min(candidates)
    return dict(dx=dx,dy=dy,foreground_overlap_fraction=overlap)


def main():
    coco=json.loads(Path('/data/dataset/COCO2014/annotations/instances_val2014.json').read_text())
    images={r['id']:r for r in coco['images']};categories={r['id']:r['name'] for r in coco['categories']}
    by_image=defaultdict(list)
    for r in coco['annotations']:by_image[r['image_id']].append(r)
    inv=json.loads((OUT/'cohort/dataset_inventory.json').read_text())
    pope=next(r for r in inv['datasets'] if r['dataset']=='POPE')['candidates'][0]
    questions=[]
    for shard in pope['arrow_shards']:
        questions.extend(read_arrow(shard['path']).drop(['image']).to_pylist())
    random.Random(60973).shuffle(questions);seen=set();selected={True:[],False:[]};exclusions=[]
    for row in questions:
        image_id=int(row['image_source'].split('_')[-1])
        match=re.fullmatch(r'Is there (?:a|an) (.+) in the image\?',row['question'])
        if not match:continue
        category=match[1];key=(image_id,category)
        if key in seen:continue
        seen.add(key)
        if image_id not in images:continue
        anns=by_image[image_id];target=[a for a in anns if categories[a['category_id']]==category]
        present=row['answer'].lower()=='yes'
        if present!=bool(target):
            exclusions.append(dict(image_id=image_id,category=category,reason='POPE label disagrees with instance inventory'));continue
        if len(selected[present])>=86:continue
        im=images[image_id];size=(im['width'],im['height']);mask=None;sham=None
        if present:
            if len(target)!=1 or target[0]['iscrowd'] or not isinstance(target[0]['segmentation'],list):continue
            mask=polygon_mask(size,target);fraction=float(mask.mean())
            if not .015<=fraction<=.22:continue
            other=[a for a in anns if a['id']!=target[0]['id'] and isinstance(a['segmentation'],list)]
            occupied=polygon_mask(size,other) if other else np.zeros(mask.shape,bool)
            overlap=float(occupied[mask].mean())
            if overlap>.1:continue
            all_occupied=occupied|mask
            sham=find_sham(mask,all_occupied)
            if sham is None:continue
        base=dict(base_id=f'pope_{image_id}_{category.replace(" ","_")}',dataset='POPE_COCO2014',cohort='C3',
            image_id=image_id,image_path=str(Path('/data/dataset/COCO2014/val2014')/im['file_name']),
            width=im['width'],height=im['height'],license_id=im['license'],category=category,present=present,
            question=row['question'],prompt=row['question']+' Reason from the visible image, then answer yes or no.',answer='yes' if present else 'no',
            pope_question_id=row['question_id'],pope_category=row['category'],target_annotations=target,
            object_inventory=sorted({categories[a['category_id']] for a in anns}),
            other_rois=[dict(annotation_id=a['id'],category=categories[a['category_id']],bbox=a['bbox']) for a in anns if a not in target],
            mask_fraction=float(mask.mean()) if mask is not None else None,
            target_overlap_fraction=overlap if present else None,sham_translation=sham,
            primary_selection_used_model_scores=False)
        selected[present].append(base)
        print(f"present={len(selected[True])} absent={len(selected[False])}",flush=True)
        if all(len(v)>=86 for v in selected.values()):break
    # Two present + one absent mechanics; three of each pilot; eighty each primary.
    final=[]
    for present,rows in selected.items():
        mechanics=2 if present else 1
        for i,row in enumerate(rows):
            row['phase']='mechanics' if i<mechanics else 'pilot' if i<mechanics+3 else 'primary'
            if row['phase']=='primary' and i>=mechanics+3+80:row['phase']='reserve'
            final.append(row)
    write(OUT/'c3_object_stress/pope_manifest.jsonl',final)
    write(OUT/'c3_object_stress/present_object_manifest.jsonl',[r for r in final if r['present']])
    write(OUT/'c3_object_stress/absent_object_manifest.jsonl',[r for r in final if not r['present']])
    write(OUT/'cohort/object_candidate_exclusions.jsonl',exclusions)
    write(OUT/'c3_object_stress/coco_object_annotations.jsonl',[dict(image_id=k,annotations=by_image[k]) for k in sorted({r['image_id'] for r in final})])
    print(json.dumps(dict(present=len(selected[True]),absent=len(selected[False]),label_disagreements=len(exclusions)),indent=2))


if __name__=='__main__':main()
