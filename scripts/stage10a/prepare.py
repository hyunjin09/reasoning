"""Freeze reviewed events, exact native token boundaries and a gold-free queue."""
import os
from pathlib import Path
from transformers import AutoTokenizer
from scripts.stage10a.common import ROOT,OLD,DATA,PROTOCOL,load,save,sha,now


def boundaries(tokenizer,ids,text):
    result=[]
    for n in range(len(ids)+1):
        decoded=tokenizer.decode(ids[:n],skip_special_tokens=True,clean_up_tokenization_spaces=False)
        if text.startswith(decoded):result.append((n,len(decoded)))
    return result


def main():
    assert os.environ.get('SLURM_JOB_ID')
    previous=load(OLD/'config.json');assert load(OLD/'stage9a5_thinking_full_baseline.json')['gates']['pass']
    for name,d in previous['files_sha256'].items():assert sha(Path(previous['checkpoint'])/name)==d
    tokenizer=AutoTokenizer.from_pretrained(previous['checkpoint'],local_files_only=True)
    review=load(ROOT/'audit/semantic_review.json');assert review['sealed'] and not review['used_final_correctness']
    taskpath=OLD/'audit/inference_tasks.json';tasks={r['query_id']:r for r in load(taskpath)['rows']}
    inputs=[taskpath,ROOT/'audit/semantic_review.json',OLD/'config.json',OLD/'stage9a5_thinking_full_baseline.json',
            DATA/'stage9a3_synthetic_dataset_manifest.json',Path('plan/stage10a_causal_perceptual_to_textual_handoff_plan.md')]
    rows=[]
    for original in review['rows']:
        r=dict(original);q=r['query_id'];gp=OLD/'full/results'/f'{q}_full/generation.json';rp=gp.with_name('result.json')
        g=load(gp);assert sha(gp)==r['generation_sha256'];ids=g['generated_token_ids'][:g['reasoning_tokens']]
        text=tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False);assert text==r['native_reasoning']
        bounds=boundaries(tokenizer,ids,text);anchors={}
        for anchor in ('pre','emit','post'):
            target=r[f'{anchor}_char']
            pair=max((v for v in bounds if v[1]<=target),key=lambda x:x[0]) if anchor=='pre' else min((v for v in bounds if v[1]>=target),key=lambda x:x[0])
            n,c=pair;assert not text[min(c,target):max(c,target)].strip(),f'Boundary cuts content: {q} {anchor}'
            assert 0<n<512
            anchors[anchor]=dict(native_tokens=n,char_boundary=c,prefix_text=text[:c],prefix_ids=ids[:n],
                remaining_tokens=512-n,first_masked_generated_query=n,access_mask_cutoff=n-1)
        assert anchors['pre']['native_tokens']<anchors['emit']['native_tokens']<anchors['post']['native_tokens']
        r.update(anchors=anchors,split='primary' if q in review['primary_ids'] else 'reserve',
                 generation_path=str(gp),result_path=str(rp),task=tasks[q])
        rows.append(r);inputs += [gp,rp,Path(tasks[q]['image_path'])]
    # Membership is already sealed; local fact truth is added without replacing any event.
    gold={r['query_id']:r for r in load(DATA/'stage9a3_synthetic_dataset_manifest.json')['queries']}
    truth=[dict(query_id=r['query_id'],emitted_count=r['emitted_count'],source_count=gold[r['query_id']]['count'],
                fact_correct=r['emitted_count']==gold[r['query_id']]['count']) for r in rows]
    save(ROOT/'audit/fact_truth_after_selection.json',dict(at=now(),selection_sha256=sha(ROOT/'audit/semantic_review.json'),rows=truth,no_membership_change=True))
    selection=dict(at=now(),frozen=True,rows=rows,primary_ids=review['primary_ids'],reserve_ids=review['reserve_ids'],
        semantic_review_sha256=sha(ROOT/'audit/semantic_review.json'),protocol_sha256=sha(PROTOCOL),
        independent_unit='image',final_correctness_used_for_selection=False,intervention_outcomes_used=False)
    save(ROOT/'stage10a_event_selection.json',selection)
    cfg=dict(at=now(),checkpoint=previous['checkpoint'],files_sha256=previous['files_sha256'],
        max_total_tokens=512,seed=920260927,bootstrap_draws=4000,allowed_nodes=['node02','node03','node06','node07'],
        max_gpus=8,protocol_sha256=sha(PROTOCOL),selection_sha256=sha(ROOT/'stage10a_event_selection.json'),
        previous_config_sha256=sha(OLD/'config.json'),inputs_sha256={str(p):sha(p) for p in sorted(set(inputs))})
    save(ROOT/'config.json',cfg)
    with (ROOT/'stage10a_handoff_spec.md').open('x') as f:f.write(PROTOCOL.read_text())
    save(ROOT/'audit/resource_estimate.json',dict(at=now(),primary_gate_a_continuations=144,
        generation_upper_gpu_hours=144*512*.06/3600,all_primary_continuations_upper=336,
        all_primary_generation_upper_gpu_hours=336*512*.06/3600,validation_startup_allowance_gpu_hours=1,
        target_primary_gpu_hours=7,stop_before_optional_if_projected_gpu_hours_above=10,max_concurrent_gpus=8))
    print('FREEZE',len(rows),'primary',len(review['primary_ids']),'reserve',len(review['reserve_ids']),flush=True)
    print('POST_OPTION_BINDING',sum(r['post_contains_option_binding'] for r in rows if r['split']=='primary'),flush=True)


if __name__=='__main__':main()
