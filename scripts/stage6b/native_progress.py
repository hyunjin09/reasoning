"""One bounded progress snapshot, without opening large telemetry records."""
from datetime import datetime,timezone
from scripts.stage6b.common import OUT,read_json,read_jsonl,write_json


def main():
    counts_path=OUT/'audit/native_expected_endpoint_counts.json'
    if not counts_path.exists():
        rows=read_jsonl(OUT/'trajectory/native_endpoint_manifest_v3_schedule.jsonl')
        write_json(counts_path,{r['id']:len(r['spans']) for r in rows},freeze=True)
    counts=read_json(counts_path);workers=[]
    for rank in range(2):
        shard=OUT/'raw/native_primary_02'/f'shard_{rank:02d}';sig=read_json(shard/'signature.json')
        done=[eid for eid in sig['event_ids'] if (shard/(eid+'.json')).exists()]
        remaining=[eid for eid in sig['event_ids'] if eid not in done]
        current=remaining[0] if remaining else None
        progress=shard/(str(current)+'_progress.json')
        observed=read_json(progress) if progress.exists() else None
        workers.append({'rank':rank,'completed_traces':len(done),'expected_traces':len(sig['event_ids']),
            'completed_endpoints':sum(counts[eid] for eid in done),'current_trace':current,
            'current_expected_endpoints':counts[current] if current else None,'current_observed_progress':observed,
            'summary_complete':(shard/'run_summary.json').exists() and read_json(shard/'run_summary.json')['completed']})
    result={'timestamp':datetime.now(timezone.utc).isoformat(),'run_id':'native_primary_02','total_endpoints':sum(counts.values()),
        'completed_endpoints':sum(w['completed_endpoints'] for w in workers),
        'observed_in_progress_endpoints':sum((w['current_observed_progress'] or {}).get('completed_endpoints',0) for w in workers),
        'workers':workers}
    write_json(OUT/'audit/native_primary_02_progress.json',result)
    print(result)


if __name__=='__main__':main()
