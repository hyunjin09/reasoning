"""Deterministic sharding retains every item/seed task exactly once."""
def assigned_tasks(rows, *, rank, workers):
    if workers not in (2,4) or not 0<=rank<workers:
        raise ValueError('Expected two Slurm GPUs with one or two workers each')
    if len({r['task_id'] for r in rows})!=len(rows):
        raise ValueError('Duplicate item/seed task')
    if len({(str(r['item_id']),r['seed']) for r in rows})!=len(rows):
        raise ValueError('Duplicate item/seed identity')
    return rows[rank::workers]
