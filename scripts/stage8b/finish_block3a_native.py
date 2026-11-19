"""Small completeness receipt; no GPU work or scientific interpretation."""
import argparse,json,os
from datetime import datetime,timezone
from pathlib import Path
from visual_reasoning.stage8b.block1_data import digest,save

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);args=p.parse_args()
    cfg=json.loads(Path(args.config).read_text());root=Path(cfg['output_dir'])
    rows=[json.loads(s) for s in Path(cfg['manifest']).read_text().splitlines()]
    decision=json.loads(Path(cfg['layout_decision']).read_text())
    completed=[]
    for rank in range(decision['worker_count']):
        worker=json.loads((root/'census'/f'worker{rank}'/'completed.json').read_text());assert worker['completed']
        completed+=worker['items']
    assert len(completed)==len(set(completed))==128 and set(completed)=={r['task_id'] for r in rows}
    receipts={};tokens=0;seconds=0
    for row in rows:
        path=root/'examples'/row['task_id']/'result.json';r=json.loads(path.read_text())
        assert r['seed']==row['seed'] and str(r['item_id'])==str(row['item_id'])
        receipts[str(path)]=digest(path);tokens+=r['tokens'];seconds+=r['runtime']['elapsed_seconds']
    save(root/'completed.json',dict(at=datetime.now(timezone.utc).isoformat(),complete=True,trajectories=128,
        tokens=tokens,summed_process_seconds=seconds,slurm_job_id=os.environ.get('SLURM_JOB_ID'),
        config_sha256=digest(args.config),receipt_sha256=receipts,scientific_gate='pending independent semantic review'))
    print(json.dumps(dict(event='native_batch_complete',trajectories=128,tokens=tokens)))

if __name__=='__main__':main()
