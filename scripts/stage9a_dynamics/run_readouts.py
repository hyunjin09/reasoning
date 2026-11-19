"""Secondary fixed-history evidence scores for all50 previously frozen events."""
import gc
import json
import os
import socket
import time
import traceback
from pathlib import Path
import torch

from scripts.stage8c.prepare import save,sha
from scripts.stage9a.run_native import inputs,now
from visual_reasoning.stage0.modeling import load_runtime,runtime_environment
from visual_reasoning.stage3c9.streaming import prefill_streaming_state,advance_streaming_state,clone_streaming_state
from visual_reasoning.stage9a_dynamics.access import TemporalAccessMask
from visual_reasoning.stage8b.single_execution import NativeProgress

ROOT=Path('outputs/stage9a_dynamics/v1')


@torch.inference_mode()
def candidate_score(model,state,ids,seed):
    assert ids
    local=clone_streaming_state(state);lp=[]
    for token in ids:
        lp.append(float(local.last_logits.float().log_softmax(-1)[token]))
        advance_streaming_state(model=model,state=local,token_ids=[token],seed=seed,chunk_size=1)
    del local
    return dict(token_log_probabilities=lp,sum_log_probability=sum(lp),mean_log_probability=sum(lp)/len(lp),next_token_log_probability=lp[0])


def score_event(model,processor,event,task,conditions):
    began=time.perf_counter();prepared,meta=inputs(processor,task)
    native=json.loads((Path(event['native_dir'])/'generation.json').read_text())['generated_token_ids']
    stop=event['readout_start'];assert event['prefix_token_ids']==native[:stop]
    assert event['original_token_ids']==native[stop:stop+len(event['original_token_ids'])]
    selected=[dict(condition_id='full',intervals=[],mode='standard')]
    selected += [c for c in conditions if c.get('event_id')==event['event_id'] and c['assay']=='demand' and c.get('eligible',True)]
    assert len(selected)==5
    earliest=min([stop]+[max(0,min(lo for lo,hi in c['intervals'])-1) for c in selected if c['intervals']])
    base,_=prefill_streaming_state(model=model,prepared=prepared,seed=event['seed'])
    advance_streaming_state(model=model,state=base,token_ids=native[:earliest],seed=event['seed'],chunk_size=1)
    results=[]
    for condition in selected:
        state=clone_streaming_state(base)
        with TemporalAccessMask(visual=meta['visual_token_indices'],prompt_length=meta['prompt_token_count'],intervals=condition['intervals']):
            advance_streaming_state(model=model,state=state,token_ids=native[earliest:stop],seed=event['seed'],chunk_size=1)
            original=candidate_score(model,state,event['original_token_ids'],event['seed'])
            cf=candidate_score(model,state,event['counterfactual_token_ids'],event['seed'])
        results.append(dict(condition_id=condition['condition_id'],radius=condition.get('radius'),role=condition.get('role','full'),
            intervals=condition['intervals'],original=original,counterfactual=cf,
            masked_query_count_before_readout=sum(any(lo<=t and (hi is None or t<hi) for lo,hi in condition['intervals']) for t in range(1,stop)),
            masked_query_count_during_original_readout=sum(any(lo<=t and (hi is None or t<hi) for lo,hi in condition['intervals']) for t in range(max(1,stop),stop+len(event['original_token_ids']))),
            original_minus_counterfactual=original['sum_log_probability']-cf['sum_log_probability']))
        del state;gc.collect();torch.cuda.empty_cache()
    return dict(event_id=event['event_id'],task_id=task['task_id'],family_id=task['family_id'],arm=task['arm'],
        source_id=event['source_id'],readout_start=stop,readout_end=event['readout_end_extended'],
        fixed_native_history=True,mask_changes_subsequent_cache=True,rows=results,runtime_seconds=time.perf_counter()-began,
        at=now(),slurm_job_id=os.environ['SLURM_JOB_ID'])


def main():
    assert os.environ.get('SLURM_JOB_ID') and torch.cuda.device_count()==1
    cfg=json.loads((ROOT/'config.json').read_text());assert socket.gethostname().split('.')[0] in cfg['allowed_nodes']
    assert json.loads((ROOT/'stage9a_mask_backend_validation.json').read_text())['pass_all']
    tasks={r['task_id']:r for r in json.loads((ROOT/'audit/tasks.json').read_text())['rows']}
    events=json.loads((ROOT/'audit/local_readouts.json').read_text())['rows'];assert len(events)==50
    conditions=json.loads((ROOT/'audit/interventions.json').read_text())['rows']
    worker=ROOT/'readouts/workers'/('slurm_'+os.environ['SLURM_JOB_ID']);worker.mkdir(parents=True,exist_ok=True)
    model=processor=None;current=None;completed=[]
    for event in sorted(events,key=lambda e:(e['arm']=='thinking',e['task_id'],e['readout_start'])):
        dest=ROOT/'readouts/events'/event['event_id']/'result.json'
        if dest.exists():continue
        task=tasks[event['task_id']];key='thinking' if task['arm']=='thinking' else 'instruct'
        if current!=key:
            if model is not None:del model,processor;gc.collect();torch.cuda.empty_cache()
            checkpoint=Path(cfg['models'][key]['checkpoint'])
            processor,model=load_runtime(checkpoint,'cuda:0');current=key
            save(worker/(key+'_environment.json'),dict(runtime_environment(checkpoint,model,cfg['max_new_tokens']),at=now(),slurm_job_id=os.environ['SLURM_JOB_ID'],node=socket.gethostname()))
        print(json.dumps(dict(event='readout_start',event_id=event['event_id'],at=now())),flush=True)
        try:
            with NativeProgress(model,event['event_id']):
                result=score_event(model,processor,event,task,conditions)
            save(dest,result);completed.append(event['event_id'])
        except Exception as exc:
            save(worker/'failure.json',dict(at=now(),event_id=event['event_id'],error=repr(exc),traceback=traceback.format_exc()));raise
        print(json.dumps(dict(event='readout_complete',event_id=event['event_id'],seconds=result['runtime_seconds'],at=now())),flush=True)
        gc.collect();torch.cuda.empty_cache()
    save(worker/'completed.json',dict(at=now(),completed=completed))
    save(ROOT/'audit/readouts_complete.json',dict(at=now(),events=50,results_sha256={str(p):sha(p) for p in (ROOT/'readouts/events').glob('*/result.json')}))


if __name__=='__main__':main()
