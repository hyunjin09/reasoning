"""Freeze source edits and the12-image post2x2 using native semantic eligibility only."""
import os,copy,hashlib
import numpy as np
from PIL import Image
from transformers import AutoTokenizer
from scripts.stage10a.common import ROOT,DATA,load,save,sha,now,verify_config
from scripts.stage10a.edits import replace_fact
from visual_reasoning.stage9a3.dataset import render


def main():
    assert os.environ.get('SLURM_JOB_ID')
    cfg=verify_config();assert load(ROOT/'audit/gate_b_inference.json')['gate_b_pass']
    tokenizer=AutoTokenizer.from_pretrained(cfg['checkpoint'],local_files_only=True)
    selected=load(ROOT/'stage10a_event_selection.json');truth={r['query_id']:r for r in load(ROOT/'audit/fact_truth_after_selection.json')['rows']}
    edits={r['query_id']:r for r in load(ROOT/'audit/text_edit_annotations.json')['rows']}
    candidates=[r for r in selected['rows'] if r['split']=='primary' and truth[r['query_id']]['fact_correct'] and not r['post_contains_option_binding']]
    assert len(candidates)==12 and sum(r['attribute']=='color' for r in candidates)==6
    candidates.sort(key=lambda r:hashlib.sha256(('stage10a-v1-920260927:'+r['image_id']).encode()).hexdigest())
    scenes={r['image_id']:r for r in load(DATA/'stage9a3_synthetic_dataset_manifest.json')['rows']}
    rows=[];annotations=[];image_dir=ROOT/'counterfactual_images';image_dir.mkdir(exist_ok=True)
    for e in candidates:
        original=scenes[e['image_id']];rerender=image_dir/f'{e["image_id"]}_original_check.png';assert not rerender.exists()
        render(original,rerender)
        with Image.open(original['image_path']) as im:old_pixels=np.asarray(im.convert('RGB'))
        with Image.open(rerender) as im:check_pixels=np.asarray(im.convert('RGB'))
        assert np.array_equal(old_pixels,check_pixels),'Original renderer pixels changed'
        scene=copy.deepcopy(original);attr=e['attribute'];target=e['target']
        eligible=[o for o in scene['objects'] if o[attr]!=target]
        eligible.sort(key=lambda o:((o['angle']%90!=0) if attr=='shape' and target=='square' else False,-o['diameter'],o['object_id']))
        chosen=eligible[0];object_id=chosen['object_id'];old_value=chosen[attr];chosen[attr]=target
        count=sum(o[attr]==target for o in scene['objects']);assert count==e['emitted_count']+1<=5
        diffs=[(a['object_id'],k) for a,b in zip(original['objects'],scene['objects']) for k in a if a[k]!=b[k]]
        assert diffs==[(object_id,attr)]
        cf_path=image_dir/f'{e["image_id"]}_counterfactual.png';assert not cf_path.exists();render(scene,cf_path)
        with Image.open(cf_path) as im:changed=np.asarray(im.convert('RGB'))
        assert not np.array_equal(old_pixels,changed)
        original_prefix=e['anchors']['post']['prefix_text']; cf_prefix=replace_fact(original_prefix,e['pre_char'],e['emit_char'],edits[e['query_id']]['counterfactual'])
        assert original_prefix[e['pre_char']:e['emit_char']]==e['fact_text']
        annotation=dict(query_id=e['query_id'],image_id=e['image_id'],attribute=attr,target=target,
            original_count=e['emitted_count'],counterfactual_count=count,object_id=object_id,old_value=old_value,new_value=target,
            original_pixel_identity_verified=True,original_rerender_sha256=sha(rerender),counterfactual_image_path=str(cf_path),
            counterfactual_image_sha256=sha(cf_path),changed_scene=scene,only_changed_scene_field=diffs,
            original_fact=e['fact_text'],counterfactual_fact=edits[e['query_id']]['counterfactual'],
            later_text_unchanged=original_prefix[e['emit_char']:],source_edit_rule='Largest eligible object; upright preferred for square targets; ties by object_id.')
        annotations.append(annotation)
        for i,t in [(0,0),(1,0),(0,1),(1,1)]:
            condition=f'I{i}T{t}';key=f'{e["query_id"]}_{condition}_post';dest=ROOT/'dominance/results'/key
            prefix=cf_prefix if t else original_prefix
            ids=tokenizer.encode(prefix,add_special_tokens=False) if t else e['anchors']['post']['prefix_ids']
            assert tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)==prefix
            assert 0<len(ids)<512 and 151668 not in ids
            task=dict(e['task'])
            if i:task.update(image_path=str(cf_path),image_sha256=sha(cf_path))
            rows.append(dict(task_id=key,query_id=e['query_id'],image_id=e['image_id'],attribute=attr,anchor='post',condition=condition,
                image_cf=bool(i),text_cf=bool(t),task=task,prefix_ids=ids,prefix_text=prefix,prefix_tokens=len(ids),remaining_tokens=512-len(ids),
                original_count=e['emitted_count'],counterfactual_count=count,generation_path=str(dest/'generation.json'),result_path=str(dest/'result.json')))
    save(ROOT/'audit/dominance_annotations.json',dict(at=now(),frozen=True,rows=annotations,
        selection_rule='All12 primary events with correct native emitted fact and no option binding at the already-frozen post anchor;6color/6shape. No intervention effect ranking.',
        outcomes_used_for_selection=False,pre_not_run='The selected fact has not been emitted at pre; injecting it would invent a self-generated pre fact.',
        limitation='Only the selected first fact is edited. Later native recounts retain the original value; this is not an edit of every occurrence of the count.'))
    paths=['scripts/stage10a/common.py','scripts/stage10a/runtime.py','scripts/stage10a/image_text.py','scripts/stage10a/prepare_dominance.py',
        'scripts/stage10a/validate_dominance.py','scripts/stage10a/worker_dominance.py','scripts/stage10a/analyze_dominance.py',
        'code/visual_reasoning/stage9a3/dataset.py']
    save(ROOT/'audit/dominance_manifest.json',dict(at=now(),frozen=True,stage='dominance',rows=rows,n_images=12,logical_continuations=48,
        config_sha256=sha(ROOT/'config.json'),selection_sha256=sha(ROOT/'stage10a_event_selection.json'),
        gate_b_sha256=sha(ROOT/'audit/gate_b_inference.json'),annotations_sha256=sha(ROOT/'audit/dominance_annotations.json'),
        source_sha256={p:sha(p) for p in paths}))
    print('FROZEN_DOMINANCE',len(rows),'IMAGES',len(annotations),flush=True)


if __name__=='__main__':main()
