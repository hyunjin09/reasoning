"""Build pending factorial assets, local readouts and attention-blind token maps."""
import math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from transformers import AutoProcessor
from scripts.stage4a.prepare_config import ROOT,OUT,read_json,read_jsonl,write_json,write_jsonl,sha
from visual_reasoning.stage4a.edits import render_factorial,validate_factorial,review_sheet,CONDITIONS
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c8.fresh import exact_numeric_candidate
from visual_reasoning.stage3b7.roi import map_changed_pixels_to_tokens,fixed_ring,cell_darkness,choose_matched_irrelevant


def main():
    config=read_json(OUT/'config/stage4a_config.json')
    processor=AutoProcessor.from_pretrained(config['model_checkpoint'],local_files_only=True)
    dataset={str(r['sample_index']):r for r in load_mathverse_rows(Path(config['dataset_root']))}
    records=[]
    for item in read_jsonl(OUT/'cohort/manual_annotations.jsonl'):
        if item.get('candidate_excluded'):continue
        base=item['base_problem_id'];target=OUT/'counterfactual_assets'/base
        if item.get('asset_revision',1)>1:target=target/f"attempt_{item['asset_revision']:02d}"
        metadata_path=target/'metadata.json'
        if metadata_path.exists():records.append(read_json(metadata_path));continue
        if (target/'automatic_validation_failure.json').exists():
            print(f'base={base} priorfailedconstructionpreserved; explicitrevisionrequired',flush=True);continue
        target.mkdir(parents=True,exist_ok=True)
        with Image.open(item['source_image']) as handle:native=handle.convert('RGB')
        arrays,specs=render_factorial(native,item['facts']);checks=validate_factorial(arrays,item['facts'])
        paths={c:target/(c+'.png') for c in CONDITIONS}
        for c in CONDITIONS:Image.fromarray(arrays[c]).save(paths[c])
        review_sheet(arrays,item['facts'],target/'review_sheet.png')
        if not checks['passed']:
            write_json(target/'automatic_validation_failure.json',{'base_problem_id':base,'facts':item['facts'],
                       'render_specs':specs,'validation':checks,'causal_scores_available':False})
            print(f'base={base} pixelorprotectedstrokevalidationfailed; reviewrequired',flush=True);continue
        prep={};meta={}
        for c in CONDITIONS:prep[c],meta[c]=prepare_custom_image(processor,dataset[item['example_id']],paths[c],device='cpu')
        m=meta['OO'];grid=m['visual_mapping']['merged_grid_shape'];temporal,rows,cols=grid
        assert temporal==1
        for c in CONDITIONS:
            assert meta[c]['prompt_token_ids']==m['prompt_token_ids']
            assert meta[c]['visual_token_indices']==m['visual_token_indices']
            assert meta[c]['image_grid_thw']==m['image_grid_thw']
        original_input=read_json(ROOT/item['artifact_dir']/'input.json')
        native_query=str(dataset[item['example_id']].get('query_cot') or dataset[item['example_id']].get('question') or '')
        assert original_input['generation_query']==native_query
        assert original_input['prompt_token_count']==m['prompt_token_count']
        assert original_input['visual_token_indices']==m['visual_token_indices']
        groups={};maps={}
        for x,c in [('A','AO'),('B','OB')]:
            changed=np.any(arrays['OO']!=arrays[c],axis=2)|np.any(arrays['OO']!=arrays[x+'_sham'],axis=2)
            projected=map_changed_pixels_to_tokens(changed,merged_rows=rows,merged_cols=cols)
            # Qwen packs the four spatial-merge patches consecutively per token.
            # Include resized interpolation support measured directly in patch input.
            patch_changed=(prep['OO']['pixel_values']!=prep[c]['pixel_values']).any(dim=1)
            patch_changed|=(prep['OO']['pixel_values']!=prep[x+'_sham']['pixel_values']).any(dim=1)
            assert len(patch_changed)==rows*cols*4
            touched=patch_changed.reshape(rows*cols,4).any(dim=1).nonzero().flatten().tolist()
            local=sorted(set(projected)|set(touched));groups[x]=[m['visual_token_indices'][i] for i in local]
            maps[x]={'source_pixel_projection':projected,'resized_patch_support':touched,'local_positions':local,
                     'count':len(local),'method':'union of exact edited-pixel projection and measured resized patch support'}
        overlap=sorted(set(groups['A'])&set(groups['B']))
        irrelevant={};dark=cell_darkness(arrays['OO'],merged_rows=rows,merged_cols=cols)
        excluded=sorted(set(fixed_ring(maps['A']['local_positions'],merged_rows=rows,merged_cols=cols,radius=1))|
                        set(fixed_ring(maps['B']['local_positions'],merged_rows=rows,merged_cols=cols,radius=1)))
        for x in ['A','B']:
            try:
                local,audit=choose_matched_irrelevant(target_local=maps[x]['local_positions'],excluded_local=excluded,darkness_by_cell=dark)
                if not math.isfinite(audit['distance_from_target_center']):audit['distance_from_target_center']=None
                irrelevant[x]={'local_positions':local,'audit':audit,'manual_review':'pending'}
                groups['I_'+x]=[m['visual_token_indices'][i] for i in local]
            except ValueError as error:irrelevant[x]={'unavailable':str(error)}
        tokens=read_jsonl(ROOT/item['artifact_dir']/'tokens.jsonl');events={}
        for e,event in item['events'].items():
            candidate=exact_numeric_candidate(tokens=tokens,match_start=event['match_start'],match_end=event['match_end'],
                       counterfactual_value=item['facts'][event['fact']]['counterfactual_value'],tokenizer=processor.tokenizer)
            assert candidate['ed_generated_index']==event['candidate_start_token']
            events[e]={**event,**candidate}
        result={**item,'render_specs':specs,'paths':{c:str(p.relative_to(ROOT)) for c,p in paths.items()},
                'asset_sha256':{c:sha(p) for c,p in paths.items()},'pixel_validation':checks,'layout_exact':True,
                'native_generation_layout_exact':True,'prompt_metadata':m,'source_groups':groups,'roi_mapping':maps,
                'native_generation_query_exact':True,'generation_query':native_query,
                'irrelevant_mapping':irrelevant,'A_B_overlap':overlap,'token_map_validated':not overlap,
                'events':events,'manual_asset_review':'pending','metadata_path':str(metadata_path.relative_to(ROOT))}
        overlay=native.convert('RGBA');layer=Image.new('RGBA',overlay.size,(0,0,0,0));draw=ImageDraw.Draw(layer)
        for x,color in [('A',(230,30,30,100)),('B',(30,70,230,100))]:
            for i in maps[x]['local_positions']:
                row,col=divmod(i,cols);draw.rectangle([col*native.width//cols,row*native.height//rows,(col+1)*native.width//cols-1,(row+1)*native.height//rows-1],fill=color)
        Image.alpha_composite(overlay,layer).convert('RGB').save(target/'roi_overlay.png')
        write_json(metadata_path,result);records.append(result)
        print(f'base={base} pixels=pass layout=pass tokensA={len(groups["A"])} tokensB={len(groups["B"])} overlap={overlap}',flush=True)
        del prep
    write_jsonl(OUT/'cohort/assets_pending.jsonl',[{k:r[k] for k in ['base_problem_id','example_id','screen_order','metadata_path','A_B_overlap','manual_asset_review']} for r in records])


if __name__=='__main__':main()
