"""One Slurm allocation, finite technical profiles, no downstream launcher."""
import os, subprocess, sys, time, signal
from scripts.stage14d1_recovery.contracts import *

def main():
    assert 'SLURM_JOB_ID' in os.environ
    start=time.time()
    matrix=load(R/'protocol/execution_matrix.json')
    deadline=start+matrix['max_allocation_seconds']-90
    exits=[]
    for profile in matrix['profiles']:
        if time.time()>deadline-300:
            exits.append(dict(profile=profile['name'],status='NOT_ADMITTED_DEADLINE'))
            break
        env=dict(os.environ,VLLM_ENABLE_V1_MULTIPROCESSING=str(profile['multiprocessing']),
                 SAVA_RECOVERY_TRACE=str((R/'traces'/profile['name']).resolve()),
                 SAVA_RECOVERY_DEADLINE=str(deadline))
        # No model/library upgrade; each profile gets a genuinely fresh process/engine.
        command=[sys.executable,'-m','scripts.stage14d1_recovery.worker',profile['name']]
        proc=subprocess.Popen(command,env=env,start_new_session=True)
        try:
            code=proc.wait(timeout=max(1,deadline-time.time()))
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait()
            code=124
        exits.append(dict(profile=profile['name'],returncode=code,finished_at=now()))
        save(R/'audit'/f'profile_exit_{profile["name"]}.json',exits[-1])
        if code!=0:
            # Preserve the failure; never automatically retry an equivalent profile.
            break
    save(R/'audit/runner_exit.json',dict(at=now(),job=os.environ['SLURM_JOB_ID'],profiles=exits,
                                       elapsed_seconds=time.time()-start,no_scientific_pilot=True))

if __name__=='__main__':
    main()
