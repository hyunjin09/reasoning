"""Combine preserved and resumed receipts without rewriting either native run."""
import argparse,json,os
from datetime import datetime,timezone
from pathlib import Path
from visual_reasoning.stage8b.block1_data import digest,save


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args();cfg=json.loads(Path(a.config).read_text())
    root=Path(cfg['output_dir']);completed=[]
    for rank in range(8):
        worker=json.loads((root/'census'/f'worker{rank}'/'completed.json').read_text());assert worker['completed'];completed+=worker['items']
    remaining=[json.loads(s) for s in Path(cfg['manifest']).read_text().splitlines()]
    assert len(completed)==len(set(completed))==len(remaining) and set(completed)=={r['task_id'] for r in remaining}
    all_rows=[json.loads(s) for s in Path(cfg['full_manifest']).read_text().splitlines()]
    assert digest(cfg['full_manifest'])==cfg['full_manifest_sha256']
    receipts=dict(cfg['reused_receipt_sha256']);ids=set();tokens=0;seconds=0
    for row in remaining:
        p=root/'examples'/row['task_id']/'result.json';receipts[str(p)]=digest(p)
    expected={r['task_id']:r for r in all_rows}
    for path,sha in receipts.items():
        assert digest(path)==sha
        r=json.loads(Path(path).read_text());assert r['task_id'] not in ids;ids.add(r['task_id']);task=expected[r['task_id']]
        assert str(r['item_id'])==str(task['item_id']) and r['seed']==task['seed']
        tokens+=r['tokens'];seconds+=r['runtime']['elapsed_seconds']
    assert ids==set(expected) and len(ids)==128
    result=dict(at=datetime.now(timezone.utc).isoformat(),complete=True,trajectories=128,resumed=len(remaining),reused=len(cfg['reused_receipt_sha256']),
        tokens=tokens,summed_process_seconds=seconds,slurm_job_id=os.environ.get('SLURM_JOB_ID'),receipt_sha256=receipts,
        config_sha256=digest(a.config),scientific_gate='pending full semantic review and same-item replication')
    save(root/'completed.json',result);save(Path(cfg['completion_index']),result)
    print(json.dumps(dict(event='native_batch_complete',trajectories=128,resumed=len(remaining),tokens=tokens)))

if __name__=='__main__':main()
