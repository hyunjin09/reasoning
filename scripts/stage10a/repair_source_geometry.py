"""Version one source identity before science; preserve all v1 frozen artifacts."""
import os,copy
from PIL import Image
import numpy as np
from scripts.stage10a.common import ROOT,DATA,load,save,sha,now
from visual_reasoning.stage9a3.dataset import render


def main():
    assert os.environ.get('SLURM_JOB_ID')
    assert not list((ROOT/'dominance/results').glob('*/result.json'))
    old_mp=ROOT/'audit/dominance_manifest.json';m=load(old_mp)
    old_ap=ROOT/'audit/dominance_annotations.json';a=load(old_ap)
    old_vp=ROOT/'audit/dominance_validation.json';v=load(old_vp)
    assert v['pass_all'] and v['manifest_sha256']==sha(old_mp)
    for p,d in m['source_sha256'].items():assert sha(p)==d,p
    scene=copy.deepcopy(next(r for r in load(DATA/'stage9a3_synthetic_dataset_manifest.json')['rows'] if r['image_id']=='image007'))
    eligible=[o for o in scene['objects'] if o['shape']!='square']
    eligible.sort(key=lambda o:(o['angle']%90!=45,-o['diameter'],o['object_id']))
    chosen=eligible[0];assert chosen['object_id']==1 and chosen['angle']%90==45 and chosen['color']=='blue'
    old_value=chosen['shape'];chosen['shape']='square'
    dest=ROOT/'counterfactual_images/image007_counterfactual_v2.png';assert not dest.exists();render(scene,dest)
    assert sum(o['shape']=='square' for o in scene['objects'])==2
    annotation=next(r for r in a['rows'] if r['query_id']=='image007_shape')
    annotation.update(object_id=chosen['object_id'],old_value=old_value,counterfactual_image_path=str(dest),
        counterfactual_image_sha256=sha(dest),changed_scene=scene,only_changed_scene_field=[(chosen['object_id'],'shape')],
        source_edit_rule='Largest eligible object, upright angle45 modulo90 preferred for square targets, ties by object_id.')
    changed=[]
    for r in m['rows']:
        if r['query_id']=='image007_shape' and r['image_cf']:
            r['task'].update(image_path=str(dest),image_sha256=sha(dest));changed.append(r['task_id'])
    assert len(changed)==2
    ap=ROOT/'audit/dominance_v2_annotations.json';mp=ROOT/'audit/dominance_v2_manifest.json'
    a.update(at=now(),version=2,supersedes_annotations_sha256=sha(old_ap),reason='Pre-outcome source-geometry correction; angle0 renders a rotated square, while45 renders upright.')
    save(ap,a)
    sources=dict(m['source_sha256']);sources.pop('scripts/stage10a/worker_dominance.py');sources.pop('scripts/stage10a/analyze_dominance.py')
    for p in ('scripts/stage10a/worker_dominance_v2.py','scripts/stage10a/analyze_dominance_v2.py','scripts/stage10a/repair_source_geometry.py'):sources[p]=sha(p)
    m.update(at=now(),stage='dominance_v2',version=2,supersedes_manifest_sha256=sha(old_mp),annotations_sha256=sha(ap),source_sha256=sources)
    save(mp,m)
    save(ROOT/'audit/dominance_v2_validation.json',dict(at=now(),pass_all=True,examples=2,manifest_sha256=sha(mp),
        validation_reused=True,original_validation_path=str(old_vp),original_validation_sha256=sha(old_vp),
        reason='Only scientific source-object choice changed before outcomes; fresh multimodal runtime and disjoint technical tasks are byte-identical to the two successful checks.',
        unchanged_runtime_sha256={p:sha(p) for p in ('scripts/stage10a/runtime.py','scripts/stage10a/image_text.py','scripts/stage10a/validate_dominance.py')}))
    save(ROOT/'audit/source_geometry_repair.json',dict(at=now(),diagnosis='supported',before_scientific_outcomes=True,
        observation='Visual review showed image007 source edit as a diamond. Renderer square vertices use angle+pi/2; axis-aligned edges need45 modulo90.',
        evidence=['code/visual_reasoning/stage9a3/dataset.py',str(old_ap),'outputs/stage10a/v1/counterfactual_images/image007_counterfactual.png'],
        changed_tasks=changed,original_manifest_path=str(old_mp),original_manifest_sha256=sha(old_mp),
        active_manifest_path=str(mp),active_manifest_sha256=sha(mp),cohort_conditions_anchors_unchanged=True,
        additional_gpu_validation_runs=0))
    print('FROZEN_DOMINANCE_V2',len(m['rows']),'changed source task inputs',changed,flush=True)


if __name__=='__main__':main()
