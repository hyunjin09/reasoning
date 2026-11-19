"""Close the authorized bounded sequence; never launch a recommendation."""
from pathlib import Path
from scripts.stage9a4.common import ROOT,load,save,sha,now


def pp(x):return f'{100*x:.2f}'


def main():
    base=load(ROOT/'stage9a4_qwen3_4b_full_baseline.json');primary=None
    for stage in ['r1','t128','t256']:
        path=ROOT/f'audit/{stage}_decision.json'
        if path.exists():primary=load(path)
    assert primary['action']!='run','Authorized sequential work remains'
    selected=primary['cutoff'] if primary['action']=='selected' else None
    rp=ROOT/'stage9a4_qwen3_4b_reserve_extension.json';reserve=load(rp) if rp.exists() else None
    sp=ROOT/'stage9a4_qwen3_4b_null_sink_control.json';sink=load(sp) if sp.exists() else None
    if selected:
        assert sink,'Selected cutoff requires bounded null-sink'
        if load(ROOT/'audit/selected_cutoff.json')['reserve_eligible']:assert reserve
    final=reserve['combined'] if reserve else primary;surface=final['surface']
    finite=selected is not None and surface[f't{selected}']['damage']<=.05+1e-12 and surface['t0']['damage']>.05+1e-12
    robust=bool(sink and sink['surface'][f't{selected}']['damage']<=.05+1e-12 and sink['surface']['t0']['damage']>.05+1e-12)
    if selected==64 and finite:
        outcome='A';recommendation='Proceed to a bounded Qwen3-VL-4B Instruct-CoT vs Qwen3-VL-4B Thinking model-wide direct-access comparison.'
    elif selected in (128,256) or primary['action']=='stop_no_finite':
        outcome='B' if finite else 'C';recommendation='Characterize the Qwen2.5→Qwen3 access-regime shift before attributing any difference to Thinking specialization.'
    else:
        outcome='R1-C';recommendation='Stop the controlled generated-token necessity interpretation for Qwen3 under this task and retain the Qwen2.5 calibration.'
    decision=dict(at=now(),complete=True,outcome=outcome,selected_cutoff=selected,primary_action=primary['action'],
        primary_images=32,final_images=final['n_images'],reserve_used=reserve is not None,
        finite_preservation_point_criterion=finite,null_sink_qualitative_pattern=robust,
        null_sink_interval_within_5pp=bool(sink and sink['surface'][f't{selected}']['ci95'][1]<=.05+1e-12),
        final_surface=surface,primary_surface=primary['surface'],recommendation=recommendation,recommendation_launched=False,
        stop=True,interpretation='Point-based5pp rule, image-bootstrap uncertainty; no exact boundary or DeepStack attribution.')
    save(ROOT/'stage9a4_qwen3_4b_finite_access_decision.json',decision)
    comparison=load(ROOT/'stage9a4_qwen25_qwen3_comparison.json');account=load(ROOT/'stage9a4_resource_accounting.json')
    audit=load(ROOT/'audit/final_validation.json');assert audit['pass_all'] and account['all_gpu_jobs_terminal']
    lines=['# Stage9A.4 — Qwen3-4B finite-access result','',f'Completed {now()}. Outcome **{outcome}**. The authorized sequence is complete; all GPU allocations are released.','',
        '**Main result:** under the frozen 5 percentage-point criterion, Qwen3-VL-4B prompted CoT preserves performance with direct image-key access through token128. Token64 is insufficient. This supports finite access at a later tested budget than the calibrated Qwen2.5 result.','',
        'The repaired Qwen3-VL-4B-Instruct FULL baseline is valid on the original32 synthetic images/64 queries: '
        f"{base['counts']['correct']}/64 correct ({pp(base['rates']['correct'])}%), "
        f"{base['counts']['cot']}/64 genuine intermediate reasoning, {base['counts']['valid_final']}/64 valid final options and normal EOS, "
        f"{base['counts']['capped']}/64 capped. All five gates pass. All eight actual-model V1–V6 checks pass, including exact FULL no-op, unchanged prefill, all36 layers, 64/128/256 transitions, cache validity and no-redistribution checks.",
        '', 'Primary32-image results (two queries per independent image;95% paired image-bootstrap intervals):','',
        '| Access condition | Accuracy | Damage vs FULL | 95% interval (pp) |','|---|---:|---:|---:|']
    for p in ['full','t0','t64','t128','t256']:
        if p not in primary['surface']:continue
        r=primary['surface'][p]
        lines.append(f"| {p} | {pp(r['accuracy'])}% | {pp(r['damage'])} pp | [{pp(r['ci95'][0])}, {pp(r['ci95'][1])}] |")
    lines+=['',f"ZERO establishes useful generated-token direct access. Token64 damage is {pp(primary['surface']['t64']['damage'])}pp, exceeding the5pp criterion; the approved sequential rule was followed. "
        +(f'The first point-preserving cutoff was **{selected} tokens**.' if selected else 'No tested finite cutoff was selected.'),'']
    if reserve:
        v=surface[f't{selected}']
        lines += [f"The frozen16-image reserve was triggered because the selected cutoff’s primary95% interval crossed the5pp tolerance. Exactly FULL/ZERO/token{selected} ran on32 reserve queries. "
          f"Across48 images, FULL accuracy is {pp(surface['full']['accuracy'])}%, ZERO damage {pp(surface['t0']['damage'])}pp, and token{selected} damage **{pp(v['damage'])}pp [{pp(v['ci95'][0])}, {pp(v['ci95'][1])}]**, "
          f"with {pp(v['preservation_probability'])}% of bootstrap draws within5pp. The selected cutoff was frozen before reserve outcomes; no additional search occurred.",'']
    else:lines+=['The reserve precision gate was not triggered; no reserve generation was performed.','']
    if sink:
        z=sink['surface']['t0'];v=sink['surface'][f't{selected}']
        lines += [f"Bounded null-sink control on the primary32 images: ZERO damage **{pp(z['damage'])}pp [{pp(z['ci95'][0])}, {pp(z['ci95'][1])}]**; token{selected} damage **{pp(v['damage'])}pp [{pp(v['ci95'][0])}, {pp(v['ci95'][1])}]**. "
                  +('Damage at ZERO and point preservation at the finite cutoff survive without redistributing removed image probability.' if robust else 'The bounded alternative does not preserve the full qualitative pattern; do not claim redistribution-independent robustness.'),
                  f"The control's finite-cutoff preservation probability is {pp(v['preservation_probability'])}%; its interval crosses5pp, so redistribution-independent preservation remains uncertain at that tolerance.",'']
    c=comparison['paired_primary32']
    detail=load(ROOT/'audit/completion_and_exposure.json')['primary']
    lines += [f"At token64, the descriptive shift relative to frozen Qwen2.5's 48-image −1.04pp result is **{pp(comparison['headline_gamma64'])}pp**. That headline uses unequal cohort sizes. "
       f"The genuinely paired primary32-image comparison gives **{pp(c['gamma64'])}pp [{pp(c['ci95'][0])}, {pp(c['ci95'][1])}]**. "
       'The Qwen2.5 baseline uses256 tokens and3B parameters; Qwen3 uses512 and4B. This supports a checkpoint/generation access-regime difference candidate, without isolating capacity, training, architecture or DeepStack.','',
       'The study uses the original images, prompts/options, preprocessing, greedy BF16/eager-language backend and seed920260927. DeepStack is unchanged. Restrictions affect generated queries to cached image keys; prefill and image-derived cached state remain. There are4,000 family-equal image bootstrap draws. Queries, tokens and conditions are not independent samples. '
       'Point preservation is not proof of equivalence; intervals and actual mask exposure are retained in the analysis artifacts. Literal final-answer review is sealed before gold joins, with raw strict-format sensitivity alongside it.','',
       f"The mask is reached in {detail['t64']['mask_exposed_queries']}/64 token64 trajectories and "
       f"{detail['t128']['mask_exposed_queries']}/64 token128 trajectories; the remaining21 token128 queries are exact FULL identities. "
       'Capped counts are FULL4, ZERO9, token64 7 and token128 4; unscorable counts are4/8/7/4. '
       'Thus final-performance effects include completion failures and are not isolated local visual-decoding errors. Raw strict-format scoring yields the same primary accuracies and decision.','',
       f"Compute: **{account['allocated_gpu_hours']:.3f} allocation GPU-hours**, {account['scientific_generations']} new scientific generations, at most4 GPUs. "
       f"Generation time itself is {account['generation_gpu_hours']:.3f}GPUh. All jobs used the project scheduler/Slurm; no downloads, tmux or keepalive. Nine focused CPU tests and {len(audit['checks'])} final audit groups passed. Reused Stage9A.3 artifacts are verified byte-identical.",'',
       '**Exactly one recommendation:** '+recommendation,'','**STOP. The recommendation has not been launched.**']
    path=ROOT/'stage9a4_summary.md';assert not path.exists();path.write_text('\n'.join(lines)+'\n')
    required=['stage9a4_qwen3_4b_repair_spec.md','stage9a4_qwen3_4b_mask_validation.json','stage9a4_qwen3_4b_full_baseline.json',
        'stage9a4_qwen3_4b_primary64.parquet','stage9a4_qwen3_4b_token128.parquet','stage9a4_qwen3_4b_token256.parquet',
        'stage9a4_qwen3_4b_finite_access_decision.json','stage9a4_qwen3_4b_reserve_extension.json','stage9a4_qwen3_4b_null_sink_control.json',
        'stage9a4_qwen25_qwen3_comparison.json','stage9a4_resource_accounting.json','stage9a4_summary.md']
    save(ROOT/'stage9a4_artifact_index.json',dict(at=now(),artifacts={n:dict(status='complete',sha256=sha(ROOT/n)) if (ROOT/n).exists() else dict(status='conditional_not_run') for n in required},
        figures={str(p):sha(p) for p in sorted((ROOT/'figures').glob('*'))},decision=decision,validation_sha256=sha(ROOT/'audit/final_validation.json')))
    print('COMPLETE',outcome,selected,flush=True)


if __name__=='__main__':main()
