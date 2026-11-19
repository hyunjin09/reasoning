"""Reviewed, pre-generation 12-family mechanics stimuli and semantic factorial."""
import json
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from scripts.stage6a.prepare_candidates import OUT, write
from scripts.stage6a.review_candidates import open_image
from scripts.stage6a.build_object_candidates import polygon_mask
from visual_reasoning.stage5a.edits import numeric_edit
from visual_reasoning.stage6a.stimuli import rect_mask, translate_mask, apply_stress, asset_path


def load(path):return [json.loads(l) for l in path.read_text().splitlines()]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',default='mechanics',choices=['mechanics','pilot','primary']);parser.add_argument('--definitions');parser.add_argument('--output-label')
    parser.add_argument('--cohorts',nargs='+',choices=['C1','C2','C3','C4'],default=['C1','C2','C3','C4'])
    parser.add_argument('--split-file',help='Frozen prospective source split; required for released primary controls')
    args=parser.parse_args();phase=args.phase
    if phase!='primary' and set(args.cohorts)!={'C1','C2','C3','C4'}:
        raise ValueError('Validation and pilot must retain all four cohorts')
    authored=json.loads(Path(args.definitions).read_text()) if args.definitions else {}
    output_label=args.output_label or phase
    if '/' in output_label:raise ValueError('Invalid output label')
    asset_root=OUT/'assets'/output_label
    if (OUT/'native'/output_label).exists():raise RuntimeError('Do not rewrite assets/manifests after generation begins')
    pool={r['base_id']:r for r in load(OUT/'cohort/semantic_candidate_order.jsonl')}
    definitions=[
      ('mathverse_661',[180,92,202,118],[320,110,342,136],'6','8','radius','603.19','904.78'),
      ('mathvision_2903',[1910,790,1990,920],[2060,980,2140,1110],'8','9','point x-coordinate','25*pi','36*pi'),
      ('mathvista_630',[54,56,77,78],[87,20,110,42],'56','66','angle at A','72','82')]
    definitions=authored.get('c1',definitions)
    if 'C1' not in args.cohorts:definitions=[]
    rows=[];bases=[];audits=[]
    for base_id,roi,sham_roi,value,alternate,entity,answer,cf_answer in definitions:
        base={**pool[base_id], 'cohort':'C1','phase':phase,'answer':answer,
              'target':dict(source_id='T',roi=roi,value=value,counterfactual=alternate,entity=entity),
              'semantic_review':'direct image and question reviewed before generation; target not repeated in question',
              'ground_truth_readouts':dict(intact=value,counterfactual=alternate),
              'counterfactual_answer':cf_answer}
        base['dataset_original_answer']=pool[base_id]['answer']
        base.update(authored.get('c1_overrides',{}).get(base_id,{}))
        native=open_image(base)
        outputs,edit=numeric_edit(native,base['target'])
        # Use the isolated glyph rectangle for stress, preserving nearby geometry
        # and punctuation even when the broader localization ROI includes them.
        ex0,ey0,ex1,ey1=edit['edit_roi']
        mask=rect_mask(native.size,edit['edit_roi'])
        sham_roi=[sham_roi[0],sham_roi[1],sham_roi[0]+ex1-ex0,sham_roi[1]+ey1-ey0]
        sham=rect_mask(native.size,sham_roi)
        assets=asset_root/base_id;assets.mkdir(parents=True,exist_ok=True)
        base['roi_mask_paths']={name:str(asset_path(assets,'roi_mask',name)) for name in ('target','sham')}
        conditions={'intact':native,'counterfactual':outputs['semantic'],'counterfactual_render_sham':outputs['sham']}
        for condition in ('mild','strong','mask'):
            conditions[condition]=apply_stress(native,mask,condition)
            conditions['sham_'+condition]=apply_stress(native,sham,condition)
        for name,image in conditions.items():
            path=asset_path(assets,'condition',name);image.save(path)
            rows.append({**base,'condition':name,'image_path':str(path),'event_id':base_id+'__'+name,
                         'answer':cf_answer if name=='counterfactual' else answer})
        Image.fromarray(mask.astype('uint8')*255).save(base['roi_mask_paths']['target'])
        Image.fromarray(sham.astype('uint8')*255).save(base['roi_mask_paths']['sham'])
        bases.append(base);audits.append(dict(base_id=base_id,numeric_edit=edit,sham_roi=sham_roi,target_area=int(mask.sum()),sham_area=int(sham.sum())))
    factorial=[
      dict(base_id='docvqa_45005',roi=[430,414,535,440],other_roi=[468,447,529,473],entity='Salaries',other_entity='Office Expenses',
           answers=['12180.00','336.80'],prompts=[
        'What amount is listed for Salaries under Expenditures?',
        'In the table containing Salaries, what amount is listed for Office Expenses under Expenditures?',
        'What amount appears in the first data row of the middle numeric column?',
        'What amount appears in the second data row of the middle numeric column?']),
      dict(base_id='docvqa_7013',roi=[545,829,789,874],other_roi=[545,874,789,919],entity='sender phone number',other_entity='sender fax number',
           answers=['(336) 741-3514','(336) 741-0881'],prompts=[
        "What is Teresa Wood's phone number on this fax cover sheet?",
        "On the fax cover sheet containing Teresa Wood's phone number, what fax number is listed for her?",
        "What number is printed on the line immediately below the sender's name?",
        "What number is printed on the last filled line of the sender's contact block?"]),
      dict(base_id='docvqa_59626',roi=[689,649,815,677],other_roi=[217,648,265,676],entity='Printed in country',other_entity='month/year code',
           answers=['U.S.A.','4/72'],prompts=[
        'In which country was the Polaroid form printed?',
        "On this form with a 'Printed in' line, what month/year code appears at the bottom left?",
        'Which three-letter country abbreviation appears at the lower-right corner?',
        'What month/year code appears beside P558B-1 at the bottom left?'])]
    factorial=authored.get('c2',factorial)
    if 'C2' not in args.cohorts:factorial=[]
    for design in factorial:
        base={**pool[design['base_id']],**design,'cohort':'C2','phase':phase,
              'semantic_review':'two spatially distinct fields independently read before generation',
              'unmatched_properties':['answer character length','prompt character length','semantic task difficulty uncalibrated']}
        im=open_image(base);assets=asset_root/base['base_id'];assets.mkdir(parents=True,exist_ok=True)
        path=asset_path(assets,'condition','intact');im.save(path);base['image_path']=str(path)
        for i,cell in enumerate(('AR','A_only','R_only','Neither')):
            rows.append({**base,'condition':cell,'event_id':base['base_id']+'__'+cell,
                'prompt':design['prompts'][i]+' Reason carefully, then give the requested value.',
                'answer':design['answers'][i%2], 'target':dict(source_id='T',roi=design['roi'],entity=design['entity']),
                'demanded_sources':['T'] if i%2==0 else ['X'],
                'mentioned_sources':['T'] if i<2 else [],
                'other_sources':[dict(source_id='X',roi=design['other_roi'],entity=design['other_entity'])]})
        bases.append(base)
    objects=[r for r in load(OUT/'c3_object_stress/pope_manifest.jsonl') if r['phase']==phase and 'C3' in args.cohorts]
    for base in objects:
        im=open_image(base);assets=asset_root/base['base_id'];assets.mkdir(parents=True,exist_ok=True)
        conditions={'intact':im}
        if base['present']:
            mask=polygon_mask(im.size,base['target_annotations']);shift=base['sham_translation']
            sham=translate_mask(mask,shift['dx'],shift['dy'])
            for condition in ('strong','mask'):conditions[condition]=apply_stress(im,mask,condition)
            conditions['sham']=apply_stress(im,sham,'mask')
            if phase=='primary':conditions['sham_strong']=apply_stress(im,sham,'strong')
            base['roi_mask_paths']={name:str(asset_path(assets,'roi_mask',name)) for name in ('target','sham')}
            Image.fromarray(mask.astype('uint8')*255).save(base['roi_mask_paths']['target'])
            Image.fromarray(sham.astype('uint8')*255).save(base['roi_mask_paths']['sham'])
            y,x=np.nonzero(mask);base['target']=dict(source_id='T',roi=[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)],entity=base['category'])
        for name,image in conditions.items():
            path=asset_path(assets,'condition',name);image.save(path)
            rows.append({**base,'condition':name,'event_id':base['base_id']+'__'+name,'image_path':str(path)})
        bases.append(base)
    c4=[r for r in load(OUT/'c4_natural_failure/coco_native_manifest.jsonl') if r['phase']==phase and 'C4' in args.cohorts]
    rows.extend([{**r,'event_id':r['base_id']+'__intact'} for r in c4]);bases.extend(c4)
    if args.split_file:
        if phase!='primary':raise ValueError('Prospective split applies to primary cohorts only')
        assignments=json.loads(Path(args.split_file).read_text())['assignments']
        for row in bases+rows:
            row.update(assignments[row['base_id']])
            if row['split'] not in ('discovery','confirmation'):raise ValueError('Excluded source overlap')
    # Controls have independent image preparation; unrelated images are resampled
    # to the recipient dimensions to keep visual token grid geometry fixed.
    features={}
    if phase=='primary':
        for base in [b for b in bases if b['cohort'] in ('C1','C3')]:
            small=open_image(base);w,h=small.size;small.thumbnail((128,128))
            pixels=np.asarray(small.convert('RGB')).astype(float)/255
            gray=pixels.mean(2)
            features[base['base_id']]=np.array([np.log(w/h),gray.mean(),gray.std(),
                np.abs(np.diff(gray,axis=0)).mean(),np.abs(np.diff(gray,axis=1)).mean()])
    for base in [b for b in bases if b['cohort'] in ('C1','C3')]:
        intact=next(r for r in rows if r['base_id']==base['base_id'] and r['condition']=='intact')
        donors=[b for b in bases if b['cohort']==base['cohort'] and b['base_id']!=base['base_id']]
        matching='same dataset domain and dimensions; complexity approximate'
        if phase=='primary':
            donors=[b for b in donors if b['dataset']==base['dataset'] and
                b.get('image_id',b['base_id'])!=base.get('image_id',base['base_id'])]
            if args.split_file:donors=[b for b in donors if b['split']==base['split']]
            if base['cohort']=='C3':
                donors=[b for b in donors if base['category'] not in b['object_inventory']]
            if not donors:raise ValueError('No valid unrelated donor for '+base['base_id'])
            donors.sort(key=lambda b:(float(np.linalg.norm(features[b['base_id']]-features[base['base_id']])),b['base_id']))
            matching='same dataset; distinct source image; nearest pre-generation aspect/brightness/contrast/edge-density feature vector; resized to recipient dimensions; C3 queried category absent from donor annotation inventory'
            if args.split_file:matching+='; donor restricted to recipient discovery/confirmation split'
        donor=donors[0];im=open_image(donor).resize(open_image(base).size,Image.Resampling.LANCZOS)
        path=asset_path(asset_root/base['base_id'],'condition','unrelated');im.save(path)
        rows.append({**intact,'condition':'unrelated','event_id':base['base_id']+'__unrelated','image_path':str(path),'unrelated_donor':donor['base_id'],'control_matching':matching})
        rows.append({**intact,'condition':'no_image','event_id':base['base_id']+'__no_image','image_path':None,'no_image':True})
    expected=12 if phase=='mechanics' else 24 if phase=='pilot' else len(bases)
    assert len(bases)==expected and len({r['base_id'] for r in bases})==expected
    write(OUT/f'cohort/{output_label}_base_manifest.jsonl',bases);write(OUT/f'cohort/{output_label}_manifest.jsonl',rows)
    (OUT/f'audit/{output_label}_stimulus_construction.json').write_text(json.dumps(audits,indent=2)+'\n')
    print(json.dumps(dict(bases=len(bases),conditions=len(rows)),indent=2))


if __name__=='__main__':main()
