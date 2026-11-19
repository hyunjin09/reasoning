"""Four bound GPUs and exact, outcome-blind continuation task assignment."""

def runtime_rank(env, *, visible_devices, allocation, lane, workers_per_gpu):
    if not allocation or env.get('SLURM_JOB_ID')!=str(allocation) or visible_devices!=1:
        raise ValueError('Expected one Slurm-bound GPU per parent in the authorized allocation')
    parent=int(env.get('SLURM_PROCID','-1'))
    if env.get('SLURM_NTASKS')!='4' or parent not in range(4) or workers_per_gpu!=2 or lane not in (0,1):
        raise ValueError('Expected four Slurm parents with two workers/GPU')
    return 2*parent+lane


def balanced_remaining(rows, completed, costs):
    ids={r['task_id'] for r in rows}
    if len(ids)!=len(rows) or not set(completed)<=ids:
        raise ValueError('Duplicate tasks or unknown completed identity')
    if len({(str(r['item_id']),r['seed']) for r in rows})!=len(rows):
        raise ValueError('Duplicate item/seed pair')
    remaining=[dict(r) for r in rows if r['task_id'] not in completed]
    remaining.sort(key=lambda r:(-costs[str(r['item_id'])],r['task_id']))
    loads=[0]*8
    for row in remaining:
        rank=min(range(8),key=lambda i:(loads[i],i));row['assigned_rank']=rank;loads[rank]+=costs[str(row['item_id'])]
    return remaining,loads
