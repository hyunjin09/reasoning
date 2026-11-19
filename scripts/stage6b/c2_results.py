"""Deterministic C2 result joins; no cohort or threshold selection by effects."""
from scripts.stage6b.common import ROOT, OUT, read_json, read_jsonl, sha


def load_complete_run(run_id, split):
    manifest = {r['id']:r for r in read_jsonl(OUT/'config/phase_a_events.jsonl') if r['split']==split}
    result = {}
    for rank in range(2):
        shard = OUT/'raw'/run_id/f'shard_{rank:02d}'
        signature = read_json(shard/'signature.json')
        summary = read_json(shard/'run_summary.json')
        assert summary['completed'] and signature['split']==split
        assert signature['manifest_sha256']==sha(OUT/'config/phase_a_events.jsonl')
        assert signature['config_sha256']==sha(OUT/'config/stage6b_config.json')
        for p,h in signature['code_sha256'].items():
            assert sha(ROOT/p)==h, p
        for eid in signature['event_ids']:
            assert eid in manifest and eid not in result
            row=read_json(shard/(eid+'.json'))
            assert row['id']==eid and all(row['checks'].values())
            result[eid]=row
    assert set(result)==set(manifest)
    return manifest,result


def features(row, source='T'):
    keys=['attention_density','attention_mass','qk_cosine','scaled_logit','alpha_v_norm','post_wo_norm','visual_attention_share']
    return {name:sum(row['passive']['telemetry'][str(layer)]['groups'][source]['mean_'+name]
                     for layer in [28,29])/2 for name in keys}


def flatten(entry, result):
    native=read_json(entry['native_generation_path'])
    length=int(native['generated_token_count'])
    return {'id':entry['id'],'base_id':entry['base_id'],'condition':entry['condition'],
        'split':entry['split'],'group_id':entry['group_id'],'roles':entry['roles'],
        'focal_features':features(result,'T'),'other_features':features(result,'X'),
        'vsd':{source:{str(w):result['arms']['N']['D']-result['arms'][source+f'_W{w}']['D'] for w in [2,8]} for source in ['T','X']},
        'native_D':result['arms']['N']['D'],'correct_logP':result['arms']['N']['L_o'],
        'foil_logP':result['arms']['N']['L_c'],
        'normalized_progress':entry['event']['candidate_start_token']/max(1,length),
        'correct_candidate_tokens':len(entry['event']['original_divergent_suffix_ids']),
        'focal_roi_tokens':len(entry['source_groups']['T']),
        'local_correctness':entry['event']['reviewed_claim']['local_visual_correctness'],
        'final_correctness':entry['final_correctness']}
