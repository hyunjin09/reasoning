"""Source-only cohort assembly and exact processor-pixel review in existing allocation.

This writes proposals. The separate review/freeze gate must pass before generation.
"""
import argparse
import gc
import hashlib
import math
import os
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
import torch
from PIL import Image, ImageDraw
from transformers import AutoProcessor
from scripts.stage7a.common import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl, sha, configure_fresh_processor
from scripts.stage7a.build_edit_review import identity
from visual_reasoning.stage6a.runtime import prepare_condition
from visual_reasoning.stage6a.stimuli import rect_mask, apply_stress
from visual_reasoning.stage3b7.roi import map_changed_pixels_to_tokens, fixed_ring, cell_darkness, choose_matched_irrelevant


def exact_processed_image(batch, processor):
    """Invert installed Qwen image processor patch packing, retaining actual resize pixels."""
    t, h, w = batch['image_grid_thw'][0].tolist()
    ip = processor.image_processor
    p, m, tp = ip.patch_size, ip.merge_size, ip.temporal_patch_size
    assert t == 1
    packed = batch['pixel_values'].reshape(h//m, w//m, m, m, 3, tp, p, p)
    assert torch.equal(packed[..., 0, :, :], packed[..., 1, :, :])
    rgb = packed[:, :, :, :, :, 0].permute(4, 0, 2, 5, 1, 3, 6).reshape(3, h*p, w*p)
    mean = torch.tensor(ip.image_mean)[:, None, None]
    std = torch.tensor(ip.image_std)[:, None, None]
    raw = ((rgb * std + mean) * 255).round().clamp(0, 255).to(torch.uint8)
    return Image.fromarray(raw.permute(1, 2, 0).numpy())


def source_components(bases):
    parent = {b['base_id']: b['base_id'] for b in bases}
    def root(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]; k = parent[k]
        return k
    pairs = []
    for i, a in enumerate(bases):
        for b in bases[:i]:
            x, y = a['identity'], b['identity']
            exact = x['decoded_stimulus_sha256'] == y['decoded_stimulus_sha256']
            near = abs(math.log((x['width']/x['height'])/(y['width']/y['height']))) <= .15 and (int(x['phash'],16)^int(y['phash'],16)).bit_count() <= 4
            if exact or near:
                parent[root(a['base_id'])] = root(b['base_id'])
                pairs.append(dict(a=a['base_id'], b=b['base_id'], exact=exact, near=near))
    groups = defaultdict(list)
    for b in bases: groups[root(b['base_id'])].append(b['base_id'])
    return list(groups.values()), pairs


def split_sources(bases, groups):
    by_id = {b['base_id']: b for b in bases}
    stratum = lambda b: b['dataset'] + ('_present' if b.get('present') else '_absent') if b['cohort']=='C3' else b['dataset']
    totals = Counter(stratum(b) for b in bases)
    desired = {k: round(v/3) for k,v in totals.items()}
    discovery = Counter(); assignments = {}
    # Keep exact/near image clusters intact, including all future conditions.
    ordered = sorted(groups, key=lambda g: (-len(g), hashlib.sha256(('70910:'+min(g)).encode()).hexdigest()))
    for group in ordered:
        counts = Counter(stratum(by_id[k]) for k in group)
        before = sum(abs(discovery[k]-desired[k]) for k in counts)
        after = sum(abs(discovery[k]+v-desired[k]) for k,v in counts.items())
        split = 'discovery' if after < before else 'confirmation'
        if split == 'discovery': discovery.update(counts)
        for k in group: assignments[k] = dict(split=split, group_id='image_family:'+min(group))
    return assignments, dict(totals=totals, target_discovery=desired, actual_discovery=discovery)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run-id', required=True); args=parser.parse_args()
    config=read_json(OUT/'config/stage7a_config.json')
    assert os.environ['SLURM_JOB_ID']==config['runtime']['slurm_allocation']
    assert not (OUT/'audit/cohort_freeze.json').exists()
    pool={r['base_id']:r for r in read_jsonl(OUT/'cohort/source_candidate_order.jsonl')}
    reviews=read_json(OUT/'annotations/source_edit_review.json')
    definitions=read_json(OUT/'annotations/provisional_source_definitions.json')
    bases=[]
    for review in reviews:
        k=review['base_id']; definition=definitions[k]
        for filename,digest in review['image_sha256'].items(): assert sha(OUT/'assets'/k/filename)==digest
        base={**pool[k], **definition, 'fields':review['fields'], 'image_path':str(OUT/'assets'/k/'condition__intact.png'),
              'answer':definition['final_answer'], 'dataset_original_answer':pool[k]['answer'],
              'template_family':'MathVista_TabMWP' if pool[k].get('metadata',{}).get('source')=='TabMWP' else definition['family']}
        base['prompt']=definition.get('prompt',pool[k]['prompt'])
        bases.append(base)
    object_review={r['base_id']:r for r in read_json(OUT/'annotations/object_source_review.json')}
    for source in read_jsonl(OUT/'cohort/provisional_object_sources.jsonl'):
        review=object_review[source['base_id']]
        if review['status']!='accept': continue
        bases.append({**source,'fields':{},'family':'natural_object_presence','template_family':'POPE_presence', 'availability_review':review})
    for b in bases:
        with Image.open(b['image_path']) as im: b['identity']=identity(im.convert('RGB'))
    groups, near_pairs=source_components(bases)
    assignments, split_counts=split_sources(bases,groups)
    for b in bases: b.update(assignments[b['base_id']])
    write_json(OUT/'cohort/proposed_discovery_confirmation_split.json',dict(assignments=assignments, counts=split_counts,
        unit='exact/near-image family; all questions, conditions and events nested',
        template_policy='Causal discovery/confirmation is base-family grouped, dataset stratified. Shared templates are recorded; later probes require separate dataset/template-held-out folds, and ordinary base split never claims unseen-template generalization.'))
    write_json(OUT/'audit/new_source_overlap.json',dict(pairs=near_pairs,groups=groups))
    processor=AutoProcessor.from_pretrained(config['model_checkpoint'],local_files_only=True)
    configure_fresh_processor(processor)
    manifest=[]; audits=[]; field_strips=[]
    for i, b in enumerate(bases):
        k=b['base_id']; dest=OUT/'assets'/k; image=Image.open(b['image_path']).convert('RGB')
        seedrow={**b,'condition':'intact','event_id':k+'__intact'}
        batch, meta=prepare_condition(processor,seedrow,'cpu')
        processed=exact_processed_image(batch,processor)
        processed.save(dest/'processed_review__intact.png')
        _,h,w=meta['visual_mapping']['merged_grid_shape']; masks={}; local={}
        for role, f in b['fields'].items(): masks[role]=rect_mask(image.size,f['roi'])
        if b['cohort']=='C3':
            for role in ['T','X','I']:
                path=dest/f'roi_mask__{role}.png'
                if path.exists():masks[role]=np.asarray(Image.open(path))>0
        for role, mask in masks.items():
            local[role]=map_changed_pixels_to_tokens(mask,merged_rows=h,merged_cols=w)
        irrelevant_audit={'unavailable':'No target footprint for absent object'}
        if b['cohort']!='C3':
            excluded=fixed_ring(sorted(set(local['T'])|set(local['X'])),merged_rows=h,merged_cols=w,radius=1)
            darkness=cell_darkness(np.asarray(processed),merged_rows=h,merged_cols=w)
            try:
                selected, irrelevant_audit=choose_matched_irrelevant(target_local=local['T'],excluded_local=excluded,darkness_by_cell=darkness)
                # Existing Stage5A low-ink threshold, fixed before outcomes.
                if irrelevant_audit['mean_darkness']>.03: raise ValueError('No independently identifiable low-ink matched control')
                local['I']=selected
                imask=np.zeros((image.height,image.width),bool)
                for v in selected:
                    yy,xx=divmod(v,w)
                    imask[math.ceil(yy*image.height/h):math.ceil((yy+1)*image.height/h),math.ceil(xx*image.width/w):math.ceil((xx+1)*image.width/w)]=True
                masks['I']=imask
            except ValueError as error: irrelevant_audit={'unavailable':str(error)}
        for role, mask in masks.items(): Image.fromarray(mask.astype('uint8')*255).save(dest/f'roi_mask__{role}.png')
        b['local_source_groups']=local; b['processor_geometry']=meta['visual_mapping'];b['image_grid_thw']=meta['image_grid_thw']
        b['irrelevant_audit']=irrelevant_audit
        b['source_map_overlaps']={a+'_'+c:sorted(set(local[a])&set(local[c])) for a in local for c in local if a<c}
        conditions={'intact':image}
        if 'T' in masks:
            conditions.update({name:apply_stress(image,masks['T'],name) for name in ['strong','mask']})
            if 'I' in masks:conditions['sham_mask']=apply_stress(image,masks['I'],'mask')
        # Negative object bases have no fake target mask or target suppression.
        for name,view in conditions.items():
            view.save(dest/f'condition__{name}.png')
            manifest.append({**b,'condition':name,'event_id':k+'__'+name,'image_path':str(dest/f'condition__{name}.png'),
                'arm_candidates':['A','B','C','E'],'target_availability':('queried_object_absent' if b['cohort']=='C3' and not b['present'] else ('available' if name in ['intact','sham_mask'] else ('degraded' if name=='strong' else ('partial_only' if b['cohort']=='C3' else 'printed_target_masked'))))})
        donors=[a for a in bases if a['base_id']!=k and a['split']==b['split'] and a['cohort']==b['cohort'] and a['family']!=b['family']]
        if b['cohort']=='C3':donors=[a for a in bases if a['base_id']!=k and a['split']==b['split'] and a['cohort']=='C3' and b['category'] not in a['object_inventory']]
        # The frozen source bank has only four geometry bases; cross-dataset C1 donors are permitted and disclosed.
        donors.sort(key=lambda a:(a['dataset']!=b['dataset'],abs(math.log((a['identity']['width']/a['identity']['height'])/(image.width/image.height))),a['base_id']))
        if donors:
            donor=donors[0]; unrelated=Image.open(donor['image_path']).convert('RGB').resize(image.size,Image.Resampling.LANCZOS)
            unrelated.save(dest/'condition__unrelated.png')
            manifest.append({**b,'condition':'unrelated','event_id':k+'__unrelated','image_path':str(dest/'condition__unrelated.png'),
                'arm_candidates':['B'],'target_availability':'source_image_unavailable','unrelated_donor':donor['base_id'],
                'control_matching':'same split/cohort, distinct source family; prefer same dataset then closest aspect; resize to recipient dimensions; no effect-based matching'})
        manifest.append({**b,'condition':'no_image','event_id':k+'__no_image','image_path':None,'no_image':True,'arm_candidates':['B'],'target_availability':'unavailable'})
        if b['fields']:
            atext,btext=b['fields']['T']['entity'],b['fields']['X']['entity']
            prompt=(f'Read the following three requested fields from the image in order. For each, identify the requested field and give its printed value, with a short explanation. '
                    f'First: {atext}. Second: {btext}. Third: {atext}. Finish with the three values in the same order.')
            manifest.append({**b,'condition':'aba','event_id':k+'__aba','image_path':b['image_path'],'prompt':prompt,'arm_candidates':['D'],
                'requested_source_sequence':['T','X','T'],'answer':None,'target_availability':'available'})
            strip=Image.new('RGB',(1200,220),'white');draw=ImageDraw.Draw(strip);draw.text((5,3),k+' ACTUAL processor pixels: native / sham / semantic',fill='black')
            for j,role in enumerate(['T','X']):
                f=b['fields'][role]; x0,y0,x1,y1=f['roi']
                roi=[round(x0*processed.width/image.width),round(y0*processed.height/image.height),round(x1*processed.width/image.width),round(y1*processed.height/image.height)]
                draw.text((5,20+j*100),f"{role} {f['value']} -> {f['counterfactual']} at {processed.size}, field pixels={roi[2]-roi[0]}x{roi[3]-roi[1]}",fill='black')
                for v,name in enumerate(['intact',role+'_sham',role+'_semantic']):
                    if name=='intact':view=processed
                    else:
                        altered={**seedrow,'image_path':str(dest/f'condition__{name}.png')};bb,_=prepare_condition(processor,altered,'cpu');view=exact_processed_image(bb,processor);del bb
                    pad=4;box=[max(0,roi[0]-pad),max(0,roi[1]-pad),min(view.width,roi[2]+pad),min(view.height,roi[3]+pad)]
                    crop=view.crop(box); scale=min(4,380/crop.width,73/crop.height);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.NEAREST)
                    strip.paste(crop,(v*400+5,38+j*100))
            strip.save(OUT/'review'/(k+'_processed.png'));field_strips.append(k)
        audits.append(dict(base_id=k,grid=meta['image_grid_thw'],processed_size=processed.size,local_source_groups=local,
            token_overlap=b['source_map_overlaps'],irrelevant=irrelevant_audit,donor=donors[0]['base_id'] if donors else None,
            raw_processor_pixels_inverted=True,processed_legibility='pending manual review',fields=list(b['fields'])))
        print(f'{i+1}/{len(bases)} {k} visual_tokens={h*w} overlaps={b["source_map_overlaps"]}',flush=True)
        del batch, image, processed, masks;gc.collect()
    for offset in range(0,len(field_strips),6):
        chunk=field_strips[offset:offset+6];sheet=Image.new('RGB',(1200,220*len(chunk)),'white')
        for j,k in enumerate(chunk):sheet.paste(Image.open(OUT/'review'/(k+'_processed.png')),(0,220*j))
        sheet.save(OUT/'review'/f'processed_batch_{offset//6:02d}.png')
    write_jsonl(OUT/'cohort/proposed_base_manifest.jsonl',bases)
    write_jsonl(OUT/'cohort/proposed_native_manifest.jsonl',manifest)
    write_json(OUT/'audit/proposed_processor_and_source_maps.json',audits)
    write_json(OUT/'raw'/args.run_id/'run_summary.json',dict(completed=True,cpu_only=True,bases=len(bases),native_conditions=len(manifest),
        cohort_bases=dict(Counter(b['cohort'] for b in bases)),split_counts=split_counts,scientific_generation=False))


if __name__=='__main__':main()
