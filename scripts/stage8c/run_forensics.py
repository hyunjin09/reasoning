"""Capture every diagnostic stage using unchanged native cached BF16 inference."""
import json
import os
import socket
import time
import traceback
from datetime import datetime,timezone
from pathlib import Path
import joblib
import numpy as np
import torch

from scripts.stage8c.prepare import save,sha
from scripts.stage8c.prepare_repair import ROOT
from visual_reasoning.stage0.modeling import load_runtime,runtime_environment,_reset_generation_state
from visual_reasoning.stage3b0.runtime import suffix_position_ids
from visual_reasoning.stage8b.v2_protocol import prepared_input
from visual_reasoning.stage8b.block0 import episodes
from visual_reasoning.stage8c.gain import VisualGain
from visual_reasoning.stage8c.forensics import DecompositionForensics


@torch.inference_mode()
def run_item(model,processor,detector,item,dest):
    row=item['input'];rid=row['item_id'];old=Path(item['source_native_dir'])
    for path,digest in item['source_sha256'].items():assert sha(path)==digest,path
    ids=json.loads((old/'generation.json').read_text())['generated_token_ids']
    reference=np.load(old/'passive.npz')['retrieval_score']
    batch,meta=prepared_input(processor,dict(row,answer=''))
    prompt=meta['prompt_token_count'];current_ids=batch['input_ids'][0].tolist()
    boundaries=[i for i,t in enumerate(current_ids) if t in processor.tokenizer.all_special_ids and i not in meta['visual_token_indices']]
    save(dest/'token_index_manifest.json',dict(item_id=rid,prompt_length=prompt,
        visual_patch_positions=meta['visual_token_indices'],special_nonvisual_positions=boundaries,
        prompt_nonvisual_positions=meta['prompt_nonvisual_token_indices'],
        multimodal_boundary_ids={token:processor.tokenizer.convert_tokens_to_ids(token) for token in ['<|vision_start|>','<|vision_end|>']},
        prefix_token_ids=current_ids+ids[:max(c['end'] for c in item['cases'])-1],
        prior_reasoning_positions='[prompt_length, current cache length)',padding_positions=[],
        note='Only image patch placeholder tokens define V; boundary/system/user/prior-reasoning tokens are nonvisual. All unpadded current-query positions are causally valid.'))
    selected={t:c['case_id'] for c in item['cases'] for t in range(c['start'],c['end'])}
    start=time.perf_counter();_reset_generation_state(model,seed=1234)
    with DecompositionForensics(model,visual=meta['visual_token_indices'],prompt_length=prompt,
            path=dest/'forensic_rows.jsonl',item_id=rid) as recorder:
        with VisualGain(model,visual=meta['visual_token_indices'],prompt_length=prompt,
                        detector=detector,gain=1.,policy='never') as observer:
            positions=model._prepare_position_ids_for_generation(batch['input_ids'],dict(batch))
            out=model(**batch,position_ids=positions,use_cache=True,return_dict=True,logits_to_keep=1)
            cache=out.past_key_values;rope=model.model.rope_deltas.detach().clone()
            del out
            for t in range(1,max(selected)+1):
                recorder.select(selected.get(t),t)
                out=model(input_ids=torch.tensor([[ids[t-1]]],device='cuda'),
                    attention_mask=torch.ones((1,prompt+t),dtype=torch.long,device='cuda'),
                    position_ids=suffix_position_ids(prompt_length=prompt+t-1,suffix_length=1,rope_deltas=rope,device=torch.device('cuda')),
                    past_key_values=cache,use_cache=True,return_dict=True,logits_to_keep=1)
                cache=out.past_key_values;del out
                if t%512==0:print(json.dumps(dict(event='cached_replay_progress',item_id=rid,token=t,total=max(selected))),flush=True)
        # Persist all measurements, partitions and detector arrays BEFORE gates.
        np.savez_compressed(dest/'passive.npz',**observer.arrays())
        save(dest/'source_partitions.json',recorder.partitions)
    scores=observer.arrays()['retrieval_score'];onsets={e['start_token'] for e in episodes(scores,4)}
    coverage=[dict(c,observed_R=float(scores[c['anchor']]),observed_onset=c['anchor'] in onsets) for c in item['cases']]
    result=dict(item_id=rid,family_id=item['family_id'],rows=len(recorder.rows),coverage=coverage,
        elapsed_seconds=time.perf_counter()-start,peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
        peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved(),
        reference_scores_exact=bool(np.array_equal(scores,reference[:len(scores)],equal_nan=True)),
        partition_pass=all(r['partition_pass'] for r in recorder.rows),
        gqa_pass=all(r['gqa_native_mapping_exact'] for r in recorder.rows),
        pre_legacy_pass=all(r['pre_legacy']['pass_bounds'] for r in recorder.rows),
        pre_bf16_pass=all(r['pre_bf16_sum']['pass_bounds'] for r in recorder.rows),
        post_legacy_pass=all(r['post_legacy']['pass_bounds'] for r in recorder.rows),
        post_bf16_joint_pass=all(r['post_bf16_joint']['pass_bounds'] for r in recorder.rows),
        residual_joint_pass=all(r['residual_joint']['pass_bounds'] for r in recorder.rows),
        at=datetime.now(timezone.utc).isoformat())
    save(dest/'result.json',result)
    print(json.dumps(dict(event='forensics_complete',**result)),flush=True)
    return result


def main():
    rank=int(os.environ['SLURM_PROCID'])
    assert os.environ['SLURM_NTASKS']=='2' and socket.gethostname().split('.')[0]=='node02'
    assert torch.cuda.device_count()==1;torch.cuda.set_device(0)
    cfg=json.loads((ROOT/'audit/forensic_config.json').read_text())
    for path,digest in cfg['source_sha256'].items():assert sha(path)==digest,path
    manifest=json.loads(Path(cfg['prefix_manifest']).read_text())
    freeze=json.loads(Path(cfg['detector_freeze']).read_text())
    assert sha(cfg['detector_freeze'])==cfg['detector_freeze_sha256']
    assert sha(freeze['retrieval']['models'])==freeze['retrieval']['models_sha256']
    detector=joblib.load(freeze['retrieval']['models'])['joint']['model']
    processor,model=load_runtime(Path(cfg['model_checkpoint']),'cuda:0')
    assert next(model.parameters()).dtype==torch.bfloat16
    env=runtime_environment(Path(cfg['model_checkpoint']),model,cfg['max_new_tokens'])
    env.update(slurm_job_id=os.environ['SLURM_JOB_ID'],rank=rank,hostname=socket.gethostname(),
        config_sha256=sha(ROOT/'audit/forensic_config.json'),bf16_reduced_precision_reduction=torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction)
    save(ROOT/'forensic'/f'worker{rank}'/'environment.json',env)
    try:
        results=[run_item(model,processor,detector,item,ROOT/'forensic'/'items'/item['input']['item_id'])
                 for item in manifest['inputs'][rank::2]]
        save(ROOT/'forensic'/f'worker{rank}'/'completed.json',dict(results=results,completed=True))
    except Exception:
        save(ROOT/'forensic'/f'worker{rank}'/'failure.json',dict(traceback=traceback.format_exc()))
        raise


if __name__=='__main__':main()
