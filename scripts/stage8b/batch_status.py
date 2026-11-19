"""Read native completion receipts without exposing scientific outcomes or R."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='outputs/stage8b/config/transfer32_v1.json')
    args = parser.parse_args()
    cfg = json.loads(Path(args.config).read_text())
    rows = [json.loads(x) for x in Path(cfg['manifest']).read_text().splitlines()]
    root = Path(cfg['output_dir'])
    workers = []
    all_receipts = []
    for rank in range(2):
        completed, active, unstarted = [], [], []
        for row in rows[rank::2]:
            dest = root/'examples'/row['item_id']
            if (dest/'result.json').exists():
                receipt = json.loads((dest/'result.json').read_text())
                assert receipt['item_id'] == row['item_id'] and receipt['rank'] == rank
                completed.append(receipt)
            elif dest.exists():
                active.append(row['item_id'])
            else:
                unstarted.append(row['item_id'])
        all_receipts.extend(completed)
        workers.append(dict(rank=rank, complete=len(completed), current=active, unstarted=len(unstarted)))
    result = dict(at=datetime.now(timezone.utc).isoformat(), output_dir=str(root), total=len(rows),
                  completed=len(all_receipts), eos=sum(x['normal_eos'] for x in all_receipts),
                  generated_tokens=sum(x['tokens'] for x in all_receipts), workers=workers,
                  wrapper_present=(root/'wrapper.json').exists(), scientific_scores_opened=False)
    elapsed = [x['runtime']['elapsed_seconds'] for x in all_receipts]
    if elapsed:
        result['completed_runtime_seconds'] = dict(mean=mean(elapsed), minimum=min(elapsed), maximum=max(elapsed))
        result['completed_gpu_hours'] = sum(elapsed)/3600
    result['eta'] = 'Not yet reliable; unfinished long traces are censored and completed-only averages may underestimate remaining work.'
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
