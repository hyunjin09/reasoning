import os,json,subprocess,torch
from pathlib import Path
assert os.environ['SLURM_JOB_ID']=='114451'
r=int(os.environ['SLURM_PROCID']);props=torch.cuda.get_device_properties(0)
p=Path('runs/stage7a_bench/mmlong_node02_2gpu_20260915')/('torch_gpu_'+str(r)+'.json')
assert not p.exists()
p.write_text(json.dumps(dict(rank=r,device_count=torch.cuda.device_count(),torch_uuid=str(props.uuid),name=props.name,total_memory=props.total_memory,nvidia_gpu_inventory=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,pci.bus_id,name','--format=csv,noheader'],text=True),slurm_job_id=os.environ['SLURM_JOB_ID'],slurm_step_id=os.environ.get('SLURM_STEP_ID'),cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES')),indent=2)+'\n')
print(p.read_text(),flush=True)
