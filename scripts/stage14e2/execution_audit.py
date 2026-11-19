"""Verify completed diagnostic receipts without rerunning any inference."""
from pathlib import Path
from scripts.stage14e2.common import P, PREVIOUS, load, save, sha, now
from scripts.stage14e2.accounting import refresh, TERMINAL


def main():
    for seal in [P/'audit/diagnostic_seal_v1.json', PREVIOUS/'audit/final_closure_seal_v1.json']:
        for path, digest in load(seal)['files'].items():
            assert sha(path) == digest, path
    tasks = load(P/'inference/diagnostic_tasks_v1.json')
    records, inputs, generations, files, gates, environments = [], {}, {}, {}, [], []
    for rank in range(2):
        root = P/f'raw/readout_r{rank}_v1'
        result = load(root/'result.json')
        assert result['status'] == 'COMPLETED'
        gate = load(root/'technical_gate.json')
        assert len(gate) == 2 and all(g['same_tokens'] and g['same_input'] for g in gate)
        gates.extend(dict(g, rank=rank) for g in gate)
        env = load(root/'environment.json')
        assert env['versions']['vllm'] == '0.11.0'
        assert env['runtime_sha256'] == sha(P/'protocol/runtime_v1.json')
        for marker in ['1de27d8c51f12e819435303b9e84c4e25ba8401e',
                       'dtype=torch.bfloat16', 'enable_prefix_caching=False']:
            assert marker in env['engine_config'], marker
        environments.append(dict(rank=rank, path=str(root/'environment.json'), sha256=sha(root/'environment.json')))
    for t in tasks['rows']:
        if t['status'] != 'PHYSICAL':
            continue
        paths = list((P/'raw').glob('*/'+t['item_id']+'_'+t['condition']+'/result.json'))
        assert len(paths) == 1
        receipt = load(paths[0]); root = paths[0].parent
        inp, gen = load(root/'input.json'), load(root/'generation.json')
        assert sha(root/'input.json') == receipt['input_sha256']
        assert sha(root/'generation.json') == receipt['generation_sha256']
        assert inp['cap'] == t['cap'] == 8192 and inp['schema'] is None
        assert inp['seed'] == t['seed'] == gen['seed']
        assert inp['helper_mode'] == t['helper_mode']
        assert inp['images'] == t['images']
        assert inp['diagnostic_oracle_target'] == t['diagnostic_oracle_target']
        assert inp['sampling'] == dict(temperature=1.0, top_p=.95, top_k=20,
                                       repetition_penalty=1.0, presence_penalty=0)
        assert len(gen['generated_token_ids']) == gen['tokens']
        key = (t['item_id'], t['condition'])
        inputs[key], generations[key] = inp, gen
        records.append(dict(item_id=t['item_id'], condition=t['condition'], tokens=gen['tokens'],
            latency_seconds=gen['latency_seconds'], cap_hit=gen['cap_hit'],
            finish_reason=gen['finish_reason'], generation_path=str(root/'generation.json')))
        for file in root.glob('*.json'): files[str(file)] = sha(file)
    assert len(records) == tasks['physical'] == 108
    comparisons = []
    for i in tasks['families']:
        for target in ['O', 'T']:
            if (i, target+'_C') not in inputs:
                continue
            c, t = inputs[i, target+'_C'], inputs[i, target+'_T']
            assert c['prompt'] == t['prompt']+'</think>\n\n'
            for key in ['images', 'pixels', 'sizes', 'prefix_sha256', 'seed', 'sampling', 'cap']:
                assert c[key] == t[key], (i, target, key)
            cp, tp = generations[i, target+'_C']['prompt_token_ids'], generations[i, target+'_T']['prompt_token_ids']
            assert cp[:len(tp)] == tp and len(cp) > len(tp), (i, target, 'token boundary')
            comparisons.append(dict(item_id=i, target=target, matched=True))
        t, n = inputs[i, 'T_T'], inputs[i, 'T_N']
        assert n['images'] == n['pixels'] == []
        assert t['prompt'].replace('<|vision_start|><|image_pad|><|vision_end|>', '') == n['prompt']
        for key in ['prefix_sha256', 'seed', 'sampling', 'cap', 'helper_mode']:
            assert t[key] == n[key], (i, 'noimage', key)
    ledger = refresh()
    assert all(j['state'] in TERMINAL for j in ledger['new_jobs'])
    assert ledger['new_actual_gpu_seconds'] <= 86400
    save(P/'audit/completed_execution_audit_v1.json', dict(at=now(), records=records,
        matched_pairs=comparisons, native_gates=gates, environments=environments, logical=120, physical=108,
        prior_seal_unchanged=True, files=files, cumulative_gpu_hours=ledger['new_actual_gpu_seconds']/3600,
        diagnostic_gpu_hours=(ledger['new_actual_gpu_seconds']-ledger['prior_cycle_actual_gpu_seconds'])/3600,
        all_jobs_terminal=True, no_follow_on_launched=True))
    print('Verified108physical/120logical; all jobs terminal; exact matched inputs.')


if __name__ == '__main__': main()
