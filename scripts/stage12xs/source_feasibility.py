"""Record the source-pool boundary without launching or enlarging the study."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from scripts.stage12xs.common import ROOT, load, now, save, sha
from scripts.stage12xs.selection import components, order


def proposed_metadata():
    """Reconstruct the sealed order; expose only metadata for an unapproved proposal."""
    exclusion = load(ROOT / 'stage12xs_historical_exclusion_manifest.json')
    fm = load('outputs/stage8c_v2/v1/stage8c_v2_family_manifest.json')
    prior = load('outputs/stage11b/v1/audit/freshness_repair_v2.json')['edges']
    catalog = [json.loads(s) for s in Path('outputs/stage8b/v2/cohort/census_manifest_v1.jsonl').read_text().splitlines()]
    by = {r['item_id']: r for r in catalog}
    groups = list(fm['groups']) + [[r['a'], r['b']] for r in exclusion['source_only_alias_edges'] + prior]
    comp = components(by, groups)
    families = defaultdict(list)
    for item, component in comp.items():
        families[component].append(item)
    excluded = {i for f in exclusion['families'] for i in f['item_ids']}
    rows = []
    for members in families.values():
        if excluded.intersection(members):
            assert set(members) <= excluded
            continue
        previous = sorted({fm['item_family'][i] for i in members})
        family = previous[0] if len(previous) == 1 else 'stage12xs_family_' + hashlib.sha256('|'.join(previous).encode()).hexdigest()[:20]
        item = min(members, key=lambda i: (order(i, 'representative'), int(i)))
        source = by[item]
        rows.append(dict(item_id=item, family_id=family, member_item_ids=sorted(members, key=int),
                         answer_type='multiple_choice' if source['options'] else 'open_ended',
                         level=source['level'], subject=source['subject'],
                         source_hash=order(family, 'source'), b4_hash=order(family, 'b4'),
                         transfer_hash=order(family, 'transfer')))
    rows.sort(key=lambda r: (r['source_hash'], r['family_id']))
    original = load(ROOT / 'stage12xs_source_candidate_manifest.json')
    assert len(rows) == original['n_eligible_source_families'] == 659
    assert [r['item_id'] for r in rows[:128]] == original['initial_ids'] + original['reserve_ids']
    return rows[128:192]


def main():
    stamp = now()
    manifest = load(ROOT / 'stage12xs_source_candidate_manifest.json')
    ids = manifest['initial_ids'] + manifest['reserve_ids']
    annotations = {i: load(ROOT / 'annotations/primary' / f'{i}.json') for i in ids}
    assert len(ids) == len(set(ids)) == len(annotations) == 128
    assert len({r['family_id'] for r in manifest['rows']}) == 128
    for r in manifest['rows']:
        a = annotations[r['item_id']]
        assert a['family_id'] == r['family_id']
        assert a['image_sha256'] == r['image_sha256'] == sha(r['image'])
        assert a['model_outcomes_used'] is False
        assert (1 <= len(a['facts']) <= 4) if a['eligible'] else not a['facts']
    good = [i for i in ids if annotations[i]['eligible']]
    bad = [i for i in ids if not annotations[i]['eligible']]
    assert len(good) == 83 and len(bad) == 45
    special = {'1755': 'uncertified occluded geometry', '2303': 'question/image conflict',
               '720': 'underspecified source question', '620': 'answer-safe evidence not certified'}
    text_complete = [i for i in bad if i not in special]
    assert len(text_complete) == 41
    # A deliberately narrower second-check certificate avoids depending on any
    # of the more implicit geometric conventions or the four special exclusions.
    less_explicit = {'2366', '2978', '2722', '2346', '2308', '2836', '2382', '2873'}
    core = [i for i in text_complete if i not in less_explicit]
    assert len(core) == 33
    save(ROOT / 'audit/source_eligibility_recheck_v1.json', dict(
        at=stamp, reviewer='main agent, separate source-question reread; unblinded to own first review',
        independent_review=False, replaces_required_final_cohort_25_percent_qc=False,
        item_ids=core, result='All 33 questions already specify the necessary mathematical input; no nonempty minimal image-only evidence set.',
        maximum_eligible_even_if_every_other_exclusion_reversed=128-len(core),
        scientific_outcomes_used=False,
        records=[dict(item_id=i, question_sha256=hashlib.sha256(next(r['question'] for r in manifest['rows'] if r['item_id']==i).encode()).hexdigest(),
                      source_reason=annotations[i]['source_only_rationale']) for i in core]))
    review = dict(at=stamp, status='PRIMARY_SOURCE_REVIEW_COMPLETE; FINAL_COHORT_QC_NOT_REACHED',
                  reviewed=128, provisionally_eligible=83, ineligible=45,
                  initial=dict(reviewed=96, eligible=64, ineligible=32),
                  reserve=dict(reviewed=32, eligible=19, ineligible=13),
                  required_final_families=96, shortfall_before_final_qc=13,
                  eligible_ids=good, ineligible_ids=bad,
                  exclusion_categories={'text_complete_no_necessary_image_fact':text_complete, **{v:[k] for k,v in special.items()}},
                  annotation_files={str(ROOT/'annotations/primary'/f'{i}.json'):sha(ROOT/'annotations/primary'/f'{i}.json') for i in ids},
                  final_25_percent_qc='Pending: no complete 96-family eligible cohort exists.',
                  evidence_rendering_frozen=False, generation_started=False, scientific_outcomes_used=False)
    save(ROOT/'stage12xs_e_star_review.json', review)
    proposal = dict(at=stamp, status='PROPOSED_ONLY_NOT_AUTHORIZED',
                    reason='Source-only pre-generation eligibility shortfall, not model-outcome-dependent adaptation.',
                    source_selection_rule=manifest['selection_rule'],
                    proposed_additional_candidate_limit=64, proposed_source_ranks=[129,192],
                    stop_source_replacements_when_final_eligible_count=96,
                    unchanged=['historical exclusions','family identity','E* eligibility','96 final families','recipes','caps','seeds','phase gates','14 GPU-hour hard limit'],
                    forbid=['generation before full E* freeze/QC','inspection of model outcomes for source selection','scientific cohort expansion after yield'],
                    rows=proposed_metadata())
    save(ROOT/'audit/source_pool_amendment_proposed_candidates_v1.json', proposal)
    save(ROOT/'stage12xs_decision.json', dict(at=stamp, execution_status='BLOCKED_SOURCE_ELIGIBILITY',
        stage_complete=False, scientific_decision=None, not_a_candidate_yield_or_portability_result=True,
        observation='83 provisionally eligible families from all 128 frozen candidates; 13 short before final QC.',
        strict_second_check_upper_bound=95,
        plan_boundary='Section 6: If an item is not E*-eligible, replace only from the pre-frozen reserve in deterministic order.',
        selected_action='Preserve the source audit and request a bounded prospective source-reserve amendment before generation.',
        recommendation='Approve screening at most the next 64 already-ordered fresh source families, stopping replacement once 96 eligible families pass QC.',
        recommendation_executed=False, phase_A_calls=0, phase_B_calls=0, phase_C_calls=0))
    save(ROOT/'stage12xs_resource_accounting.json', dict(at=stamp, allocated_gpu_hours=0,
        gpu_jobs=[], model_calls=0, model_downloads=0, dataset_downloads=0, package_changes=0,
        cpu_work='Historical provenance/hash audit; 128 source image/question reviews; source-only annotations and feasibility verification.',
        stage_target_gpu_hours=10, stage_hard_gpu_hours=14,
        remaining_if_source_amendment_approved=dict(phase_A_calls=288, phase_B_max_calls=48, phase_C_max_calls=250,
            gpu_hours='Unchanged target <10 / hard 14; estimate will be refined before Slurm launch, after cohort freeze.'),
        scheduler_observation='squeue -u hyunjin returned no jobs at source-audit close. No Stage12X-S job was submitted.'))
    print(json.dumps({k:review[k] for k in ['reviewed','provisionally_eligible','ineligible','shortfall_before_final_qc']}))


if __name__ == '__main__':
    main()
