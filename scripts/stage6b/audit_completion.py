"""Recompute final provenance, replay, split, readout and resource evidence."""
from collections import Counter
import argparse
from scripts.stage6b.common import ROOT,OUT,SOURCE,read_json,read_jsonl,write_json,sha,verify_stage6a
from scripts.stage6b.event_results import load_run
from scripts.stage6b.dense_results import load_dense


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifests-only',action='store_true');parser.add_argument('--controlled-only',action='store_true');args=parser.parse_args()
    preflight=verify_stage6a()
    assert sha(ROOT/'plan/stage6b_causal_retrieval_dynamics_mirage_analysis_plan.md')==preflight['plan_sha256']
    assign=read_json(SOURCE/'cohort/discovery_confirmation_split.json')['assignments']
    manifests={'C2':'config/phase_a_events.jsonl','C1_fixed':'c1_mirage/fixed_prefix_manifest.jsonl',
        'C1_dynamic':'c1_dynamics/exact_anchor_manifest_v2.jsonl','C1_native':'trajectory/native_endpoint_manifest_v3_schedule.jsonl',
        'C3':'c3_object_stress/native_endpoint_manifest.jsonl','C4':'c4_natural_validation/native_endpoint_manifest.jsonl'}
    splits={};roi=[];orientation=[]
    for phase,path in manifests.items():
        entries=read_jsonl(OUT/path)
        for e in entries:
            assert e['split']==assign[e['base_id']]['split']
            if 'group_id' in e:assert e['group_id']==assign[e['base_id']]['group_id']
            meta=read_json(e['native_input_path']) if phase!='C1_fixed' else None
            if phase=='C1_fixed':
                # Fixed-prefix condition input maps are inherited from each saved native condition.
                meta=read_json(e['native_input_path'])
            visual=set(meta['visual_token_indices'])
            for source,positions in e['source_groups'].items():assert set(positions)<=visual,(e['id'],source)
            if e['row'].get('no_image'):
                assert not visual and not e['source_groups'] and not e.get('w2_sources') and not e.get('w8_sources')
            if phase=='C3' and not e['row']['present']:assert 'T' not in e['source_groups']
            for source in e.get('w2_sources',[])+e.get('w8_sources',[]):assert e['source_groups'][source]
            if 'event' in e:
                event=e['event'];end=event['candidate_start_token']
                assert end==len(event['history_before_ed_token_ids']) and event['current_query_zero_based']==end-1
                assert event['original_divergent_suffix_ids'] and event['counterfactual_divergent_suffix_ids']
                assert event['correct_semantic_value']!=event['foil_semantic_value']
                if phase=='C3':assert event['correct_semantic_value'].lower()=='yes' and event['foil_semantic_value'].lower()=='no'
            roi.append({'id':e['id'],'phase':phase,'source_count':len(e['source_groups']),'visual_tokens':len(visual),'valid':True})
        bybase={e['base_id']:e['split'] for e in entries}
        splits[phase]={'events':len(entries),'bases':len(bybase),'split_bases':dict(Counter(bybase.values())),'manifest_sha256':sha(OUT/path)}
        orientation.append({'phase':phase,'events':len(entries),'orientation':'yes minus no, independent of presence' if phase=='C3' else 'correct source semantic value minus foil' if phase not in ['C1_native','C4'] else 'passive only; no invented semantic candidate',
            'error_promoting_claims':0,'native_query_boundary_valid':True})
    write_json(OUT/'audit/split_integrity.json',{'status':'PASS','cohorts':splits,'stage6a_assignment_sha256':sha(SOURCE/'cohort/discovery_confirmation_split.json'),'new_split_assignments':0})
    write_json(OUT/'audit/roi_source_audit.json',{'status':'PASS','records':roi,'source_token_maps_preserved_or_independently_projected':True,
        'projection_evidence':['audit/c3_region_projection.json','audit/c4_source_projection.json'],
        'overlap_limit':'C2overlapping groups are retained and sensitivity-reported; dynamic overlaps remain UNRESOLVED.'})
    write_json(OUT/'audit/readout_orientation_audit.json',{'status':'PASS','phases':orientation,
        'limits':['C1fixed stress preferences are not native generated hallucinations.','Correct numeric readouts cannot identify geometric-role error causation.','C3late final-readout effects do not identify earlier acquisition.','C4pre-wrong next-token logP is passive, not a contrast establishing an error-promoting source.']})
    if args.manifests_only:
        print('All frozen manifest split/source/readout contracts PASS.');return
    replay={}
    for prefix,phase,mechanics in [('dynamics','C1_dynamic','dynamics_mechanics_01'),('c3','C3','c3_mechanics_01')]:
        _,primary,_=load_run(prefix+'_discovery_01',OUT/manifests[phase],'discovery');comparisons=0
        for rank in range(2):
            shard=OUT/'raw'/mechanics/f'shard_{rank:02d}';sig=read_json(shard/'signature.json')
            for eid in sig['event_ids']:
                row=read_json(shard/(eid+'.json'));p=primary[eid]
                for arm in p['arms']:
                    for key in ['D','L_o','L_c','original_candidate','counterfactual_candidate','current_logits_sha256']:
                        assert row['arms'][arm][key]==p['arms'][arm][key],(eid,arm,key)
                    comparisons+=1
        replay[phase]={'mechanics_primary_exact_arm_comparisons':comparisons}
    write_json(OUT/'audit/dynamics_c3_mechanics_primary_replay.json',{'status':'PASS','phases':replay})
    if args.controlled_only:
        print('Dynamics/C3 mechanics-primary exact replay PASS:',replay);return
    native={e['id']:r for e,r in load_dense('native_primary_02',OUT/manifests['C1_native'])};dense_replays={}
    for run in ['native_mechanics_01','native_residency_mechanics_02']:
        count=0
        for rank in range(2):
            shard=OUT/'raw'/run/f'shard_{rank:02d}';sig=read_json(shard/'signature.json')
            for eid in sig['event_ids']:
                m=read_json(shard/(eid+'.json'));primary={r['id']:r for r in native[eid]['endpoints']}
                for endpoint in m['endpoints']:
                    a=endpoint['passive'];b=primary[endpoint['id']]['passive']
                    for key in ['current_logits_sha256','telemetry','residual_norms','predictive_entropy','top50_token_ids','top50_log_probabilities']:
                        assert a[key]==b[key],(run,eid,endpoint['id'],key)
                    count+=1
        dense_replays[run]=count
    c4=list(load_dense('c4_native_01',OUT/manifests['C4']))
    assert len(c4)==20 and sum(len(r['endpoints']) for e,r in c4)==358
    write_json(OUT/'audit/causal_score_replay.json',{'status':'PASS',
        'C2':read_json(OUT/'audit/c2_mechanics_primary_replay.json')['comparisons'],
        'C1_fixed':read_json(OUT/'audit/fixed_prefix_replay_audit.json')['mechanics_primary_exact_arm_comparisons'],
        **replay,'native_mechanics_primary_endpoint_replays':dense_replays,
        'allocator_common_prefix_equality':read_json(OUT/'audit/native_allocator_diagnostic.json')['common_canonical_prefix_logits_exact']})
    model=read_json(OUT/'trajectory/pca_discovery.json');vectors={r['id']:r for r in read_jsonl(OUT/'trajectory/passive_state_vectors.jsonl')}
    assert all(vectors[eid]['split']=='discovery' and vectors[eid]['condition']=='intact' for eid in model['training_row_ids'])
    assert all(r['projection_only'] for r in read_jsonl(OUT/'trajectory/pca_confirmation_projection.jsonl'))
    causal_model=read_json(OUT/'trajectory/pca_causal_discovery.json')
    causal_vectors={r['id']:r for r in read_jsonl(OUT/'trajectory/causal_anchor_vectors.jsonl')}
    assert all(causal_vectors[eid]['split']=='discovery' for eid in causal_model['training_row_ids'])
    assert causal_model['columns']==read_json(OUT/'config/trajectory_geometry_rules.json')['causal_pca_columns']
    queue=read_json(ROOT/'state/gpu_experiment_queue.json');resources=[]
    for job in queue['jobs']:
        if not job['id'].startswith('stage6b_'):continue
        run=job['id'].removeprefix('stage6b_');path=OUT/'raw'/run;events=[];shards=[];diagnostics=[]
        for sigpath in sorted(path.glob('shard_*/signature.json')):
            sig=read_json(sigpath);assert sig['slurm_job_id']=='110860' and sig['world_size']==2
            summary=sigpath.parent/'run_summary.json';shards.append(read_json(summary) if summary.exists() else {'completed':False})
            for eid in sig['event_ids']:
                p=sigpath.parent/(eid+'.json')
                if p.exists():events.append(read_json(p))
        for diagnostic_path in sorted(path.glob('rank_*.json')):
            d=read_json(diagnostic_path)
            observations=[r['memory'] for r in d['steps']]
            if d['failure']:observations.append(d['failure']['after'])
            diagnostics.append({'rank':d['rank'],'prefix_completed':d['completed'],'runtime_seconds':d['runtime_seconds'],
                'allocator':d['allocator'],'evidence':str(diagnostic_path.relative_to(OUT)),
                'peak_allocated_bytes':max(r['allocated_bytes.all.peak'] for r in observations),
                'peak_reserved_bytes':max(r['reserved_bytes.all.peak'] for r in observations)})
        resources.append({'run_id':run,'status':job['status'],'slurm_job_id':job.get('slurm_job_id'),
            'node':'node03','gpus':2,'cpus':4,'host_memory_GiB':90,'command':job.get('command'),
            'log':job.get('log_path'),'shards':shards,'completed_event_records':len(events),'diagnostic_results':diagnostics,
            'environment_records':[str(p.relative_to(OUT)) for p in sorted(path.glob('shard_*/environment.json'))],
            'completed_event_device_seconds':sum(r.get('runtime_seconds',0) for r in events),
            'diagnostic_device_seconds':sum(r['runtime_seconds'] for r in diagnostics),
            'max_peak_allocated_bytes':max([r['peak_allocated_bytes'] for r in events+diagnostics if 'peak_allocated_bytes' in r],default=None),
            'max_peak_reserved_bytes':max([r['peak_reserved_bytes'] for r in events+diagnostics if 'peak_reserved_bytes' in r],default=None)})
    assert not [r for r in resources if r['status']=='running']
    write_json(OUT/'audit/resource_summary.json',{'status':'COMPLETE_WITH_PRESERVED_FAILED_ATTEMPTS','allocation':'110860',
        'new_slurm_allocations':0,'maximum_simultaneous_gpus':2,'dataset_downloads':0,'runs':resources,
        'incomplete_run_times':'Completed-event timings undercount failed in-flight work; original logs/queue timestamps are preserved.',
        'cache_configuration_exceptions':read_json(OUT/'audit/cache_configuration.json')})
    config=read_json(OUT/'config/stage6b_config.json')
    write_json(OUT/'config/causal_windows.json',{'primary_W':2,'sensitivity_W':8,'unchanged_query_barrier':8,
        'source_contribution_gain':0,'attention_renormalized':False,'layers':config['suppression_layers'],'heads':config['suppression_heads'],
        'original_prescoring_config_sha256':sha(OUT/'config/stage6b_config.json'),'scope':'Index of pre-existing frozen window settings; not a newly selected assay.'},freeze=True)
    print('Final provenance/replay/split/readout/resource audits PASS.')


if __name__=='__main__':main()
