"""Re-derive Stage6A mechanics checks from saved inputs, pixels and native tokens."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scripts.stage6a.build_mechanics import OUT, load
from scripts.stage6a.inventory import ROOT
from visual_reasoning.stage3b7.roi import map_changed_pixels_to_tokens
from visual_reasoning.stage6a.stimuli import rect_mask
from visual_reasoning.stage6a.segmentation import segment_native


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',default='mechanics');args=ap.parse_args();phase=args.phase
    rows=load(OUT/f'cohort/{phase}_manifest.jsonl');by_id={r['event_id']:r for r in rows}
    results={};inputs={};spans=[];maps=[];errors=[]
    paths=[]
    reuse_path=OUT/f'cohort/{phase}_reused_results.jsonl'
    if reuse_path.exists():paths.extend(ROOT/r['result_path'] for r in load(reuse_path))
    paths.extend((OUT/f'native/{phase}').glob('shard_*/examples/*/result.json'))
    for path in paths:
        result=json.loads(path.read_text());eid=result['event_id'];row=by_id[eid]
        data=json.loads((path.parent/'input.json').read_text());results[eid]=result;inputs[eid]=data
        if data['prompt']!=row['prompt'] or data['condition']!=row['condition']:errors.append([eid,'routing'])
        if row.get('no_image'):
            if data['visual_token_indices'] or data['image_grid_thw'] is not None or data['image_path'] is not None:errors.append([eid,'no_image'])
        else:
            im=Image.open(row['image_path']).convert('RGB')
            if hashlib.sha256(im.tobytes()).hexdigest()!=data['decoded_image_sha256']:errors.append([eid,'image_hash'])
            visual=data['visual_token_indices'];_,gh,gw=data['visual_mapping']['merged_grid_shape']
            if len(visual)!=gh*gw or len(set(visual))!=len(visual):errors.append([eid,'grid'])
            for source in ([row['target']] if row.get('target') else [])+row.get('other_sources',[]):
                mask=rect_mask(im.size,source['roi'])
                local=map_changed_pixels_to_tokens(mask,merged_rows=gh,merged_cols=gw)
                absolute=[visual[i] for i in local]
                # Independent pixel enumeration agrees with the frozen mapper.
                y,x=np.nonzero(mask);direct=sorted(set((y*gh//im.height*gw+x*gw//im.width).tolist()))
                if local!=direct or not local:errors.append([eid,'roi_map'])
                maps.append(dict(event_id=eid,base_id=row['base_id'],source_id=source['source_id'],
                    roi=source['roi'],local_token_indices=local,absolute_token_indices=absolute,
                    grid=[1,gh,gw],mapping_rule='Stage3B7 original-pixel floor projection to merged cells',
                    image_condition=row['condition'],roi_semantic_applicability='original image only' if row['condition']=='unrelated' else 'condition specific'))
        tokens=load(path.parent/'tokens.jsonl');generation=json.loads((path.parent/'generation.json').read_text())
        if ''.join(t['decoded_token'] for t in tokens)!=generation['raw_decoded_response']:errors.append([eid,'decode'])
        if [t['token_id'] for t in tokens]!=generation['generated_token_ids']:errors.append([eid,'token_ids'])
        segmented=segment_native(tokens)
        for span in segmented:
            a,b=span['token_start'],span['token_end']
            if not 0<=a<b<=len(tokens) or span['text']!=''.join(t['decoded_token'] for t in tokens[a:b]):errors.append([eid,'span_indices'])
            spans.append(dict(event_id=eid,base_id=row['base_id'],cohort=row['cohort'],**span))
    # Validate full mask/sham and semantic edits against original pixels.
    manipulation=[]
    for row in rows:
        name=row['condition'];eid=row['event_id'];base=row['base_id']
        if name not in ('mild','strong','mask','sham_mild','sham_strong','sham_mask','sham','counterfactual','counterfactual_render_sham'):continue
        intact=by_id[base+'__intact'];native=np.asarray(Image.open(intact['image_path']).convert('RGB'));edited=np.asarray(Image.open(row['image_path']).convert('RGB'))
        changed=np.any(native!=edited,axis=2)
        if name.startswith('counterfactual'):
            info=next(r for r in json.loads((OUT/f'audit/{phase}_stimulus_construction.json').read_text()) if r['base_id']==base)
            mask=rect_mask((native.shape[1],native.shape[0]),info['numeric_edit']['edit_roi'])
        else:
            kind='sham' if name.startswith('sham') else 'target'
            file=row.get('roi_mask_paths',{}).get(kind,str(OUT/'assets'/base/f'{kind}_mask.png'))
            mask=np.asarray(Image.open(file))>0
        exact=not bool((changed & ~mask).any())
        if not exact:errors.append([eid,'outside_mask_changed'])
        manipulation.append(dict(event_id=eid,changed_pixels=int(changed.sum()),mask_area=int(mask.sum()),outside_mask_exact=exact))
    no_image=[r for r in results.values() if r['condition']=='no_image']
    unrelated=[]
    for eid,data in inputs.items():
        if by_id[eid]['condition']=='unrelated':
            original=inputs.get(by_id[eid]['base_id']+'__intact')
            if original:
                different=data['decoded_image_sha256']!=original['decoded_image_sha256'];same_grid=data['image_grid_thw']==original['image_grid_thw']
                unrelated.append(dict(event_id=eid,different_image=different,same_grid=same_grid,fresh_prepare_recorded='fresh prepare' in data['image_state_policy']))
                if not different or not same_grid:errors.append([eid,'unrelated'])
    replays=[r for r in results.values() if r.get('native_replay')]
    expected_baselines=sum(r['condition'] in ('intact','AR') for r in rows)
    expected_replays=expected_baselines if phase.startswith('mechanics') else 0
    all_complete=len(results)==len(rows)
    checks={
      'all_planned_conditions_complete':all_complete,
      'deterministic_native_replay':len(replays)>=expected_replays and all(r['native_replay']['token_ids_exact'] and r['native_replay']['raw_text_exact'] for r in replays),
      'correct_image_variant_routing':all_complete and not any(e[1] in ('routing','image_hash') for e in errors),
      'exact_roi_visual_token_mapping':all_complete and bool(maps) and not any(e[1] in ('grid','roi_map') for e in errors),
      'no_op_native_self':len(replays)>=expected_replays and all(r['native_replay']['token_ids_exact'] for r in replays),
      'target_sham_mask_isolation':not any(e[1]=='outside_mask_changed' for e in errors),
      'counterfactual_source_isolation':all(r['outside_mask_exact'] for r in manipulation if 'counterfactual' in r['event_id']),
      'no_image_path_validity':len(no_image)==sum(bool(r.get('no_image')) for r in rows) and all(r['ended_with_eos'] for r in no_image) and not any(e[1]=='no_image' for e in errors),
      'unrelated_fresh_image_state':len(unrelated)==sum(r['condition']=='unrelated' for r in rows) and all(r['different_image'] and r['same_grid'] and r['fresh_prepare_recorded'] for r in unrelated),
      'trace_segmentation_exact':all_complete and bool(spans) and not any(e[1] in ('decode','span_indices') for e in errors),
      'annotation_indices_exact':all_complete and not any(e[1] in ('token_ids','span_indices','roi_map') for e in errors),
      'validation_primary_split_isolation':all(r.get('phase')==phase.split('_v')[0] for r in rows) and all(r.get('phase')==phase.split('_v')[0] for r in results.values()),
      'cohort_membership_blindness':all(r.get('membership_used_attention') is False and r.get('membership_used_causal_scores') is False for r in results.values()) and len(results)>0}
    report=dict(phase=phase,status='PASS' if all(checks.values()) else 'IN_PROGRESS' if not all_complete else 'FAIL',
        completed_conditions=len(results),planned_conditions=len(rows),native_replays=len(replays),
        eos_completions=sum(r['ended_with_eos'] for r in results.values()),checks=checks,errors=errors,
        limitation='No causal state comparison; raw artifacts support future extraction. Fresh-cache property follows fresh input preparation and unchanged generation reset; no cache donor supplied.')
    from scripts.stage6a.prepare_candidates import write
    write(OUT/f'traces/{phase}_reasoning_spans.jsonl',spans);write(OUT/f'regions/{phase}_roi_maps.jsonl',maps)
    for name,data in [(f'{phase}_validation',report),(f'{phase}_manipulation_audit',manipulation),(f'{phase}_unrelated_image_audit',unrelated)]:
        (OUT/'audit'/f'{name}.json').write_text(json.dumps(data,indent=2)+'\n')
    if phase=='mechanics':(OUT/'audit/mechanical_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
