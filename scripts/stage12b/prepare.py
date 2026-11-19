"""Freeze source-preserving requests before any Stage12B generation."""
import hashlib, random
from pathlib import Path
from scripts.stage12b.common import ROOT, CAPS, load, save, sha, now
from scripts.stage12b.protocol import build_prompt

def main():
    original=Path('outputs/stage12a/v1/stage12a_frozen_e_star_manifest.json')
    source=load(original);rows=source['rows'];plan=Path('plan/stage12b_visual_failure_bottleneck_profiling_plan.md')
    assert len(rows)==61 and sum(len(r['facts']) for r in rows)==157
    assert not (ROOT/'generations').exists()
    for r in rows:assert sha(r['image'])==r['image_sha256']
    for src,dst in [(original,ROOT/'audit/frozen_stage12a_manifest.json'),(plan,ROOT/'audit/approved_plan.md')]:
        with dst.open('xb') as f:f.write(src.read_bytes())
    old=load('outputs/stage12ar/v1/config.json');model=load('outputs/stage9a4/v1/config.json')
    cfg={k:old[k] for k in ['environment','recipe','runtime']}
    cfg.update(at=now(),model={k:model[k] for k in ['checkpoint','revision','files_sha256']},
        caps=CAPS,source_manifest_sha256=sha(original),seed_policy='int(SHA256(stage12a-gen-v1|family_id)[:8],16) mod2**31; same seed E/N/O',
        bootstrap_seed=120220260929,bootstrap_draws=4000,resource=dict(target_gpu_hours=6,hard_gpu_hours=8,max_concurrent_gpus=8),
        technical_gate=dict(E='parseable>=10,repetition<=1',N='final>=10,caps<=1,repetition<=1',O='final>=10,caps<=1,repetition<=1'),
        oracle_rendering='Exact frozen probe_request followed by exact gold_value: request supplies existing entity binding, especially bare values. No new fact or derivation.')
    cfg['runtime']['batch_size']=18
    cfg['model']['name']=model['model']
    for name,h in cfg['model']['files_sha256'].items():assert sha(Path(model['checkpoint'])/name)==h,name
    cfg['source_sha256']={str(p):sha(p) for p in Path('scripts/stage12b').glob('*.py')}
    for p in ['scripts/stage12b/run.sh','scripts/stage11cr/protocol.py','outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision/run_mathv.py','code/visual_reasoning/stage8b/v2_scoring.py']:
        cfg['source_sha256'][p]=sha(p)
    save(ROOT/'config.json',cfg)
    ids=source['technical_selection']['ids'];tasks=[]
    for r in rows:
        for a in 'ENO':
            tasks.append(dict(task_id=f'{a}_{r["item_id"]}_v1',item_id=r['item_id'],family_id=r['family_id'],arm=a,
                prompt_version=1,prompt=build_prompt(r,a),image=r['image'] if a!='O' else None,
                image_sha256=r['image_sha256'] if a!='O' else None,answer_type=r['answer_type'],
                cap=CAPS[a],seed=int(hashlib.sha256(('stage12a-gen-v1|'+r['family_id']).encode()).hexdigest()[:8],16)%(2**31)))
    save(ROOT/'stage12b_frozen_manifest.json',dict(at=now(),frozen=True,n_families=61,n_facts=157,
        source=str(original),source_sha256=sha(original),plan_sha256=sha(plan),config_sha256=sha(ROOT/'config.json'),
        technical_ids=ids,technical_selection=source['technical_selection'],rows=rows,tasks=tasks))
    for a,name in [('E','evidence_probe'),('N','native'),('O','oracle')]:
        save(ROOT/f'stage12b_{name}_prompts.json',dict(at=now(),arm=a,rows=[t for t in tasks if t['arm']==a]))
    # Same fixed12 selected before Stage12A outcomes. No correctness-based replacement.
    for shard in range(2):
        selected=ids[shard::2]
        tt=[next(t for t in tasks if t['item_id']==i and t['arm']==a) for i in selected for a in 'ENO']
        save(ROOT/f'audit/technical_{shard}.json',dict(at=now(),frozen=True,phase='technical',config_sha256=sha(ROOT/'config.json'),rows=tt))
    ordered=sorted(rows,key=lambda r:r['family_id'])
    sampled=random.Random(120220260929).sample(ordered,13)
    save(ROOT/'audit/oracle_second_review_selection.json',dict(at=now(),seed=120220260929,
        rule='random.Random(seed).sample(sorted61byfamily_id,13)',ids=[r['item_id'] for r in sampled],
        outcome_inspection=False))
    print('Prepared183 calls; technical',ids,'secondreview',[r['item_id'] for r in sampled])

if __name__=='__main__':main()
