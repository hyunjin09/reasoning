"""Prospective Stage13A freeze, with no outcome-based family selection."""
import hashlib,math
from pathlib import Path
from scripts.stage13a.execution import *

SPEC='''# Stage13A prospective execution specification

The approved plan is authoritative. Exactly96 X-S final-QC families, unmodified
questions, facts, golds and oracle renderings. Both arms receive identical
image-free single-user Q+E*, no system/CoT suffix. Native model chat templates
with add_generation_prompt=True; Thinking template opens <think> naturally.
No historical outcome substitutes for a primary call.

## Runtime and seeds
Reuse pinned4B Instruct ebb281ec70b05090aa6165b016eac8ec08e71b17 and Thinking
1de27d8c51f12e819435303b9e84c4e25ba8401e. Instruct temperature.7,top-p.8,top-k20,
repetition1,presence1.5,32768tokens. Thinking temperature1,top-p.95,top-k20,
repetition1,presence0,81920tokens. BF16/vLLM0.11/Torch2.8/Transformers4.57.1,
TP1,batch18,maxmodel128000,engine seed42. EOS uses pinned checkpoint defaults;
stop_token_ids=[] and no added stop strings, inherited validated worker path.
Exactly576 calls, three replicates0..2 per family/checkpoint. Seeds use the
full SHA256(stage13a-v1|family_id|checkpoint|replicate) integer modulo2**31.
Checkpoint strings are Qwen/Qwen3-VL-4B-Instruct and Qwen/Qwen3-VL-4B-Thinking.
Verify distinct from all Stage12Y seeds. No best-of selection or retries of
attempted scientific calls; never-started calls can be resumed unchanged after
documented infrastructure repair. Raw tokens, output, prompts and receipts saved.

## Blind review and validity
Review/score all I-EQ calls before opening any T-EQ response or paired outcomes.
Finish I-EQ first-pass and all QC before T-EQ review. Technical status may be
monitored for both. All ambiguous/capped/expression cases receive second review,
plus exactly ceil(.20*288)=58 preselected task IDs per arm ordered by
SHA256(stage13a-v1|score-audit|task_id). Union, not replacement; same-agent QC.
Input validity and outcome extraction precede correctness. Repetition alone is
never exclusion. A clear unretracted cap-before-stop answer remains scoreable.
Pre-outcome caps are missing. Normal-stop refusal/no-answer is INCORRECT, using
an explicit NO_ANSWER marker, not technical missingness. Frozen MathVision
equivalence; score own final answer, never a paired answer or discarded guess.
Preserve original decisions and explicit adjudications when needed.

## Frozen analysis choices
Primary set contains only families with all six replicate slots resolved.
Per-family T mean minus I mean; family-equal mean in percentage points.
10,000 percentile family bootstrap draws; inherited analysis seed120220260929.
Report median and positive/zero/negative counts. Confirm only n>=80,mean>=5pp,
CI lower>0 and absolute checkpoint scoreability difference<=10pp. The exception
for larger scoreability differences requires the full96 least-favorable missing
assignment to retain mean>=5pp and bootstrap lower>0. Coverage<80 always returns
TECHNICALLY_UNRESOLVED. With adequate technical coverage, mean<=0 yields
NO_ADVANTAGE, otherwise a failed effect/CI gate yields SIGNAL_PARTIAL.
Full96 missing bounds assign each unresolved slot0/1 unfavorably/favorably for T;
no probabilistic imputation. Majority needs guaranteed2/3 correct or2/3 incorrect,
otherwise unresolved. Exact two-sided binomial discordant-family comparison is
descriptive. No seed/token independence or post-hoc subgroup analysis.

## Budget sensitivity frozen before outcomes
32k-comparable requires six resolved primary outputs and each Thinking response
has a scoreable, unretracted commitment before generated token32768. If total
tokens<32768 this is immediate; longer outputs require own-response token-boundary
review, never correctness-based inclusion. Recompute the same family estimator.
Operationalize too-small/inconclusive using the same n>=80,mean>=5pp,CI lower>0
requirements. Only a CONFIRMED primary with failure of this comparable check
triggers the already-approved cap-matched panel. This operational detail is
frozen prospectively, not selected after outcomes.
The optional24 families are first24 in SHA256(stage13a-v1|capmatched24|family_id)
order, using family identity only. All72 optional task rows are sealed now.
They use the same three primary Thinking seeds/prompt/recipe, changing cap only
to32768. Compare with existing primary Instruct replicates. Report paired n,
missing bounds and uncertainty descriptively; do not replace the primary gate.
Do not run any optional call before the gate and resource authorization seal.

## Resource/closure discipline
Target<10/hard14 allocatedGPUh. Eight finite primary1GPU Slurm shards,72calls each,
90minute limits reserve12GPUh; expected6–10GPUh from inherited batched throughput.
Capture allocation/cleanup accounting before records disappear. Assess remaining
budget before any optional launch. Maximum8 concurrent GPUs, nodes02/03/06/07,
project scheduler only. No keepalive or tmux. No unapproved budget extension.
Seal Stage13A primary inference before the historical12Y comparison; cohorts are
not independent and never pooled. Save all required artifacts/four figure pairs,
exactly one plan-prescribed recommendation, release GPUs and STOP. No scale,
prompt, subgroup, portability or other mechanism follow-on is authorized.
'''

def main():
    assert not (ROOT/'config.json').exists()
    old=load('outputs/stage12ys/v1/config.json');source=load(OLD/'stage12xs_fresh96_manifest.json')
    rows=source['rows'];assert len(rows)==len({r['family_id'] for r in rows})==96
    source_seal=load(OLD/'audit/final_source_seal.json')
    for p,h in source_seal['files'].items():assert sha(p)==h,p
    for model in old['models'].values():
        for name,h in model['model']['files_sha256'].items():assert sha(Path(model['model']['checkpoint'])/name)==h
    ROOT.mkdir(parents=True,exist_ok=True)
    with (ROOT/'stage13a_equal_evidence_confirmation_spec.md').open('x') as f:f.write(SPEC)
    save(ROOT/'stage13a_frozen96_manifest.json',dict(at=now(),rows=rows,n_families=96,source=str(OLD/'stage12xs_fresh96_manifest.json'),source_sha256=sha(OLD/'stage12xs_fresh96_manifest.json')))
    primary=[task(r,m,k) for r in rows for m in ['I','T'] for k in range(3)]
    assert len({t['seed'] for t in primary})==576
    prior={t['seed'] for p in Path('outputs/stage12ys/v1/audit').glob('phase*_execution.json') for t in load(p)['tasks']}
    assert not prior.intersection(t['seed'] for t in primary)
    selected=sorted(rows,key=lambda r:hashlib.sha256(('stage13a-v1|capmatched24|'+r['family_id']).encode()).hexdigest())[:24]
    optional=[task(r,'T',k,'S') for r in selected for k in range(3)]
    save(ROOT/'stage13a_seed_manifest.json',dict(at=now(),primary=primary,optional=optional,stage12y_seed_overlap=0))
    save(ROOT/'stage13a_capmatched24_manifest.json',dict(at=now(),status='FROZEN_NOT_AUTHORIZED_TO_RUN',selected_ids=[r['item_id'] for r in selected],selection='SHA256(stage13a-v1|capmatched24|family_id), ascending first24; source identity only',tasks=optional))
    audit={m:sorted([t['task_id'] for t in primary if t['model_key']==m],key=lambda tid:hashlib.sha256(('stage13a-v1|score-audit|'+tid).encode()).hexdigest())[:58] for m in ['I','T']}
    save(ROOT/'audit/random_review_manifest.json',dict(at=now(),tasks=audit,selection='58/288 per arm plus all later ambiguities'))
    preserved={str(p):sha(p) for directory in sorted(Path('outputs').glob('stage12*')) for p in directory.rglob('*') if p.is_file() and not any(x in p.parts for x in ['cache','__pycache__','.pytest_cache'])}
    save(ROOT/'audit/historical_preservation.json',dict(at=now(),files=preserved))
    inputs=[ROOT/'stage13a_frozen96_manifest.json',ROOT/'stage13a_seed_manifest.json',ROOT/'stage13a_capmatched24_manifest.json',ROOT/'stage13a_equal_evidence_confirmation_spec.md',ROOT/'audit/random_review_manifest.json',OLD/'audit/final_source_seal.json']
    hashes={str(p):sha(p) for p in inputs};hashes.update(source_seal['files'])
    save(ROOT/'stage13a_input_hashes.json',dict(at=now(),files=hashes,generation_started=False))
    code=list(Path('scripts/stage13a').glob('*.py'))+[Path('scripts/stage13a/run.sh'),Path('scripts/stage12xs/common.py'),Path('code/visual_reasoning/stage8b/v2_scoring.py'),Path('code/visual_reasoning/stage8b/scoring.py')]
    save(ROOT/'config.json',dict(at=now(),models=old['models'],runtime=old['runtime'],environment=old['environment'],caps=CAPS,resource=dict(target_gpu_hours=10,hard_gpu_hours=14,max_concurrent_gpus=8),source_sha256={str(p):sha(p) for p in code},plan_sha256=sha('plan/stage13a_confirmatory_equal_evidence_thinking_advantage_plan.md')))
    save(ROOT/'audit/phaseP_execution.json',dict(at=now(),phase='P',tasks=primary))
    paths=shards('P',primary,4)
    save(ROOT/'audit/preflight.json',dict(at=now(),passed=True,n_families=96,new_primary_calls=576,optional_calls=72,shards=paths,historical_files=len(preserved),estimated_gpu_hours=[6,10],primary_reservation_gpu_hours=12,hard_gpu_hours=14,downloads=False))
    print('PREFLIGHT PASS',len(preserved),'preserved files;',len(paths),'primary shards')

if __name__=='__main__':main()
