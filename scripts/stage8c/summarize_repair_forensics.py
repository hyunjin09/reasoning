"""Aggregate persisted measurements without discarding failed prefixes."""
import argparse
import json
from pathlib import Path
from datetime import datetime,timezone
import pyarrow as pa
import pyarrow.parquet as pq
from scripts.stage8c.prepare import save,sha
from scripts.stage8c.prepare_repair import ROOT

METRICS=['pre_native_replay','pre_legacy','pre_bf16_sum','pre_fp32_diagnostic',
         'post_native_reproject','post_legacy','post_bf16_separate','post_bf16_joint',
         'residual_native_replay','residual_separate','residual_left_associative','residual_joint']


def stats(rows,key):
    values=[r[key] for r in rows]
    worst=max(rows,key=lambda r:r[key]['max_abs'])
    return dict(rows=len(rows),failed_rows=sum(not v['pass_bounds'] for v in values),
        all_pass=all(v['pass_bounds'] for v in values),
        max_relative_l2=max(v['relative_l2'] for v in values),max_abs=max(v['max_abs'] for v in values),
        largest_error=dict(item_id=worst['item_id'],case_id=worst['case_id'],token_index=worst['token_index'],
                           layer=worst['layer'],**worst[key]))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['forensic','candidate'],required=True);args=ap.parse_args()
    phase=args.phase
    manifest=json.loads((ROOT/'stage8c_repair_prefix_manifest.json').read_text())
    for rank in range(2):assert json.loads((ROOT/phase/f'worker{rank}'/'completed.json').read_text())['completed']
    rows=[];coverage=[];sources={}
    for item in manifest['inputs']:
        dest=ROOT/phase/'items'/item['input']['item_id']
        p=dest/'forensic_rows.jsonl'
        local=[json.loads(x) for x in p.read_text().splitlines()]
        expected=sum(c['end']-c['start'] for c in item['cases'])*4
        assert len(local)==expected and len({(r['token_index'],r['layer']) for r in local})==expected
        rows.extend(dict(r,implementation=phase) for r in local)
        report=json.loads((dest/'result.json').read_text());coverage.extend(report['coverage'])
        for path in dest.iterdir():
            if path.is_file():sources[str(path)]=sha(path)
    assert len(coverage)==8 and len({c['family_id'] for c in coverage})==4
    flattened=[]
    for r in rows:
        flat={k:v for k,v in r.items() if k not in METRICS+['per_head','concatenation']}
        flat['per_head']=json.dumps(r['per_head']);flat['q_to_kv']=json.dumps(r['q_to_kv'])
        for m in METRICS:
            for k,v in r[m].items():flat[m+'__'+k]=json.dumps(v) if isinstance(v,list) else v
        flattened.append(flat)
    table=pa.Table.from_pylist(flattened)
    pq.write_table(table,ROOT/'audit'/f'{phase}_forensic_metrics.parquet')
    per_case={c['case_id']:{m:stats([r for r in rows if r['case_id']==c['case_id']],m) for m in METRICS} for c in coverage}
    summary=dict(at=datetime.now(timezone.utc).isoformat(),implementation=phase,rows=len(rows),
        cases=8,families=4,coverage=coverage,metrics={m:stats(rows,m) for m in METRICS},per_case=per_case,
        partition_pass=all(r['partition_pass'] for r in rows),gqa_pass=all(r['gqa_native_mapping_exact'] for r in rows),
        concatenation_native_exact=all(r['concat_native_exact'] for r in rows),
        projection_bias_present=any(r['bias_exists'] for r in rows),
        source_sha256=sources,
        diagnostic_stage_order='partition -> head space -> W_O -> residual; later values are logged, not used to excuse an earlier failure')
    save(ROOT/'audit'/f'{phase}_summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ['per_case','source_sha256']},indent=2))


if __name__=='__main__':main()
