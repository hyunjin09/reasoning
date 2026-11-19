"""Independently inspect saved canonical controls before primary scoring."""
from scripts.stage6b.common import ROOT, OUT, read_json, read_jsonl, sha, write_json


def main():
    directory = OUT/'raw/c2_mechanics_01'
    signatures = [read_json(directory/f'shard_{rank:02d}/signature.json') for rank in range(2)]
    rows = []
    source_sites = 0
    for rank, signature in enumerate(signatures):
        shard = directory/f'shard_{rank:02d}'
        assert signature['rank']==rank and signature['world_size']==2
        assert signature['slurm_job_id']=='110860' and signature['node']=='node03'
        assert signature['mechanics'] and signature['split']=='discovery'
        for path, expected in signature['code_sha256'].items():
            assert sha(ROOT/path)==expected, path
        summary = read_json(shard/'run_summary.json')
        assert summary['completed'] and summary['expected_events']==4
        env = read_json(shard/'environment.json')
        assert env['dtype']=='torch.bfloat16' and 'A6000' in env['gpu_name']
        for eid in signature['event_ids']:
            row = read_json(shard/(eid+'.json')); rows.append(row)
            assert all(row['checks'].values()) and row['split']=='discovery'
            native = row['arms']['N']
            for other in [row['arms']['noop_W8'],row['arms']['unhooked'],row['passive']]:
                for key in ('D','L_o','L_c','current_logits_sha256','original_candidate','counterfactual_candidate'):
                    assert native[key]==other[key], (eid,key)
            assert row['arms']['T_W2']==row['arms']['replay_W2']
            for name, arm in row['arms'].items():
                assert arm['finite']
                if name=='unhooked':continue
                assert arm['clone_no_alias']
                assert arm['past_cache_audit']['passed']
                assert len(arm['step_audits'])==8
                assert all(step['layers']==list(range(36)) and step['finite'] for step in arm['step_audits'])
                if '_W' in name and name!='noop_W8':
                    width=8 if name.endswith('W8') else 2
                    assert len(arm['source_audits'])==36*width
                for audit in arm['source_audits']:
                    source_sites+=1
                    assert audit['selected_heads']==list(range(32))
                    assert all(audit[k] for k in ('query_exact','key_exact','value_exact','attention_exact',
                        'explicit_source_reference_exact','all_outputs_finite','lambda_one_exact','lambda_zero_exact'))
                    assert not audit['qkv_directly_modified'] and not audit['attention_directly_modified']
                    assert audit['selected_head_expected_max_abs_error']==0
                    assert audit['outside_window_max_abs_delta']==0
            assert (shard/(eid+'_distribution.npz')).is_file()
    assert len(rows)==8 and len({r['base_id'] for r in rows})==2
    report = {'status':'PASS','run_id':'c2_mechanics_01','events':8,'discovery_families':2,
        'devices':2,'slurm_job_id':'110860','canonical_dtype':'bfloat16',
        'all_controls_exact':True,'validated_source_layer_sites':source_sites,
        'validated_code_sha256':signatures[0]['code_sha256'],
        'max_peak_allocated_bytes':max(r['peak_gpu_allocated_bytes'] for r in rows),
        'max_peak_reserved_bytes':max(r['peak_gpu_reserved_bytes'] for r in rows),
        'measured_event_device_seconds':sum(r['runtime_seconds'] for r in rows),
        'scope':'C2 image source W2/W8, native/no-op/unhooked/repeated suppression and unmodified passive replay. C1 stress/no-image interfaces require their later specific audits.',
        'selection':'First two frozen discovery families; no confirmation effects inspected.'}
    write_json(OUT/'audit/canonical_path_audit.json',report,freeze=True)
    print('Canonical C2 path PASS on both GPUs: 8 events, '+str(source_sites)+' source-layer sites')


if __name__=='__main__':
    main()
