"""Verify completed census provenance, denominators, blinding order and stop boundary."""
import os
from datetime import datetime
from collections import Counter
import pandas as pd
from scripts.stage10b.common import ROOT,load,save,sha,now
from scripts.stage10b.protocol import decision


def main():
    assert os.environ.get('SLURM_JOB_ID')
    corpus=load(ROOT/'stage10b_corpus_manifest.json');rows=corpus['rows'];ids={r['trajectory_id'] for r in rows if r['eligible']}
    assert len(rows)==len(ids)==224 and Counter(r['dataset'] for r in rows)=={'MathVision':128,'MathVerse':96}
    assert len({r['family_id'] for r in rows})==224 and all(r['duplicate_of'] is None for r in rows)
    source_count=0
    for r in rows:
        for p,h in r['source_sha256'].items():assert sha(p)==h,p;source_count+=1
        assert sha(r['packet_path'])==r['packet_sha256'] and sha(r['image'])==r['image_sha256']
    ip=ROOT/'audit/semantic_independent_passes_frozen.json';sp=ROOT/'audit/semantic_adjudication_frozen.json'
    independent=load(ip);semantic=load(sp);historical=load(ROOT/'audit/reaccess_historical.json')
    assert semantic['sealed'] and not semantic['routing_opened'] and semantic['independent_passes_sha256']==sha(ip)
    assert all(set(v)==ids for v in independent['reviews'].values())
    for p,h in independent['annotation_source_sha256'].items():assert sha(p)==h,p
    assert datetime.fromisoformat(corpus['at'])<=datetime.fromisoformat(independent['at'])<=datetime.fromisoformat(semantic['at'])<=datetime.fromisoformat(historical['at'])
    assert historical['semantic_sha256']==sha(sp) and not historical['causal_outcomes_used']
    frozen=load(ROOT/'audit/pre_signal_analysis_freeze_v3.json');assert not frozen['per_event_routing_opened']
    assert datetime.fromisoformat(frozen['at'])<datetime.fromisoformat(historical['at'])
    for p,h in frozen['source_sha256'].items():assert sha(p)==h,p
    events=load(ROOT/'audit/analyzed_events.json')['rows'];inference=load(ROOT/'stage10b_yield_inference.json')
    assert len({e['event_id'] for e in events})==len(events)
    semantic_tids={e['trajectory_id'] for e in events if e['semantic_clean']}
    clean=[e for e in events if e['semantic_clean'] and e['C5']];clean_tids={e['trajectory_id'] for e in clean}
    primary=[e for e in events if e['primary_for_trajectory']]
    assert len(primary)==len(clean_tids) and {e['trajectory_id'] for e in primary}==clean_tids
    for e in primary:assert e['onset']==min(x['onset'] for x in clean if x['trajectory_id']==e['trajectory_id'])
    assert inference['pooled']['clean']==len(clean_tids) and inference['pooled']['new_demand']==len(semantic_tids)
    for d in ('MathVision','MathVerse'):
        own={r['trajectory_id'] for r in rows if r['dataset']==d};r=inference['datasets'][d]
        assert r['eligible']==len(own) and r['new_demand']==len(own&semantic_tids) and r['clean']==len(own&clean_tids)
    for e in clean:
        assert e['prior_availability']=='ABSENT' and all(e[c] for c in ('C1','C2','C3','C4')) and 0<=e['lag']<31
        assert e['category']=='CLEAN' and e['target_positions'] and e['irrelevant_positions']
        assert not(set(e['target_positions'])&set(e['irrelevant_positions']))
        q={r['offset']:r for r in e['rows']};t=e['lag']
        assert all(q[i]['target_image_mass']>=.05 and q[i]['target_control_mean_ratio']>=1.5 for i in (t,t+1))
        if e['evidence_channel']=='detector_and_target_routing':assert all(q[i]['retrieval_score']>e['threshold'] for i in (t,t+1))
        else:assert 0<=e['observation_offset']<32
    candidate=pd.read_parquet(ROOT/'stage10b_candidate_events.parquet')
    assert len(candidate)==len(clean) and set(candidate.event_id)=={e['event_id'] for e in clean}
    negatives=pd.read_parquet(ROOT/'stage10b_negative_cases.parquet');tr=negatives[negatives.record_kind=='trajectory']
    assert len(tr)==224-len(clean_tids) and set(tr.trajectory_id)==ids-clean_tids
    assert dict(Counter(tr.category))=={k:v for k,v in inference['primary_negative_categories'].items() if v}
    gate=load(ROOT/'stage10b_go_nogo_decision.json');agree=load(ROOT/'stage10b_annotation_agreement.json')
    counts={d:inference['datasets'][d]['clean'] for d in ('MathVision','MathVerse')}
    assert gate['decision']==decision(len(clean_tids),counts,counts,agree['acceptable_for_strong_go'])
    assert gate['recommendation_count']==1 and not gate['followup_launched']
    account=load(ROOT/'stage10b_resource_accounting.json');assert account['all_gpu_jobs_terminal'] and account['allocated_gpu_hours']<1
    assert account['new_generations']==account['causal_interventions']==0 and account['passive_repaired_trajectories']<=32
    artifacts=['stage10b_recurrent_demand_census_spec.md','stage10b_corpus_manifest.json','stage10b_semantic_annotations.parquet',
        'stage10b_reaccess_annotations.parquet','stage10b_candidate_events.parquet','stage10b_negative_cases.parquet',
        'stage10b_annotation_agreement.json','stage10b_yield_inference.json','stage10b_go_nogo_decision.json',
        'stage10b_resource_accounting.json','stage10b_summary.md']
    if account['passive_repaired_trajectories']:artifacts.append('stage10b_passive_reinstrumentation.parquet')
    figures=list((ROOT/'figures').glob('*.png'))+list((ROOT/'figures').glob('*.pdf'))
    assert len(figures)==8 and all(p.stat().st_size>1000 for p in figures)
    hashes={str(ROOT/p):sha(ROOT/p) for p in artifacts};hashes.update({str(p):sha(p) for p in figures})
    save(ROOT/'audit/final_audit.json',dict(at=now(),pass_all=True,native_source_files_verified=source_count,
        eligible=224,semantic_trajectories=len(semantic_tids),clean_trajectories=len(clean_tids),
        blinding_order_verified=True,semantic_sources_immutable=True,independent_denominators_verified=True,
        frozen_gate_verified=True,all_gpu_jobs_terminal=True,followup_launched=False,artifact_sha256=hashes,
        method='Main-agent arithmetic/provenance audit; not a third independent semantic annotation pass.'))
    print('AUDIT PASS',len(artifacts),'artifacts;4 PNG/PDF figures;',len(clean_tids),'clean independent trajectories',flush=True)


if __name__=='__main__':main()
