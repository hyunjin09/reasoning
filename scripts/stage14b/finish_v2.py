"""Stage14B closure with immutable adjudications and observed resource accounting."""
from scripts.stage14b.common import *
from scripts.stage14b.scoring_v6 import install
install()
from scripts.stage14b.analyze import scored
from scripts.stage14b.accounting_v2 import accounting


def number(x):return 'unresolved' if x is None else f'{x:.2f}'
def interval(x):return 'unresolved' if not x else f'{x[0]:.2f} to {x[1]:.2f}'


def validate_seals():
    for key in ('primary','secondary','confirmation'):
        assert (ROOT/'audit'/f'{key}_analysis_seal.json').exists(),key+' analysis incomplete'
    for mode in ('main','confirmatory'):
        for model in 'IT':
            assert (ROOT/'audit'/f'{mode}_{model}_scoring_seal.json').exists()
            supplemental=load(ROOT/'audit'/f'{mode}_{model}_supplemental_qc_seal_v1.json')
            assert supplemental['all_resolved']
    for name in ('source_manifest_hashes','prospective_seal','scoring_adjudication_v6_seal','primary_analysis_seal','figure_manifest'):
        for path,digest in load(ROOT/'audit'/f'{name}.json')['files'].items():assert sha(path)==digest,path
    secondary=load(ROOT/'audit/secondary_analysis_seal.json')
    assert sha(secondary['file'])==secondary['sha256']
    assert sha(ROOT/'analysis/confirmatory_results.json')==load(ROOT/'audit/confirmation_analysis_seal.json')['sha256']
    assert len(load(ROOT/'audit/figure_manifest.json')['files'])==10


def main():
    validate_seals()
    main_rows=scored('main');fresh=scored('confirmatory')
    assert len(main_rows)==17536 and len(fresh)==9600
    resources=accounting()
    assert not resources['active_gpu_jobs'],'Release all GPU allocations before closure'
    assert not resources['unknown_gpu_duration_jobs'],'Reconcile missing GPU duration evidence before closure'
    p=load(ROOT/'analysis/primary_results.json');s=load(ROOT/'analysis/secondary_results.json');c=load(ROOT/'analysis/confirmatory_results.json')
    a,b,d=p['P1_G_img'],p['P2_R_I'],p['P3_G_post']
    supported=a['robust_positive'] and b['substantial_by_frozen_rule'] and d['robust_positive']
    recommendation=('Review and authorize Stage14C task-selectivity testing, taking the reported seed robustness and source limitations into account; Stage14B does not identify a mechanism.' if supported else
                    'Review the sealed large-scale effects and missingness, and revise the supported claims before authorizing another stage.')
    lines=['# Stage14B large-scale math phenomenon','',
        'Stage14B is complete: 17,536 main calls and 9,600 fresh confirmation calls, plus 24 technical preflight calls. All scoring, prescribed reviews, primary/secondary/confirmation analyses and five figures are sealed. No follow-on stage was launched.','',
        'All three frozen main-study phenomenon criteria pass.' if supported else 'At least one frozen main-study phenomenon criterion is not robustly established. Negative or uncertain evidence is retained.','',
        '## Primary effects','',
        '| Endpoint | Estimate | 95% interval | Paired/scored coverage |',
        '|---|---:|---:|---|',
        f"| Native Thinking − Instruct | {number(a['paired_difference_pp'])} pp | {interval(a['cluster']['ci95_pp'])} pp | {a['paired_n']}/3040 complete pairs |",
        f"| Instruct E* rescue | {number(b['bootstrap']['estimate_pp'])}% | {interval(b['bootstrap']['ci95_pp'])}% | {b['rescued']}/{b['resolved_followups']} scored native-wrong followups; {b['unresolved_followups']} unresolved |",
        f"| Equal-evidence Thinking − Instruct | {number(d['paired_difference_pp'])} pp | {interval(d['cluster']['ci95_pp'])} pp | {d['paired_n']}/1000 complete pairs |",'',
        f"Worst/best missingness bounds: native gap {interval(a['missingness_bounds_pp'])} pp; post-evidence gap {interval(d['missingness_bounds_pp'])} pp. Rescue bounds over all {b['native_wrong']} native-wrong families: {interval([100*x for x in b['all_native_wrong_bounds']])}%. Missing/unscorable is never relabelled wrong.",'',
        'Intervals use 10,000 bootstrap draws with the frozen seed; known conservative family clusters are preserved. Intervals are unadjusted, without a multiplicity-adjusted significance claim. The 3,040 native problems are not 3,040 verified independent tasks.','',
        '## Accuracy and completion','',
        '| Population/arm | Correct | Wrong | Unscorable | Technical missing | Scored-answer accuracy | Correct/N lower coverage bound |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for key in ('I_image','T_image','I_evidence','T_evidence','I_native','T_native'):
        counts=p['counts_by_arm'][key];correct=counts.get('CORRECT',0);wrong=counts.get('WRONG',0);n=sum(counts.values())
        acc=100*correct/(correct+wrong) if correct+wrong else None
        lines.append(f"| {key} | {correct} | {wrong} | {counts.get('UNSCORABLE',0)} | {counts.get('TECHNICAL_MISSING',0)} | {number(acc)}% | {100*correct/n:.2f}% |")
    lines+=['','Image/evidence rows refer to MATH-Vision; native rows refer to all six MathVerse versions. Marginal scored-answer accuracies can use different denominators, so subtracting them is not the complete-pair effect. Full paired transition tables, including unresolved states, are in `analysis/transition_tables.json` and `analysis/primary_results.json`.','',
        '## MathVerse modality profile','',
        '| Version | Instruct scored accuracy | Thinking scored accuracy | Paired gap | Family 95% interval |',
        '|---|---:|---:|---:|---:|']
    for version,r in p['P4_mathverse']['versions'].items():
        lines.append(f"| {version} | {number(100*r['I']['resolved_accuracy'])}% | {number(100*r['T']['resolved_accuracy'])}% | {number(r['paired_difference_pp'])} pp | {interval(r['cluster']['ci95_pp'])} pp |")
    profile=p['P4_mathverse'];clean=s['mathverse_clean_profile']
    lines+=['',f"The preregistered contrast, mean gap(VD, VO) − mean gap(TD, TL), is {number(profile['profile_contrast']['estimate_pp'])} pp, 95% interval {interval(profile['profile_contrast']['ci95_pp'])}; {profile['contrast_complete_families']}/788 fully scored families. The frozen source-clean layer gives {number(clean['profile_contrast']['estimate_pp'])} pp, interval {interval(clean['profile_contrast']['ci95_pp'])}, using {clean['contrast_complete_families']} complete families. The clean layer and repeat-cluster/source-defect sensitivities do not redefine the census.",'',
        '## Frozen multi-seed robustness','',
        'The source-selected 300 MATH-Vision and 300 MathVerse subsets use main replicate0 and fresh replicates1/2. This is stochastic-decoding robustness, not untouched independent confirmation.','',
        '| Replicate | Native I/T scored accuracy | Native gap | Instruct rescue | Evidence I/T scored accuracy | Post-evidence gap | MathVerse profile contrast |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for seed,row in c['per_seed'].items():
        native,evidence=row['G_img'],row['G_post']
        lines.append(f"| {seed} | {number(100*native['I']['resolved_accuracy'])}% / {number(100*native['T']['resolved_accuracy'])}% | {number(native['paired_difference_pp'])} pp | {number(row['R_I']['bootstrap']['estimate_pp'])}% | {number(100*evidence['I']['resolved_accuracy'])}% / {number(100*evidence['T']['resolved_accuracy'])}% | {number(evidence['paired_difference_pp'])} pp | {number(row['mathverse']['profile_contrast']['estimate_pp'])} pp |")
    lines+=['','| Endpoint | Seed mean | Sample SD | Fraction retaining main sign |','|---|---:|---:|---:|']
    for name,row in c['stability'].items():lines.append(f"| {name} | {number(row['mean_pp'])} | {number(row['sd_pp'])} | {number(row['sign_stability_fraction'])} |")
    st=c['transition_stability']
    lines+=['',f"Item/condition/model outcomes are identical across all three seeds in {st['identical_binary_all_seeds']}/{st['all_three_resolved']} fully scored slots; {st['unknown_any_seed']} slots contain an unresolved seed. Paired I/T outcome patterns are identical across seeds in {st['paired_model_patterns_stable_all_seeds']}/{st['paired_model_patterns_all_seeds_resolved']} fully scored item/condition pairs. Full per-seed counts, modality estimates and intervals are preserved in `analysis/confirmatory_results.json`.",'',
        '## Validity and interpretation limits','',
        '- This compares pinned Qwen3-VL-4B variants under their validated native recipes, with preregistered 32,768/81,920 output-token caps. It is neither a causal Thinking-toggle nor an equal-compute comparison.',
        '- E* rescue concerns incomplete demonstrated recovery of task-critical visual evidence. Evidence supply can change accessibility, representation and binding. A post-evidence advantage does not identify its downstream mechanism.',
        '- All unresolved parser/equivalence records, the fixed 10% hash audit, caps and native nonletter-option golds were reviewed by the same agent. This is not independent human reliability evidence. Versioned presentation repairs and second adjudications preserve original outputs, golds and records. Some initial extraction strings remain parser artifacts; semantic grading uses documented terminal-response review.',
        '- Native source/gold defects remain. The frozen absolute numeric tolerance of 1e-6 can reject rounded responses when native gold is exact, even where source wording permits rounding. No outcome-based gold, tolerance, cohort or recipe adjustment was made.',
        '- Conservative aliases and prior source-catalog exposure are disclosed. Unknown dependence may remain. Source strata are secondary and do not replace the primary cohort.','',
        '## Resources and artifacts','',
        f"Observed allocation intervals or worker-exit proxies total {resources['gpu_hours_observed_or_proxy']:.3f} GPU-hours, including failed startup jobs. Retained exact Slurm intervals are used where available; otherwise shutdown/release tails are not observed. The Slurm accounting service is unavailable. CPU preprocessing/watchers contribute zero GPU-hours. No GPU allocation remains active. Parent-process CUDA counters do not measure vLLM child peak VRAM; those counters are not presented as peak device usage.",'',
        'Raw responses and input/seed receipts: `raw/`. Reviewed scores: `scoring/`. Main, secondary and seed analyses: `analysis/`. Five PNG/PDF figures: `figures/`. Source/condition/code seals, job records and accounting: `audit/`. Main seed0 is reused exactly, with no unnecessary regeneration.','',
        f'Exactly one recommendation: {recommendation}','','Stage14B complete. STOP.']
    body='\n'.join(lines)+'\n'
    write_text(ROOT/'summaries/stage14b_final_summary.md',body)
    write_text(ROOT/'summaries/stage14b_primary_summary.md','\n'.join(lines[:lines.index('## Frozen multi-seed robustness')])+'\n\nSee the final summary for seed robustness, scoring limitations and resources.\n')
    write_text(ROOT/'summaries/next_stage_recommendation.md',recommendation+'\n\nNOT_LAUNCHED\n')
    save(ROOT/'audit/resource_accounting.json',resources)
    save(ROOT/'audit/completion_validation.json',dict(at=now(),complete=True,main_calls=17536,confirmation_new_calls=9600,
        preflight_calls=24,source_hashes_unchanged=True,all_gpu_jobs_closed=True,figures=5,follow_on_launched=False))
    save(ROOT/'audit/condition_identity_audit.json',dict(at=now(),prospective_seal_sha256=sha(ROOT/'audit/prospective_seal.json'),
        main_raw_seal_sha256=sha(ROOT/'audit/main_raw_seal.json'),confirmation_raw_seal_sha256=sha(ROOT/'audit/confirmatory_raw_seal.json')))
    catalog=[x for parent in ['spec','manifests','scoring','analysis','figures','summaries'] for x in (ROOT/parent).glob('*') if x.is_file()]
    save(ROOT/'audit/artifact_catalog.json',dict(at=now(),files={str(x):sha(x) for x in catalog},status='COMPLETE_STOP'))
    print(body)

if __name__=='__main__':main()
