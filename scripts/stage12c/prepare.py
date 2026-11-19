"""Freeze approved C/T requests and analysis rules before any generation."""
import hashlib
from pathlib import Path
import pandas as pd
from scripts.stage12c.common import ROOT, COT_SUFFIX, load, save, sha, now
from scripts.stage12c.protocol import authorize_manifest


def main():
    assert not (ROOT/'generations').exists() and not (ROOT/'config.json').exists()
    amendment=load(ROOT/'audit/thinking_recipe_resolution.json')
    selection=load(ROOT/'audit/identity_selection.json')
    assert sha(ROOT/'audit/identity_selection.json')==amendment['identity_selection_sha256']
    for p,h in load(ROOT/'audit/preserved_history_hashes.json')['files'].items():assert sha(p)==h,p
    old=load('outputs/stage12bs/v1/stage12bs_full_manifest.json')
    previous=load('outputs/stage12bs/v1/config.json')
    thinking=load('outputs/stage9a5/v1/config.json')
    model_t={k:thinking[k] for k in ['checkpoint','revision','files_sha256']}
    model_t['name']='Qwen/Qwen3-VL-4B-Thinking'
    assert model_t['revision']==amendment['revision']
    cfg=dict(at=now(),environment=previous['environment'],runtime=previous['runtime'],
        arms=dict(C=dict(model=previous['model'],recipe=previous['recipe'],cap=32768),
                  T=dict(model=model_t,recipe=amendment['recipe'],cap=amendment['max_output_tokens'])),
        seed_policy='Reuse each frozen Stage12B native N per-family seed unchanged in C and T.',
        inherited_seed_policy=previous['seed_policy'],bootstrap_seed=previous['bootstrap_seed'],bootstrap_draws=4000,
        clarification_sha256=sha(ROOT/'audit/thinking_recipe_resolution.json'),
        resource=dict(target_gpu_hours=6,hard_gpu_hours=8,max_concurrent_gpus=8))
    sources=list(Path('scripts/stage12c').glob('*.py'))+[Path('scripts/stage12c/run.sh'),
        Path('scripts/stage12br/protocol.py'),Path('scripts/stage12bs/protocol.py'),
        Path('code/visual_reasoning/stage8b/v2_scoring.py'),Path('code/visual_reasoning/stage8b/scoring.py'),
        Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision/run_mathv.py')]
    cfg['source_sha256']={str(p):sha(p) for p in sources};save(ROOT/'config.json',cfg)
    tasks=[]
    for t in old['tasks']:
        if t['arm']!='N':continue
        for arm in 'CT':
            new=dict(t,arm=arm,task_id=f"{arm}_{t['item_id']}_v1",cap=cfg['arms'][arm]['cap'],
                     prompt=t['prompt']+(COT_SUFFIX if arm=='C' else ''))
            assert new['seed']==t['seed'] and new['image_sha256']==t['image_sha256']
            tasks.append(new)
    assert len(tasks)==122
    labels=pd.read_parquet('outputs/stage12bs/v1/stage12bs_failure_profiles.parquet')
    assert labels.bottleneck.value_counts()['B1']==labels.bottleneck.value_counts()['B4']==11
    full=dict(at=now(),frozen=True,source='outputs/stage12bs/v1/stage12bs_full_manifest.json',
        source_sha256=sha('outputs/stage12bs/v1/stage12bs_full_manifest.json'),n_families=61,n_facts=157,
        config_sha256=sha(ROOT/'config.json'),rows=old['rows'],tasks=tasks,
        sanity_ids=selection['sanity_ids'],remaining_ids=selection['remaining_ids'],
        frozen_labels_path='outputs/stage12bs/v1/stage12bs_failure_profiles.parquet',
        frozen_labels_sha256=sha('outputs/stage12bs/v1/stage12bs_failure_profiles.parquet'),
        labels=labels.to_dict('records'))
    save(ROOT/'stage12c_frozen_bottleneck_manifest.json',full)
    for arm,name in [('C','cot'),('T','thinking')]:
        rows=[t for t in tasks if t['arm']==arm]
        save(ROOT/f'stage12c_{name}_manifest.json',dict(at=now(),frozen=True,arm=arm,config_sha256=sha(ROOT/'config.json'),
             n_calls=61,tasks=rows,model_revision=cfg['arms'][arm]['model']['revision'],recipe=cfg['arms'][arm]['recipe'],cap=cfg['arms'][arm]['cap']))
        sanity=dict(at=now(),frozen=True,phase='sanity',arm=arm,config_sha256=sha(ROOT/'config.json'),
                    rows=[t for t in rows if t['item_id'] in selection['sanity_ids']])
        authorize_manifest(sanity,full);save(ROOT/f'audit/sanity_{arm}.json',sanity)
        for rank in range(2):
            ids=selection['remaining_ids'][rank::2]
            remainder=dict(at=now(),frozen=True,phase='remaining',arm=arm,config_sha256=sha(ROOT/'config.json'),
                           rows=[t for t in rows if t['item_id'] in ids])
            # Only structural preflight; launch/worker enforce the actual saved sanity gate.
            authorize_manifest(remainder,full,sanity_pass=True);save(ROOT/f'audit/remaining_{arm}_{rank}.json',remainder)
    order=sorted([r['family_id'] for r in old['rows']],key=lambda f:(hashlib.sha256(('stage12c-audit-v1|'+f).encode()).hexdigest(),f))
    rules=dict(at=now(),frozen=True,generation_started=False,correctness_opened=False,
        sanity=dict(n=12,input_valid=12,scoreable_minimum=10,pre_outcome_caps_maximum=1),
        full_gate=dict(input_valid=61,scoreable_minimum=51,pre_outcome_caps_maximum=5),
        full_gate_rationale='Same prospective rate-preserving extension used in Stage12B-S: ceiling10/12 and floor1/12, no repetition exclusion.',
        primary_strata=['B1','B4'],descriptive_strata=['B2','B3'],
        primary_denominator='Scientifically scoreable outcomes within each frozen stratum, with total frozen stratum and missingness reported separately; unscoreable never coded as wrong.',
        missingness_sensitivity='Also report observed rescues/11 and identification bounds k/11 to(k+missing)/11, explicitly not imputing correctness.',
        paired_denominator='Only jointly scoreable arms; missing pairs get their own transition category.',
        bootstrap=dict(seed=cfg['bootstrap_seed'],draws=4000,unit='family',weight='equal',
                       selectivity='Resample complete frozen families within B1 and B4 separately, retaining C/T pairing and missingness.'),
        random_audit=dict(seed='stage12c-audit-v1',family_hash_order=order,rule='Firstceil20% of families with neither arm ambiguity-flagged; review both arms. Every ambiguity-triggered arm reviewed separately.'),
        scoring='Separate arm-only correctness packets; frozen MathVision equivalence; all technical labels sealed before correctness packets.',
        trace_evidence=dict(n_families=26,arms=['C','T'],packet='family_id,E*,one trace only; no correctness/paired outcome/bottleneck label',
            precedence=['WRONG_OR_CONFLICTING if any explicit wrong/contradicted atom','FULL if all atoms explicitly correct','PARTIAL if some correct','NOT_EXTERNALIZED otherwise'],
            scope='Before the committed final answer; explicit geometrical binding required; cannot infer evidence from a correct final answer.'),
        thinking_scoreability='Native scratchpad candidates are provisional; inspect surviving task commitment after native </think>. No candidate promoted solely because the cap was reached.',
        decision='Technical gate first; informative if any arm-stratum has>=5rescues OR paired B1+B4 Thinking-only>=4; never count union as five per arm.',
        stopping='17artifacts,5figures,exactlyone recommendation; no follow-on launch')
    save(ROOT/'audit/analysis_rules.json',rules)
    spec=f'''# Stage12C selective rescue: frozen specification

Frozen {now()} before any C/T generation. Authority: preserved approved_plan.md plus the explicit prospective user clarification in thinking_recipe_resolution.json. Historical synthetic greedy512 is excluded from recipe inheritance.

Preserve61 independent MathVision families,157 E* facts, every Stage12B-S E/N/O label and all1742 historical files. C copies each original native N request and appends only ` Let's think step by step.`; T copies N without suffix. Both preserve image bytes, original question/options, preprocessing and per-family N seed. C checkpoint ebb281ec70b05090aa6165b016eac8ec08e71b17; T checkpoint1de27d8c51f12e819435303b9e84c4e25ba8401e.

C: temperature.7,top-p.8,top-k20,repetition1,presence1.5,max32768. T: temperature1,top-p.95,top-k20,repetition1,presence0,max40960. BF16/vLLM0.11.0, native processor/templates, original image preprocessing, engine seed42,batch limit18,max model length128000. No added system or answer-format prompt. Native T template includes <think>; raw whole outputs/tokens and </think> are preserved. Native EOS; no extra stop strings/IDs. One logical call per family/arm, no retries or replacement.

The already-sealed sanity selection is unchanged: SHA256(stage12c-sanity-v1|family_id), first12, identity only. Run24calls first; each arm requires12input-valid,>=10scoreable,<=1pre-outcome cap. Repetition never excludes. A cap with a surviving unique final commitment can be scoreable; provisional scratchpad candidates cannot become finals by truncation. Both arms must pass before98 remaining calls. Full-cohort technical gate preserves the same rates:61valid,>=51scoreable,<=5pre-outcome caps per arm. Missing outcomes remain technical missingness, never wrong.

Correctness remains unopened through technical review and all planned generation. Arm-only scoring uses frozen MathVision equivalence. Mandatory ambiguity second reviews plus ceil20% hash-ordered unambiguous-family audit, both arms separately. Trace-evidence annotation on frozen26 complete native failures uses only family/E*/one trace and precedes correctness joins. Same-agent separate-pass quality control, not independent inter-rater reliability.

Primary P1–P4 are C/T rescue in B1/B4; each has11 frozen families. Arm-scoreable denominators with explicit missingness; also report observed rescue/11 and bounds without wrong-answer imputation. Paired transitions use jointly scoreable C/T with missing pairs separate.4000 family-equal stratified bootstrap draws, seed{cfg['bootstrap_seed']}, preserve paired C/T within families. B2=1/B3=3 and B1 explicit-wrong7/unresolved-only4 are descriptive. No hidden-state interpretation of visible trace evidence or causal Thinking-on language.

First two one-GPU60-minute finite jobs bound sanity allocation by2GPUh. Conditional remainder uses four one-GPU60-minute jobs (25/24 calls per arm), with prospective total allocation envelope checked against hard8GPUh, target<6. Expected full run roughly3–5GPUh using prior4B batching throughput; measured sanity throughput updates this estimate. Only authorized node02/03/06/07, max8 GPUs, no tmux/keepalive. Each worker exits when its queue finishes.

Produce17 required artifacts/five figure pairs and exactlyone recommendation; never launch additional E/N/O, C/T oracle, mechanistic experiment, new dataset or follow-on. Technical failure stops the branch and preserves all partial outputs.
'''
    (ROOT/'stage12c_selective_rescue_spec.md').write_text(spec)
    paths=[ROOT/'config.json',ROOT/'stage12c_selective_rescue_spec.md',ROOT/'stage12c_frozen_bottleneck_manifest.json',
           ROOT/'stage12c_cot_manifest.json',ROOT/'stage12c_thinking_manifest.json',ROOT/'audit/analysis_rules.json',
           ROOT/'audit/identity_selection.json',ROOT/'audit/thinking_recipe_resolution.json']
    paths+=list((ROOT/'audit').glob('sanity_*.json'))+list((ROOT/'audit').glob('remaining_*.json'))
    save(ROOT/'audit/prospective_freeze.json',dict(at=now(),generation_started=False,correctness_opened=False,files={str(p):sha(p) for p in paths}))
    print('FROZEN:61families;122calls;24sanity +98conditional. C32768/T40960; fixed seeds/IDs preserved.')


if __name__=='__main__':main()
