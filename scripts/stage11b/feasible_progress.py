"""Metadata-only progress against the remaining original discovery comparisons."""
from collections import Counter
import json
from scripts.stage11b.common import ROOT, load, now
from scripts.stage11b.protocol import CANDIDATES, in_stratum

eligible = {r['item_id'] for r in load(ROOT/'annotations/discovery_evidence_final.json')['rows']
            if r['eligible'] and in_stratum(r, CANDIDATES[2])}
rows = {}
for queue in ['discovery', 'source_feasible']:
    for path in (ROOT/queue/'results').glob('*/result.json'):
        row = load(path)
        assert row['task_id'] not in rows
        rows[row['task_id']] = row
required = [r for r in rows.values() if r['item_id'] in eligible and not r['budget_interrupted']]
jobs = [dict(id=j['id'], status=j['status'], slurm_job_id=j.get('slurm_job_id'), node=j.get('node'))
        for j in load('state/gpu_experiment_queue.json')['jobs'] if j['id'].startswith('stage11b_feasible_')]
print(json.dumps(dict(at=now(), required_total=72, required_complete=len(required),
    by_arm=dict(Counter(r['arm'] for r in required)), all_complete_records=len(rows),
    required_capped=sum(r['at_length_cap'] for r in required),
    budget_interrupted_records=sum(r['budget_interrupted'] for r in rows.values()), jobs=jobs), indent=2))
