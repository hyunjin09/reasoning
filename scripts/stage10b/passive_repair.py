"""Bounded Slurm-only teacher-forced instrumentation of frozen MathVerse prefixes."""
import os,time,socket,gc,hashlib
from pathlib import Path
import numpy as np
import torch,joblib
from PIL import Image
from scripts.stage10b.common import ROOT,load,save,sha,now
from scripts.stage10b.routing import roi_indices,reaccess
from visual_reasoning.stage0.modeling import load_runtime,runtime_environment
from visual_reasoning.stage3c9.streaming import prefill_streaming_state,advance_streaming_state,clone_streaming_state
from visual_reasoning.stage8b.passive import PassiveRecorder


def inputs(processor,row):
    old=load(Path(row['native_directory'])/'input.json')
    assert sha(row['image'])==row['image_sha256']
    with Image.open(row['image']) as source:image=source.convert('RGB')
    messages=[{'role':'user','content':[{'type':'image','image':image},
                                      {'type':'text','text':old['generation_query']}]}]
    batch=processor.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,
                                       return_dict=True,return_tensors='pt')
    ids=batch['input_ids'][0];visual=(ids==int(processor.image_token_id)).nonzero().flatten().tolist()
    assert len(ids)==old['prompt_token_count'] and visual==old['visual_token_indices']
    assert batch['image_grid_thw'][0].tolist()==old['image_grid_thw']
    assert list(image.size)==old['original_image_size']
    evidence=dict(prompt_ids_sha256=hashlib.sha256(ids.numpy().tobytes()).hexdigest(),
                  pixel_values_sha256=hashlib.sha256(batch['pixel_values'].numpy().tobytes()).hexdigest(),
                  historical_input_sha256=sha(Path(row['native_directory'])/'input.json'),
                  prompt_length=len(ids),visual_positions=visual,
                  preprocessing='Unchanged Stage8A HF image/chat-template path; source image/query/revision verified.')
    return {k:v.to('cuda:0') if isinstance(v,torch.Tensor) else v for k,v in batch.items()},old,evidence


def main():
    started=time.monotonic();assert os.environ.get('SLURM_JOB_ID')
    assert torch.cuda.device_count()==1 and socket.gethostname().split('.')[0] in ('node02','node03','node06','node07')
    mp=ROOT/'audit/passive_repair_manifest.json';cfg=load(mp);assert cfg['frozen'] and len(cfg['trajectories'])<=32
    sp=ROOT/'audit/semantic_adjudication_frozen.json';assert sha(sp)==cfg['semantic_sha256']
    for p,h in cfg['source_sha256'].items():assert sha(p)==h,p
    corpus=load(ROOT/'stage10b_corpus_manifest.json');by={r['trajectory_id']:r for r in corpus['rows']}
    events=load(sp)['events'];gcfg=load('outputs/stage9a/v1/stage9a_generation_config.json');info=gcfg['models']['thinking']
    for name,h in info['files_sha256'].items():assert sha(Path(info['checkpoint'])/name)==h,name
    rulepath=Path(gcfg['detector_freeze']);assert sha(rulepath)==gcfg['detector_freeze_sha256']
    rule=load(rulepath)['retrieval'];assert sha(rule['models'])==rule['models_sha256']
    fitted=joblib.load(rule['models'])['joint'];assert fitted['threshold']==rule['tau_R'] and fitted['spec']==rule['spec']
    processor,model=load_runtime(Path(info['checkpoint']),'cuda:0')
    assert str(next(model.parameters()).dtype)=='torch.bfloat16'
    env=runtime_environment(Path(info['checkpoint']),model,0)
    assert (env['language_layers'],env['attention_heads'],env['kv_heads'])==(28,16,8)
    assert '6000' in env['gpu_name']
    env.update(at=now(),slurm_job_id=os.environ['SLURM_JOB_ID'],hostname=socket.gethostname(),
               gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),manifest_sha256=sha(mp),
               new_generated_tokens=0,inference='teacher-forced passive forward only; no ablation',dtype='bfloat16')
    save(ROOT/'repair/environment.json',env)
    done=[];noop_checked=False
    for tid in cfg['trajectories']:
        if time.monotonic()-started>cfg['worker_soft_limit_seconds']:
            raise TimeoutError('Passive repair soft budget exhausted; retain completed receipts, never extend automatically.')
        row=by[tid];assert row['dataset']=='MathVerse' and row['passive_path'] is None
        assert row['model_revision']==info['revision']
        for p,h in row['source_sha256'].items():assert sha(p)==h,p
        own=sorted([e for e in events if e['trajectory_id']==tid and e['semantic_clean']],key=lambda e:e['onset'])
        assert own
        dest=ROOT/'repair'/tid;assert not dest.exists()
        begin=time.monotonic();prepared,old,input_evidence=inputs(processor,row)
        gen=load(Path(row['native_directory'])/'generation.json');ids=gen['generated_token_ids'];seed=gen['seed']
        state,prefill_audit=prefill_streaming_state(model=model,prepared=prepared,seed=seed)
        save(dest/'input_verification.json',input_evidence);save(dest/'prefill.json',prefill_audit)
        # Capture the union once; overlapping events do not replay/duplicate queries.
        wanted=sorted({i for e in own for i in range(e['onset'],min(e['onset']+32,len(ids)))})
        assert wanted and min(wanted)>0
        focus=[];scores=[];features=[]
        for query in wanted:
            target_generated=query-1
            if state.generated_length<target_generated:
                advance_streaming_state(model=model,state=state,token_ids=ids[state.generated_length:target_generated],seed=seed,chunk_size=64)
            assert state.generated_length==target_generated
            if not noop_checked:
                reference=clone_streaming_state(state)
                advance_streaming_state(model=model,state=reference,token_ids=[ids[target_generated]],seed=seed,chunk_size=1)
            with PassiveRecorder(visual=old['visual_token_indices'],prompt_length=old['prompt_token_count'],
                                 model=fitted['model'],reference_check=not noop_checked) as observer:
                advance_streaming_state(model=model,state=state,token_ids=[ids[target_generated]],seed=seed,chunk_size=1)
            a=observer.arrays();assert len(a['features'])==1
            if not noop_checked:
                same=torch.equal(state.last_logits,reference.last_logits)
                cache_equal=all(torch.equal(x.keys,y.keys) and torch.equal(x.values,y.values)
                                for x,y in zip(state.cache.layers,reference.cache.layers))
                save(ROOT/'repair/observer_validation.json',dict(at=now(),trajectory_id=tid,query=query,
                    logits_bitwise_equal=same,cache_bitwise_equal=cache_equal,
                    reference_feature_rows=observer.reference_rows,passive_reference_exact=observer.reference_rows==4,
                    scope='One unchanged query at the first frozen repair event; no generation or source manipulation.'))
                assert same and cache_equal and observer.reference_rows==4
                del reference;noop_checked=True
            focus.append(a['visual_focus'][0]);scores.append(a['retrieval_score'][0]);features.append(a['features'][0])
        focus=np.asarray(focus);scores=np.asarray(scores);features=np.asarray(features);index={q:i for i,q in enumerate(wanted)}
        np.savez_compressed(dest/'passive_queries.npz',generated_token_indices=np.array(wanted),visual_focus=focus,
                            retrieval_score=scores,features=features,visual_positions=np.array(old['visual_token_indices']))
        grid=old['visual_mapping']['merged_grid_shape'];results=[]
        for e in own:
            target=roi_indices(e.get('target_roi_normalized'),grid);control=roi_indices(e.get('irrelevant_roi_normalized'),grid)
            if e.get('irrelevant_roi_normalized') is None:control=sorted(set(range(int(np.prod(grid))))-set(target))
            control=sorted(set(control)-set(target));qs=list(range(e['onset'],min(e['onset']+32,len(ids))));ii=[index[q] for q in qs]
            result=reaccess(focus[ii],scores[ii],[q-e['onset'] for q in qs],target=target,irrelevant=control,
                            tau=rule['tau_R'],observation_offset=e.get('observation_offset'))
            results.append(dict(event_id=e['event_id'],trajectory_id=tid,dataset=row['dataset'],onset=e['onset'],
                semantic_clean=e['semantic_clean'],**result,threshold=rule['tau_R'],source_grid=grid,
                detector_compatibility='Same2BThinking checkpoint, frozen Stage8A feature calculation/detector; observer/noop validation passed.',
                provenance='passive_reconstruction_of_frozen_native_prefix',query_alignment='Captured query i-1 predicts frozen generated token i.',
                passive_path=str(dest/'passive_queries.npz'),passive_sha256=sha(dest/'passive_queries.npz')))
        torch.cuda.synchronize()
        save(dest/'complete.json',dict(at=now(),trajectory_id=tid,rows=results,seconds=time.monotonic()-begin,
            max_cuda_memory_bytes=torch.cuda.max_memory_allocated(),manifest_sha256=sha(mp),
            new_generated_tokens=0,teacher_forced_tokens=state.generated_length,
            reconstruction_limit='Native outputs unchanged. Prefix uses64-token eager chunks; original per-query routing was not saved for direct numerical comparison.'))
        done.append(tid);print('COMPLETE',tid,len(wanted),'passive queries',round(time.monotonic()-begin,2),'seconds',flush=True)
        del prepared,state,observer;gc.collect();torch.cuda.empty_cache()
    save(ROOT/'repair/complete.json',dict(at=now(),trajectories=done,worker_seconds=time.monotonic()-started,
        slurm_job_id=os.environ['SLURM_JOB_ID'],manifest_sha256=sha(mp),new_generated_tokens=0))


if __name__=='__main__':main()
