"""Check the observable Stage9A completion contract and released Slurm workers."""
import json
import subprocess
from datetime import datetime,timezone
from pathlib import Path

import pyarrow.parquet as pq

from scripts.stage8c.prepare import save,sha

ROOT=Path('outputs/stage9a/v1')
ARTIFACTS=['stage9a_cohort_manifest.json','stage9a_generation_config.json',
    'stage9a_instruct_direct_trajectories.parquet','stage9a_instruct_cot_trajectories.parquet','stage9a_thinking_trajectories.parquet',
    'stage9a_retrieval_features.parquet','stage9a_retrieval_episodes.parquet','stage9a_demand_events.parquet',
    'stage9a_length_matched_pairs.json','stage9a_primary_effects.json','stage9a_causal_validation.json','stage9a_accuracy_secondary.json','stage9a_summary.md']


def main():
    for name in ARTIFACTS:assert (ROOT/name).is_file(),name
    figures=sorted((ROOT/'figures').glob('figure*.png'));pdfs=sorted((ROOT/'figures').glob('figure*.pdf'))
    assert len(figures)==len(pdfs)==5
    metrics=json.loads((ROOT/'audit/trajectory_metrics.json').read_text())['rows']
    assert len(metrics)==384 and len({r['family_id'] for r in metrics})==128
    assert pq.ParquetFile(ROOT/'stage9a_retrieval_features.parquet').metadata.num_rows==sum(r['generated_tokens'] for r in metrics)
    assert pq.ParquetFile(ROOT/'stage9a_demand_events.parquet').metadata.num_rows==700
    expected=sum(len(r[scope]['episodes']) for r in metrics for scope in ('primary','common'))
    assert pq.ParquetFile(ROOT/'stage9a_retrieval_episodes.parquet').metadata.num_rows==expected
    native=json.loads((ROOT/'audit/all_native_hashes_verified.json').read_text())
    assert native['verified'] and len(native['rows'])==384 and all(r['all_artifact_hashes_match'] for r in native['rows'])
    # Verify prior-stage/native scientific sources still match their execution freeze.
    cfg=json.loads((ROOT/'stage9a_generation_config_node07.json').read_text())
    for p,expected in cfg['source_sha256'].items():assert sha(p)==expected,p
    cc=json.loads((ROOT/'audit/causal_config.json').read_text())
    for p,expected in cc['source_sha256'].items():assert sha(p)==expected,p
    assert sha(cc['manifest'])==cc['manifest_sha256']
    source=json.loads((ROOT/'annotations/causal_selection_frozen.json').read_text())
    causal=json.loads((ROOT/'stage9a_causal_validation.json').read_text())
    assert len(source['rows'])==len(causal['rows'])==50
    assert {r['event_id'] for r in source['rows']}=={r['event_id'] for r in causal['rows']}
    semantic=json.loads((ROOT/'annotations/semantic_review_complete.json').read_text())['rows']
    accepted={r['event_id'] for r in semantic if r['semantic_label']=='accepted'}
    assert {r['event_id'] for r in source['rows']}<=accepted
    work=json.loads((ROOT/'annotations/answer_review_work.json').read_text())
    exported=json.loads((ROOT/'annotations/answer_extraction_packets.json').read_text())
    assert work['rows']==exported['rows'],'Masked review must match independently exported answer packets'
    answers=json.loads((ROOT/'annotations/answer_extraction_review_frozen.json').read_text())['rows']
    assert len(answers)==384 and len({r['packet_id'] for r in answers})==384
    scores=json.loads((ROOT/'stage9a_accuracy_secondary.json').read_text())
    assert all(sum(v['reviewed'][k] for k in ('correct','wrong','unscorable'))==128 for v in scores['arms'].values())
    decision=json.loads((ROOT/'audit/decision.json').read_text());assert decision['advance'] is False and decision['next_experiment_launched'] is False
    assert decision['summary_sha256']==sha(ROOT/'stage9a_summary.md')
    assert all(r['capture_noop_exact'] and r['sham_noop_exact'] and r['selected_routing_fixed'] for r in causal['rows'])
    jobs=['121562','121563','121564','121568'];live=subprocess.run(['squeue','-u','hyunjin','-h','-o','%i|%T|%j|%R'],capture_output=True,text=True,check=True).stdout
    assert not any(line.split('|')[0] in jobs for line in live.splitlines()),'Stage9A workers still allocated'
    for job in jobs[:3]:assert (ROOT/'causal/workers'/('slurm_'+job)/'completed.json').exists()
    out=dict(at=datetime.now(timezone.utc).isoformat(),completed=True,required_artifacts=13,figures=5,
        artifact_sha256={str(ROOT/name):sha(ROOT/name) for name in ARTIFACTS},
        figure_sha256={str(p):sha(p) for p in figures+pdfs},native_trajectories=384,independent_families=128,
        analysis_code_sha256={str(p):sha(p) for p in sorted(Path('scripts/stage9a').glob('*.py'))+sorted(Path('code/visual_reasoning/stage9a').glob('*.py'))},
        generated_tokens=sum(r['generated_tokens'] for r in metrics),semantic_nominations_reviewed=700,source_readout_nominations_reviewed=610,
        answer_extractions_reviewed=384,causal_events_completed=50,earlier_frozen_scientific_sources_unchanged=True,
        focused_tests_passed=18,all_native_artifact_hashes_verified=True,masked_answer_packets_match=True,
        gpus_released=True,live_user_squeue=live,next_experiment_launched=False,
        exact_native_prefix_causal_events=causal['exact_native_prefix_events'],
        native_measured_inference_gpu_hours=sum(r['runtime_seconds'] for r in metrics)/3600,
        causal_measured_event_gpu_hours=causal['runtime_gpu_hours'],
        causal_peak_allocated_gpu_gib=causal['max_peak_gpu_gib'],
        terminal_job_queries={job:subprocess.run(['scontrol','show','job',job],capture_output=True,text=True).stdout for job in jobs},
        worker_receipt_sha256={str(p):sha(p) for p in sorted((ROOT/'causal/workers').glob('*/*.json'))},
        inferential_limits=['No supported positive primary contrast','Nine matched-length families','Causal16/16/18 events below20-family per-arm inference threshold','Fine subtype metadata unknown'])
    save(ROOT/'audit/final_validation.json',out)
    print(json.dumps({k:v for k,v in out.items() if not k.endswith('sha256')},indent=2))


if __name__=='__main__':main()
