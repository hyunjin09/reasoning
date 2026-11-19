from copy import deepcopy
from pathlib import Path

import pytest

from scripts.stage7a.common import read_json, write_json, write_jsonl, sha
from scripts.stage7a_bench.causal_provenance_v2 import object_sha
import scripts.stage7a_bench.native_prior_convergence_v2 as module
from scripts.stage7a_bench.tests.test_native_prior_convergence_v2 import fixture


def artifact_fixture(monkeypatch, tmp_path):
    entry, generation, tokens, meta, result, review, _ = fixture()
    entry.update(causal_pilot_frozen=True, native_input=meta)
    out = tmp_path/'outputs/stage7a_bench_v2'
    run = out/'causal_pilot/native_controls/run01'
    config = dict(runtime=dict(slurm_allocation='existing'),
                  locked_generation_protocol=dict(max_new_tokens=40960, seed=1234))
    write_json(out/'config/runtime.json', config)
    config_sha = sha(out/'config/runtime.json')
    execution = dict(runtime_sha256=config_sha, dependencies={'test': 'frozen'})
    cert = out/'causal_pilot/mechanics/bench.json'
    write_json(cert, dict(status='PASS_ACTUAL_4B_CAUSAL_MECHANICS', execution_signature=execution))
    variants = {'fixed_'+c:dict(event_id='base__fixed_'+c, condition=c)
                for c in module.CONDITIONS}
    provenance = {'review_sha256': 'fixed_bank'}
    signature = dict(mode='native_controls', execution_signature=execution,
        mechanics_certificate=dict(path=str(cert), sha256=sha(cert)),
        generation_protocol=config['locked_generation_protocol'],
        entry_sha256={entry['id']:object_sha(entry)},
        control_provenance={entry['id']:provenance}, control_rows={entry['id']:variants})
    write_json(run/'signature.json', signature)
    write_json(run/'environment.json', dict(parameter_dtype='torch.bfloat16', slurm_job_id='existing'))
    write_json(out/'causal_pilot/wrappers/run01.json',
               dict(completed=True, exit_code=0, slurm_job_id='existing'))
    records, reviews = [], {}
    for condition in module.CONDITIONS:
        dest = run/'examples'/entry['id']/condition
        variant = variants['fixed_'+condition]
        write_json(dest/'manifest_row.json', variant)
        write_json(dest/'input.json', dict(meta, **variant))
        write_json(dest/'generation.json', generation)
        write_jsonl(dest/'tokens.jsonl', tokens)
        outcome = dict(result, **variant, entry_id=entry['id'],
            generation_sha256=sha(dest/'generation.json'), tokens_sha256=sha(dest/'tokens.jsonl'))
        write_json(dest/'result.json', outcome)
        hashes = {k+'_sha256':sha(dest/(k+('.jsonl' if k == 'tokens' else '.json')))
                  for k in ('input', 'generation', 'tokens', 'result')}
        reviews[condition] = dict(deepcopy(review), **hashes)
        records.append(dict(entry_id=entry['id'], condition=condition, result_sha256=hashes['result_sha256']))
    write_json(run/'run_summary.json', dict(completed=True, mode='native_controls', results=records))
    packet = out/'causal_pilot/native_control_reviews/e00.json'
    write_json(packet, dict(entry_id=entry['id'], status='REVIEWED_NATIVE_CONTROL_BANK',
        causal_or_passive_scores_used=False, run_directory=str(run), conditions=reviews,
        signature_sha256=sha(run/'signature.json'), summary_sha256=sha(run/'run_summary.json')))
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    def stage_path(name, subdirectory):
        path = Path(name).resolve()
        if not path.is_relative_to(out/subdirectory): raise ValueError('Outside active stage')
        return path
    monkeypatch.setattr(module, 'stage_path', stage_path)
    monkeypatch.setattr(module, 'load_prior_controls', lambda e: (variants, provenance))
    def check_input(entry, native, row, changed):
        assert changed['event_id'] == row['event_id'] and changed['condition'] == row['condition']
    monkeypatch.setattr(module, 'verify_fixed_input', check_input)
    return entry, packet, run, out


def test_full_artifacts_can_supply_reviewed_gate(monkeypatch, tmp_path):
    entry, packet, _, _ = artifact_fixture(monkeypatch, tmp_path)
    evidence = module.load_native_convergence(entry, dict(path=str(packet), sha256=sha(packet)))
    assert evidence['available'] and evidence['converges']
    assert evidence['fixed_prefix_scores_used'] is False and evidence['causal_state'] is None


@pytest.mark.parametrize('change', ['packet_hash', 'generation_hash', 'tokens_hash', 'summary_hash',
    'wrong_entry', 'changed_bank', 'missing_condition', 'wrong_protocol', 'wrapper_failed',
    'wrong_dtype', 'wrong_mechanics', 'missing_summary_result', 'outside'])
def test_corrupt_control_artifacts_cannot_certify_convergence(monkeypatch, tmp_path, change):
    entry, packet, run, out = artifact_fixture(monkeypatch, tmp_path)
    packet_data = read_json(packet)
    if change == 'packet_hash':
        with pytest.raises(ValueError): module.load_native_convergence(entry, dict(path=str(packet), sha256='bad'))
        return
    if change == 'outside':
        with pytest.raises(ValueError): module.load_native_convergence(entry, dict(path=str(run/'signature.json'), sha256='bad'))
        return
    if change == 'wrong_entry': entry['id'] = 'other'
    if change in ('generation_hash', 'tokens_hash'):
        path = run/'examples'/entry['id']/'mask'/('generation.json' if change == 'generation_hash' else 'tokens.jsonl')
        path.write_text(path.read_text()+'\n')
    if change == 'summary_hash': (run/'run_summary.json').write_text('{}')
    if change == 'missing_condition': del packet_data['conditions']['mask']
    if change in ('changed_bank', 'wrong_protocol'):
        signature = read_json(run/'signature.json')
        if change == 'changed_bank': signature['control_rows'][entry['id']]['fixed_mask']['event_id'] = 'other'
        else: signature['generation_protocol']['max_new_tokens'] = 128
        write_json(run/'signature.json', signature)
        packet_data['signature_sha256'] = sha(run/'signature.json')
    if change == 'wrapper_failed':
        write_json(out/'causal_pilot/wrappers/run01.json', dict(completed=False, exit_code=1, slurm_job_id='existing'))
    if change == 'wrong_dtype':
        write_json(run/'environment.json', dict(parameter_dtype='torch.float32', slurm_job_id='existing'))
    if change == 'wrong_mechanics': write_json(out/'causal_pilot/mechanics/bench.json', {'status': 'CPU_ONLY'})
    if change == 'missing_summary_result':
        summary = read_json(run/'run_summary.json'); summary['results'].pop(0)
        write_json(run/'run_summary.json', summary); packet_data['summary_sha256'] = sha(run/'run_summary.json')
    write_json(packet, packet_data)
    with pytest.raises(ValueError): module.load_native_convergence(entry, dict(path=str(packet), sha256=sha(packet)))
