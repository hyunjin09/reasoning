"""Read-only native progress across preserved and active continuation outputs."""
import json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('outputs/stage8b_block3a/v1')


def main():
    active_path=ROOT/'audit/active_native_run.json'
    active=json.loads(active_path.read_text()) if active_path.exists() else None
    cfg=json.loads(Path(active['config']).read_text()) if active else json.loads((ROOT/'audit/native_config.json').read_text())
    out=Path(cfg['output_dir']);tasks=[json.loads(s) for s in Path(cfg.get('full_manifest',cfg['manifest'])).read_text().splitlines()]
    scheduled=[json.loads(s) for s in Path(cfg['manifest']).read_text().splitlines()]
    layout=json.loads(Path(cfg['layout_decision']).read_text()) if Path(cfg['layout_decision']).exists() else None
    roots=active['example_roots'] if active else [str(out/'examples')]
    paths=[p for root in roots for p in Path(root).glob('*/result.json')]
    assert len({p.parent.name for p in paths})==len(paths),'Duplicate completed task across runs'
    receipts={p.parent.name:json.loads(p.read_text()) for p in paths}
    base=json.loads((ROOT/'audit/base_cohort.json').read_text())['anchors']
    prior={str(a['original']['item_id']):json.loads((Path(a['native_dir'])/'result.json').read_text())['tokens'] for a in base}
    completion=Path(active['completion_index']) if active else out/'completed.json'
    workers=cfg.get('worker_count',layout['worker_count'] if layout else None)
    result=dict(at=datetime.now(timezone.utc).isoformat(),completed=len(receipts),total=len(tasks),
        completed_tokens=sum(r['tokens'] for r in receipts.values()),reviews=len(list((ROOT/'annotations/reviews').glob('*.json'))),
        batch_complete=completion.exists(),worker_count=workers,gpus=cfg['gpus'],current=[])
    if layout:
        nominal=layout['measurements']['double' if layout['workers_per_gpu']==2 else 'single']['tokens_per_second']/layout['worker_count']
        remaining=[]
        for rank in range(workers):
            log=Path(cfg['log_dir'])/f'census_{rank}.log';events=[]
            if log.exists():
                for line in log.read_text(errors='replace').splitlines():
                    if line.startswith('{'):
                        try:events.append(json.loads(line))
                        except json.JSONDecodeError:pass
            starts=[e for e in events if e.get('event')=='start_example'];latest=starts[-1] if starts else None
            task=latest['task_id'] if latest else None
            progress=[e for e in events if e.get('event')=='token_progress' and e.get('item_id')==task]
            last=progress[-1] if progress else None;done=task in receipts
            tokens=0 if done or not last else last['forward_tokens']
            speed=tokens/last['elapsed_seconds'] if tokens>=1024 and last['elapsed_seconds']>0 else nominal
            assigned=[r for r in scheduled if r['assigned_rank']==rank] if active else scheduled[rank::workers]
            pending=[r for r in assigned if r['task_id'] not in receipts]
            # Never let a long current trace erase the estimated cost of future tasks.
            projected=sum(max(0,prior[r['item_id']]-tokens) if r['task_id']==task else prior[r['item_id']] for r in pending)
            remaining.append(projected/speed/3600)
            result['current'].append(dict(rank=rank,task=task,task_complete=done,latest_forward_tokens=tokens,
                tokens_per_second=speed,remaining_tasks=len(pending),prior_length_projection_hours=remaining[-1]))
        result['prior_length_projection_hours']=max(remaining)
        result['eta_limitation']='Discovery-length projection; stochastic lengths and long-context speed may differ. Excludes annotation/conditional causal work and an unfinished current trace beyond its original length.'
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
