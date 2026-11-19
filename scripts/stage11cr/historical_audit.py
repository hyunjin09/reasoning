"""Recover execution fields from pinned code/receipts; never read accuracy files."""
from pathlib import Path
from scripts.stage11cr.common import ROOT, OLD, load, save, sha, now


def main():
    cfg=load(ROOT/'config.json');nine=load('outputs/stage9a/v1/stage9a_generation_config.json')
    second_path=Path('outputs/stage8b/v2/config/transfer32_t1_node02_four_v1.json')
    second=load(second_path)
    fields={}
    for source in ['Stage9A','Stage8B_v2','Stage11C']:
        hist=source!='Stage11C';modelkeys=['thinking'] if source=='Stage8B_v2' else ['thinking','instruct']
        models={k:cfg['models'][k] for k in modelkeys}
        fields[source]=dict(model_revision={k:v['revision'] for k,v in models.items()},
            tokenizer_revision={k:v['revision'] for k,v in models.items()},
            processor_revision={k:v['revision'] for k,v in models.items()},
            chat_template={k:v['files_sha256']['chat_template.json'] for k,v in models.items()},
            system_prompt='None; one user message',user_prompt='Original question/options; CoT suffix only in CoT arm',
            image_insertion='First user content image object then text; process_vision_info then HF processor',
            bos_id=151643,eos_ids=[151645,151643],stop_token_ids=[151645,151643],
            max_new_tokens=40960 if hist else [4096,8192],total_context_limit=262144,
            decoding='sampling' if hist else 'greedy',temperature=1. if hist else None,
            top_p=.95 if hist else None,top_k=20 if hist else None,repetition_penalty=1.,
            use_cache=True,cache_implementation='UNKNOWN (not explicitly recorded; library default)',
            per_call_rope_reset=hist,per_call_seed='row.seed' if hist else 'not set; greedy',
            batch_size=1,attention_backend=dict(text='eager' if hist else 'sdpa',vision='sdpa'),
            dtype='bfloat16',tf32='UNKNOWN (not recorded)' if hist else False,
            image_preprocessing=dict(min_pixels=602112,max_pixels=4014080,patch_size=16,merge_size=2),
            generation_termination='HF generate EOS or max_new_tokens'+('' if hist else ' or wall-budget max_time'),
            return_dict_in_generate=hist,padding='none' if hist else 'left; zero padding at batch1',
            response_postprocessing='decode saved generated ids; final-answer extraction is postgeneration',
            answer_extraction='Local literal-answer review before correctness join; no generation stopping effect',
            logits_available=False,logits_note='Saved generated tokens; no full logits in these native sources',
            torch_version='2.7.1+cu118',transformers_version='5.12.1')
    fields['Stage8B_v2']['per_call_seed']=second['seed']
    fields['Stage8B_v2']['answer_extraction']='Posthoc local cap-independent adapter after sealed semantic-prefix review; unresolved extraction/equivalence retained for review. No generation stopping effect.'
    sources=['outputs/stage9a/v1/stage9a_generation_config.json',str(second_path),str(OLD/'config.json'),
        'code/visual_reasoning/stage0/modeling.py','code/visual_reasoning/stage8b/v2_protocol.py',
        'code/visual_reasoning/stage8b/passive.py','scripts/stage9a/run_native.py','scripts/stage11b/generation.py',
        'outputs/stage9a/v1/native/workers/slurm_120903/thinking_environment.json',
        'outputs/stage9a/v1/audit/preflight/complete.json',
        'outputs/stage8b/v2/native/transfer32_t1_node02_four_v1/census/worker0/environment.json',
        'scripts/stage8b/run_native_v2_four.py','scripts/stage8b/score_native_v2.py']
    source_checks={}
    for label,old in [('Stage9A',nine),('Stage8B_v2',second)]:
        source_checks[label]={p:sha(p)==d for p,d in old['source_sha256'].items() if p in sources}
        assert all(source_checks[label].values())
    summaries={}
    for label,base in [('Stage9A',Path('outputs/stage9a/v1/native/examples')),
                       ('Stage8B_v2',Path('outputs/stage8b/v2/native/transfer32_t1_node02_four_v1/examples'))]:
        rows=[]
        for p in sorted(base.glob('*/generation.json')):
            g=load(p)
            rows.append(dict(path=str(p),tokens=len(g['generated_token_ids']),normal_eos=g.get('normal_eos','UNKNOWN'),
                at_length_cap=g.get('at_length_cap','UNKNOWN'),arm=g.get('arm','thinking' if label=='Stage8B_v2' else 'UNKNOWN')))
        summaries[label]=rows
    save(ROOT/'stage11cr_historical_runtime_comparison.json',dict(at=now(),sources=fields,
        source_sha256={p:sha(p) for p in sources},archived_source_hash_checks=source_checks,
        historical_completion_metadata=summaries,accuracy_files_opened=False,
        limitation='Batch/TF32/default-cache details distinguished from observed receipts. Stage8B-v2 is an independent execution source, not an independent code implementation.'))
    priorities=[('chat_template',['chat_template','system_prompt','user_prompt']),('eos_stop',['bos_id','eos_ids','stop_token_ids']),
        ('length_semantics',['max_new_tokens','total_context_limit']),('generation_kwargs',['decoding','temperature','top_p','top_k','repetition_penalty','return_dict_in_generate']),
        ('revisions',['model_revision','tokenizer_revision','processor_revision']),('image',['image_insertion','image_preprocessing']),
        ('cache',['use_cache','cache_implementation','per_call_rope_reset','per_call_seed']),('backend',['attention_backend','tf32']),
        ('batch',['batch_size','padding']),('postprocessing',['response_postprocessing','generation_termination'])]
    matrix=[]
    for priority,(name,keys) in enumerate(priorities,1):
        matrix.append(dict(priority=priority,dimension=name,
            fields={k:dict(historical=fields['Stage9A'][k],failed=fields['Stage11C'][k],
                          differs=fields['Stage9A'][k]!=fields['Stage11C'][k]) for k in keys},
            completion_improvement=None,exact_replay_improvement=None,new_divergence=None,status='CPU_AUDIT_ONLY'))
    save(ROOT/'audit/discrepancy_matrix_before_execution.json',dict(at=now(),rows=matrix,accuracy_used=False))
    # Fully qualified launch file is a new immutable wrapper around the first freeze.
    manifest=load(ROOT/'known_good_tasks.json')
    manifest.update(at=now(),parent_sha256=sha(ROOT/'known_good_tasks.json'),
        source_sha256={p:sha(p) for p in ['scripts/stage11cr/worker.py','scripts/stage11cr/common.py','scripts/stage11cr/run.sh',
        'scripts/stage11b/generation.py','code/visual_reasoning/stage0/modeling.py','code/visual_reasoning/stage8b/v2_protocol.py']})
    save(ROOT/'run_known_good_tasks.json',manifest)
    total=sum(r['historical_tokens'] for s in manifest['shards'] for r in s['rows'])
    save(ROOT/'audit/initial_resource_estimate.json',dict(at=now(),known_good_tokens=total,
        observed_historical_seconds=sum(load(Path(r['historical_dir'])/'generation.json')['runtime']['elapsed_seconds']
            for s in manifest['shards'] for r in s['rows']),
        known_good_estimated_gpu_hours=[total*.025/3600+.06,total*.045/3600+.12],
        note='Exact historical tokens schedule four balanced oneGPU shards. Max35min each; stage commitment<=2.333GPUh, actual target<2. Nonprimary/scientific work still gated.',
        hard_stage_gpu_hours=9))
    print('R0_FROZEN',total,'historical tokens; no accuracy opened')


if __name__=='__main__':main()
