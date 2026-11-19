"""CPU-only Slurm allocation accounting; never sums overlapping request latency."""
import re
import subprocess
from collections import Counter, defaultdict
from scripts.stage14d1.common import P, load, now, save

def accounting():
    launches = [load(p) for p in (P/'audit/launches').glob('job_*.json')]
    ids = sorted({str(x['job']['slurm_job_id']) for x in launches})
    raw = subprocess.run(['sacct', '-j', ','.join(ids), '-X', '-n', '-P',
                          '--format=JobIDRaw,State,ElapsedRaw,AllocTRES,NodeList,Start,End'],
                         check=True, capture_output=True, text=True).stdout
    jobs = []
    for line in raw.splitlines():
        ident, status, elapsed, tres, node, start, end, *_ = line.split('|')
        if ident not in ids:
            continue
        match = re.search(r'(?:^|,)gres/gpu=(\d+)(?:,|$)', tres)
        gpus = int(match[1]) if match else 0
        jobs.append(dict(job_id=ident, status=status, elapsed_seconds=int(elapsed),
                         allocated_gpus=gpus, gpu_seconds=int(elapsed)*gpus,
                         node=node, start=start, end=end, alloc_tres=tres))
    assert {r['job_id'] for r in jobs} == set(ids), 'Missing Slurm accounting'
    versions = {}
    for root in sorted((P/'raw').iterdir()):
        if not root.is_dir():
            continue
        kinds = defaultdict(Counter)
        for path in root.glob('*/generation.json'):
            generation = load(path)
            inp = load(path.parent/'input.json')
            kinds[inp['kind']].update(calls=1, output_tokens=generation['tokens'],
                                      prompt_tokens=generation['prompt_tokens'],
                                      visual_tokens=generation['visual_tokens'],
                                      cap_hits=int(generation['cap_hit']))
        versions[root.name] = dict(kinds)
    return dict(at=now(), jobs=jobs, total_allocated_GPU_hours=sum(j['gpu_seconds'] for j in jobs)/3600,
                stage_ceiling_GPU_hours=16, technical_ceiling_GPU_hours=2,
                physical_completed_calls=versions, raw_sacct=raw,
                latency_policy='Allocated GPU wall time includes startup and idle; request latency overlaps and is not added as GPU usage.',
                main_cap_hits='NOT_MEASURED; technical solver caps do not measure final completion.')

if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser()
    parser.add_argument('--output')
    args = parser.parse_args()
    result = accounting()
    if args.output:
        save(args.output, result)
    print(json.dumps(result, indent=2))
