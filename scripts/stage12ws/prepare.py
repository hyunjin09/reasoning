"""Freeze source-derived block material, aliases, seeds and Phase A before replay."""
from pathlib import Path
from scripts.stage12ws.common import ROOT,load,save,sha,now
from scripts.stage12ws.blocks import MAP
from scripts.stage12ws.protocol import seed,partition,retain,order_blocks,DERIVED

def textfile(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:f.write(text)
    return str(path)

def main():
    assert not ROOT.exists(), 'Never replace a frozen study'
    prior=Path('outputs/stage12vs/v1');old=load(prior/'config.json')
    history={str(p):sha(p) for parent in ['outputs','reports','scripts'] for folder in sorted(Path(parent).glob('stage12*'))
             if folder.name!='stage12ws' for p in sorted(folder.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    save(ROOT/'audit/preserved_history.json',dict(at=now(),files=history))
    textfile(ROOT/'audit/reports_index_before.md',Path('reports/index.md').read_text())
    cfg=dict(old,at=now(),arms={'I':old['arms']['I']},seed_rule='SHA256(stage12ws-v1|family_id|replicate) fullint modulo2**31',
             resource=dict(target_gpu_hours=6,hard_gpu_hours=8,max_concurrent_gpus=8))
    runtime=['common.py','protocol.py','worker.py','run.sh','launch.py','review.py','scoring.py']
    cfg['runtime_source_sha256']={str(Path('scripts/stage12ws')/n):sha(Path('scripts/stage12ws')/n) for n in runtime}
    for n in ['scripts/stage12us/protocol.py','scripts/stage12ts/worker.py','scripts/qwen3vl_official_eval/common.py','code/visual_reasoning/stage8b/v2_scoring.py']:
        cfg['runtime_source_sha256'][n]=sha(n)
    save(ROOT/'config.json',cfg)
    textfile(ROOT/'stage12ws_distributed_state_spec.md','Frozen at '+now()+'\n\n'+Path('scripts/stage12ws/spec.md').read_text())
    primary=load(prior/'stage12vs_primary_manifest.json');ss=load(prior/'stage12vs_semantic_steps.json')['rows']
    source=load(prior/'stage12vs_coarse_prefix_manifest.json')['families']
    oracle={r['item_id']:r for r in load('outputs/stage12bs/v1/stage12bs_full_manifest.json')['tasks'] if r['arm']=='O'}
    orig_oracle={r['item_id']:r for r in load('outputs/stage12b/v1/stage12b_oracle_prompts.json')['rows']}
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(cfg['arms']['I']['model']['checkpoint'],local_files_only=True)
    families=[];annotations=[];seeds=[];tasks=[]
    for src in source:
        item=src['item_id'];family=src['family_id'];steps=[s for s in ss if s['item_id']==item]
        full=Path(src['source_prefix_path']).read_text();assert ''.join(s['text'] for s in steps)==full
        assert sha(src['source_prefix_path'])==src['source_prefix_sha256']
        blocks=partition([s['text'] for s in steps],[b[0] for b in MAP[item]])
        for b,a in zip(blocks,MAP[item]):
            b.update(role=a[1],token_count=len(tok.encode(b['text'],add_special_tokens=False)))
            p=ROOT/'blocks'/f"{item}_B{b['block_id']}.txt";textfile(p,b['text'])
            b.update(path=str(p),sha256=sha(p))
            keys=['boundary_rationale','direct_image_derived_propositions','derived_propositions','new_entity_bindings','new_intermediate_values','corrections','contradictions_or_reopenings','repeated_propositions']
            annotations.append(dict(item_id=item,block_id=b['block_id'],start_step=b['start_step'],end_step=b['end_step'],role=b['role'],token_count=b['token_count'],**dict(zip(keys,a[2:]))))
        assert oracle[item]['prompt']==orig_oracle[item]['prompt'] and oracle[item]['image'] is None
        derived=[b['block_id'] for b in blocks if b['role'] in DERIVED];order=order_blocks(blocks)
        ids=[b['block_id'] for b in blocks]
        texts={'FULL':full,'Q':'','ESTAR':'','ESTAR_D':retain(blocks,derived),
               'MINUS_D':retain(blocks,[i for i in ids if i not in derived]),
               'ORDER':''.join(next(b['text'] for b in blocks if b['block_id']==i) for i in order)}
        texts.update({f'MINUS_B{i}':retain(blocks,[j for j in ids if j!=i]) for i in ids})
        if item=='750':texts.update({f'P{k}':''.join(s['text'] for s in steps[:k]) for k in [299,448,598]})
        conditions={}
        for name,txt in texts.items():
            p=ROOT/'prefixes'/f'{item}_{name}.txt';textfile(p,txt)
            conditions[name]=dict(prefix_path=str(p),prefix_sha256=sha(p),prefix_tokens=len(tok.encode(txt,add_special_tokens=False)),
                question=oracle[item]['prompt'] if name.startswith('ESTAR') else src['question'])
        families.append(dict(**src,blocks=[{k:v for k,v in b.items() if k!='text'} for b in blocks],derived_blocks=derived,order=order,conditions=conditions))
        for rep in range(7):
            seeds.append(dict(item_id=item,family_id=family,replicate=rep,seed=seed(family,rep)))
            for cond in ['FULL','Q']:
                tasks.append(dict(task_id=f'A_{item}_{cond}_r{rep}',phase='phaseA',cohort='primary',item_id=item,
                    family_id=family,target='I',condition=cond,replicate=rep,seed=seed(family,rep),**conditions[cond]))
    save(ROOT/'stage12ws_primary_manifest.json',dict(at=now(),primary=primary['primary'],descriptive_negative=primary['descriptive_negative'],families=families,
         condition_aliases={'C2':'FULL','F1':'750_P299','F2':'750_P448','F3':'750_P598','F4':'750_P448'},negative_new_calls=0))
    save(ROOT/'stage12ws_block_segmentation.json',dict(at=now(),families=[dict(item_id=f['item_id'],blocks=f['blocks']) for f in families],source_only=True))
    save(ROOT/'stage12ws_block_annotations.json',dict(at=now(),rows=annotations,source_only=True,
        caveat='Source-based summaries with step citations, not exhaustive or independent-rater proposition certification; mathematical and visual truth not inferred from primary role.'))
    save(ROOT/'stage12ws_seed_manifest.json',dict(at=now(),rule=cfg['seed_rule'],replicate_index=list(range(7)),rows=seeds))
    save(ROOT/'audit/phaseA_execution.json',dict(at=now(),tasks=tasks))
    for item in MAP:
        save(ROOT/'queues'/f'phaseA_{item}.json',dict(frozen=True,phase='phaseA',target='I',config_sha256=sha(ROOT/'config.json'),rows=[t for t in tasks if t['item_id']==item]))
    paths=list(ROOT.glob('stage12ws_*'))+[ROOT/'config.json']+list(Path('scripts/stage12ws').glob('*'))
    paths+=[prior/n for n in ['stage12vs_semantic_steps.json','stage12vs_step_annotations.json','stage12vs_coarse_prefix_manifest.json','stage12vs_fine_localization.json']]
    paths+=[Path('outputs/stage12us/v1/stage12us_source_prefixes.json'),Path('outputs/stage12us/v1/stage12us_primary_inference.json'),Path('outputs/stage12bs/v1/stage12bs_full_manifest.json')]
    save(ROOT/'audit/source_seal.json',dict(at=now(),hashes={str(p):sha(p) for p in paths if p.is_file()},no_generation=True))
    save(ROOT/'audit/resource_estimate.json',dict(at=now(),phaseA_calls=56,phaseB_max=189,phaseC_new=84,phaseD_new_max=84,phaseE=28,phaseF_unique=21,
        before_controls_max_calls=462,controls='adaptive seven-call exact controls, aliases reused; hard GPU envelope governs',expected_gpu_hours_range=[4,6],target=6,hard=8,
        basis='V-S162calls2.406GPUh included12Thinking and14startups; W-S is Instruct only with larger batches and phase gates. Estimate uncertain, updated from actual time.'))
    print('FROZEN',len(annotations),'blocks',len(seeds),'seeds',len(tasks),'initial calls; preserved',len(history))

if __name__=='__main__':main()
