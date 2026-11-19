"""Freeze untouched validation identities and exact approved contracts."""
import hashlib
from pathlib import Path
from scripts.stage12ar.common import ROOT, CAPS, load, save, sha, now
from scripts.stage12ar.protocol import SELECTION_SEED, select_validation, build_prompt, D_MC, D_OPEN, C0, C1


def main():
    oldroot = Path('outputs/stage12a/v1')
    original = oldroot / 'stage12a_frozen_e_star_manifest.json'
    source = load(original)
    plan = Path('plan/stage12ar_answer_only_reasoning_contract_validation_plan.md')
    assert not (ROOT / 'generations').exists()
    assert len(source['rows']) == 61 and sum(len(r['facts']) for r in source['rows']) == 157
    development = source['technical_selection']['ids']
    assert development == ['2035','750','528','2749','653','725','2359','57','2975','1140','1988','2553']
    validation = select_validation(source['rows'], development)
    assert not set(development) & set(validation)
    for r in source['rows']:
        assert sha(r['image']) == r['image_sha256']
    for src, dst in [(original, ROOT / 'audit/frozen_stage12a_manifest.json'),
                     (plan, ROOT / 'audit/approved_plan.md')]:
        with dst.open('xb') as f: f.write(src.read_bytes())
    oldcfg = load(oldroot / 'config.json')
    cfg = {k: oldcfg[k] for k in ['model', 'environment', 'recipe', 'runtime', 'seed_policy']}
    cfg['at'] = now()
    cfg['caps'] = CAPS
    cfg['source_manifest_sha256'] = sha(original)
    cfg['source_sha256'] = {str(p): sha(p) for p in Path('scripts/stage12ar').glob('*.py')}
    for p in ['scripts/stage12ar/run.sh','scripts/stage11cr/protocol.py',
              'outputs/qwen3vl_official_eval/v1/sources/qwen/evaluation/MathVision/run_mathv.py']:
        cfg['source_sha256'][p] = sha(p)
    cfg['technical_only'] = True
    cfg['resource'] = dict(target_gpu_hours=1.5, hard_gpu_hours=2.5, max_concurrent_gpus=8)
    cfg['technical_gate'] = dict(D='format>=10,final>=11,reasoning<=1,caps0,repetition0',
        C='format>=10,final>=10,reasoning>=10,caps<=1,repetition<=1', no_prompt_adaptation=True)
    save(ROOT / 'config.json', cfg)
    by_id = {r['item_id']: r for r in source['rows']}
    def task(item, arm, phase):
        r = by_id[item]
        seed = int(hashlib.sha256(('stage12a-gen-v1|' + r['family_id']).encode()).hexdigest()[:8], 16) % (2**31)
        return dict(task_id=f'{phase}_{arm}_{item}_v1', item_id=item, family_id=r['family_id'],
            arm=arm, prompt_version=1, image=r['image'], image_sha256=r['image_sha256'],
            prompt=build_prompt(r, arm), answer_type=r['answer_type'], cap=CAPS[arm], seed=seed)
    dev_tasks = [task(i, a, 'development') for i in development for a in ['D','C0','C1']]
    dev = dict(at=now(), frozen=True, phase='development_inventory', config_sha256=sha(ROOT / 'config.json'),
        ids=development, rows=dev_tasks, actual_execution_order='D12, stop if invalid; otherwise C0/C1 24')
    save(ROOT / 'stage12ar_development_manifest.json', dev)
    validation_tasks = [task(i, a, 'validation') for i in validation for a in ['D','C0','C1']]
    val = dict(at=now(), frozen=True, config_sha256=sha(ROOT / 'config.json'), ids=validation,
        selection_seed=SELECTION_SEED, selection_rule='SHA256(seed|family_id); lowest5 MC and7 open, merged in hash order; natural hash mix fallback only if these quotas unavailable.',
        allowed_selection_fields=['family_id','item_id','answer_type'], correctness_opened=False,
        rows=[{k:by_id[i][k] for k in ['item_id','family_id','question','answer_type','image','image_sha256']} for i in validation],
        prospective_tasks=validation_tasks,
        execution_note='Only D plus the one development-selected C candidate may execute:24 calls maximum. The other12 candidate task templates remain NOT_RUN.')
    save(ROOT / 'stage12ar_validation_manifest.json', val)
    for label, arms in [('development_D',['D']), ('development_C',['C0','C1'])]:
        save(ROOT / 'audit' / f'{label}.json', dict(at=now(), frozen=True, phase=label,
            config_sha256=sha(ROOT / 'config.json'), rows=[t for t in dev_tasks if t['arm'] in arms]))
    with (ROOT / 'stage12ar_prompt_contracts.md').open('x') as f:
        f.write('# Stage12A-R exact appended contracts\n\nEach suffix follows the unchanged original question with two newlines; original image first. No added system message or assistant prefill.\n\n')
        for label, suffix in [('D-MC',D_MC),('D-Open',D_OPEN),('C0',C0),('C1',C1)]:
            f.write(f'## {label}\n\n```text\n{suffix}\n```\n\n')
    spec = '''# Stage12A-R contract-validation specification

This is the user-approved plan's technical stage, stored separately from immutable Stage12A evidence. No correctness or Lost-Keys endpoints are opened, including after technical success. No scientific rerun is authorized by this stage.

Preserve all61 families,157 E* facts, original images/questions/source answers and E prompts. Development uses the fixed12 IDs. Validation uses12 disjoint families selected before generation: five MC and seven open by SHA256(stage12ar-validation-v1|family_id). Only IDs and native answer type determine selection; no difficulty, subject, native outcomes or correctness. All61 source image hashes verified. No download required.

One exact D suffix, cap64; two exact C candidates C0/C1, cap32768. Same pinned Qwen3-VL-2B-Instruct/BF16/vLLM0.11.0, processor/image bounds, engine42 and Stage12A per-family request seed policy. Sampling .7/.8/top20/repetition1/presence1.5, native EOS, no logit constraints or added stop strings. Exact full requests are in the manifests.

Run D development first. If invalid, stop without C or validation. Otherwise run exactly C0/C1 on all12 development cases; if neither passes, stop. Select one passing C by fewer severe repetitions, fewer caps, more committed finals, more format-valid responses, shorter median generated length, then C0. Freeze selection before any validation generation. Run D and that C on untouched12; no adaptation thereafter. Maximum60 actual calls, no E or other generation.

Output-only annotation is manual and bound to raw-output hashes. D FORMAT_VALID means the entire response normalizes to one option letter or native value/expression with no calculations, equations showing evaluation, explanations or alternatives. Mathematical markup/trailing punctuation may normalize. COMMITTED_FINAL can be true even if visible intermediate calculations make D invalid. VISIBLE_REASONING includes calculations, derivations or substantive intermediate problem-solving; an answer label alone is not reasoning.

C0 FORMAT_VALID requires a clear terminal native answer, optionally boxed or marked by an answer label or unambiguous concluding phrase; no literal Final answer marker is demanded because C0 does not request it. C1 requires its terminal Final answer: X line, with X replaced by the actual single native answer. For both, MC requires one option letter in the terminal answer field; open requires one value/expression. A letter accompanied by option text/value in that field is not strict format-valid. Placeholder X, unresolved alternatives, giving up, or a provisional answer followed by renewed analysis is not terminal commitment. Read output only; do not judge whether the answer is mathematically correct. Any extraction ambiguity stays explicit and cannot be resolved using gold.

C VISIBLE_REASONING requires substantive intermediate reasoning, not merely a promise to think or the final answer alone. SEVERE_REPETITION uses the same semantic criterion as Stage12A: prolonged repeated non-progressing derivation/interpretation cycles; eventual normal stopping does not erase it. Exact32-gram metrics support but do not replace semantic review. CAP_HIT comes from runtime finish_reason and token count. Preserve stop reasons, raw text/token IDs, token lengths and quotes supporting each decision.

D gates, both sets: format>=10/12, committed>=11/12, visible reasoning<=1/12, caps0, severe repetition0. C gates, both sets: visible reasoning>=10/12, committed>=10/12, format>=10/12, caps<=1/12, severe repetition<=1/12. No relaxed gates or further candidates/budgets.

Decision precedence: development D failure=D_INVALID; no passing development C=C_INVALID; if development passes but untouched validation fails, use CONTRACT_UNSTABLE (plan section19's generalization-specific state), recording D_INVALID/C_INVALID component flags as applicable. CONTRACT_VALID only if both stages pass. No task correctness is computed for any decision.

Target<1.5/hard2.5 allocated GPUh including startup and failed attempts. Finite single-GPU jobs via project scheduler/Slurm, authorized A6000 nodes02/03/06/07. D30minutes, later waves at most40minutes each and budget-checked against actual prior cost. Workers exit after their explicit queues; observational watchers cannot launch another wave. No scientific rerun after closure.
'''
    with (ROOT / 'stage12ar_contract_validation_spec.md').open('x') as f: f.write(spec)
    files = [ROOT / p for p in ['config.json','stage12ar_development_manifest.json','stage12ar_validation_manifest.json',
        'stage12ar_prompt_contracts.md','stage12ar_contract_validation_spec.md','audit/development_D.json','audit/development_C.json','audit/frozen_stage12a_manifest.json','audit/approved_plan.md']]
    save(ROOT / 'audit/prospective_freeze.json', dict(at=now(), correctness_opened=False,
        files={str(p):sha(p) for p in files}, original_stage12a_manifest_sha256=sha(original),
        original_stage12a_closure_sha256=sha(oldroot / 'audit/closure_validation.json'),
        development_calls=36, validation_max_calls=24, E_calls=0,
        validation_ids=validation, validation_answer_types={a:sum(by_id[i]['answer_type']==a for i in validation) for a in ['multiple_choice','open_ended']}))
    print('FROZEN_VALIDATION', validation)


if __name__ == '__main__': main()
