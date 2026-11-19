"""Freeze reuse, new generation, scoring and inference without viewing correctness."""
import hashlib
from pathlib import Path
from scripts.stage12bs.common import ROOT,load,save,sha,now
from scripts.stage12bs.protocol import authorize_manifest


def main():
    assert not (ROOT/'config.json').exists()
    old_path=Path('outputs/stage12b/v1/stage12b_frozen_manifest.json');old=load(old_path)
    repaired=load('outputs/stage12br/v1/stage12br_validation_manifest.json')
    assert load('outputs/stage12br/v1/stage12br_validation_decision.json')['decision']=='VALIDITY_REPAIRED'
    dev=set(old['technical_ids']);val=set(repaired['validation_ids']);assert len(dev)==len(val)==12 and not dev&val
    remaining=[r['item_id'] for r in old['rows'] if r['item_id'] not in dev|val]
    assert len(remaining)==37 and len(old['rows'])==61 and sum(len(r['facts']) for r in old['rows'])==157
    for r in old['rows']:assert sha(r['image'])==r['image_sha256']
    for src,dst in [('outputs/stage12a/v1/stage12a_frozen_e_star_manifest.json','audit/frozen_stage12a_manifest.json'),
                    ('plan/stage12bs_full_scientific_failure_profiling_plan.md','audit/approved_plan.md'),
                    ('outputs/stage12br/v1/stage12br_validity_rules.json','audit/inherited_validity_rules.json'),
                    ('outputs/stage12br/v1/stage12br_pathology_annotation_guide.md','audit/inherited_pathology_guide.md')]:
        (ROOT/dst).write_bytes(Path(src).read_bytes())
    reuse=[]
    for t in old['tasks']:
        if t['item_id'] not in dev|val:continue
        origin=Path('outputs/stage12b/v1' if t['item_id'] in dev else 'outputs/stage12br/v1')
        folder=origin/'generations'/t['task_id'];receipt=load(folder/'result.json');g=load(folder/'generation.json')
        assert load(folder/'input.json')['task']==t
        assert receipt['generation_sha256']==sha(folder/'generation.json') and receipt['input_sha256']==sha(folder/'input.json')
        reuse.append(dict(task_id=t['task_id'],origin=str(origin),generation_sha256=sha(folder/'generation.json'),
                          input_sha256=sha(folder/'input.json'),result_sha256=sha(folder/'result.json')))
    assert len(reuse)==72
    base=load('outputs/stage12b/v1/config.json')
    cfg={k:base[k] for k in ['environment','recipe','runtime','model','caps','source_manifest_sha256','seed_policy','oracle_rendering','bootstrap_seed','bootstrap_draws']}
    cfg.update(at=now(),resource=dict(target_gpu_hours=5,hard_gpu_hours=7,max_concurrent_gpus=4))
    fixed_sources=list(Path('scripts/stage12bs').glob('*.py'))+[Path('scripts/stage12bs/run.sh'),old_path,
        Path('scripts/stage12br/protocol.py'),Path('scripts/stage12b/protocol.py'),
        Path('code/visual_reasoning/stage8b/v2_scoring.py'),Path('code/visual_reasoning/stage8b/scoring.py'),
        Path('outputs/stage12b/v1/stage12b_oracle_integrity_review.json'),
        Path('outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision/run_mathv.py')]
    cfg['source_sha256']={str(p):sha(p) for p in fixed_sources};save(ROOT/'config.json',cfg)
    order=sorted((r['family_id'] for r in old['rows']),key=lambda f:(hashlib.sha256(('stage12bs-audit-v1|'+f).encode()).hexdigest(),f))
    analysis=dict(at=now(),frozen=True,correctness_opened=False,
        full_gate=dict(input_valid=61,scoreable_minimum=51,truncated_before_outcome_maximum=5),
        full_gate_rationale='Preserve Stage12B-R12-case gate rates at61; ceiling minimum/floor maximum. Frozen prospectively, no outcome tuning.',
        native_denominator='N input-valid and scoreable; unscoreable never encoded as wrong',
        complete_denominator='All E/N/O input-valid and scoreable; profile only native failures in this set',
        secondary_failure_precedence=['R1orR2:LOOP_OR_REOPEN','elseR3:NONCONVERGENT','else stable committed failure:WRONG_CONVERGED','else:OTHER'],
        persistence_types=['R1','R2','R3'],persistence_same_type='at least one shared pathology; preserve full N/O label sets',
        random_audit=dict(seed='stage12bs-audit-v1',family_hash_order=order,
            rule='After first-pass ambiguity flags, exclude families flagged in any arm; take firstceil(.2*n)remaining by frozen order; second-pass all3arms separately. Also review every ambiguity-triggered arm.'),
        scoring_second_review='One-agent separate blinded second pass, with first labels and paired-arm responses absent. Quality-control agreement only; no independent human inter-rater claim.',
        representative_examples='Lexicographically smallest conservative family_id in each nonemptyB1–B4 after all labels frozen',
        bootstrap_seed=cfg['bootstrap_seed'],bootstrap_draws=4000,
        bootstrap_contrasts=['rescue_Eplus_minus_Eminus','paired_oracle_minus_native'],
        profile_informative='>=20 scoreable native failures; at least twoB1–B3>=5 or one>=10; full validity and oracle integrity pass',
        stopping='16artifacts,5figures,exactly1recommendation; no C/T or other follow-on')
    save(ROOT/'audit/analysis_rules.json',analysis)
    full=dict(at=now(),frozen=True,source=str(old_path),source_sha256=sha(old_path),n_families=61,n_facts=157,
        development_ids=old['technical_ids'],validation_ids=repaired['validation_ids'],remaining_ids=remaining,
        config_sha256=sha(ROOT/'config.json'),tasks=old['tasks'],rows=old['rows'],reuse=reuse)
    save(ROOT/'stage12bs_full_manifest.json',full)
    new=dict(at=now(),frozen=True,phase='remaining',config_sha256=sha(ROOT/'config.json'),n_families=37,n_calls=111,
        tasks=[t for t in old['tasks'] if t['item_id'] in remaining],ids=remaining)
    save(ROOT/'stage12bs_remaining_generation_manifest.json',new)
    for rank in range(4):
        ids=remaining[rank::4]
        shard=dict(at=now(),frozen=True,phase='remaining',config_sha256=sha(ROOT/'config.json'),rows=[t for i in ids for t in new['tasks'] if t['item_id']==i])
        authorize_manifest(shard,new);save(ROOT/f'audit/remaining_{rank}.json',shard)
    spec=f'''# Stage12B-S full scientific profile specification

Frozen {now()} before new generation and correctness opening. The approved plan is preserved in audit/approved_plan.md. All61 families/157facts and183 exact requests are copied from Stage12B. Reuse72 saved calls from24disjoint technical families; generate only111 calls for remaining37, without retries or replacement.

Same4B Instruct revision ebb281ec70b05090aa6165b016eac8ec08e71b17, BF16/vLLM0.11.0, processor, image preprocessing, engine seed42, batch size18, max model length128000; .7temperature/.8top-p/top-k20/repetition1/presence1.5; E256,N/O32768; exact original family seeds. Four one-GPU finite queues of30/27/27/27 calls,60minute limits (4GPUh absolute launch envelope), expected1.5–2.5GPUh from previous throughput. Stage target<5/hard7GPUh includes startup and failures; prior stages reported separately.

Correctness stays closed until all183 generations and input/scoreability records are complete and denominators frozen. Stage12B-R validity and R1–R5 definitions are inherited byte-for-byte. Full-scale validation preserves their rates prospectively: every arm61/61input-valid,>=51/61scoreable,<=5/61pre-outcome truncations. No repetition exclusion; cap-after-outcome retained when a unique commitment survives.

N accuracy/P1 uses input-valid scoreable N; complete-profile C requires all3arms valid/scoreable; F is native failures in C. Missing outcomes are TECHNICAL_UNRESOLVED, never wrong. B1=(E-,O+),B2=(E+,O+),B3=(E+,O-),B4=(E-,O-) within F. P2 oracle rescue; P3–P6 corresponding B1–B4 fractions. PROFILE_INFORMATIVE requires>=20 scoreable native failures and twoB1–B3>=5 or one>=10 plus full validity/oracle integrity. Otherwise sparse or technical breakdown, without a repetition threshold.

Arm-separated E/N/O scoring packets include only that arm's response, frozen question/request and gold. E atom labels CORRECT/INCORRECT/UNRESOLVED; E+ iff all atoms correct. N/O use frozen MathVision option/numeric mathematical equivalence; nonstandard equivalents require explicit second review. Every prospectively specified ambiguity trigger gets a second pass without paired outcomes or first labels. Additionally audit ceil20% of otherwise unambiguous families by frozen SHA256(stage12bs-audit-v1|family_id) order, all3arms separately. This single-agent second-pass audit estimates quality control, not independent human reliability.

R1/R2/R3 are pathology types for N-to-O persistence; R4 remains a descriptive advancing-computation label. Secondary failure precedence: R1/R2=>LOOP_OR_REOPEN,elseR3=>NONCONVERGENT,otherwise stable committed failure=>WRONG_CONVERGED,otherwiseOTHER. Persistence SAME_TYPE means any sharedR1–R3; retain exact sets. No primary taxonomy changes.

Wilson95 intervals for family proportions;4000 family-bootstrap draws,seed{cfg['bootstrap_seed']}, for delta oracle rescue by E recoverability and paired oracle-minus-native accuracy. No atom/token pseudoreplication. S1 excludes original12development; S2 excludes all24technical cases. Figures: assay, B1–B4 composition, rescue by E, pathology by B, deterministic smallest-family-ID examples after labels frozen.

Preserve all old artifacts. Produce16 required artifacts and5 figure pairs; exactlyone plan-specified recommendation, never execute it. No CoT, Thinking, new benchmark, intervention, prompt or sampling repair.
'''
    (ROOT/'stage12bs_scientific_profile_spec.md').write_text(spec)
    paths=[ROOT/'config.json',ROOT/'stage12bs_scientific_profile_spec.md',ROOT/'stage12bs_full_manifest.json',ROOT/'stage12bs_remaining_generation_manifest.json',ROOT/'audit/analysis_rules.json']
    paths+=list((ROOT/'audit').glob('remaining_*.json'))
    save(ROOT/'audit/prospective_freeze.json',dict(at=now(),correctness_opened=False,generation_started=False,files={str(p):sha(p) for p in paths}))
    print('FROZEN',len(reuse),'reused;111new;37families;4finite shards')


if __name__=='__main__':main()
