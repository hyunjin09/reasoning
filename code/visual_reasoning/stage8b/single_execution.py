"""Operational guards and score-blind progress for one Slurm-bound worker."""
import json
import time


def runtime_rank(env, *, visible_devices, allocation):
    if not allocation or env.get('SLURM_JOB_ID') != str(allocation):
        raise ValueError('Must use the authorized Slurm allocation')
    if int(visible_devices) != 1:
        raise ValueError('The task must see exactly one Slurm-bound GPU')
    if env.get('SLURM_PROCID') != '0' or env.get('SLURM_NTASKS') != '1':
        raise ValueError('Expected exactly one Slurm task with rank zero')
    return 0


def assigned_rows(rows, *, rank):
    if rank != 0:
        raise ValueError('Only rank zero is authorized')
    return list(rows)


class NativeProgress:
    def __init__(self, model, item_id):
        self.model, self.item_id = model, item_id
        self.tokens = 0

    def __enter__(self):
        self.started = time.monotonic()
        self.handle = self.model.lm_head.register_forward_hook(self.observe)
        return self

    def observe(self, _module, _inputs, _outputs):
        self.tokens += 1
        if self.tokens == 1 or self.tokens % 1024 == 0:
            print(json.dumps(dict(event='token_progress', item_id=self.item_id,
                forward_tokens=self.tokens, elapsed_seconds=time.monotonic()-self.started)), flush=True)

    def __exit__(self, *_exc):
        self.handle.remove()
