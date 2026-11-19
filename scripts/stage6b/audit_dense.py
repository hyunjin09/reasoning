"""Accept optimized passive replay only after equality with fresh canonical roots."""
import argparse
from scripts.stage6b.common import ROOT,OUT,read_json,sha,write_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--audit-file',default='native_dense_mechanics.json');args=p.parse_args();count=0;root_count=0;events=0;maxprefix=0
    for rank in range(2):
        shard=OUT/'raw'/args.run_id/f'shard_{rank:02d}'
        sig=read_json(shard/'signature.json');summary=read_json(shard/'run_summary.json')
        assert summary['completed'] and sig['mechanics'] and sig['split']=='discovery'
        assert sig['rank']==rank and sig['world_size']==2 and sig['slurm_job_id']=='110860' and sig['node']=='node03'
        for path,h in sig['code_sha256'].items():assert sha(ROOT/path)==h,path
        for eid in sig['event_ids']:
            r=read_json(shard/(eid+'.json'));events+=1
            assert all(r['checks'].values())
            assert len(r['fresh_root_mechanics'])==len(r['endpoints'])
            for c in r['fresh_root_mechanics']:
                assert c['fresh_canonical_root_exact'];root_count+=1;maxprefix=max(maxprefix,c['checkpoint_length'])
            for endpoint in r['endpoints']:
                passive=endpoint['passive'];count+=1
                assert passive['native_passive_logits_exact'] and passive['mechanics_all_kv_exact']
                assert set(passive['telemetry'])=={'28','29'}
    assert maxprefix>=2048,'Mechanics must exercise actual chunk reuse'
    write_json(OUT/'audit'/args.audit_file,{'status':'PASS','run_id':args.run_id,'events':events,
        'native_endpoints':count,'fresh_canonical_root_equalities':root_count,'maximum_reused_prefix':maxprefix,
        'all_passive_logits_and_KV_exact':True,'devices':2,'code_sha256':sig['code_sha256'],
        'scope':'Full2048chunk reuse with exact original partialchunk and8single-query barriers; no candidate imputation.'},freeze=True)
    print('Dense canonical replay PASS:',count,'endpoints,',maxprefix,'reused prefix tokens.')


if __name__=='__main__':main()
