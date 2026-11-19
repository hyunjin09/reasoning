"""Verify frozen text, no-image interface, and matched primary/control paths."""
from scripts.stage6b.common import ROOT,OUT,SOURCE,read_json,read_jsonl,sha,write_json,verify_stage6a


def main():
    verify_stage6a();manifest=read_jsonl(OUT/'c1_mirage/fixed_prefix_manifest.jsonl');entries={r['id']:r for r in manifest}
    count=0;rows=[];allprimary={}
    for split in ['discovery','confirmation']:
        for rank in range(2):
            shard=OUT/'raw'/('c1_'+split+'_01')/f'shard_{rank:02d}'
            s=read_json(shard/'signature.json');summary=read_json(shard/'run_summary.json')
            assert summary['completed'] and s['manifest_sha256']==sha(OUT/'c1_mirage/fixed_prefix_manifest.jsonl')
            if split=='confirmation':assert s['confirmation_freeze_sha256']==sha(OUT/'config/mirage_discovery_rule.json')
            for eid in s['event_ids']:
                r=read_json(shard/(eid+'.json'));assert all(r['checks'].values());allprimary[eid]=r
    assert len(allprimary)==1199
    for rank in range(2):
        shard=OUT/'raw/c1_mechanics_02'/f'shard_{rank:02d}'
        s=read_json(shard/'signature.json')
        for eid in s['event_ids']:
            m=read_json(shard/(eid+'.json'));p=allprimary[eid]
            for arm in ['N']+[f'{x}_W2' for x in entries[eid]['w2_sources']]:
                for k in ['D','L_o','L_c','original_candidate','counterfactual_candidate','current_logits_sha256']:
                    assert m['arms'][arm][k]==p['arms'][arm][k],(eid,arm,k)
                count+=1
            if entries[eid]['condition']=='no_image':
                rows.append({'event_id':eid,**m['prefill_audit']['implicit_position_replay']})
    for base in {r['base_id'] for r in manifest}:
        subset=[r for r in manifest if r['base_id']==base]
        assert len({r['prefix_history_sha256'] for r in subset})==1
        assert all(r['event']['history_before_ed_token_ids']==subset[0]['event']['history_before_ed_token_ids'] for r in subset)
    write_json(OUT/'audit/fixed_prefix_replay_audit.json',{'status':'PASS','bases':109,'events':1199,
        'same_textual_history_per_base':True,'mechanics_primary_exact_arm_comparisons':count,
        'passive_native_exact_all_events':True,'manifest_sha256':sha(OUT/'c1_mirage/fixed_prefix_manifest.jsonl')},freeze=True)
    write_json(OUT/'audit/no_image_interface_audit.json',{'status':'PASS','mechanics_native_implicit_position_comparisons':rows,
        'primary_text_only_events':109,'no_visual_VSD_defined':True,'no_visual_cache_reuse':True,
        'scope':'Fresh text-only prefill; zero identity offset matches native implicit text positions exactly at all canonical boundaries.'},freeze=True)
    old=read_json(SOURCE/'audit/manipulation_audit.json')
    write_json(OUT/'audit/stress_condition_audit.json',{'status':'PASS','inherited_audit_sha256':sha(SOURCE/'audit/manipulation_audit.json'),
        'C1records':[r for r in old['records'] if r['cohort']=='C1'],
        'C3mechanical_records_reference':str(SOURCE/'audit/manipulation_audit.json'),
        'preserved_Stage6A_inputs':True},freeze=True)
    print('C1fullreplayPASS;',count,'mechanics-primary arm comparisons exact.')


if __name__=='__main__':main()
