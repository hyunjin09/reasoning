"""Prospective channel-contract check on the disjoint technical four only."""
from scripts.stage13c.execution import *
from scripts.stage13c.protocol import dummy_ids

SPEC='''# Stage13C prospective execution specification

The approved Stage13C plan controls all scientific hypotheses, conditions,
denominators, numeric gates and the 18 allocated-GPU-hour hard stop.
The source-only scientific24, disjoint technical4 and initial8 are already sealed.
No new model output was used in selection. First technically resolved historical
Thinking replicate in ascending order supplies length and source deductions.

All inputs are image-free, exact frozen Stage13A Q+E*. Pinned 4B checkpoints and
model-specific sampling remain unchanged: I(.7,.8,20,rep1,pres1.5,32768 cap);
T(1,.95,20,rep1,pres0,81920 cap). Caps count all generated tokens, including
forced reasoning and its closing token. Native template, checkpoint EOS, no new
stop strings. No system, CoT or answer-only instruction is added.

Forced traces are actual per-token V1 autoregressive decoding steps with KV
continuation. No forced token enters prefill. After exact prescribed reasoning
tokens, force native </think>, then ordinary final-channel generation. Block
reopening <think>; do not add a second free reasoning channel. Native final-answer
prose remains possible under the unchanged recipe; technical review must flag
continued deliberation/dummy continuation or channel violations, rather than
silently treating them as compliant. Receipts archive token IDs, counts and
zero-based close/start positions. Prefix caching and speculative decoding are off.
BF16 vLLM0.11, TP1, batch4, max_model_len128000, GPU utilization.9, engine seed42.
Batch4 is a prospective memory bound for long forced KV trajectories.

Technical execution is staged: first short16/longL on all four technical families,
one technical seed each (8 calls), to establish the critical runtime contract.
Then native/derived/dummy and Instruct context checks on the same technical four
before any scientific call. A failed forced contract blocks science immediately.
No technical correctness enters any selection. All scientific D extraction,
leakage/correctness audits, dummy IDs, donor mappings, seeds and prompts must be
sealed before scientific generation; no scientific outcome is opened beforehand.

Five fresh replicates0..4 per scientific condition. Seed full SHA256 integer of
stage13c-v1|family_id|condition|replicate modulo2**31; technical namespace
stage13c-v1-technical. Source strata: answer format, difficulty, E* atoms1/2+;
Hamilton N/4 proportional quotas, lexical remainder ties, prescribed family hash.
Technical and initial8 hash namespaces are recorded in the selection manifest.
Semantic initial gate uses the first eight safe families in the already frozen
initial8-order over all24 (or all eligible if fewer); no outcomes enter eligibility.
An arm with >20% technical missingness stops remaining science; no prompt/cap tuning.

Derived content is an ordered, deduplicated extraction of source intermediate
propositions, not a new solution. Retain source errors; correctness is secondary.
Exclude target-resolving conclusions and all five leakage classes from primary
semantic inputs. No-safe families stay in the buffer assay. Donors are drawn
within the scientific or disjoint technical cohort separately by the plan's
minimal Instruct-token-length difference and SHA256 tie rule.

Primary analysis uses family means across all5 seeds, complete pairs (allC0-C3
for portable contrasts), 10000 family-bootstrap draws, inherited seed120220260929.
Use integer correct-replicate differences to preserve exact zero bounds. Report
positive/zero/negative families, full-cohort worst/best missingness bounds, all
original minimum-family and effect/CI gates. Arm-separated own-response scoring
before paired labels, inherited MathVision equivalence, all ambiguities plus
deterministic20% random second review; same-agent QC, not independent reliability.
Cap after an unretracted clear final may be valid; cap-before-outcome is missing;
normal-stop no-answer is scientific incorrect. Repetition alone is not exclusion.
Optional historical I-/T+ summaries only after primary sealing, descriptive.

At most1080 scientific calls; technical calls bounded to36 if allD safe.
Target<14/hard18 allocatedGPUh, up to8 scheduler/Slurm GPUs on authorized nodes.
Reserve complete walltime envelopes before submission; save terminal accounting.
Preserve all prior Stage12/13 artifacts. Exactly one plan-matched recommendation,
then STOP; no follow-on stage or hypothesis tuning.
'''

def main():
    from transformers import AutoTokenizer
    old=load(OLD/'config.json')
    ROOT.mkdir(parents=True,exist_ok=True)
    with (ROOT/'stage13c_post_evidence_mechanism_spec.md').open('x') as f:f.write(SPEC)
    cfg=dict(at=now(),models=old['models'],runtime=dict(old['runtime'],batch_size=4),environment=old['environment'],
        resource=dict(target_gpu_hours=14,hard_gpu_hours=18,max_concurrent_gpus=8),
        source_sha256={str(p):sha(p) for p in list(Path('scripts/stage13c').glob('*.py'))+[Path('scripts/stage13c/run.sh'),Path('scripts/stage12xs/common.py')]},
        plan_sha256=sha('plan/stage13c_computational_buffer_vs_derived_state_priming_plan.md'))
    save(ROOT/'config.json',cfg)
    tok=AutoTokenizer.from_pretrained(cfg['models']['T']['model']['checkpoint'])
    phrase=tok.encode('Let me think.',add_special_tokens=False);close=tok.encode('</think>',add_special_tokens=False);op=tok.encode('<think>',add_special_tokens=False)
    assert len(close)==len(op)==1
    sources={r['item_id']:r for r in load(ROOT/'stage13c_source_trace_manifest.json')['rows']};tasks=[]
    for row in load(ROOT/'stage13c_technical4_manifest.json')['rows']:
        text=row['prompts']['O'];messages=[dict(role='user',content=[dict(type='text',text=text)])]
        chat=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        assert chat.endswith('<|im_start|>assistant\n<think>\n')
        prompt_ids=tok.encode(chat,add_special_tokens=False)
        assert not set([151652,151653,151655,151656]).intersection(prompt_ids)
        for condition,n in [('T_SHORT',16),('T_LONG',sources[row['item_id']]['reasoning_token_count'])]:
            forced=dummy_ids(phrase,n)+close
            tasks.append(dict(task_id=f"technical_{condition}_{row['item_id']}_r0",phase='technical_buffer',
                item_id=row['item_id'],family_id=row['family_id'],condition=condition,model_key='T',
                cap=81920,seed=seed(row['family_id'],condition,0,True),replicate=0,prompt=text,
                chat_prompt=chat,prompt_token_ids=prompt_ids,forced_token_ids=forced,close_id=close[0],open_id=op[0]))
    save(ROOT/'audit/technical_buffer_tasks.json',dict(at=now(),tasks=tasks,scientific=False))
    sources_code=['.venv/official_eval/lib/python3.12/site-packages/vllm/v1/sample/logits_processor/'+x for x in ['interface.py','state.py','builtin.py']]
    save(ROOT/'audit/implementation_sources.json',dict(at=now(),official_docs='https://docs.vllm.ai/en/v0.11.0/features/custom_logitsprocs.html',
        conceptual_reference='https://arxiv.org/abs/2603.09906',local_implementation_hashes={p:sha(p) for p in sources_code}))
    preserved={str(p):sha(p) for directory in sorted(Path('outputs').glob('stage12*'))+[Path('outputs/stage13a'),Path('outputs/stage13b')]
        for p in directory.rglob('*') if p.is_file() and not any(x in p.parts for x in ['cache','__pycache__','.pytest_cache'])}
    save(ROOT/'audit/historical_preservation.json',dict(at=now(),files=preserved))
    print('TECHNICAL_BUFFER_MANIFESTS',shards('technical_buffer',tasks,2),'PRESERVED',len(preserved),flush=True)

if __name__=='__main__':main()
