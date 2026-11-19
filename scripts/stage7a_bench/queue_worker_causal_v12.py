"""Record real worker exits and complete the pool only after both have exited."""
import argparse,os,subprocess,sys,time
from scripts.stage7a.common import ROOT,write_json,read_json
sys.path.insert(0,str(ROOT/'infra'))
from harness_state import mutate_gpu_queue,now_iso


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True)
    args,extra=parser.parse_known_args();mechanics='--mechanics' in extra
    rank=int(os.environ.get('SLURM_PROCID','0'));count=int(os.environ.get('SLURM_NTASKS','1'))
    if count!=(1 if mechanics else 2) or rank not in range(count):raise RuntimeError('Unexpected Slurm worker layout')
    run_id=args.run_id if mechanics else args.run_id+'__worker'+str(rank)
    command=[str(ROOT/'.venv/bin/python'),'scripts/stage7a_bench/causal_run_v12.py','--run-id',run_id,*extra]
    if not mechanics:command+=['--worker-index',str(rank)]
    code=1
    try:code=subprocess.call(command)
    finally:
        record=dict(exit_code=code,completed=code==0,slurm_job_id=os.environ.get('SLURM_JOB_ID'),
                    slurm_step_id=os.environ.get('SLURM_STEP_ID'),worker_index=rank,finished_at=now_iso())
        write_json(ROOT/'outputs/stage7a_bench_v2/causal_pilot/wrappers'/(run_id+'.json'),record,freeze=True)
    if rank==0 and not mechanics and code==0:
        peer=ROOT/'outputs/stage7a_bench_v2/causal_pilot/wrappers'/(args.run_id+'__worker1.json')
        while not peer.exists():time.sleep(1)
        try:
            from transformers import AutoTokenizer
            from scripts.stage7a_bench.aggregate_causal_pool_v12 import aggregate
            config=read_json(ROOT/'outputs/stage7a_bench_v2/config/runtime_node02_two_gpu_v12.json')
            tokenizer=AutoTokenizer.from_pretrained(config['model_checkpoint'],local_files_only=True)
            aggregate(args.run_id,tokenizer)
        except BaseException:
            code=1
            import traceback
            traceback.print_exc()
        finally:
            write_json(ROOT/'outputs/stage7a_bench_v2/causal_pilot/wrappers'/(args.run_id+'.json'),
                dict(exit_code=code,completed=code==0,slurm_job_id=os.environ.get('SLURM_JOB_ID'),
                     finished_at=now_iso(),pool_workers=2),freeze=True)
    if rank==0:
        def finish(queue):
            job=next(j for j in queue['jobs'] if j['id']=='stage7a_bench_v2_causal_'+args.run_id)
            if job['slurm_job_id']!=os.environ.get('SLURM_JOB_ID'):raise RuntimeError('Queue allocation differs')
            job.update(status='succeeded' if code==0 else 'failed',exit_code=code,completed=code==0,finished_at=now_iso())
        mutate_gpu_queue(ROOT,finish)
    sys.exit(code)


if __name__=='__main__':main()
