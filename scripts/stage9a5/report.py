"""Render the bounded Stage9A.5 result and exactly one unexecuted recommendation."""
import os
from scripts.stage9a5.common import ROOT, COT, load, save, sha, now


def pp(x):return f'{100*x:.2f}'


def interval(r):return f"[{pp(r['ci95'][0])}, {pp(r['ci95'][1])}]"


def main():
    assert os.environ.get('SLURM_JOB_ID')
    inf=load(ROOT/'stage9a5_cot_vs_thinking_inference.json')
    base=load(ROOT/'stage9a5_thinking_full_baseline.json');cotbase=load(COT/'stage9a4_qwen3_4b_full_baseline.json')
    c=load(ROOT/'stage9a5_absolute_access_comparison.json');rel=load(ROOT/'stage9a5_relative_time_analysis.json')
    control=load(ROOT/'stage9a5_null_sink_control.json');acct=load(ROOT/'stage9a5_resource_accounting.json')
    audit=load(ROOT/'audit/final_validation.json');assert audit['pass_all'] and acct['all_gpu_jobs_terminal']
    primary=c['contrasts']['t128'];selected=inf['selected_cutoff']
    lines=[f'# Stage9A.5 — Qwen3-VL-4B native Thinking vs prompted CoT',
           f'Completed {now()}. **Outcome {inf["outcome"]}; COMPLETE / STOP.**',
           inf['interpretation'],
           f'Thinking-specific prolonged visual-access necessity is **{"supported" if inf["thinking_specific_prolonged_claim"] else "not supported"}** under the preregistered claim gate. '
           f'The primary Thinking-minus-CoT damage contrast at128 is {pp(primary["difference"])}pp,95% CI {interval(primary)}pp. '
           f'{primary["images_more_thinking_damage"]}/32 images have greater Thinking damage, '
           f'{primary["images_less_thinking_damage"]}/32 lower damage and{primary["images_equal_damage"]}/32 tied.',
           '## Fixed design and validity',
           'Same32 frozen synthetic images, one color-count and one shape-count query each. All64 queries remain in every primary condition; missing final options receive no credit. '
           'The Stage9A.4 CoT reference, checkpoint files, questions, option permutations, images and preprocessing were hash-verified and reused without regeneration.',
           'New arm: native Qwen3-VL-4B-Thinking, revision1de27d8c51f12e819435303b9e84c4e25ba8401e. The explicit CoT instruction was removed; the native template opens `<think>`. '
           'Literal option review applies only after native `</think>`, with scratchpad proposals excluded. FULL reasoning and final-answer reviews were sealed without gold before scoring.',
           'Both matched-scale arms: greedy BF16, TF32 off,512-token cap, native EOS, eager language/SDPA vision, native DeepStack unchanged. '
           'All36 decoder layers are covered by generated-query→image-key restriction. Prefill and image-derived cache remain available. '
           'The prefill-predicted first output is native; query index t=absolute−prompt+1 is blocked when t>cutoff.',
           '| FULL metric | CoT | Thinking |','|---|---:|---:|']
    for name,key in [('Correct','correct'),('Substantive reasoning','cot'),('Valid final option','valid_final'),('Normal EOS','normal_eos'),('At512-token cap','capped'),('Unscorable','unscorable')]:
        lines.append(f'| {name} | {cotbase["counts"][key]}/64 | {base["counts"][key]}/64 |')
    lines += [f'Thinking observed generated length mean/median: {base["length_summary"]["mean"]:.2f}/{base["length_summary"]["median"]:g}; '
              f'native reasoning tokens: {base["reasoning_length_summary"]["mean"]:.2f}/{base["reasoning_length_summary"]["median"]:g}. '
              'All G1–G5 pass. Eight exact FULL no-op checks and eight actual-model V1–V6 checks pass, including unchanged prefill, cached continuation parity, exact zero image attention and64/128/256 boundaries.',
              '## Absolute access results',
              'Damage is FULL accuracy minus condition accuracy. Independent unit=image; each image has equal weight and its two queries remain paired. '
              'Intervals use4,000 paired image-cluster bootstrap draws, seed920260927. Preservation is the frozen point criterion damage≤5pp; interval uncertainty is reported separately.',
              '| Condition | CoT accuracy | CoT damage,95% CI (pp) | Thinking accuracy | Thinking damage,95% CI (pp) |',
              '|---|---:|---:|---:|---:|']
    for p in ['full','t0','t64','t128']+(['t256'] if 't256' in c['thinking']['surface'] else []):
        a=c['cot']['surface'].get(p);b=c['thinking']['surface'][p]
        av=f'{pp(a["accuracy"])}%' if a else 'Not run';ad=f'{pp(a["damage"])} {interval(a)}' if a else 'Not run'
        lines.append(f'| {p} | {av} | {ad} | {pp(b["accuracy"])}% | {pp(b["damage"])} {interval(b)} |')
    lines += [f'Selected Thinking cutoff: **{selected}**. At128, {100*c["thinking"]["surface"]["t128"]["preservation_probability"]:.3f}% of bootstrap draws meet5pp. '
              'No token256 execution was triggered when128 preserved. No normalized50%/75% assay or precision reserve was triggered; frozen gate receipts record the reasons.',
              f'Literal final-channel and raw strict final-channel accuracy agree at FULL ({pp(base["raw_accuracy"])}%). '
              'Full raw-sensitivity surfaces are retained in the machine-readable comparison. Whole-trajectory extraction is separately labeled and never substitutes scratchpad proposals for final answers.',
              '## Relative exposure',
              'The common descriptive horizon is observed FULL generated length, including final/EOS. Capped lengths are right-censored; cutoff/N is an upper bound on the complete-horizon fraction for those traces. '
              'Ratios above1 are reported as budget/horizon ratios, with clipped fractions also preserved. Actual exposure uses N−1>cutoff.',
              '| Arm | Median observed tokens | Median64/N | Median128/N | Reaches64 mask | Reaches128 mask |',
              '|---|---:|---:|---:|---:|---:|']
    for arm in ('cot','thinking'):
        a=rel['arms'][arm];k=a['cutoffs'];lines.append(f'| {arm} | {a["median_observed_tokens"]:g} | {k["64"]["median_item_fraction"]:.3f} | {k["128"]["median_item_fraction"]:.3f} | {pp(k["64"]["fraction_observed_reaching_mask"])}% | {pp(k["128"]["fraction_observed_reaching_mask"])}% |')
    lines += ['Observed lengths differ, but the same absolute128 cutoff preserves both arms. These descriptions do not establish equality of relative-phase causal necessity.',
              '## Bounded redistribution control',
              'The null-sink intervention zeros image attention contributions without renormalizing non-image probabilities. It uses only primary32 FULL/ZERO/selected128; exact FULL and normal-ended non-exposed rows are reused.',
              '| Arm/condition | Accuracy | Damage (pp) | 95% CI (pp) |','|---|---:|---:|---:|']
    if control['status']=='complete':
        for arm,s in [('CoT',control['cot_reference']['surface']),('Thinking',control['surface'])]:
            for p in ('full','t0',f't{selected}'):
                if p in s:
                    r=s[p];lines.append(f'| {arm}/{p} | {pp(r["accuracy"])}% | {pp(r["damage"])} | {interval(r)} |')
        r=control['surface'][f't{selected}']
        lines += [f'Qualitative control support: **{inf["control_qualitative_support"]}**. Thinking selected-cutoff preservation fraction across bootstrap draws: {100*r["preservation_probability"]:.3f}%. '
                  'The frozen CoT control128 interval crosses5pp, so its point preservation is not high-precision evidence. Interpret the Thinking control with its displayed interval as well.']
        diagnostic=load(ROOT/'audit/control_completion_diagnostic.json')
        dd=diagnostic['thinking_null_sink']['t128'];cc=diagnostic['paired_control_contrasts']['t128']
        lines += [f'**Thinking128 preservation fails this control.** The paired null-sink Thinking-minus-CoT damage contrast is {pp(cc["difference"])}pp,95% CI {interval(cc)}pp (secondary robustness comparison). '
                  f'Of{dd["correct_to_wrong"]} FULL-correct queries lost at null-sink128, '
                  f'{dd["lost_with_no_final"]} have no final answer and{dd["lost_with_valid_wrong_final"]} have valid wrong answers; '
                  f'{dd["wrong_to_correct"]} queries improve. These observed counts do not identify the cause of changed completion. '
                  'The512 cap, scoring rule and selected condition were retained. No cap repair,256 search or reserve was launched after the failed control. '
                  '[Diagnostic receipt](audit/control_completion_diagnostic.json).']
        ds=diagnostic['thinking_standard']
        lines += [f'Completion also matters in the primary panel: all{ds["t64"]["correct_to_wrong"]} FULL-correct losses at standard64 '
                  f'and the{ds["t128"]["correct_to_wrong"]} loss at standard128 lack final answers. '
                  'The measured necessity endpoint is performance within the frozen512-token budget, including completion. '
                  'These losses do not establish that an emitted local visual value became wrong. The reason the interventions delay or prevent completion remains unknown.']
    lines += ['## Native use and claim limits',
              '[Stage4A](../../stage4a/summaries/stage4a_summary.md) established demand-aligned A→B→A source dependence and later A re-engagement in a frozen MathVerse local-read assay:36/48 bases met its dynamic definition. '
              'Its trigger-retargeting O3 claim was not established. That prior local source-use evidence and this synthetic access-removal assay answer different questions; the present result does not invalidate native dynamic retrieval.',
              'This is a bounded32-image mechanistic comparison, not a benchmark-population estimate or equivalence test. Checkpoint/training specialization remains confounded. '
              'No effect is causally attributed to thinking, DeepStack, or a particular objective. Persistent visual representations are not ruled out, and FULL access is not proven strictly necessary.',
              '## Verification and resources',
              f'11 focused tests pass. Final independent audit passes{len(audit["checks"])} groups, including unchanged input/reference hashes, all receipts and exact aliases, native answer-channel boundaries, and independently reconstructed damage/paired-contrast bootstraps.',
              f'{acct["scientific_generations"]} new scientific generations ({acct["counts"]}); {acct["allocated_gpu_hours"]:.3f} allocated GPU-hours, '
              f'{acct["generation_gpu_hours"]:.3f} measured generation GPU-hours. Peak reserved VRAM{acct["peak_reserved_bytes"]/2**30:.2f}GiB. '
              f'At most{acct["observed_peak_gpus"]} GPUs concurrently; all GPU jobs completed and released. Existing local checkpoints/data and project .venv reused; no download, package install, tmux allocation or keepalive.',
              'Figures: [FULL validity](figures/figure1_full_validity.png), [absolute access](figures/figure2_absolute_access.png), '
              '[token128 contrast](figures/figure3_token128_contrast.png), [relative exposure](figures/figure4_relative_exposure.png), '
              '[native use vs necessity](figures/figure5_native_use_vs_necessity.png). Each also has a PDF.',
              '## Exactly one recommendation',inf['recommendation'],
              '**STOP.** The recommendation has not been executed. No new experiment or later stage was launched.']
    path=ROOT/'stage9a5_summary.md'
    rendered=''
    for i,line in enumerate(lines):
        separator='\n' if i and line.startswith('|') and lines[i-1].startswith('|') else '\n\n'
        rendered+=(separator if i else '')+line
    with path.open('x') as f:f.write(rendered+'\n')
    required=['stage9a5_qwen3_4b_thinking_spec.md','stage9a5_thinking_mask_validation.json','stage9a5_thinking_full_baseline.json',
              'stage9a5_thinking_primary64.parquet','stage9a5_thinking_token256.parquet','stage9a5_absolute_access_comparison.json',
              'stage9a5_relative_time_analysis.json','stage9a5_relative_time_intervention.json','stage9a5_reserve_extension.json',
              'stage9a5_null_sink_control.json','stage9a5_cot_vs_thinking_inference.json','stage9a5_resource_accounting.json','stage9a5_summary.md']
    entries=[]
    for name in required:
        p=ROOT/name
        if p.exists():entries.append(dict(path=str(p),sha256=sha(p),status='present'))
        else:
            assert name=='stage9a5_thinking_token256.parquet' and 't256' not in c['thinking']['surface']
            entries.append(dict(path=str(p),status='not_run',reason='Token128 preserved; token256 gate closed.'))
    save(ROOT/'stage9a5_artifact_index.json',dict(at=now(),artifacts=entries,
        figures_sha256={str(p):sha(p) for p in sorted((ROOT/'figures').glob('*'))},
        analysis_source_sha256={str(p):sha(p) for p in sorted(__import__('pathlib').Path('scripts/stage9a5').glob('*.py'))}))
    print(path,flush=True)


if __name__=='__main__':main()
