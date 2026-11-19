"""Persist batch status; sbatch exits and releases both GPUs without tmux."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from harness_state import mutate_gpu_queue


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--exit-code',type=int,required=True);args=ap.parse_args()
    root=Path('outputs/stage8b/v2/native/transfer32_t1_v1')
    paths=list(root.glob('examples/*/result.json'))
    rows=[json.loads(p.read_text()) for p in paths]
    expected={json.loads(line)['item_id'] for line in Path('outputs/stage8b/v2/cohort/transfer32_manifest_v1.jsonl').read_text().splitlines()}
    completed=args.exit_code==0 and len(rows)==len(expected) and {r['item_id'] for r in rows}==expected
    if completed:
        for r in rows:
            for path,digest in r['provenance_sha256'].items():
                assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
        env=[json.loads((root/'census'/f'worker{i}'/'environment.json').read_text()) for i in range(2)]
        assert len({e['gpu_uuid'] for e in env})==2
    record=dict(completed=completed,exit_code=args.exit_code,examples=len(rows),slurm_job_id=os.environ['SLURM_JOB_ID'],
        at=datetime.now(timezone.utc).isoformat(),result_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        gpu_release='Batch exits after this receipt; verify terminal Slurm state independently.',
        next_step='CPU semantic transfer audit; no automatic main-census or causal launch')
    root.mkdir(parents=True,exist_ok=True);p=root/'wrapper.json';assert not p.exists();p.write_text(json.dumps(record,indent=2)+'\n')
    def update(q):
        job=next(j for j in q['jobs'] if j['id']=='stage8b_v2_transfer32_t1_v1')
        job.update(status='succeeded' if completed else 'failed',finished_at=record['at'],result_path=str(p))
    mutate_gpu_queue(Path.cwd(),update)
    print(json.dumps({k:v for k,v in record.items() if k!='result_sha256'}),flush=True)
    if args.exit_code==0 and not completed:raise RuntimeError('Successful process exit but incomplete artifact coverage')


if __name__=='__main__':main()
