"""Assemble complete two-worker evidence; never turn partial work into completion."""
import shutil
from pathlib import Path
from scripts.stage7a.common import ROOT,read_json,sha,write_json
from scripts.stage7a_bench.causal_pool_v12 import partition_entries
from scripts.stage7a_bench.causal_run_v14 import validate_mechanics
from scripts.stage7a_bench.pilot_freeze_v14 import load_frozen_pilot,dependency_hashes

OUT=ROOT/'outputs/stage7a_bench_v2'


def reference(p):return dict(path=str(p.relative_to(ROOT)),sha256=sha(p))


def aggregate(run_id,tokenizer):
    dirs=[OUT/'causal_pilot/raw'/(run_id+'__worker'+str(i)) for i in range(2)]
    records=[]
    for i,p in enumerate(dirs):
        record={k:read_json(p/(k+'.json')) for k in ['signature','environment','run_summary']}
        wrapper_path=OUT/'causal_pilot/wrappers'/(p.name+'.json');record['wrapper']=read_json(wrapper_path)
        if record['wrapper'].get('completed') is not True or record['wrapper'].get('exit_code')!=0 or record['run_summary'].get('completed') is not True:
            raise ValueError('Both worker processes must complete successfully')
        records.append(record)
    signature=records[0]['signature'];execution=signature['execution_signature']
    pilot=load_frozen_pilot(execution['pilot'],tokenizer);entries=pilot['selected_entries']
    if execution['dependencies']!=dependency_hashes():raise ValueError('Worker dependencies changed')
    config=read_json(OUT/'config/runtime_node02_two_gpu_v14.json')
    expected_runtime=config['runtime']['slurm_allocation']
    uuids=[r['environment'].get('gpu_uuid') for r in records]
    if len(set(uuids))!=2 or set(uuids)!=set(config['assigned_gpu_uuids']):
        raise ValueError('Two distinct authorized GPUs required')
    all_events={};sources={};elapsed=0.
    for i,(directory,record) in enumerate(zip(dirs,records)):
        sig=record['signature'];summary=record['run_summary'];env=record['environment'];wrapper=record['wrapper']
        device_certificate=read_json(directory/'device_mechanics_certificate.json')
        if device_certificate.get('gpu_uuid')!=env['gpu_uuid']:
            raise ValueError('Per-device mechanics GPU mismatch')
        validate_mechanics(device_certificate,execution,entries)
        expected_ids=[e['id'] for e in partition_entries(entries,i)]
        if (sig['execution_signature']!=execution or sig['mechanics'] is not False or sig['event_ids']!=expected_ids or
            sig['mechanics_certificate']!=signature['mechanics_certificate'] or env['slurm_job_id']!=expected_runtime or
            wrapper['slurm_job_id']!=expected_runtime or env['parameter_dtype']!='torch.bfloat16' or
            env['node'].split('.')[0]!='node02' or len(summary['events'])!=len(expected_ids)):
            raise ValueError('Worker identity, runtime or fixed partition differs')
        if not isinstance(summary['seconds'],(float,int)) or summary['seconds']<=0:raise ValueError('Invalid worker time')
        elapsed+=summary['seconds']
        for eid,event in zip(expected_ids,summary['events']):
            if eid in all_events:raise ValueError('Duplicate scientific event')
            for k,extension in [('event','.json'),('distributions','.npz')]:
                ref=event[k];expected=directory/'events'/(eid+extension)
                if ROOT/ref['path']!=expected or sha(expected)!=ref['sha256']:raise ValueError('Swapped worker artifact')
                sources[str(expected.relative_to(ROOT))]=ref['sha256']
            data=read_json(ROOT/event['event']['path'])
            if data['id']!=eid or data['complete'] is not True or data['source_assay_mechanics'] is not False:
                raise ValueError('Incomplete or wrong event')
            all_events[eid]=event
        for path,digest in execution['dependencies'].items():
            if sha(directory/'source_snapshot'/path)!=digest:raise ValueError('Worker source snapshot changed')
    if set(all_events)!={e['id'] for e in entries}:raise ValueError('Incomplete pilot membership')
    cert_ref=signature['mechanics_certificate']
    if sha(ROOT/cert_ref['path'])!=cert_ref['sha256']:
        raise ValueError('Parent mechanics certificate changed')
    cert=read_json(ROOT/cert_ref['path']);validate_mechanics(cert,execution,entries)
    dest=OUT/'causal_pilot/raw'/run_id;dest.mkdir(exist_ok=False)
    new_signature=dict(signature,event_ids=[e['id'] for e in entries])
    write_json(dest/'signature.json',new_signature,freeze=True)
    for name,digest in execution['dependencies'].items():
        target=dest/'source_snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(dirs[0]/'source_snapshot'/name,target)
    final=[]
    for entry in entries:
        record={}
        for k,ext in [('event','.json'),('distributions','.npz')]:
            target=dest/'events'/(entry['id']+ext);target.parent.mkdir(exist_ok=True)
            shutil.copyfile(ROOT/all_events[entry['id']][k]['path'],target);record[k]=reference(target)
        final.append(record)
    environment=dict(records[0]['environment'],pool_workers=2,worker_environments=[r['environment'] for r in records],
        execution_scope='Two Slurm-bound single-GPU workers; per-worker cache CPU residency. Longest events serialize after peer process exit.')
    write_json(dest/'environment.json',environment,freeze=True)
    write_json(dest/'run_summary.json',dict(completed=True,events=final,mechanics=False,seconds=elapsed,
        seconds_definition='Sum of measured one-GPU worker runtimes, including loading and waits; GPU-seconds, not pool wall time.',
        pool_workers=2,passive_features_collected=False,worker_artifact_sha256=sources),freeze=True)
    write_json(dest/'pool_provenance.json',dict(worker_runs=[str(d.relative_to(ROOT)) for d in dirs],
        worker_records=records,scientific_selection_changed=False,all_original_worker_artifacts_preserved=True),freeze=True)
    return dest
