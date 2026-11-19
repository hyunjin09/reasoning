"""After L0, exact-match old evidence and merge identical-anchor aliases."""
from pathlib import Path
from scripts.stage10ar.common import ROOT,OLD,PRIOR,load,save,sha,now,verify_config


def main():
    cfg=verify_config();validation=load(ROOT/'audit/technical_validation.json');assert validation['pass_all']
    assert cfg['annotations_sha256']==sha(ROOT/'stage10ar_anchor_annotations.json')
    events={r['query_id']:r for r in load(ROOT/'stage10ar_anchor_annotations.json')['rows']}
    cohort=load(ROOT/'stage10ar_primary_cohort.json');external={}
    oldcfg=load(OLD/'config.json');priorcfg=load(PRIOR/'config.json')
    assert oldcfg['checkpoint']==cfg['checkpoint']==priorcfg['checkpoint']
    assert oldcfg['seed']==cfg['seed']==priorcfg['seed'] and oldcfg['max_new_tokens']==cfg['max_total_tokens']==priorcfg['max_total_tokens']
    tasks={r['query_id']:r for r in load(OLD/'audit/inference_tasks.json')['rows']}
    for q,e in events.items():assert e['task']==tasks[q]
    for r in load(OLD/'audit/t1_manifest.json')['rows']:
        if r['cutoff']==0 and r['mode']=='standard':external[r['query_id'],'image_off',0]=(r,OLD/'audit/t1_manifest.json')
    for r in load(PRIOR/'audit/gate_a_manifest.json')['rows']:
        external[r['query_id'],r['condition'],r['prefix_tokens']]=(r,PRIOR/'audit/gate_a_manifest.json')
    rows=[];seen={};reused=0
    for q in cohort['primary_ids']:
        e=events[q]
        for anchor,a in e['anchors'].items():
            if a is None:continue
            for condition in ('image_off','text_only'):
                key=(q,condition,a['native_tokens']);task_id=f'{q}_{condition}_{anchor}';dest=ROOT/'primary/results'/task_id
                row=dict(task_id=task_id,query_id=q,image_id=e['image_id'],attribute=e['attribute'],target=e['target'],anchor=anchor,condition=condition,
                    prefix_tokens=a['native_tokens'],prefix_ids=a['prefix_ids'],remaining_tokens=a['remaining_tokens'],
                    generation_path=str(dest/'generation.json'),result_path=str(dest/'result.json'),execution='run')
                if key in seen:
                    original=seen[key];row.update(execution='alias',canonical_task_id=original['task_id'],
                        generation_path=original['generation_path'],result_path=original['result_path'])
                elif key in external:
                    old,mp=external[key];receipt=load(old['result_path']);g=load(old['generation_path'])
                    assert receipt['generation_sha256']==sha(old['generation_path'])
                    assert receipt['manifest_sha256']==sha(mp)
                    n=a['native_tokens'];assert g['generated_token_ids'][:n]==a['prefix_ids'] and g['tokens']<=512
                    dest=ROOT/'primary/reused'/task_id
                    row.update(execution='reuse',generation_path=str(dest/'generation.json'),result_path=str(dest/'result.json'),
                        source_generation_path=old['generation_path'],source_result_path=old['result_path'])
                    g=dict(g,prefix_tokens=n,continuation_token_ids=g['generated_token_ids'][n:],continuation_tokens=g['tokens']-n)
                    if 'continuation_text' not in g:
                        assert n==0
                        g['continuation_text']=g['text']
                    save(row['generation_path'],g)
                    save(row['result_path'],dict(at=now(),reused=True,query_id=q,condition=condition,anchor=anchor,
                        generation_sha256=sha(row['generation_path']),source_generation_path=old['generation_path'],source_result_path=old['result_path'],
                        source_generation_sha256=sha(old['generation_path']),source_result_sha256=sha(old['result_path']),
                        source_manifest_path=str(mp),source_manifest_sha256=sha(mp),prefix_tokens=n,input=receipt['input'],
                        equivalence='Same task/checkpoint/seed/cap/precision/backend; exact native prefix. A0 ZERO equivalence independently validated.',
                        config_sha256=sha(ROOT/'config.json')))
                    reused+=1
                if key not in seen:seen[key]=row
                rows.append(row)
    paths=['scripts/stage10ar/common.py','scripts/stage10ar/runtime.py','scripts/stage10ar/protocol.py','scripts/stage10ar/worker.py',
        'scripts/stage10a/runtime.py','code/visual_reasoning/stage9a3/access.py','code/visual_reasoning/stage9a_dynamics/generation.py']
    save(ROOT/'audit/primary_manifest.json',dict(at=now(),frozen=True,rows=rows,query_order=cohort['primary_ids'],
        config_sha256=sha(ROOT/'config.json'),validation_sha256=sha(ROOT/'audit/technical_validation.json'),
        source_sha256={p:sha(p) for p in paths},logical_continuations=len(rows),unique_continuations=len(seen),
        reused_continuations=reused,new_continuations=len(seen)-reused,aliases=len(rows)-len(seen)))
    save(ROOT/'audit/resource_estimate.json',dict(at=now(),new_continuations=len(seen)-reused,reused_continuations=reused,
        logical_continuations=len(rows),unique_continuations=len(seen),aliases=len(rows)-len(seen),
        remaining_generation_upper_gpu_hours=sum(r['remaining_tokens']*.06/3600 for r in rows if r['execution']=='run'),
        startup_validation_allowance_gpu_hours=.5,target_gpu_hours=3,hard_projected_gpu_hours=5,max_gpus=8))
    print('MANIFEST',len(rows),'logical',len(seen),'unique',reused,'reused',len(seen)-reused,'new',flush=True)


if __name__=='__main__':main()
