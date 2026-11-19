"""Bounded CPU-only gate coordinator; no settings selection or scientific analysis."""
import argparse
import subprocess
import time
from collections import defaultdict
from scripts.stage14b.common import *
from scripts.stage14b.protocol import extract
from scripts.stage14b.validate import checked,preflight
from scripts.stage14b.status import status


def automated_response_review():
    """Validate readable committed-final examples per input branch, without gold."""
    groups=defaultdict(list);packets=[]
    metadata={}
    for name in ('mathvision_3040_eval_manifest','mathvision_e1000_eval_manifest','mathverse_788_eval_manifest'):
        for r in rows(ROOT/'manifests'/f'{name}.jsonl'):metadata[r['identity'],name]=r
    for t in all_tasks('preflight'):
        if t['condition']=='seedcheck':continue
        result=checked(t);assert result is not None
        g=result['generation']
        name='mathverse_788_eval_manifest' if t['identity'].startswith('verse:') else 'mathvision_e1000_eval_manifest' if t['condition']=='evidence' else 'mathvision_3040_eval_manifest'
        # Only source options, no gold or model-correctness comparison.
        options=metadata[t['identity'],name]['options']
        extraction=extract(g['raw_decoded_response'],options,t['model_key'],g['finish_reason'])
        group=t['model_key']+'_'+('mathverse' if t['identity'].startswith('verse:') else t['condition'])
        packet=dict(task_id=t['task_id'],group=group,extraction=extraction,tokens=g['tokens'],finish_reason=g['finish_reason'],
            response_tail=g['raw_decoded_response'][-2500:],generation_sha256=sha(Path(result['receipt']).parent/'generation.json'))
        packets.append(packet)
        if extraction['status']=='EXTRACTED':groups[group].append(t['task_id'])
    required={m+'_'+c for m in 'IT' for c in ('image','evidence','mathverse')}
    passed=required<=set(groups)
    # This is explicitly an automated technical inspection, not a human annotation claim.
    save(ROOT/'audit/preflight_response_review.json',dict(at=now(),correctness_used=False,
        extraction_and_format_review_pass=passed,reviewed_task_ids=[r['task_id'] for r in packets],packets=packets,
        extracted_by_branch=dict(groups),required_branches=sorted(required),
        review_scope='Automatic response-only schema/extraction inspection under frozen rules; raw excerpts retained for agent review. No scientific correctness or semantic gold comparison.',
        pass_rule='At least one explicit committed answer per model/native-MV/evidence-MV/MathVerse branch; no accuracy criterion, no retuning. Failure holds for agent inspection.'))
    assert passed,('technical extraction coverage failed',required-set(groups))


def run(hours=48):
    assert 0<hours<=72
    assert os.environ.get('SLURM_JOB_ID'),'Coordinator is a finite CPU-only Slurm job'
    job=os.environ['SLURM_JOB_ID'];dest=ROOT/'audit/coordinator'/job;start=time.monotonic()
    save(dest/'started.json',dict(at=now(),hours=hours,job=job,gpus=0,authorized_main_calls=17536,maximum_concurrent_gpus=8,
        stop='Failure, time bound, or main launch/startup monitoring completed. Never launches confirmation/Stage14C.'))
    try:
        while time.monotonic()-start<hours*3600:
            s=status();live=[j for j in s['jobs'] if not j['closed']]
            pp=[j for j in s['jobs'] if j['mode']=='preflight' and j['job_id'] in ('136015','136016')]
            done=sum(v['complete'] for v in s['counts']['preflight'].values())
            print(now(),'preflight',done,'/24',[(j['job_id'],j['state']) for j in live],flush=True)
            if done==24 and not live:break
            if any(j['closed'] and j['state']!='COMPLETED' for j in pp):
                raise RuntimeError('Repaired technical worker failed; preserve evidence and require focused diagnosis, no auto retry')
            time.sleep(60)
        else:raise TimeoutError('Bounded preflight coordinator expired; pending jobs/evidence preserved')
        automated_response_review();preflight()
        assert load(ROOT/'audit/preflight_validation.json')['pass']
        # Capture all immutable technical evidence before the full census starts.
        save(ROOT/'audit/technical_gate_release.json',dict(at=now(),validation_sha256=sha(ROOT/'audit/preflight_validation.json'),
            response_review_sha256=sha(ROOT/'audit/preflight_response_review.json'),correctness_used=False,
            main_calls_authorized=17536,main_shards=dict(I=3,T=5),mode='Automatic mechanical release under approved Stage14B'))
        subprocess.run(['.venv/bin/python','-m','scripts.stage14b.launch_v2','main','--instruct','3','--thinking','5','--hours','72'],check=True)
        save(dest/'main_launched.json',dict(at=now(),authorized_calls=17536,scientific_outcomes_inspected=False))
        # Check early execution, bounded by remaining coordinator lifetime.
        while time.monotonic()-start<hours*3600:
            s=status();main=[j for j in s['jobs'] if j['mode']=='main']
            bad=[j for j in main if j['closed'] and j['state']!='COMPLETED']
            if bad:raise RuntimeError('Main worker failure; no automatic scientific retries or further phase launch')
            observed=[j for j in main if (j.get('heartbeat') or {}).get('completed',0)>=3 or j.get('exit')]
            print(now(),'main startup observed',len(observed),'/8',flush=True)
            if len(observed)==len(main)==8:
                save(dest/'exit.json',dict(at=now(),status='MAIN_LAUNCHED_AND_FIRST_SAMPLES_VERIFIED',jobs=[j['job_id'] for j in main],
                    next='Main finite workers drain. Freeze raws and perform arm-separated scoring/review before analysis; no further automatic launch.',gpus=0))
                return
            time.sleep(60)
        save(dest/'exit.json',dict(at=now(),status='MAIN_LAUNCHED_MONITOR_TIMEBOUND',next='Inspect main worker progress/Slurm. No extra launch.',gpus=0))
    except BaseException as exc:
        import traceback
        save(dest/'hold.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc(),main_launch_blocked=not (dest/'main_launched.json').exists()))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--hours',type=float,default=48);a=p.parse_args();run(a.hours)
