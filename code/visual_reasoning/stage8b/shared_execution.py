"""Operational sharding of two Slurm GPUs with one or two processes per GPU."""


def runtime_rank(env, *, visible_devices, allocation, lane, workers_per_gpu):
    if not allocation or env.get('SLURM_JOB_ID') != str(allocation):
        raise ValueError('Must use the authorized Slurm allocation')
    if int(visible_devices) != 1:
        raise ValueError('Each parent and its children must see one Slurm-bound GPU')
    if workers_per_gpu not in (1, 2) or not 0 <= lane < workers_per_gpu:
        raise ValueError('Invalid local worker layout')
    try:
        parent, count = int(env['SLURM_PROCID']), int(env['SLURM_NTASKS'])
    except (KeyError, ValueError) as exc:
        raise ValueError('Missing Slurm task identity') from exc
    if count != 2 or parent not in (0, 1):
        raise ValueError('Expected two Slurm GPU parents')
    return parent * workers_per_gpu + lane


def assigned_rows(rows, *, rank, workers):
    if workers not in (2, 4) or not 0 <= rank < workers:
        raise ValueError('Invalid worker rank/count')
    ids = [r['item_id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate manifest identity')
    return rows[rank::workers]


def choose_layout(*, speedup, exact_parity, double_memory_gib, device_memory_gib):
    # A numerical change is a failed technical gate, not an efficiency tradeoff.
    if not exact_parity:
        raise ValueError('Single/shared native outputs or passive statistics differ')
    return 2 if speedup >= 1.05 and double_memory_gib <= .90 * device_memory_gib else 1
