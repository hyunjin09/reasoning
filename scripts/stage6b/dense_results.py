"""Verified dense artifact joins and a fixed common passive vector."""
from scripts.stage6b.common import ROOT,OUT,read_json,read_jsonl,sha
from scripts.stage6b.event_results import feature_values


def load_dense(run_id,manifest_path):
    entries={r['id']:r for r in read_jsonl(manifest_path)};seen=set()
    for rank in range(2):
        shard=OUT/'raw'/run_id/f'shard_{rank:02d}';sig=read_json(shard/'signature.json')
        assert read_json(shard/'run_summary.json')['completed'] and not sig['mechanics']
        assert sig['manifest_sha256']==sha(manifest_path)
        for path,h in sig['code_sha256'].items():assert sha(ROOT/path)==h,path
        for eid in sig['event_ids']:
            assert eid in entries and eid not in seen;seen.add(eid)
            r=read_json(shard/(eid+'.json'));e=entries[eid]
            assert all(r['checks'].values())
            assert {x['id'] for x in r['endpoints']}=={x['id'] for x in e['spans']}
            yield e,r
    assert seen==set(entries)


def passive_vector(passive):
    record={'passive':passive};telemetry=passive['telemetry'];groups=telemetry['28']['groups']
    sources={g:feature_values(record,g) for g in groups if g not in ['visual','sink','prompt_text','reasoning']}
    target=feature_values(record,'T')
    values={'T_'+k:target[k] for k in ['attention_density','visual_attention_share','qk_cosine','scaled_logit','alpha_v_norm','post_wo_norm']}
    values.update(visual_attention_mass=feature_values(record,'visual')['attention_mass'],
        sink_attention_mass=feature_values(record,'sink')['attention_mass'],predictive_entropy=passive['predictive_entropy'],
        residual_norm_28=passive['residual_norms']['28'],residual_norm_29=passive['residual_norms']['29'])
    return values,sources
