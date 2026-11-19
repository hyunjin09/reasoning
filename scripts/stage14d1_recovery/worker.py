"""Finite technical diagnostic. No scientific-pilot entry point or scorer."""
import argparse, os, time, hashlib, json, socket, sys, traceback
from pathlib import Path
from scripts.stage14d1_recovery.contracts import *
from scripts.stage14d1.contracts_v3 import (safe_payload, helper_prompt, compact_prompt,
    SCHEMAS, parse_record, validate_query, validate_address, valid_readout, solver_suffix, ARMS)
from scripts.stage14d1.views import render_views

def run(profile_name):
    matrix=load(R/'protocol/execution_matrix.json')
    profile=next(x for x in matrix['profiles'] if x['name']==profile_name)
    assert os.environ['VLLM_ENABLE_V1_MULTIPROCESSING']==str(profile['multiprocessing'])
    assert 'SLURM_JOB_ID' in os.environ
    for path,digest in load(R/'audit/execution_seal.json')['files'].items():
        assert sha(path)==digest,path
    cfg=load(R/'protocol/runtime.json')
    record_map={r['family_id']:safe_payload(r) for r in rows(R/'data/families.jsonl')}
    work=[record_map[f] for f in matrix['original_family_order']]
    assert len(work)==8
    for row in work:
        assert sha(row['image'])==row['image_sha256']
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    from vllm import LLM,SamplingParams
    from vllm.sampling_params import StructuredOutputsParams
    sys.path.insert(0,str(Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision').resolve()))
    from run_mathv import prepare_inputs_for_vllm,build_mathv_prompt
    root=R/'raw'/profile_name
    job=os.environ['SLURM_JOB_ID']
    proc=AutoProcessor.from_pretrained(cfg['model']['model']['checkpoint'])
    rt=cfg['runtime']
    engine_kwargs=dict(model=cfg['model']['model']['checkpoint'],dtype='bfloat16',
        tensor_parallel_size=1,seed=rt['engine_seed'],gpu_memory_utilization=.85,
        max_model_len=128000,max_num_seqs=profile['batch_size'],limit_mm_per_prompt={'image':3},
        enable_prefix_caching=False,trust_remote_code=True,logprobs_mode='raw_logits',
        scheduler_cls='scripts.stage14d1_recovery.observe.Scheduler',
        worker_cls='scripts.stage14d1_recovery.observe.Worker')
    llm=LLM(**engine_kwargs);engine=llm.llm_engine
    save(root/'environment.json',dict(at=now(),profile=profile,engine_kwargs=engine_kwargs,
        job=job,node=socket.gethostname(),gpu=torch.cuda.get_device_name(0),
        vllm_config=str(engine.vllm_config),versions=cfg['environment'],
        trace_scope='Scheduler records for all requests; sampler hooks only rng-prefixed requests',
        raw_logit_return='logprobs fields contain raw logits, not normalized log probabilities'))
    deadline=float(os.environ['SAVA_RECOVERY_DEADLINE'])
    completed=0

    def batch(tasks):
        nonlocal completed
        active={};answers={};cursor=0;last_heartbeat=0
        while cursor<len(tasks) or active:
            while cursor<len(tasks) and len(active)<profile['batch_size']:
                if time.time()>deadline-120:
                    raise TimeoutError('Finite allocation admission stop')
                task=tasks[cursor];cursor+=1;rid=task['id'];row=task['row'];folder=root/rid
                assert not folder.exists(),rid
                images=task.get('images',[])
                if task['kind']=='solver':
                    inp=prepare_inputs_for_vllm(row['original_messages'],proc)
                    assert inp['prompt']==row['original_chat_prompt']
                    inp['prompt']+=row['prefix']+task.get('suffix','')
                else:
                    text=compact_prompt(task['prompt'])
                    messages=build_mathv_prompt({'question':text},lambda _:images,'MathVision') if images else [dict(role='user',content=[dict(type='text',text=text)])]
                    inp=prepare_inputs_for_vllm(messages,proc) if images else dict(prompt=proc.apply_chat_template(messages,tokenize=False,add_generation_prompt=True))
                    assert inp['prompt'].endswith('<think>\n')
                    inp['prompt']+='</think>\n\n'
                actual_images=inp.get('multi_modal_data',{}).get('image',[])
                pixels=[hashlib.sha256(im.tobytes()).hexdigest() for im in actual_images]
                sizes=[list(im.size) for im in actual_images]
                if task['kind']=='solver':
                    assert pixels==row['original_image_pixels'] and sizes==row['original_image_sizes']
                recipe=dict(cfg['helper_recipe'])
                if task.get('greedy'):
                    recipe.update(temperature=0,top_p=1,top_k=-1)
                seed=row['seed']+task.get('seed_offset',0)
                structured=StructuredOutputsParams(json=SCHEMAS[task['kind']]) if task['kind']!='solver' else None
                params=SamplingParams(**recipe,max_tokens=task['cap'],seed=seed,
                    stop_token_ids=[],ignore_eos=False,logprobs=20 if task['kind']=='solver' else None,
                    structured_outputs=structured)
                save(folder/'input.json',dict(at=now(),request_id=rid,family_id=row['family_id'],
                    item_id=row['item_id'],kind=task['kind'],prompt=inp['prompt'],prefix_sha256=row['prefix_sha256'],
                    pixels=pixels,image_sizes=sizes,seed=seed,sampling=recipe,cap=task['cap'],
                    profile=profile_name,job=job,images=[row['image']] if task['kind']=='solver' else images))
                engine.add_request(rid,inp,params)
                active[rid]=dict(task=task,started=time.time(),latest=None)
            for output in engine.step():
                a=active[output.request_id];a['latest']=output
                if not output.finished:
                    continue
                o=output.outputs[0];rid=output.request_id;folder=root/rid
                inp=load(folder/'input.json')
                logits=[{str(k):dict(value=float(v.logprob),rank=v.rank,decoded_token=v.decoded_token) for k,v in step.items()} for step in o.logprobs] if o.logprobs is not None else None
                g=dict(at=now(),request_id=rid,tokens=list(o.token_ids),prompt=list(output.prompt_token_ids),
                    seed=inp['seed'],pixels=inp['pixels'],raw=o.text,finish_reason=o.finish_reason,
                    stop_reason=o.stop_reason,cap_hit=o.finish_reason=='length',latency_seconds=time.time()-a['started'],
                    raw_logits_top20_and_selected=logits,job=job)
                save(folder/'generation.json',g)
                save(folder/'result.json',dict(input_sha256=sha(folder/'input.json'),generation_sha256=sha(folder/'generation.json')))
                answers[rid]=g;del active[rid];completed+=1
                print('COMPLETE',profile_name,rid,len(o.token_ids),o.finish_reason,flush=True)
            if time.time()>deadline-30:
                engine.abort_request(list(active))
                for rid,a in active.items():
                    o=a['latest'].outputs[0] if a['latest'] else None
                    save(root/rid/'interrupted.json',dict(reason='SAFE_ALLOCATION_DEADLINE',tokens=list(o.token_ids) if o else [],raw=o.text if o else ''))
                raise TimeoutError('Finite allocation deadline')
            if time.time()-last_heartbeat>60:
                save(root/'heartbeats'/f'{time.time_ns()}.json',dict(at=now(),completed=completed,
                    active={rid:len(a['latest'].outputs[0].token_ids) if a['latest'] else 0 for rid,a in active.items()}))
                last_heartbeat=time.time()
        return answers

    def task(row,ident,kind='solver',cap=64,**kwargs):
        return dict(id=ident,row=row,kind=kind,cap=cap,**kwargs)

    comparisons=[]
    try:
        offsets=matrix['validation_seed_offsets'] if profile_name=='independent_validation_b8' else [0]
        for offset in offsets:
            for decoding in ['sampled','greedy']:
                pair=[]
                for repeat in ['a','b']:
                    requests=[task(r,f'{decoding}_{offset}_{r["item_id"]}_{repeat}',greedy=decoding=='greedy',seed_offset=offset) for r in work]
                    pair.append(batch(requests))
                for r in work:
                    a=pair[0][f'{decoding}_{offset}_{r["item_id"]}_a'];b=pair[1][f'{decoding}_{offset}_{r["item_id"]}_b']
                    comparisons.append(dict(item_id=r['item_id'],decoding=decoding,seed_offset=offset,
                        a=a['request_id'],b=b['request_id'],**replay_comparison(a,b)))
        save(root/'replay_comparisons.json',dict(at=now(),comparisons=comparisons))
        if profile_name in ['default_b8','deterministic_b8']:
            for repeat in ['a','b']:
                batch([task(r,f'rng_{r["item_id"]}_{repeat}') for r in work])
        if profile_name=='independent_validation_b8':
            # Synthetic branch controls are independent technical tests, even if native parity fails.
            controls=[]
            for c in load(R/'protocol/control_cases.json')['cases']:
                r=dict(work[0],item_id=c['id'],family_id='synthetic_'+c['id'],question=c['question'],prefix=c['prefix'])
                r['prefix_sha256']=hashlib.sha256(r['prefix'].encode()).hexdigest()
                controls.append((r,c['expected']))
            control_results=[]
            for repeat in ['a','b']:
                output=batch([task(r,f'control_{r["item_id"]}_{repeat}','query',2048,prompt=helper_prompt(r,'query')) for r,_ in controls])
                for r,expected in controls:
                    g=output[f'control_{r["item_id"]}_{repeat}'];q=parse_record(g['raw']);ok,reason=validate_query(q,r['question'],r['prefix'])
                    control_results.append(dict(id=r['item_id'],repeat=repeat,expected=expected,parsed=q,contract_valid=ok,reason=reason,branch_match=bool(ok and q.get('status')==expected),cap_hit=g['cap_hit']))
            save(root/'grammar_controls.json',dict(at=now(),controls=control_results))
            for offset in offsets:
                require_replay([c for c in comparisons if c['decoding']=='sampled' and c['seed_offset']==offset])
            # Independent exact replay passes before any acquisition transport on the eight cases.
            queries=batch([task(r,f'{r["item_id"]}_query','query',2048,prompt=helper_prompt(r,'query')) for r in work])
            state={};eligible=[]
            for r in work:
                q=parse_record(queries[r['item_id']+'_query']['raw']);ok,reason=validate_query(q,r['question'],r['prefix'])
                state[r['item_id']]=dict(item_id=r['item_id'],family_id=r['family_id'],query=q,query_valid=ok,query_reason=reason)
                if ok and q['status']=='QUERY':eligible.append(r)
            locations=batch([task(r,f'{r["item_id"]}_locate','locate',2048,prompt=helper_prompt(r,'locate',state[r['item_id']]['query']),images=[r['image']]) for r in eligible])
            read_jobs=[];aliases={}
            for r in work:
                item=r['item_id'];s=state[item]
                read_jobs.append(task(r,f'{item}_G_read','read',2048,prompt=helper_prompt(r,'G'),images=[r['image']]))
                if r not in eligible:continue
                a=parse_record(locations[item+'_locate']['raw']);w,h=Image.open(r['image']).size;ok=validate_address(a,w,h)
                s.update(address=a,address_valid=ok)
                for arm,images in [('Q',[]),('QI',[r['image']])]:
                    read_jobs.append(task(r,f'{item}_{arm}_read','read',2048,prompt=helper_prompt(r,arm,s['query']),images=images))
                if not ok:
                    aliases[f'{item}_QIA_read']=f'{item}_QI_read';aliases[f'{item}_QGL_read']=f'{item}_QI_read';continue
                views=render_views(r['image'],a,R/'data/views'/item);s['views']=views
                read_jobs.append(task(r,f'{item}_QIA_read','read',2048,prompt=helper_prompt(r,'QIA',s['query'],a),images=[r['image']]))
                if len(views['paths'])==1:aliases[f'{item}_QGL_read']=f'{item}_QIA_read'
                else:read_jobs.append(task(r,f'{item}_QGL_read','read',2048,prompt=helper_prompt(r,'QGL',s['query'],a),images=views['paths']))
            readings=batch(read_jobs)
            for target,source in aliases.items():readings[target]=readings[source]
            resumed=[]
            for r in work:
                item=r['item_id'];s=state[item];s['readouts']={};s['continuations']={};seen={'':f'{item}_N'}
                resumed.append(task(r,f'{item}_N',cap=256));s['continuations']['N']=f'{item}_N'
                for arm in ARMS[1:]:
                    g=readings.get(f'{item}_{arm}_read');v=parse_record(g['raw']) if g else None;ok=valid_readout(v);suffix=solver_suffix(v) if ok else ''
                    s['readouts'][arm]=dict(value=v,valid=ok,physical_request=g['request_id'] if g else None)
                    if suffix not in seen:
                        seen[suffix]=f'{item}_{arm}';resumed.append(task(r,seen[suffix],cap=256,suffix=suffix))
                    s['continuations'][arm]=seen[suffix]
                save(R/'data/source_packets'/f'{item}.json',dict(item_id=item,image=r['image'],question=r['question'],prefix=r['prefix'],query=s['query'],address=s.get('address'),readouts_hidden=True,finals_hidden=True))
            batch(resumed)
            save(root/'acquisition_states.json',dict(at=now(),cases=state,read_aliases=aliases))
        save(root/'exit.json',dict(at=now(),status='COMPLETE',completed=completed))
    except BaseException as exc:
        save(root/'error.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc(),completed=completed))
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('profile');run(parser.parse_args().profile)
