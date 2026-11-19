"""Prepare a review-only G0 package. No generation, score decoding, or launch."""
import collections
import difflib
import importlib.metadata
import subprocess
from pathlib import Path

from tokenizers import Tokenizer
from scripts.stage14c.common import load, rows, sha, fingerprint, save, write_rows, now
from scripts.stage14cv.design import (
    parse_original, render_r1, parse_r1, render_r2, parse_r2, remove_conflict,
    select_expansion, rank, EXPANSION_SALT, ORDER_SALT,
)

PARENT = Path('outputs/stage14c')
ROOT = Path('outputs/stage14c_v_blindtest_validation')


def main():
    stamp = now()
    catalog = load(PARENT/'audit/artifact_catalog.json')['files']
    verified = {}

    def verify(path):
        path = Path(path)
        digest = sha(path)
        assert catalog[str(path)] == digest, path
        verified[str(path)] = digest
        return digest

    names = ['source/cohort_manifest.jsonl', 'source/evidence_atoms.jsonl',
             'source/D1_shared_unit_map_v1.jsonl', 'manifests/main_tasks.jsonl',
             'manifests/D1_tasks.jsonl', 'manifests/D1_source_membership_v1.json',
             'spec/model_and_recipe_identity.json', 'spec/diagnostic_authorization.json',
             'audit/g1_final_source_seal_v1.json', 'audit/main_raw_seal.json',
             'audit/main_I_scoring_seal.json', 'audit/main_T_scoring_seal.json',
             'audit/primary_analysis_seal.json', 'audit/primary_summary_seal.json',
             'audit/D1_raw_seal.json', 'audit/D1_scoring_seal.json', 'audit/D1_analysis_seal.json',
             'audit/final_validation.json']
    for name in names:
        verify(PARENT/name)
    closure = load(PARENT/'audit/final_closure_seal_v1.json')
    assert closure['status'] == 'COMPLETE_STOP'
    assert closure['closure_files'][str(PARENT/'audit/artifact_catalog.json')] == sha(PARENT/'audit/artifact_catalog.json')
    source = {r['family_id']: r for r in rows(PARENT/'source/cohort_manifest.jsonl')}
    evidence = [r for r in rows(PARENT/'source/evidence_atoms.jsonl') if r['benchmark'] == 'BlindTest']
    ids = [e['family_id'] for e in evidence]
    old = load(PARENT/'manifests/D1_source_membership_v1.json')['families']['BlindTest']
    new = select_expansion(ids, old)
    selected_c = set(old) | set(new)
    maps = {r['family_id']: r for r in rows(PARENT/'source/D1_shared_unit_map_v1.jsonl') if r['benchmark'] == 'BlindTest'}
    assert set(maps) == set(old)
    unit_keys = next(iter(maps.values()))['atoms'][0]['subfact_keys']
    assert len(unit_keys) == 5
    tasks = [t for t in rows(PARENT/'manifests/main_tasks.jsonl') if t['family_id'] in ids]
    probes = [t for t in rows(PARENT/'manifests/D1_tasks.jsonl') if t['family_id'] in old]
    assert len(tasks) == 1200 and len(probes) == 200
    task_lookup = {(t['family_id'], t['model_key'], t['condition']): t for t in tasks + probes}
    historical_receipts = []
    # Hash historical generations and scores as opaque bytes. Do not parse outcomes.
    for t in tasks + probes:
        result_path = PARENT/'raw'/t['collection']/t['task_id']/'attempt_0/result.json'
        verify(result_path)
        receipt = load(result_path)
        assert receipt['task_sha256'] == fingerprint(t)
        folder = result_path.parent
        assert verify(folder/'input.json') == receipt['input_sha256']
        assert verify(folder/'generation.json') == receipt['generation_sha256']
        inp = load(folder/'input.json')
        assert inp['task'] == t
        assert inp['messages'][0]['content'][-1]['text'] == t['prompt']
        assert fingerprint(t) == inp['task_sha256']
        expected_chat = '<|im_start|>user\n' + ('<|vision_start|><|image_pad|><|vision_end|>' if t['image_reference'] else '') + t['prompt'] + '<|im_end|>\n<|im_start|>assistant\n' + ('<think>\n' if t['model_key'] == 'T' else '')
        assert inp['chat_prompt'] == expected_chat
        assert inp['image_present'] == bool(t['image_reference'])
        if t['condition'] != 'D1':
            score_path = PARENT/'scoring/score_reviews'/f"{t['task_id']}.json"
            if not score_path.exists(): score_path = PARENT/'scoring/first_scores'/f"{t['task_id']}.json"
            verify(score_path)
        historical_receipts.append(dict(task_id=t['task_id'], input_sha256=receipt['input_sha256'],
            generation_sha256=receipt['generation_sha256'], result_sha256=sha(result_path),
            generation_and_score_contents_decoded=False))
    cfg = load(PARENT/'spec/model_and_recipe_identity.json')
    checkpoints = {}
    tokenizers = {}
    for model, value in cfg['models'].items():
        path = Path(value['model']['checkpoint']); files = {}
        assert path.resolve().is_relative_to(Path('/data/dataset'))
        for name, expected in value['model']['files_sha256'].items():
            p = path/name
            assert p.is_file()
            if not name.endswith('.safetensors'):
                assert sha(p) == expected
            files[name] = dict(bytes=p.stat().st_size, expected_sha256=expected,
                sha256_verified_now=not name.endswith('.safetensors'))
        checkpoints[model] = dict(path=str(path), files=files,
            weight_hash_recheck='Deferred to scheduled G2 before GPU model loading; prior pinned hashes preserved.')
        tokenizers[model] = Tokenizer.from_file(str(path/'tokenizer.json'))
    template = load(PARENT/'spec/diagnostic_authorization.json')['D1']['prompt']
    prompt_rows, ledgers, equivalence, c_diff, cohort = [], [], [], [], []
    question_counts = collections.Counter()
    import pyarrow.parquet as pq
    parquet = Path(source[ids[0]]['parquet'])
    assert parquet.resolve().is_relative_to(Path('/data/dataset'))
    table = pq.read_table(parquet, columns=['image'])
    import hashlib
    for e in evidence:
        fid = e['family_id']; s = source[fid]; question = s['question']
        question_counts[question] += 1
        image = table.slice(s['row_index'], 1).to_pylist()[0]['image']
        payload = image['bytes'] if isinstance(image, dict) else image
        assert hashlib.sha256(payload).hexdigest() == s['image_sha256']
        assert s['category'] == 'Line Plot Intersections'
        assert e['primary_atom_count'] == 1 and e['structured_subfact_total'] == 5
        assert len(e['atoms']) == 1 and e['atoms'][0]['structured_subfact_count'] == 5
        assert e['serialized_evidence'] == '- ' + e['atoms'][0]['text']
        ledger = parse_original(e['serialized_evidence'])
        values = dict(R0=e['serialized_evidence'], R1=render_r1(ledger), R2=render_r2(ledger))
        assert parse_r1(values['R1']) == parse_r2(values['R2']) == ledger
        if fid in maps:
            m = maps[fid]['atoms'][0]
            assert m['text'] == e['atoms'][0]['text'] and m['subfact_keys'] == unit_keys
        ledgers.append(dict(family_id=fid, source_evidence_sha256=fingerprint(e),
            ledger=ledger, primary_atom_count=1, structured_subfact_count=5, subfact_keys=unit_keys,
            status='G0_PROPOSAL_NOT_G1_QC_SEAL'))
        equivalence.append(dict(family_id=fid, roundtrip_to_original_pass=True,
            new_source_facts=False, omitted_source_facts=False, coordinates_or_counts_added=False,
            original_image_sha256=s['image_sha256'], original_image_bytes_verified=True,
            source_visual_second_review='PENDING_G1', original_source_QC_preserved=True,
            same_agent_source_review_not_independent=True))
        cohort.append(dict(source=s, frozen_evidence=e, R_included=True,
            C_stratum='old100' if fid in old else 'new100' if fid in new else 'not_selected'))
        for condition, value in values.items():
            prompt = 'Task-critical visual evidence:\n' + value + '\n\n' + question
            for model in 'IT':
                if condition == 'R0':
                    assert prompt == task_lookup[fid, model, 'equal_evidence']['prompt']
            seed = task_lookup[fid, 'I', 'equal_evidence']['seed']
            assert seed == task_lookup[fid, 'T', 'equal_evidence']['seed']
            prompt_rows.append(dict(family_id=fid, condition=condition, prompt=prompt,
                prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), evidence_text=value,
                image_present=False, seed=seed, model_keys=['I', 'T'], text_chars=len(prompt),
                text_tokens={m: len(tok.encode(prompt, add_special_tokens=False).ids) for m, tok in tokenizers.items()}))
        if fid in selected_c:
            c0 = template.format(native_question_with_options=question)
            c1 = template.format(native_question_with_options=remove_conflict(question))
            assert c0.startswith(c1) and c0[len(c1):] == question[len(remove_conflict(question)):]
            seed = int(hashlib.sha256(f'stage14c-v1|BlindTest|{fid}|r0|D1'.encode()).hexdigest(), 16) % 2**31
            for model in 'IT':
                if fid in old:
                    assert c0 == task_lookup[fid, model, 'D1']['prompt']
                    assert seed == task_lookup[fid, model, 'D1']['seed']
            for condition, prompt in [('C0', c0), ('C1', c1)]:
                prompt_rows.append(dict(family_id=fid, condition=condition, prompt=prompt,
                    prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), image_present=True,
                    image_sha256=s['image_sha256'], image_reference=dict(parquet=str(parquet), row_index=s['row_index']),
                    seed=seed, model_keys=['I', 'T'], stratum='old100' if fid in old else 'new100',
                    text_chars=len(prompt), text_tokens={m:len(tok.encode(prompt, add_special_tokens=False).ids) for m,tok in tokenizers.items()}))
            c_diff.append(dict(family_id=fid, removed_exact_suffix=c0[len(c1):],
                diff=''.join(difflib.unified_diff(c0.splitlines(True), c1.splitlines(True), fromfile='C0', tofile='C1')),
                insertion='', evidence_request_unchanged=True, native_question_stem_unchanged=True))
    assert len(prompt_rows) == 1300 and len(ledgers) == 300 and len(c_diff) == 200
    env = subprocess.run(['.venv/official_eval/bin/python','-c',
        'import importlib.metadata,json; print(json.dumps({p:importlib.metadata.version(p) for p in '+repr(list(cfg['environment']))+'}))'],
        check=True, text=True, capture_output=True)
    packages = __import__('json').loads(env.stdout)
    assert packages == cfg['environment']
    files_to_write = {
        'cohorts/blindtest_e300_reference_proposal_v1.jsonl':cohort,
        'cohorts/d1_old100_identity_proposal_v1.jsonl':[dict(family_id=f, original_rank=i) for i,f in enumerate(old)],
        'cohorts/d1_new100_source_hash_proposal_v1.jsonl':[dict(family_id=f, rank=i, selection_hash=rank(f,EXPANSION_SALT)[0]) for i,f in enumerate(new)],
        'source_qc/semantic_ledger_proposal_v1.jsonl':ledgers,
        'source_qc/serialization_roundtrip_audit_v1.jsonl':equivalence,
        'spec/exact_prompts_and_diffs/proposed_condition_prompts_v1.jsonl':prompt_rows,
        'spec/exact_prompts_and_diffs/c0_c1_exact_diffs_v1.jsonl':c_diff,
        'audit/historical_receipt_identity_v1.jsonl':historical_receipts,
    }
    for name, values in files_to_write.items(): write_rows(ROOT/name, values)
    save(ROOT/'spec/model_recipe_proposed_v1.json', cfg)
    save(ROOT/'spec/source_selection_proposed_v1.json',dict(at=stamp, status='PROPOSED_G0_NOT_RELEASED',
        expansion_salt=EXPANSION_SALT, expansion_rule='SHA256(salt|family_id), then family_id; first100 of300 minus old100',
        R_order=sorted(ids,key=lambda f:rank(f,ORDER_SALT)), C_order=sorted(selected_c,key=lambda f:rank(f,ORDER_SALT)),
        order_salt=ORDER_SALT, outcome_values_used=False, old_D1_order_preserved=True,
        seed_policy='Inherit historical Stage14C family-linked R seeds; inherit D1 seed formula for both old/new C; shared across conditions/models.'))
    save(ROOT/'audit/parent_identity_audit_v1.json',dict(at=stamp,status='PASS_G0_IDENTITY_ONLY',
        original_seal=str(PARENT/'audit/final_closure_seal_v1.json'), original_seal_sha256=sha(PARENT/'audit/final_closure_seal_v1.json'),
        checked_parent_files=verified, historical_raw_inputs_verified=1400,
        original_scientific_outcome_values_decoded=False, historical_aggregate_findings_known=True,
        native_source_families=300, source_images_hash_verified=300, R0_prompts_verified=600,
        historical_C0_prompts_verified=200, new_C0_prompts_constructed_from_exact_template=200,
        distinct_original_serializations=len({e['serialized_evidence'] for e in evidence}),
        question_templates=dict(question_counts), packages=packages, models=checkpoints,
        runtime_replay_validated_now=False, G1_source_QC_pending=True, new_model_calls=0,
        dataset=dict(path=str(parquet),sha256=sha(parquet),downloaded=False),
        tokenizer_length_note='Text-only tokenizer lengths; multimodal image-token expansion and full processor identity require G2.',
        discrepancies=['Plan prose describes a later/appended D1 request; exact historical order is evidence request, then question/answer-only clause.',
            'There are two native question/answer-contract variants, not one. C1 deletes the matching exact suffix.',
            'Generation is not bytewise invariant across changed batching; new matched context needs bounded G2 replay.',
            'C-P1 is reported by two models and two strata, so an unspecified two-p-value Holm family would be ambiguous. Proposed inference uses effect sizes and unadjusted CIs without significance declarations.']))
    save(ROOT/'audit/g0_proposal_data_hashes_v1.json',dict(at=now(),files={str(ROOT/n):sha(ROOT/n) for n in files_to_write},
        status='REVIEW_ONLY_NOT_A_G1_SOURCE_SEAL',scientific_calls_materialized=0,review_prompt_rows=1300,
        proposed_scientific_calls=2600,maximum_technical_calls=24,generation_authorized=False))
    print('G0 source/input audit PASS:300families,1400historicalreceipts,1300review prompts; NO_GENERATION')


if __name__ == '__main__':
    main()
