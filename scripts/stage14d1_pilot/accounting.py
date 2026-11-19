"""Fail-closed budget accounting while Slurm accounting catches up to submission."""
def budget_amounts(raw,maximum):
    parts=raw.strip().split('|')
    if len(parts)<4 or not parts[2].isdigit():return 0,maximum
    state,elapsed,tres=parts[1],int(parts[2]),parts[3]
    terminal=state in ('COMPLETED','FAILED','TIMEOUT','OUT_OF_MEMORY') or state.startswith('CANCELLED')
    charged=elapsed if 'gres/gpu=1' in tres else 0
    if charged>maximum:raise ValueError('Allocation exceeded registered reservation')
    if terminal:return charged,0
    return charged,maximum-charged
