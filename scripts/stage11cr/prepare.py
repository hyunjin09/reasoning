"""Freeze historical cases and technical rules without reading accuracy labels."""
import hashlib
from pathlib import Path
from scripts.stage11cr.common import ROOT, OLD, ARMS, load, save, sha, now


def main():
    old = load(OLD/'config.json')
    historical = Path('outputs/stage9a/v1')
    split = load(OLD/'stage11c_primary_split.json')
    primary_ids = {r['family_id'] for r in split['primary']}
    primary_images = {r['image_sha256'] for r in split['primary']}
    tasks = load(historical/'audit/native_tasks.json')['rows']
    selected = []
    for arm in ARMS:
        candidates = []
        for row in tasks:
            if row['arm'] != arm or row['family_id'] in primary_ids or row['image_sha256'] in primary_images:
                continue
            dest = historical/'native/examples'/row['task_id']
            g = load(dest/'generation.json')
            region = g['raw_decoded_response'].split('</think>')[-1]
            if not (g['normal_eos'] and not g['at_length_cap'] and
                    (arm != 'thinking' or '</think>' in g['raw_decoded_response']) and
                    ('\\boxed' in region or 'answer' in region.lower())):
                continue
            key = hashlib.sha256(('stage11cr-r1-v1:'+row['task_id']).encode()).hexdigest()
            candidates.append((key, row, dest, g))
        for key, row, dest, g in sorted(candidates, key=lambda x:x[0])[:6]:
            selected.append(dict(row, condition='native', max_new_tokens=40960,
                historical_dir=str(dest), historical_generation_sha256=sha(dest/'generation.json'),
                historical_input_sha256=sha(dest/'input.json'), historical_tokens=g['tokens'],
                historical_committed_final_review='Explicit terminal answer verified from response only; correctness not consulted.',
                selection_hash=key))
    assert len(selected)==12 and len({r['task_id'] for r in selected})==12
    cap_cases=load(OLD/'audit/cap_cases.json')['rows']
    assert len(cap_cases)==12 and not primary_ids.intersection(r['family_id'] for r in cap_cases)
    scientific_paths=[OLD/name for name in ['stage11c_primary_split.json','stage11c_e_star_gold.parquet',
        'stage11c_e_star_sufficiency_review.json','stage11c_heldout_source_manifest.json',
        'stage11c_thinking_vs_instruct_spec.md','config.json','audit/cap_cases.json','audit/closure_validation.json']]
    (ROOT/'audit').mkdir(parents=True,exist_ok=True)
    save(ROOT/'config.json', dict(at=now(), models=old['models'], allowed_nodes=old['allowed_nodes'],
        max_gpus=8, hard_gpu_hours=9, target_gpu_hours=7, technical_target_gpu_hours=2,
        nonprimary_target_gpu_hours=.5, batch_size=1, dtype='bfloat16', tf32=False,
        frozen_scientific_inputs={str(p):sha(p) for p in scientific_paths},
        known_good_historical_cap=40960, nonprimary_cap_candidates=[4096,8192],
        technical_accuracy_forbidden=True))
    save(ROOT/'stage11cr_known_good_manifest.json',dict(at=now(),frozen=True,rows=selected,
        selection_rule='Among Stage9A EOS/noncapped outputs with explicit terminal answer, six per arm by ascending SHA256(stage11cr-r1-v1:+task_id); no correctness/length filter. Saved tokens required. Primary families/images excluded.',
        seed_string='stage11cr-r1-v1:', primary_overlap=0, accuracy_used=False))
    clean_keys=['item_id','family_id','image','image_sha256','generation_query','seed']
    save(ROOT/'nonprimary_cases.json',dict(at=now(),frozen=True,
        rule='Reuse exactly the original twelve Stage11C technical cases; do not open reserve.',
        rows=[{k:r[k] for k in clean_keys} for r in cap_cases]))
    # Balance by historical token count for scheduling only, after case selection.
    shards=[]
    for arm in ARMS:
        bins=[[],[]];costs=[0,0]
        for row in sorted([r for r in selected if r['arm']==arm],key=lambda r:-r['historical_tokens']):
            k=min(range(2),key=lambda j:costs[j]);bins[k].append(row);costs[k]+=row['historical_tokens']
        for k,rows in enumerate(bins):
            shards.append(dict(id=f'{arm}_{k}',model_key='thinking' if arm=='thinking' else 'instruct',rows=rows))
    save(ROOT/'known_good_tasks.json',dict(at=now(),frozen=True,queue='known_good',protocol='historical',
        config_sha256=sha(ROOT/'config.json'),shards=shards,n_calls=12))
    spec='''# Stage11C-R repair specification

Frozen before new execution. Approved plan: plan/stage11cr_technical_repair_and_frozen_rerun_plan.md.
Original Stage11C STOP, raw generations, source annotations, 80 primary/40 reserve and all subsets remain immutable. This is technical repair, not outcome-selected scientific rescue. P1/P2/P3 and original statistical seed1120260930 remain unchanged.

## Technical sequence
R0 compares Stage9A and independent Stage8B-v2 historical runs with Stage11C. Missing historical values are UNKNOWN, never inferred as observations. The initial audit finds sampling versus greedy, eager versus SDPA text attention, per-call RNG/rope reset and wrapper differences; native templates, checkpoints, pixels and EOS IDs are compared explicitly.
R1 freezes exactly12 historical committed-answer cases (6 T/6 D) by the documented hash rule, with no correctness or length selection. Reproduce the exact Stage9A recipe first: BF16, text eager/vision SDPA, native inputs, samplingT1/top_p.95/top_k20/repetition1, original item seed, reset rope state, fresh cache, historical40960 common max_new_tokens. No passive scientific metrics are needed; archived no-op observer validation is retained. Both versions call Hugging Face model.generate, not different manual decoding algorithms.
Exact historical token identity is the strict replay criterion when recovered environment and inputs permit it. Otherwise report the specific backend/nondeterminism limitation and behavioral tier separately, never call a mismatch exact reproduction. Record prefix and first divergence, EOS, committed final, lengths and repetition. Historical logits unavailable unless actually found.
R1 gate: <=1 cap hit, >=10 committed finals, <=1 pathological repetition, no catastrophic mode/input failure. Normal-length class is recorded using ratios (<.5, .5–2, >2); mismatched cases outside .5–2 do not pass behavioral reproduction merely by reaching EOS. Accuracy labels are never consulted.
Finite discrepancy checks, if necessary: first frozen case in each arm, at8192: failed SDPA/greedy; restore sampling only; restore eager only relative to sampled SDPA. Template/EOS/length/revision/image fields require no candidate mutation if identical. Compare fresh input fingerprints and cache/rope state. No full protocol grid. Candidate ranking exactly follows the plan: historical, fewest deviations, exact replay, caps, median excess length. Stop if no justified candidate passes; no primary rerun on a failed technical gate.

## Non-primary cap validation
Reuse the exact12 original technical cases; no reserve opened. If R1 passes, freeze the repaired protocol then test common4096 first (24 calls). If it fails completion solely or partly through truncation and budget permits, test8192 once, never higher in this cap-selection branch. Choose smallest common passing cap. R3: total caps<15%, each arm<20%, each committed-final>=75%, no severe repetition imbalance (>=20pp or catastrophic repeated loops). Gold hidden; no correctness selection. STOP if neither passes.

## Scientific rerun gates
Only after R3 passes, rerun all80 native T/D from scratch (including prior16). Before scoring: each caps<20%, committed final>=75%, final-rate difference<20pp. Then original performance gate T>=25%,D>=10%,gap>=10pp,>=12 T-only correct. No oracle on failure. Oracle uses identical frozen text-only question+E*, no image or inherited multimodal state. Oracle caps<20%, final>=75%, no severe imbalance; retain the original frozen neutral-scaffolding validity check. Neutral24 only after initial oracle validity; CoT48 only for residualP2>=5pp. Reserve40 only under original precision-limited gate and remaining budget. Equal-family4000 paired bootstrap/seed1120260930,95% and Bonferroni3 intervals, original interpretation margins; no post-hoc endpoints or E* repair. Unknown/not-run is not wrong.

## Resources and stop
Existing .venv and local pinned models/images, no downloads or installations. Scheduler+Slurm only, available nodes02/03/06/07, at most8 GPUs, finite oneGPU jobs; no idle keepalive. Target technical<2GPUh/nonprimary<.5GPUh/total<7GPUh, hard total9GPUh including failed/startup/partial allocations. Prospective envelope checked before every wave. Budgets are not reset between phases. No automatic scientific wave until its gate is sealed. No new stage/benchmark/model search. Final exactly one plan-prescribed recommendation, then STOP.
'''
    (ROOT/'stage11cr_repair_spec.md').write_text(spec)
    save(ROOT/'audit/pre_execution_freeze.json',dict(at=now(),frozen=True,
        files={str(ROOT/n):sha(ROOT/n) for n in ['stage11cr_repair_spec.md','config.json','stage11cr_known_good_manifest.json','known_good_tasks.json','nonprimary_cases.json']},
        no_new_outputs_exist=not (ROOT/'known_good/results').exists(),accuracy_used=False))
    print('FROZEN',[(r['task_id'],r['historical_tokens']) for r in selected])


if __name__=='__main__':main()
