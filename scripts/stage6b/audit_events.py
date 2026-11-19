"""Inspect phase-specific saved controls before permitting primary inference."""
import argparse
from scripts.stage6b.common import ROOT, OUT, read_json, sha, write_json


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--run-id',required=True);p.add_argument('--audit-tag',required=True)
    args=p.parse_args();rows=[];sites=0
    for rank in range(2):
        shard=OUT/'raw'/args.run_id/f'shard_{rank:02d}'
        sig=read_json(shard/'signature.json');summary=read_json(shard/'run_summary.json')
        assert summary['completed'] and sig['mechanics'] and sig['split']=='discovery'
        assert sig['rank']==rank and sig['world_size']==2 and sig['slurm_job_id']=='110860'
        assert sig['node']=='node03' and sig['audit_tag']==args.audit_tag
        for path,h in sig['code_sha256'].items():assert sha(ROOT/path)==h,path
        for eid in sig['event_ids']:
            row=read_json(shard/(eid+'.json'));rows.append(row)
            assert all(row['checks'].values())
            if row['condition']=='no_image':
                assert row['prefill_audit']['visual_tokens']==0
                assert row['prefill_audit']['implicit_position_replay']['passed']
                assert 'visual' not in row['passive']['telemetry']['28']['groups']
                assert not any(k.endswith(('W2','W8')) for k in row['arms'])
            for name,arm in row['arms'].items():
                assert arm['finite']
                if name=='unhooked':continue
                assert arm['clone_no_alias'] and arm['past_cache_audit']['passed']
                assert len(arm['step_audits'])==8
                assert all(s['layers']==list(range(36)) and s['finite'] for s in arm['step_audits'])
                for a in arm['source_audits']:
                    sites+=1
                    assert a['selected_heads']==list(range(32))
                    assert all(a[k] for k in ('query_exact','key_exact','value_exact','attention_exact',
                        'explicit_source_reference_exact','all_outputs_finite','lambda_one_exact','lambda_zero_exact'))
                    assert not a['qkv_directly_modified'] and not a['attention_directly_modified']
                    assert a['selected_head_expected_max_abs_error']==a['outside_window_max_abs_delta']==0
            assert (shard/(eid+'_distribution.npz')).is_file()
    assert len({r['base_id'] for r in rows})==2
    write_json(OUT/'audit'/f'{args.audit_tag}_mechanics.json',{
        'status':'PASS','run_id':args.run_id,'events':len(rows),'discovery_bases':2,
        'conditions':sorted({r['condition'] for r in rows}),'validated_source_layer_sites':sites,
        'devices':2,'all_saved_controls_exact':True,'code_sha256':sig['code_sha256'],
        'measured_device_seconds':sum(r['runtime_seconds'] for r in rows)},freeze=True)
    print(f'{args.audit_tag}: PASS {len(rows)} events, {sites} source-layer controls')


if __name__=='__main__':main()
