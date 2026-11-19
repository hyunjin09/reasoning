import ast, importlib.metadata
from scripts.stage14d1_recovery.contracts import *
from scripts.stage14d1.contracts import safe_payload

def main():
    original=load(OLD/'audit/final_package_seal.json')
    for group in ['package_files','code_files']:
        for path,digest in original[group].items():
            assert sha(path)==digest,path
    config=load(R/'protocol/runtime.json')
    versions={name:importlib.metadata.version(name) for name in config['environment']}
    assert versions==config['environment'],versions
    for path in Path('scripts/stage14d1_recovery').glob('*.py'):
        ast.parse(path.read_text(),filename=str(path))
    cases=rows(R/'data/families.jsonl')
    sample=load(OLD/'protocol/sampler_and_seeds.json')
    assert {r['family_id'] for r in cases}==set(sample['technical_families'])
    for row in cases:
        safe_payload(row)
        assert sha(row['image'])==row['image_sha256']
    reconstruction=load(R/'audit/reconstruction_audit_initial.json')['cases']
    fields=['original_prompt_bytes_equal','original_messages_equal','pixel_hashes_equal','sizes_equal',
            'reconstructed_prompt_exact','historical_prefix_decoded_text_starts','historical_prompt_plus_512_token_identity']
    assert all(all(row[key] for key in fields) for row in reconstruction)
    # Pinned source must support these exact options; no reliance on newer batch-invariance flags.
    installed=Path('.venv/official_eval/lib/python3.12/site-packages/vllm')
    assert 'VLLM_ENABLE_V1_MULTIPROCESSING' in (installed/'envs.py').read_text()
    assert 'VLLM_BATCH_INVARIANT' not in (installed/'envs.py').read_text()
    for token in ['scheduler_cls','worker_cls','logprobs_mode']:
        assert token in (installed/'engine/arg_utils.py').read_text()
    result=dict(at=now(),status='PASS',original_files_preserved=len(original['package_files']),
        original_code_files_preserved=len(original['code_files']),families=8,versions=versions,
        original_prompt_plus_prefix_tokens_exact=8,original_image_parity=8,
        CPU_tests=['contracts_green.txt','grammar_cpu.txt'],technical_remaining_seconds=remaining_seconds(1421,[]),
        new_allocation_maximum_seconds=4800,main_pilot_enabled=False,git_metadata_available=Path('.git').exists())
    save(R/'audit/cpu_preflight.json',result)
    print(result)

if __name__=='__main__':
    main()
