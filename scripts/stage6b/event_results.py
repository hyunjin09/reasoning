"""Checked result joins for the later frozen Stage6B manifests."""
from scripts.stage6b.common import ROOT,OUT,read_json,read_jsonl,sha


def load_run(run_id,manifest_path,split):
    entries={r['id']:r for r in read_jsonl(manifest_path) if r['split']==split}
    results={};paths={}
    for rank in range(2):
        shard=OUT/'raw'/run_id/f'shard_{rank:02d}'
        sig=read_json(shard/'signature.json');summary=read_json(shard/'run_summary.json')
        assert summary['completed'] and not sig['mechanics'] and sig['split']==split
        assert sig['manifest_sha256']==sha(manifest_path)
        assert sig['config_sha256']==sha(OUT/'config/stage6b_config.json')
        for p,h in sig['code_sha256'].items():assert sha(ROOT/p)==h,p
        for eid in sig['event_ids']:
            assert eid in entries and eid not in results
            row=read_json(shard/(eid+'.json'))
            assert all(row['checks'].values())
            results[eid]=row;paths[eid]=shard/(eid+'_distribution.npz')
    assert set(entries)==set(results)
    return entries,results,paths


def feature_values(result,source):
    names=['attention_density','attention_mass','qk_cosine','scaled_logit','alpha_v_norm','post_wo_norm','visual_attention_share']
    telemetry=result['passive']['telemetry']
    if source not in telemetry['28']['groups']:return {k:None for k in names}
    return {k:sum(telemetry[str(layer)]['groups'][source].get('mean_'+k,0.) for layer in [28,29])/2 for k in names}


def distribution_similarity(a,b):
    import numpy as np
    # Full raw next-token distributions, stable JS in natural logarithms.
    a=np.asarray(a,dtype=np.float64);b=np.asarray(b,dtype=np.float64)
    a-=np.logaddexp.reduce(a);b-=np.logaddexp.reduce(b)
    mixture=np.logaddexp(a,b)-np.log(2.)
    js=float(.5*np.sum(np.exp(a)*(a-mixture))+.5*np.sum(np.exp(b)*(b-mixture)))
    k=50
    overlap=len(set(np.argpartition(a,-k)[-k:])&set(np.argpartition(b,-k)[-k:]))/k
    return {'js_divergence':js,'top50_overlap':overlap}
