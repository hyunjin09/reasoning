"""Freeze all reviewed C1 memberships before any primary C1 stress acquisition."""
import hashlib
import json
from collections import Counter
from scripts.stage6a.inventory import OUT
from scripts.stage6a.prepare_candidates import write


def load(path):return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    target=OUT/'cohort/controlled_stress_manifest.jsonl'
    assert not target.exists(), 'Do not alter a frozen acquisition manifest'
    candidates=load(OUT/'cohort/c1_primary_v2_base_manifest.jsonl')
    reviews={r['base_id']:r for r in load(OUT/'c1_diagram_stress/intact_local_claim_review.jsonl')}
    expected={r['base_id'] for r in candidates}
    assert expected<=set(reviews),f'Native review still missing for {sorted(expected-set(reviews))}'
    assert all(reviews[key]['membership_status'] in ['eligible','ineligible'] for key in expected), 'Unfinished membership review'
    eligible={key for key in expected if reviews[key]['membership_status']=='eligible'}
    boundaries={r['base_id']:r for r in load(OUT/'c1_diagram_stress/native_readout_boundaries.jsonl')}
    assert eligible<=set(boundaries), 'Validate exact native/alternate readout boundaries before stress freeze'
    selected=[{**r,'primary_membership_status':'eligible_after_native_completion_and_readout_review',
        'native_membership_review_artifact':'c1_diagram_stress/intact_local_claim_review.jsonl'}
        for r in candidates if r['base_id'] in eligible]
    counts=dict(Counter(r['dataset'] for r in selected))
    rules=json.loads((OUT/'config/cohort_rules.json').read_text())['C1']
    assert len(selected)>=rules['minimum'] and all(count>=rules['minimum_per_available_stratum'] for count in counts.values()), 'C1 minimum gate failed; report cohort repair rather than silently changing rules'
    assert len(counts)==3
    manifest=load(OUT/'cohort/c1_primary_v2_manifest.jsonl')
    for key in eligible:
        conditions={r['condition'] for r in manifest if r['base_id']==key}
        assert {'intact','counterfactual','mask'}<=conditions
    original_answers={r['base_id']:r['answer'] for r in manifest if r['condition']=='intact'}
    selected_manifest=[{**r,'source_answer':original_answers[r['base_id']],
        'primary_membership_status':'eligible_after_native_completion_and_readout_review',
        'native_membership_review_artifact':'c1_diagram_stress/intact_local_claim_review.jsonl'}
        for r in manifest if r['base_id'] in eligible]
    stress=[r for r in selected_manifest if r['condition']!='intact']
    separate_c3=(OUT/'cohort/c3_stress_manifest.jsonl').exists()
    if not separate_c3:
        stress+=[r for r in load(OUT/'cohort/c3_primary_v2_manifest.jsonl') if r['condition']!='intact']
    assert len({r['event_id'] for r in stress})==len(stress)
    assert not list((OUT/'native/controlled_stress').glob('shard_*/examples/*/generation.json'))
    write(target,stress)
    write(OUT/'c1_diagram_stress/base_manifest.jsonl',selected)
    for condition,filename in [('intact','intact'),('counterfactual','counterfactual'),('mask','mask'),('unrelated','unrelated'),('no_image','no_image')]:
        write(OUT/f'c1_diagram_stress/{filename}_manifest.jsonl',[r for r in selected_manifest if r['condition']==condition])
    write(OUT/'c1_diagram_stress/degradation_manifest.jsonl',[r for r in selected_manifest if r['condition'] in ['mild','strong']])
    write(OUT/'c1_diagram_stress/sham_manifest.jsonl',[r for r in selected_manifest if 'sham' in r['condition']])
    write(OUT/'c1_diagram_stress/aligned_distractor_manifest.jsonl',[])
    write(OUT/'c1_diagram_stress/readouts.jsonl',[{**reviews[r['base_id']],**boundaries[r['base_id']]} for r in selected])
    report=dict(status='C1_MEMBERSHIP_FROZEN_BEFORE_PRIMARY_STRESS',candidate_bases=len(candidates),
        retained_bases=len(eligible),per_dataset=counts,excluded=[reviews[key] for key in sorted(expected-eligible)],
        local_correctness_not_a_selection_variable=True,final_correctness_not_a_selection_variable=True,
        all_retained_have_counterfactual_and_full_mask=True,
        selected_intact_review_sha256=hashlib.sha256((OUT/'c1_diagram_stress/intact_local_claim_review.jsonl').read_bytes()).hexdigest(),
        stress_manifest_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),stress_events=len(stress),
        stress_cohort_counts=dict(Counter(r['cohort'] for r in stress)),
        c3_stress_acquisition='Separate frozen c3_stress run' if separate_c3 else 'Included in controlled_stress',
        optional_aligned_distractor='Not constructed: exact semantic counterfactual, degradation/mask/sham, unrelated and no-image branches provide the required availability ladder; no additional clean distractor was prospectively validated.',
        source_template_folds='Inherited unchanged from prospective source split; no condition effect or hidden-state feature read.')
    (OUT/'cohort/c1_membership_freeze.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
