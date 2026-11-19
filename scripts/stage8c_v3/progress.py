"""Read-only development progress; no outcomes, detector audit or GPU work."""
import json
from datetime import datetime,timezone
from pathlib import Path

from scripts.stage8c_v3.prepare import ROOT


def snapshot():
    active=ROOT/'audit/active_execution.json'
    config_path=json.loads(active.read_text())['config'] if active.exists() else ROOT/'audit/dev_config.json'
    cfg=json.loads(Path(config_path).read_text());phase=ROOT/cfg['phase'];workers=cfg['gpus']
    tasks=json.loads(Path(cfg['task_manifest']).read_text())['tasks']
    receipts=[json.loads(p.read_text()) for p in (phase/'examples').glob('*/result.json')]
    finished={r['task_id'] for r in receipts}
    latest={}
    for p in sorted(phase.glob('worker*/progress.jsonl')):
        rows=p.read_text().splitlines()
        if rows:
            # An append in progress may leave an incomplete final line.
            for line in reversed(rows):
                try:r=json.loads(line)
                except json.JSONDecodeError:continue
                if r['task_id'] not in finished:latest[str(r['rank'])]=r
                break
    elapsed=sum(r['runtime']['elapsed_seconds'] for r in receipts)
    tokens=sum(r['tokens'] for r in receipts)
    complete_estimate=None
    if receipts:
        by_rank={rank:[r for r in receipts if r['rank']==rank] for rank in range(workers)}
        remaining=[]
        for rank in range(workers):
            observed=by_rank[rank]
            mean=sum(r['runtime']['elapsed_seconds'] for r in observed)/len(observed) if observed else elapsed/len(receipts)
            pending=sum(t['task_id'] not in finished for t in tasks[rank::workers])
            remaining.append(max(0,pending*mean-latest.get(str(rank),{}).get('elapsed_seconds',0)))
        complete_estimate=max(remaining)/3600
    live_rates=[r['tokens']/r['elapsed_seconds'] for r in latest.values()]
    return dict(at=datetime.now(timezone.utc).isoformat(),phase=cfg['phase'],workers=workers,
        completed=len(receipts),total=len(tasks),items_with_completed_arms=len({r['item_id'] for r in receipts}),
        fully_completed_items=sum(all(t['task_id'] in finished for t in tasks if t['input']['item_id']==item)
                                  for item in {t['input']['item_id'] for t in tasks}),
        completed_gains=sorted({r['gain'] for r in receipts}),latest=latest,
        complete_sample_tokens_per_second=tokens/elapsed if elapsed else None,
        live_tokens_per_second=live_rates,
        completed_sample_mean_tokens=tokens/len(receipts) if receipts else None,
        remaining_hours_from_completed_sample_mean=complete_estimate,
        eta_caveat='Early completed samples overrepresent short trajectories; extrapolation is not a stable cohort ETA.',
        prior_length_11800_token_planning_hours=(len(tasks)-len(receipts))*11800/(sum(live_rates)*3600) if len(live_rates)==workers else None,
        max_observed_peak_allocated_bytes=max((r['runtime']['peak_gpu_allocated_bytes'] for r in receipts),default=None),
        max_observed_peak_reserved_bytes=max((r['runtime']['peak_gpu_reserved_bytes'] for r in receipts),default=None),
        completed_interventions=sum(r['actual_interventions'] for r in receipts),
        failures=[str(p) for p in (phase/'examples').glob('*/failure.json')],
        scientific_plan_complete=False)


if __name__=='__main__':print(json.dumps(snapshot(),indent=2))
