"""Slurm-only fixed-native-history local Value semantic validation."""
import argparse
import gc
import json
import os
import socket
import time
import traceback
from pathlib import Path

import numpy as np
import torch

from scripts.stage8c.prepare import save, sha
from scripts.stage9a.run_native import inputs, now
from scripts.stage8a.run_value_assays import run_query, logp
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3c9.streaming import prefill_streaming_state, advance_streaming_state, clone_streaming_state
from visual_reasoning.stage8a.instrumentation import AttentionAssay, js_divergence
from visual_reasoning.stage8b.passive import FEATURE_KEYS

LAYERS=[19,20,21,22]
ARMS=('native','target','irrelevant','sham')


@torch.inference_mode()
def score(model, processor, request, task):
    started=time.monotonic();torch.cuda.reset_peak_memory_stats()
    native_dir=Path(request['native_dir'])
    assert sha(native_dir/'input.json')==request['input_sha256']
    assert sha(native_dir/'tokens.jsonl')==request['tokens_sha256']
    prepared,meta=inputs(processor,task)
    old=json.loads((native_dir/'input.json').read_text())
    for key in ('prompt_ids_sha256','pixel_values_sha256','chat_prompt','visual_token_indices','image_grid_thw'):
        assert meta[key]==old[key],key
    checkpoint,prefill= prefill_streaming_state(model=model,prepared=prepared,seed=request['seed'])
    del prepared
    prefix=request['prefix_token_ids'];assert prefix
    advance_streaming_state(model=model,state=checkpoint,token_ids=prefix[:-1],seed=request['seed'],chunk_size=1)
    print(json.dumps(dict(event='prefix_ready',event_id=request['event_id'],tokens=len(prefix),seconds=time.monotonic()-started)),flush=True)
    values={arm:{c:[] for c in ('original','counterfactual')} for arm in ARMS}
    first_js={};passive=None;selectivity=None;parity=None;norms={}
    for candidate in ('original','counterfactual'):
        branch=clone_streaming_state(checkpoint);query=prefix[-1]
        for i,target_token in enumerate(request[candidate+'_token_ids']):
            common=dict(model=model,layers=LAYERS,visual=request['visual_positions'],prompt_length=request['prompt_length'])
            capture=AttentionAssay(**common)
            native=run_query(model,branch,query,request['seed'],capture)
            baseline=native.last_logits.clone()
            reference=run_query(model,branch,query,request['seed'])
            assert torch.equal(reference.last_logits,baseline),'capture no-op parity'
            del reference
            if candidate=='original' and i==0:
                passive=capture.records
                features=[]
                for layer in LAYERS:
                    stats=capture.records[layer]['passive'][0]
                    matrix=np.array([stats[k] for k in FEATURE_KEYS],dtype=np.float32).T
                    matrix[matrix[:,0]==0,6]=0
                    features.append(matrix)
                replay=np.concatenate(features).max(0)
                with np.load(native_dir/'passive.npz') as archive:expected=archive['features'][request['readout_start']]
                parity=dict(replay=replay.tolist(),native=expected.tolist(),max_abs=float(np.max(np.abs(replay-expected))),exact=bool(np.array_equal(replay,expected)))
                assert np.allclose(replay,expected,atol=1e-5,rtol=1e-5),'native-prefix passive mismatch'
                selectivity={}
                for layer in LAYERS:
                    a=capture.states[layer]['weights'][0,:,0,:].float()
                    total=a[:,request['visual_positions']].sum(-1).clamp_min(1e-30)
                    selectivity[layer]={kind:(a[:,request[kind+'_positions']].sum(-1)/total).cpu().tolist() for kind in ('target','donor','irrelevant')}
            values['native'][candidate].append(logp(baseline,target_token))
            for arm in ARMS[1:]:
                positions=request['irrelevant_positions' if arm=='irrelevant' else 'target_positions']
                donor={}
                for layer in LAYERS:
                    v=capture.states[layer]['value'];dv=v.clone()
                    if arm!='sham':dv[:,:,positions]=v[:,:,request['donor_positions']]
                    donor[layer]=dv
                    if candidate=='original' and i==0:
                        norms.setdefault(arm,{})[layer]=float((dv[:,:,positions].float()-v[:,:,positions].float()).norm())
                assay=AttentionAssay(**common,frozen=capture.states,donor_values=donor,positions=positions)
                changed=run_query(model,branch,query,request['seed'],assay)
                assert torch.isfinite(changed.last_logits).all()
                assert all(r['routing_max_abs_delta']==0 for r in assay.records.values())
                if arm=='sham':assert torch.equal(changed.last_logits,baseline),'self/sham parity'
                values[arm][candidate].append(logp(changed.last_logits,target_token))
                if candidate=='original' and i==0:first_js[arm]=js_divergence(baseline,changed.last_logits)
                del changed,assay,donor,dv,v
            # Restore native history at every scored token, including CF branch.
            branch=native;query=target_token
            del capture,baseline
        del branch,native
    mean={arm:{c:float(np.mean(v)) for c,v in scores.items()} for arm,scores in values.items()}
    preference={arm:s['original']-s['counterfactual'] for arm,s in mean.items()}
    effects={arm:preference['native']-preference[arm] for arm in ARMS[1:]}
    return dict(event_id=request['event_id'],task_id=request['task_id'],family_id=request['family_id'],arm=request['arm'],
        scores=values,mean_logp=mean,original_minus_counterfactual=preference,effects=effects,
        target_minus_irrelevant=effects['target']-effects['irrelevant'],first_query_js=first_js,
        native_prefix_parity=parity,capture_noop_exact=True,sham_noop_exact=True,selected_routing_fixed=True,
        passive_first_query=passive,source_selectivity=selectivity,value_delta_norms=norms,
        runtime_seconds=time.monotonic()-started,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
        prefix_tokens=len(prefix),completed=True,at=now())


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--preferred',required=True);ap.add_argument('--limit',type=int);args=ap.parse_args()
    cp=Path(args.config);cfg=json.loads(cp.read_text());root=Path(cfg['root'])
    assert os.environ.get('SLURM_JOB_ID') and torch.cuda.device_count()==1
    assert socket.gethostname().split('.')[0] in cfg['allowed_nodes']
    torch.cuda.set_device(0)
    for path,expected in cfg['source_sha256'].items():assert sha(path)==expected,path
    assert sha(cfg['manifest'])==cfg['manifest_sha256']
    manifest=json.loads(Path(cfg['manifest']).read_text());assert manifest['frozen'] and not manifest['outcomes_used']
    tasks={r['task_id']:r for r in json.loads(Path(cfg['native_tasks']).read_text())['rows']}
    (root/'causal/claims').mkdir(parents=True,exist_ok=True)
    worker='slurm_'+os.environ['SLURM_JOB_ID'];wd=root/'causal/workers'/worker
    order=[args.preferred]+[a for a in ('instruct_direct','instruct_cot','thinking') if a!=args.preferred]
    model=processor=None;current=None;done=[]
    for arm in order:
        for row in (r for r in manifest['rows'] if r['arm']==arm):
            try:(root/'causal/claims'/row['event_id']).mkdir()
            except FileExistsError:continue
            save(root/'causal/claims'/row['event_id']/'owner.json',dict(worker=worker,at=now()))
            key='thinking' if arm=='thinking' else 'instruct'
            if key!=current:
                if model is not None:del model,processor;gc.collect();torch.cuda.empty_cache()
                processor,model=load_runtime(Path(cfg['models'][key]['checkpoint']),'cuda:0');current=key
                env=runtime_environment(Path(cfg['models'][key]['checkpoint']),model,40960)
                save(wd/(key+'_environment.json'),dict(env,slurm_job_id=os.environ['SLURM_JOB_ID'],at=now(),config_sha256=sha(cp)))
            print(json.dumps(dict(event='start_event',event_id=row['event_id'],arm=arm,prefix_tokens=len(row['prefix_token_ids']),at=now())),flush=True)
            try:
                result=score(model,processor,row,tasks[row['task_id']])
                save(root/'causal/results'/(row['event_id']+'.json'),result);done.append(row['event_id'])
                print(json.dumps(dict(event='complete_event',event_id=row['event_id'],runtime_seconds=result['runtime_seconds'],at=now())),flush=True)
            except Exception as exc:
                save(wd/('failure_'+row['event_id']+'.json'),dict(event_id=row['event_id'],error=repr(exc),traceback=traceback.format_exc(),at=now()));raise
            gc.collect();torch.cuda.empty_cache()
            if args.limit and len(done)>=args.limit:break
        if args.limit and len(done)>=args.limit:break
    save(wd/'completed.json',dict(completed=done,at=now()))


if __name__=='__main__':main()
