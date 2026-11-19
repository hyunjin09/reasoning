"""Publish Stage14B only after all frozen runs, reviews and analyses are sealed."""
from scripts.stage14b.common import *
from scripts.stage14b.status import status
from scripts.stage14b.analyze import scored


def fmt(x):return 'unresolved' if x is None else f'{x:.2f}'

def main():
    for key in ('primary','secondary','confirmation'):
        assert (ROOT/'audit'/f'{key}_analysis_seal.json').exists()
    assert (ROOT/'audit/figure_manifest.json').exists()
    assert len(scored('main'))==17536 and len(scored('confirmatory'))==9600
    current=status();assert not current['active'],'Release all GPU allocations before closure'
    for p,h in load(ROOT/'audit/source_manifest_hashes.json')['files'].items():assert sha(p)==h,p
    for p,h in load(ROOT/'audit/prospective_seal.json')['files'].items():assert sha(p)==h,p
    p=load(ROOT/'analysis/primary_results.json');c=load(ROOT/'analysis/confirmatory_results.json')
    a,b,d=p['P1_G_img'],p['P2_R_I'],p['P3_G_post']
    supported=a['robust_positive'] and b['substantial_by_frozen_rule'] and d['robust_positive']
    recommendation=('Review and authorize Stage14C task-selectivity testing; do not infer a mechanism from Stage14B.' if supported else
        'Review the sealed large-scale effects and missingness, and revise the supported claims before authorizing another stage.')
    scope='Large-scale behavioral evidence supports all three preregistered phenomena.' if supported else 'At least one preregistered phenomenon is not robustly established; preserve the negative or uncertain evidence.'
    body=f'''# Stage14B large-scale math phenomenon\n\n{scope}\n\n- Native MATH-Vision: Thinking−Instruct = {fmt(a['paired_difference_pp'])} pp; known-family95%CI {a['cluster']['ci95_pp']}; complete pairs {a['paired_n']}/3040.\n- Instruct E* rescue: {b['rescued']}/{b['resolved_followups']} resolved native-wrong followups; {b['unresolved_followups']} unresolved of {b['native_wrong']} native wrong.95%CI in percent {b['bootstrap']['ci95_pp']}.\n- Equal evidence: Thinking−Instruct = {fmt(d['paired_difference_pp'])} pp;95%CI {d['cluster']['ci95_pp']}; complete pairs {d['paired_n']}/1000.\n- MathVerse modality-profile contrast = {fmt(p['P4_mathverse']['profile_contrast']['estimate_pp'])} pp;95%CI {p['P4_mathverse']['profile_contrast']['ci95_pp']}. Six-version counts and source-clean/defect sensitivities are retained in the analysis files.\n\nThe frozen300+300 robustness subsets use three seeds, including the main seed0. Seed effects, sign stability and transition stability are in analysis/confirmatory_results.json. Native problem counts are not verified independent task counts. All families had prior catalog exposure. Unknown dependence and source defects remain limitations.\n\nCompared variants use their preregistered validated native recipes and different32768/81920 token caps; this is neither a causal Thinking-toggle nor an equal-compute comparison. E* rescue concerns incomplete demonstrated task-critical evidence recovery and can change accessibility/representation/binding. A post-evidence gap does not identify the downstream mechanism. Missing and unscorable calls are separate from wrong; report their bounds alongside complete pairs.\n\nAllocated GPU-hours: {current['allocated_gpu_hours_upper']:.4f}, including technical startup failures. No active GPU jobs.\n\nExactly one recommendation: {recommendation}\n\nStage14B complete. No follow-on launched.\n'''
    write_text(ROOT/'summaries/stage14b_final_summary.md',body)
    # Primary summary is a compact projection of the already sealed primary artifact.
    write_text(ROOT/'summaries/stage14b_primary_summary.md',body.split('The frozen300+300')[0]+'\nFull primary estimates, four-way counts, transitions and bounds: analysis/primary_results.json.\n')
    write_text(ROOT/'summaries/next_stage_recommendation.md',recommendation+'\n\nNOT_LAUNCHED\n')
    save(ROOT/'audit/resource_accounting.json',current)
    save(ROOT/'audit/completion_validation.json',dict(at=now(),complete=True,main_calls=17536,confirmation_new_calls=9600,
        preflight_calls=24,source_hashes_unchanged=True,all_gpu_jobs_closed=True,figures=5,follow_on_launched=False))
    save(ROOT/'audit/condition_identity_audit.json',dict(at=now(),prospective_seal_sha256=sha(ROOT/'audit/prospective_seal.json'),
        main_raw_seal_sha256=sha(ROOT/'audit/main_raw_seal.json'),confirmation_raw_seal_sha256=sha(ROOT/'audit/confirmatory_raw_seal.json')))
    catalog=[x for parent in ['spec','manifests','scoring','analysis','figures','summaries'] for x in (ROOT/parent).glob('*') if x.is_file()]
    save(ROOT/'audit/artifact_catalog.json',dict(at=now(),files={str(x):sha(x) for x in catalog},status='COMPLETE_STOP'))
    print(body)

if __name__=='__main__':main()
