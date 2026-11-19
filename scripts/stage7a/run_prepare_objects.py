"""Bounded source-only POPE/COCO preparation in the existing allocation."""
import argparse
import os
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl
from scripts.stage6a.prepare_candidates import read_arrow
from scripts.stage6a.build_object_candidates import polygon_mask, find_sham
from visual_reasoning.stage6a.stimuli import apply_stress, translate_mask


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run-id', required=True)
    args = p.parse_args()
    config = read_json(OUT / 'config/stage7a_config.json')
    assert os.environ['SLURM_JOB_ID'] == config['runtime']['slurm_allocation']
    inventory = read_json(OUT / 'cohort/dataset_inventory.json')
    coco_paths = next(r['checked_files'] for r in inventory['datasets'] if r['dataset'] == 'COCO2014')
    annotation = next(Path(r['path']) for r in coco_paths if 'instances_' in r['path'])
    coco = read_json(annotation)
    categories = {r['id']: r['name'] for r in coco['categories']}
    supercategories = {r['id']: r['supercategory'] for r in coco['categories']}
    images = {r['id']: r for r in coco['images']}
    by_image = defaultdict(list)
    for row in coco['annotations']:
        by_image[row['image_id']].append(row)
    historical = read_jsonl(ROOT / 'outputs/stage6a/audit/source_identity_catalog.jsonl')
    excluded = {int(r['source_image_id']) for r in historical
                if r['dataset'] in ['COCO2014', 'POPE_COCO2014'] and r['source_image_id'] is not None}
    pope_paths = next(r['checked_files'] for r in inventory['datasets'] if r['dataset'] == 'POPE')
    questions = []
    for row in pope_paths:
        questions.extend(read_arrow(row['path']).drop(['image']).to_pylist())
    random.Random(70910).shuffle(questions)
    pool, seen = [], set()
    for row in questions:
        image_id = int(row['image_source'].split('_')[-1])
        if image_id in excluded or image_id in seen or image_id not in images:
            continue
        match = re.fullmatch(r'Is there (?:a|an) (.+) in the image\?', row['question'])
        if not match:
            continue
        seen.add(image_id)
        pool.append(dict(**row, image_id=image_id, asked_category=match[1]))
        if len(pool) == config['screening_budget']['max_candidates']['C3']:
            break
    write_jsonl(OUT / 'cohort/object_candidate_order.jsonl', pool, freeze=True)
    selected, exclusions = [], []
    count = Counter()
    for order, row in enumerate(pool):
        image_id, category = row['image_id'], row['asked_category']
        info, anns = images[image_id], by_image[image_id]
        present = row['answer'].lower() == 'yes'
        target = [a for a in anns if categories[a['category_id']] == category]
        reason = None
        if present != bool(target):
            reason = 'POPE answer disagrees with COCO instance inventory'
        elif count[present] >= 12:
            reason = 'predeclared 12-per-presence source quota filled; no model outcomes consulted'
        elif present and (len(target) != 1 or target[0]['iscrowd'] or not isinstance(target[0]['segmentation'], list)):
            reason = 'primary positive source requires a single noncrowd polygon instance'
        if reason:
            exclusions.append(dict(image_id=image_id, reason=reason))
            continue
        size = (info['width'], info['height'])
        mask = polygon_mask(size, target) if present else None
        sham = None
        others = [a for a in anns if a not in target and isinstance(a['segmentation'], list)]
        if present:
            occupied = polygon_mask(size, others) if others else np.zeros(mask.shape, bool)
            if not .015 <= float(mask.mean()) <= .22:
                reason = 'target area outside predeclared 1.5%-22%'
            elif float(occupied[mask].mean()) > .10:
                reason = 'more than10% of target overlaps other annotated objects'
            else:
                sham = find_sham(mask, occupied | mask)
                if sham is None: reason = 'no disjoint matched translated-mask sham'
        if reason:
            exclusions.append(dict(image_id=image_id, reason=reason))
            continue
        # Category/supercategory plausibility then object area; never attention.
        target_super = supercategories[target[0]['category_id']] if present else None
        alternatives = sorted(others, key=lambda a: (
            supercategories[a['category_id']] != target_super, -a['area'], a['id']))
        alternative = next((a for a in alternatives
                            if mask is None or not np.logical_and(mask, polygon_mask(size,[a])).any()), None)
        key = f'pope_{image_id}_{category.replace(" ","_")}'
        source = annotation.parent.parent / 'val2014' / info['file_name']
        image = Image.open(source).convert('RGB')
        dest = OUT / 'assets' / key
        dest.mkdir(parents=True, exist_ok=True)
        image.save(dest / 'condition__intact.png')
        views = [image]
        if present:
            sham_mask = translate_mask(mask, sham['dx'], sham['dy'])
            Image.fromarray(mask.astype('uint8')*255).save(dest/'roi_mask__T.png')
            Image.fromarray(sham_mask.astype('uint8')*255).save(dest/'roi_mask__I.png')
            for condition in ['strong','mask']:
                changed = apply_stress(image, mask, condition)
                changed.save(dest/f'condition__{condition}.png')
            sham_image = apply_stress(image, sham_mask, 'mask')
            sham_image.save(dest/'condition__sham_mask.png')
            views += [Image.open(dest/'condition__mask.png'), sham_image]
        if alternative:
            xmask = polygon_mask(size,[alternative])
            Image.fromarray(xmask.astype('uint8')*255).save(dest/'roi_mask__X.png')
        selected.append(dict(base_id=key,dataset='POPE_COCO2014',cohort='C3',image_id=image_id,
            image_path=str(dest/'condition__intact.png'),source_image_path=str(source),
            width=image.width,height=image.height,license_id=info['license'],category=category,
            present=present,answer='yes' if present else 'no',question=row['question'],
            prompt=row['question']+' Reason from the visible image, then answer yes or no.',
            target_annotations=target,alternative_annotation=alternative,
            alternative_category=categories[alternative['category_id']] if alternative else None,
            object_inventory=sorted({categories[a['category_id']] for a in anns}),
            sham_translation=sham,source_candidate_order=order,
            semantic_review='pending independent full-image/mask/sham review',
            target_absence='Requires full-image review; annotation absence alone is insufficient',
            selection_used_model_outputs=False))
        sheet = Image.new('RGB',(1200,440),'white');draw=ImageDraw.Draw(sheet)
        for i, view in enumerate(views):
            view=view.copy();view.thumbnail((390,390));sheet.paste(view,(400*i+5,35))
            draw.text((400*i+5,5),key+' '+['native','target masked','matched sham'][i],fill='black')
        sheet.save(OUT/'review'/(key+'_objects.png'))
        count[present] += 1
        print(key,present,dict(count),flush=True)
    write_jsonl(OUT/'cohort/provisional_object_sources.jsonl',selected,freeze=True)
    write_jsonl(OUT/'cohort/object_source_exclusions.jsonl',exclusions,freeze=True)
    for offset in range(0,len(selected),4):
        part=selected[offset:offset+4];sheet=Image.new('RGB',(1200,440*len(part)),'white')
        for i,row in enumerate(part):sheet.paste(Image.open(OUT/'review'/(row['base_id']+'_objects.png')),(0,440*i))
        sheet.save(OUT/'review'/f'object_batch_{offset//4:02d}.png')
    write_json(OUT/'raw'/args.run_id/'run_summary.json',dict(completed=True,cpu_only=True,
        candidates=len(pool),provisional_sources=len(selected),presence_counts={str(k):v for k,v in count.items()},
        exclusions=len(exclusions),native_or_causal_model_execution=False))


if __name__ == '__main__':
    main()
