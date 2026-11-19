"""Four independent Slurm workers over the frozen unfinished audit rows."""


def runtime_rank(env, *, visible_devices, allocation):
    if not allocation or env.get('SLURM_JOB_ID') != str(allocation):
        raise ValueError('Must use the authorized Slurm allocation')
    if int(visible_devices) != 1:
        raise ValueError('Each task must see one Slurm-bound GPU')
    try:
        rank, count = int(env['SLURM_PROCID']), int(env['SLURM_NTASKS'])
    except (KeyError, ValueError) as exc:
        raise ValueError('Missing Slurm task identity') from exc
    if count != 4 or not 0 <= rank < 4:
        raise ValueError('Expected four Slurm tasks with rank0–3')
    return rank


def assigned_rows(rows, *, rank, reused):
    if not 0 <= rank < 4:
        raise ValueError('Expected rank0–3')
    ids = [r['item_id'] for r in rows]
    if len(set(ids)) != len(ids) or not set(reused) <= set(ids):
        raise ValueError('Invalid manifest or unknown reused item')
    return [r for r in rows if r['item_id'] not in reused][rank::4]
