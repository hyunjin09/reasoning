"""Prepare native layouts and source maps for the semantically selected prefix."""
from pathlib import Path
from collections import Counter
import numpy as np
from PIL import Image,ImageDraw
from transformers import AutoProcessor
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,write_jsonl,sha
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b7.roi import map_changed_pixels_to_tokens,cell_darkness
from visual_reasoning.stage5a.protocol import select_natural,select_atlas
from visual_reasoning.stage5a.sources import source_pixel_mask,event_groups


def main():
    if (OUT/'cohort/cohort_freeze_complete.json').exists():raise RuntimeError('Cohort already frozen')
    cfg=read_json(OUT/'config/stage5a_config.json')
    records=[r for p in sorted((OUT/'annotations').glob('provisional_manual_*.jsonl')) for r in read_jsonl(p)]
    for p in sorted((OUT/'cohort/review').glob('manual_*_span_audit.json')):
        assert read_json(p)['passed'],str(p)
    natural=select_natural(records);atlas=select_atlas(natural);atlas_ids={r['base'] for r in atlas}
    assert len(natural)==200 and len(atlas)==128
    processor=AutoProcessor.from_pretrained(cfg['model_checkpoint'],local_files_only=True)
    dataset={str(r['sample_index']):r for r in load_mathverse_rows(Path(cfg['dataset_root']))}
    for item in natural:
        b=item['base'];target=OUT/'source_assets'/b;path=target/'metadata.json'
        if path.exists():
            if read_json(path)['provisional_annotation_sha256']!=sha(OUT/('annotations/provisional_'+Path(item['events'][0]['review_evidence']).stem+'.jsonl')):
                raise RuntimeError(f'Annotation changed after source build: {b}')
            continue
        with Image.open(item['source_image']) as im:native=im.convert('RGB')
        array=np.asarray(native);prepared,meta=prepare_custom_image(processor,dataset[item['example_id']],Path(item['source_image']),device='cpu')
        old=read_json(ROOT/item['artifact_dir']/'input.json')
        assert old['generation_query']==str(dataset[item['example_id']].get('query_cot') or dataset[item['example_id']].get('question') or '')
        assert old['prompt_token_count']==meta['prompt_token_count'] and old['visual_token_indices']==meta['visual_token_indices']
        grid=meta['visual_mapping']['merged_grid_shape'];_,rows,cols=grid
        maps={k:map_changed_pixels_to_tokens(source_pixel_mask(f,array.shape),merged_rows=rows,merged_cols=cols) for k,f in item['facts'].items()}
        dark=cell_darkness(array,merged_rows=rows,merged_cols=cols)
        events=[]
        for e in item['events']:
            g=event_groups(e,item['facts'],maps,meta['visual_token_indices'],grid,dark)
            assert g['source_groups']['T']
            events.append({**e,**g})
        value={**item,'events':events,'prompt_metadata':meta,'roi_mapping':maps,'source_mapping_method':'all native pixels in reviewed source boxes, projected to exact merged visual grid; disjoint boxes use union',
               'native_generation_layout_exact':True,'native_generation_query_exact':True,'roi_reviewed':True,
               'atlas_selected':b in atlas_ids,'paths':{'O':item['source_image']},'image_sha256':{'O':sha(item['source_image'])},
               'provisional_annotation_sha256':sha(OUT/('annotations/provisional_'+Path(item['events'][0]['review_evidence']).stem+'.jsonl')),
               'metadata_path':str(path.relative_to(ROOT)),'cf_assets':{},'cf_reviewed':False}
        write_json(path,value)
        # Source/control overlays are review evidence, never an attention map.
        sheet=Image.new('RGB',(330*len(events),300),'white');d=ImageDraw.Draw(sheet)
        for j,e in enumerate(events):
            layer=Image.new('RGBA',native.size);draw=ImageDraw.Draw(layer)
            for k,color in [('I',(50,180,70,140)),('X',(20,40,230,140)),('M',(170,20,200,140)),('T',(240,50,30,140))]:
                for i in e['local_source_groups'].get(k,[]):
                    y,x=divmod(i,cols);draw.rectangle([x*native.width//cols,y*native.height//rows,(x+1)*native.width//cols-1,(y+1)*native.height//rows-1],fill=color)
            im=Image.alpha_composite(native.convert('RGBA'),layer).convert('RGB');im.thumbnail((320,270));sheet.paste(im,(330*j,25));d.text((330*j+3,3),e['event_id']+' T red I green X blue M purple',fill='black')
        sheet.save(target/'source_control_overlay.png')
        print(f'base={b} atlas={b in atlas_ids} events={len(events)} maps=pass',flush=True)
        del prepared
    write_jsonl(OUT/'cohort/provisional_natural.jsonl',[{'base_problem_id':r['base'],'metadata_path':f'outputs/stage5a/source_assets/{r["base"]}/metadata.json'} for r in natural])
    write_jsonl(OUT/'cohort/provisional_atlas.jsonl',[{'base_problem_id':r['base'],'metadata_path':f'outputs/stage5a/source_assets/{r["base"]}/metadata.json'} for r in atlas])
    write_json(OUT/'audit/source_preparation.json',{'natural':len(natural),'atlas':len(atlas),'atlas_local_incorrect_bases':sum(r['local_incorrect'] for r in atlas),'natural_cutoff':natural[-1]['screen_order'],'before_causal_scoring':True})


if __name__=='__main__':main()
