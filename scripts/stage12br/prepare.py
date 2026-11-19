"""Freeze exactly36 copied requests and prospective validity rules before GPU use."""
import json
from pathlib import Path
from scripts.stage12br.common import ROOT, load, save, sha, now
from scripts.stage12br.protocol import select_families, SELECTION_SEED, authorize_manifest


def main():
    assert not (ROOT / 'generations').exists()
    original = Path('outputs/stage12b/v1/stage12b_frozen_manifest.json')
    source = load(original)
    ids, eligible = select_families(source['rows'], source['technical_ids'])
    tasks = [next(t for t in source['tasks'] if t['item_id'] == i and t['arm'] == a) for i in ids for a in 'ENO']
    assert len(tasks) == 36 and len({t['family_id'] for t in tasks}) == 12
    for t in tasks:
        if t['image']:
            assert sha(t['image']) == t['image_sha256']
    oracle = Path('outputs/stage12b/v1/stage12b_oracle_integrity_review.json')
    assert load(oracle)['pass'] and load(oracle)['n_reviewed'] == 61
    for src, dst in [
        ('outputs/stage12a/v1/stage12a_frozen_e_star_manifest.json', 'audit/frozen_stage12a_manifest.json'),
        ('plan/stage12br_pathology_aware_validity_repair_plan.md', 'audit/approved_plan.md')]:
        with (ROOT / dst).open('xb') as f:
            f.write(Path(src).read_bytes())
    rules = dict(at=now(),frozen=True,correctness_used=False,
        formula='INPUT_VALID and SCOREABLE and not TRUNCATED_BEFORE_OUTCOME',
        gate_each_arm=dict(n=12,input_valid_required=12,scoreable_minimum=10,truncated_before_outcome_maximum=1),
        cap_after_outcome='A unique committed answer survives at termination, without unresolved later reopening: scoreable and separately flagged.',
        scoreability='E: interpretable responses for all requested facts, regardless of truth. N/O: unique task answer or clear last revision; contradictions not superseded are unscoreable.',
        decision_priority=['INPUT_INTEGRITY_FAIL','SCOREABILITY_FAIL','VALIDITY_REPAIRED'],
        boundary_clarifications='Any input failure blocks repair because each arm requires12/12. E scoreability failure also blocks repair. Missing worker receipts cannot count as valid.',
        pathologies_excluded_from_gate=['R1','R2','R3','R4'],
        R5='Terminal ambiguity also implies SCOREABLE=false',
        r4_descriptive_min_generated_tokens=4096,
        after_validation='STOP. Section21 requires separate authorization for full61-family scientific profiling.')
    save(ROOT / 'stage12br_validity_rules.json', rules)
    guide = '''# Stage12B-R pathology annotation guide — frozen before generation

Review outputs without task answers, correctness comparisons, or E* truth grading. Input checks use exact request/hash equality and the inherited source-only oracle audit; output reviewers receive requested labels and task text only, not source answers or oracle gold facts.

E is scoreable when every requested fact has an interpretable response, regardless of truth. N/O needs one task outcome, not one answer to a subsidiary fact. Accept a clear final revision superseding earlier answers. A bare native expression or option is acceptable; no new format contract. Record an exact commitment quote and extracted answer string without grading it.

Cap hit before an outcome is TRUNCATED_BEFORE_OUTCOME. A cap after a still-unique committed answer is separately cap_after_outcome, not automatically invalid. If subsequent reopening leaves incompatible terminal possibilities unresolved, the earlier answer does not establish a unique final outcome. At a normal stop, an unscoreable output is not a cap truncation.

R1 SEVERE_REPETITION: repeatedly cycles through substantially the same interpretation/calculation/argument without meaningful progress. Semantic review is primary; n-gram diagnostics only support review. Identify repeated passages and why they do not advance.

R2 REOPEN_AFTER_PROVISIONAL_ANSWER: a candidate task answer is reached, then interpretation or derivation restarts. A simple verification that does not restart the problem is not sufficient. Capture the provisional answer and later reopening.

R3 NONCONVERGENT_REASONING: continued mutually inconsistent or repeatedly revised hypotheses without stable convergence. Ordinary finite self-correction is insufficient. A last forced guess may still be a scoreable commitment while preceding reasoning remains nonconvergent; annotate the exploratory segment separately from the terminal answer.

R4 LONG_ADVANCING_COMPUTATION: at least4096 generated tokens AND substantial distinguishable computational progress (new cases, derived constraints, enumeration). The token threshold operationalizes only this descriptive label; it is never an exclusion/gate. May overlap R1 in different segments; length alone implies neither label.

R5 TERMINAL_AMBIGUITY: incompatible task answers remain at the end without unique commitment. This implies unscoreable. Lack of any task answer is unscoreable but not automatically R5.

Labels overlap, cover N/O only, and do not affect INPUT_VALID. Preserve complete raw outputs and token IDs. Review full traces in chunks as necessary, record supporting quotations and explicit negatives. One-agent annotation; no inter-rater reliability claim. Stage12B development traces are not reclassified or used as fresh validation. No task correctness or bottleneck estimates.
'''
    (ROOT / 'stage12br_pathology_annotation_guide.md').write_text(guide)
    old = load('outputs/stage12b/v1/config.json')
    cfg = {k:old[k] for k in ['environment','recipe','runtime','model','caps','source_manifest_sha256','seed_policy','oracle_rendering']}
    cfg.update(at=now(),resource=dict(target_gpu_hours=.6,hard_gpu_hours=1.0,max_concurrent_gpus=2),
               validity_rules_sha256=sha(ROOT/'stage12br_validity_rules.json'))
    paths = list(Path('scripts/stage12br').glob('*.py')) + [Path('scripts/stage12br/run.sh'),
        Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision/run_mathv.py'),original,oracle]
    cfg['source_sha256'] = {str(p):sha(p) for p in paths}
    save(ROOT/'config.json',cfg)
    manifest = dict(at=now(),frozen=True,n_families=12,n_calls=36,source=str(original),source_sha256=sha(original),
        preserved_cohort_families=61,preserved_facts=157,development_ids=source['technical_ids'],validation_ids=ids,
        selection=dict(seed=SELECTION_SEED,rule='Exclude12development; sort SHA256(seed|family_id),tie by family_id; choose first5multiple_choice and7open_ended; merge by same hash order.',
                       allowed_metadata=['item_id','family_id','answer_type'],eligible_metadata=eligible,outcomes_used=False),
        config_sha256=sha(ROOT/'config.json'),tasks=tasks)
    save(ROOT/'stage12br_validation_manifest.json',manifest)
    for shard in range(2):
        m=dict(at=now(),frozen=True,phase='validation',config_sha256=sha(ROOT/'config.json'),
               rows=[t for i in ids[shard::2] for t in tasks if t['item_id']==i])
        authorize_manifest(m,manifest)
        save(ROOT/f'audit/validation_{shard}.json',m)
    spec=f'''# Stage12B-R pathology-aware validity specification

Frozen {now()} before new generation. This user-approved repair follows the Stage12B repetition-based technical stop and validates on untouched families; it is not outcome-dependent relabeling of the old12 development cases.

Exact fresh IDs (hash order): {', '.join(ids)}. First5MC/7open by SHA256(`{SELECTION_SEED}|family_id`) among remaining49, merged by hash order; no subject, difficulty, prior output, correctness, or length used. Eligible metadata and hashes are preserved in the validation manifest. All36 tasks are byte-equivalent JSON records copied from the original183-task Stage12B manifest; runtime and model fields copied exactly. Original61families/157facts and all old evidence remain immutable.

Model Qwen3-VL-4B-Instruct ebb281ec70b05090aa6165b016eac8ec08e71b17; BF16/vLLM0.11.0, native image preprocessing and chat template; .7temperature/.8top-p/top-k20/repetition1/presence1.5; E256,N/O32768; original family seed policy. Two one-GPU queues each18calls, max30min each (combined1GPUh); startup/failures/teardown included. Historical36calls cost0.389167GPUh; expect0.4–0.6GPUh without guaranteeing length equivalence.

TECHNICALLY_VALID = INPUT_VALID and SCOREABLE and not TRUNCATED_BEFORE_OUTCOME. For each E/N/O: inputs12/12,scoreable>=10/12,truncated-before-outcome<=1/12. No repetition gate. R1–R5 retained independently under the sealed guide; R5 is intrinsically unscoreable. Any input failure blocks repair, as does an E scoreability failure (same numerical gates). Cap-after-commitment retained only when commitment remains unique at termination.

Success does not certify accuracy, E* semantic correctness, or bottleneck prevalence. No correctness/scientific scoring code runs. Full scientific profiling is NOT authorized automatically: section21 explicitly requires separate authorization after this validation, qualifying the conditional discussion in sections14/24. Stop after36calls/review/decision or hard1GPUh. No prompt/cap/sampling search, CoT, Thinking, reserves, or new benchmark.
'''
    (ROOT/'stage12br_pathology_aware_validity_spec.md').write_text(spec)
    freeze_paths = [p for p in ROOT.glob('stage12br*') if p.is_file()] + [ROOT/'config.json',ROOT/'audit/validation_0.json',ROOT/'audit/validation_1.json']
    save(ROOT/'audit/prospective_freeze.json',dict(at=now(),generation_started=False,correctness_opened=False,
        files={str(p):sha(p) for p in freeze_paths},source_hashes=cfg['source_sha256'],
        validation_ids=ids,exact_original_tasks=True,manifest_sha256=sha(ROOT/'stage12br_validation_manifest.json')))
    print('FROZEN36',ids,'manifest',sha(ROOT/'stage12br_validation_manifest.json'))


if __name__=='__main__':
    main()
