"""Deterministic final parsing of every frozen causal event, with no reselection."""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from scripts.stage8c.prepare import save,sha
from visual_reasoning.stage9a.protocol import ARMS
from visual_reasoning.stage9a.statistics import mean_interval,paired

ROOT=Path('outputs/stage9a/v1')
SHAM_JS_ROUNDOFF_TOLERANCE=64*np.finfo(np.float64).eps


def validate_result(row):
    assert row['completed'] and row['capture_noop_exact'] and row['sham_noop_exact'] and row['selected_routing_fixed']
    # Exact raw-logit and score parity remain mandatory. The FP64 logaddexp
    # expression used for JS can leave signed roundoff for identical logits.
    assert row['effects']['sham']==0
    assert abs(row['first_query_js']['sham'])<=SHAM_JS_ROUNDOFF_TOLERANCE


def main():
    manifest=json.loads((ROOT/'annotations/causal_selection_frozen.json').read_text());rows=[]
    for request in manifest['rows']:
        path=ROOT/'causal/results'/(request['event_id']+'.json')
        assert path.exists(),f'Unfinished frozen event: {request["event_id"]}'
        r=json.loads(path.read_text());validate_result(r)
        assert r['family_id']==request['family_id'] and r['arm']==request['arm']
        r.update(result_path=str(path),result_sha256=sha(path),source_id=request['source_id'],item_id=request['item_id'])
        rows.append(r)
    assert len(rows)==50 and len({r['event_id'] for r in rows})==50
    metrics=['target','irrelevant','sham','target_minus_irrelevant']
    value=lambda r,k:r[k] if k=='target_minus_irrelevant' else r['effects'][k]
    arms={a:{k:mean_interval([value(r,k) for r in rows if r['arm']==a]) for k in metrics} for a in ARMS}
    for a in ARMS:
        rr=[r for r in rows if r['arm']==a]
        arms[a].update(events=len(rr),positive_target_count=sum(r['effects']['target']>0 for r in rr),
                      positive_target_minus_irrelevant_count=sum(r['target_minus_irrelevant']>0 for r in rr))
    flat=[dict(family_id=r['family_id'],arm=r['arm'],primary={k:value(r,k) for k in metrics}) for r in rows]
    contrasts={k:paired(flat,k,confidence=.95) for k in metrics}
    pooled=defaultdict(list)
    for r in rows:pooled[r['family_id']].append(r['target_minus_irrelevant'])
    result=dict(rows=rows,arms=arms,thinking_minus_cot_paired=contrasts,
        pooled_equal_family_target_minus_irrelevant=mean_interval([float(np.mean(v)) for v in pooled.values()]),
        exact_native_prefix_events=sum(r['native_prefix_parity']['exact'] for r in rows),
        max_native_prefix_passive_abs=max(r['native_prefix_parity']['max_abs'] for r in rows),
        max_abs_sham_js=max(abs(r['first_query_js']['sham']) for r in rows),
        sham_js_roundoff_tolerance=SHAM_JS_ROUNDOFF_TOLERANCE,
        runtime_gpu_hours=sum(r['runtime_seconds'] for r in rows)/3600,
        max_peak_gpu_gib=max(r['peak_gpu_allocated_bytes'] for r in rows)/2**30,
        manifest_sha256=sha(ROOT/'annotations/causal_selection_frozen.json'),protocol=manifest['assay_protocol'],
        limitations=manifest['limitations']+['Matched-family arm contrasts use distinct native demand events, not an experimentally shared reasoning prefix',
            'Irrelevant controls match ROI geometry/cardinality, not Value perturbation norm; per-event norms retained',
            'All selected-layer routes fixed: test isolates donor Values under native routing, not all paths of visual causality'])
    save(ROOT/'stage9a_causal_validation.json',result)
    print(json.dumps(dict(completed=True,events=len(rows),families=len(pooled))))


if __name__=='__main__':main()
