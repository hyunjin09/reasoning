"""One Slurm-bound GPU worker; immutable per-item/per-dose evidence."""
import argparse
import gc
import json
import os
import socket
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import torch

from visual_reasoning.stage0.modeling import generate_once, load_runtime, runtime_environment
from visual_reasoning.stage8a.protocol import termination_status
from visual_reasoning.stage8b.v2_protocol import generation_parameters, prepared_input, completion_status
from visual_reasoning.stage8c.gain import VisualGain
from scripts.stage8c.prepare import save, sha


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);args=ap.parse_args()
    cfg=json.loads(Path(args.config).read_text());rank=int(os.environ['SLURM_PROCID'])
    assert os.environ['SLURM_NTASKS']=='2' and rank in (0,1)
    assert socket.gethostname().split('.')[0]=='node02' and torch.cuda.device_count()==1
    torch.cuda.set_device(0)
    for path,expected in cfg['source_sha256'].items():assert sha(path)==expected,path
    root=Path(cfg['output_dir'])
    assert json.loads((root/'stage8c_v2_technical_validation.json').read_text())['pass_checks']
    assert sha(root/'stage8c_v2_technical_validation.json')==cfg['validation_sha256']
    tasks=json.loads(Path(cfg['task_manifest']).read_text())['tasks']
    assert sha(cfg['task_manifest'])==cfg['task_manifest_sha256']
    freeze=json.loads(Path(cfg['detector_freeze']).read_text())
    assert sha(cfg['detector_freeze'])==cfg['detector_freeze_sha256']
    assert sha(freeze['retrieval']['models'])==freeze['retrieval']['models_sha256']
    detector=joblib.load(freeze['retrieval']['models'])['joint']['model']
    processor,model=load_runtime(Path(cfg['model_checkpoint']),'cuda:0')
    worker=root/cfg['phase']/f'worker{rank}'
    env=runtime_environment(Path(cfg['model_checkpoint']),model,cfg['max_new_tokens'])
    assert next(model.parameters()).dtype==torch.bfloat16
    env.update(slurm_job_id=os.environ['SLURM_JOB_ID'],hostname=socket.gethostname(),rank=rank,
               gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),config_sha256=sha(args.config))
    save(worker/'environment.json',env)
    eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
    completed=[]
    for task in tasks[rank::2]:
        row=task['input'];dest=root/cfg['phase']/'examples'/task['task_id']
        assert not dest.exists(), 'Use an explicit continuation manifest, never overwrite a partial attempt'
        # Inference worker receives no options/answer/local-read annotations.
        assert set(row)=={'item_id','image','image_sha256','question','generation_query','seed','family_id'}
        safe=dict(row,answer='')
        prepared,metadata=prepared_input(processor,safe)
        save(dest/'input.json',metadata);save(dest/'task.json',task)
        started=time.perf_counter();step=[0]
        def progress(_module,_args,_output):
            step[0]+=1
            if step[0]%512==0:
                status=dict(event='progress',rank=rank,task_id=task['task_id'],tokens=step[0],
                            elapsed_seconds=time.perf_counter()-started,at=datetime.now(timezone.utc).isoformat())
                print(json.dumps(status),flush=True)
                with (worker/'progress.jsonl').open('a') as stream:stream.write(json.dumps(status)+'\n')
        handle=model.register_forward_hook(progress)
        print(json.dumps(dict(event='start_example',rank=rank,task_id=task['task_id'],at=datetime.now(timezone.utc).isoformat())),flush=True)
        try:
            with VisualGain(model,visual=metadata['visual_token_indices'],prompt_length=metadata['prompt_token_count'],
                            detector=detector,gain=task['gain'],policy=task['policy'],schedule=task.get('schedule',[])) as intervention:
                generated=generate_once(model,processor,prepared,cfg['max_new_tokens'],None,
                    generation_kwargs=generation_parameters(),seed=row['seed'],collect_predictive_metrics=False)
        except Exception:
            save(dest/'failure.json',dict(traceback=traceback.format_exc(),tokens_observed=step[0],
                                         at=datetime.now(timezone.utc).isoformat()))
            raise
        finally:
            handle.remove()
        arrays=intervention.arrays();assert len(arrays['retrieval_score'])==len(generated['generated_token_ids'])==step[0]
        assert np.isnan(arrays['retrieval_score'][0]) and np.isfinite(arrays['retrieval_score'][1:]).all()
        state=termination_status(generated['generated_token_ids'],eos_ids=eos,cap=cfg['max_new_tokens'])
        state.update(completion_status(generated['raw_decoded_response'],normal_eos=state['normal_eos'],
                                      at_length_cap=state['at_length_cap'],tokens=state['tokens']))
        tokens=generated.pop('token_rows');generated.pop('attention_arrays',None)
        save(dest/'generation.json',dict(generated,**state))
        with (dest/'tokens.jsonl').open('x') as stream:
            for token in tokens:stream.write(json.dumps(token,ensure_ascii=False)+'\n')
        np.savez_compressed(dest/'passive.npz',**arrays)
        save(dest/'interventions.json',dict(events=intervention.events,gain=task['gain'],policy=task['policy'],
             actual_interventions=sum(e['rerun'] for e in intervention.events)))
        result=dict(task_id=task['task_id'],item_id=row['item_id'],family_id=row['family_id'],rank=rank,
            seed=row['seed'],gain=task['gain'],policy=task['policy'],**state,
            runtime=generated['runtime'],finished_at=datetime.now(timezone.utc).isoformat(),
            actual_interventions=sum(e['rerun'] for e in intervention.events),artifact_dir=str(dest),
            provenance_sha256={str(dest/name):sha(dest/name) for name in
                ['input.json','task.json','generation.json','tokens.jsonl','passive.npz','interventions.json']})
        save(dest/'result.json',result);completed.append(task['task_id'])
        print(json.dumps(dict(event='complete_example',task_id=task['task_id'],rank=rank,tokens=state['tokens'],
            normal_eos=state['normal_eos'],interventions=result['actual_interventions'],runtime=generated['runtime'])),flush=True)
        del prepared,generated,tokens,arrays,intervention;gc.collect();torch.cuda.empty_cache()
    save(worker/'completed.json',dict(completed=completed,at=datetime.now(timezone.utc).isoformat()))


if __name__=='__main__':main()
