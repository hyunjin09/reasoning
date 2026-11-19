"""Bounded node07 startup diagnostic before entrusting it scientific work."""
import json
import os
import socket
import time
from pathlib import Path
import torch
from scripts.stage8c.prepare import save,sha
from scripts.stage9a.run_native import now

assert os.environ.get('SLURM_JOB_ID') and torch.cuda.device_count()==1
began=time.perf_counter()
root=Path('outputs/stage9a_dynamics/v1')
cfg=json.loads((root/'config.json').read_text())
checks={}
for key,info in cfg['models'].items():
    p=Path(info['checkpoint'])
    assert sha(p/'config.json')==info['files_sha256']['config.json']
    # Bounded model-file readability check; a full hash is enforced by workers.
    with (p/'model.safetensors').open('rb') as f:assert len(f.read(1<<20))==1<<20
    checks[key]=True
x=torch.ones(32,device='cuda',dtype=torch.bfloat16)
assert float((x*x).sum())==32
torch.cuda.synchronize()
save(root/'audit/node07_probe.json',dict(pass_all=True,at=now(),node=socket.gethostname(),
    slurm_job_id=os.environ['SLURM_JOB_ID'],models_readable=checks,cuda=True,gpu=torch.cuda.get_device_name(0),elapsed_seconds=time.perf_counter()-began))
print('Node startup and GPU diagnostic passed',flush=True)
