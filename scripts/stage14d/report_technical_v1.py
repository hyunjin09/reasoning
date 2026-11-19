"""Technical-only accounting and validation. Never grade generated answers."""
import datetime as dt
import json
from pathlib import Path
import re
import statistics
import subprocess
from scripts.stage14d.prepare_technical_v1 import ROOT,save,sha


def accounting():
    previous=json.loads((ROOT/'audit/technical_startup_failure_accounting_v1.json').read_text())['jobs']
    jobs=list(previous)
    for path in sorted((ROOT/'audit/technical_launches_v2').glob('job_*.json')):
        launch=json.loads(path.read_text());jid=launch['job_id']
        captured=ROOT/'audit/technical_final_slurm_v2'/f'job_{jid}.json'
        raw=json.loads(captured.read_text())['scontrol'] if captured.exists() else subprocess.run(
            ['scontrol','show','job',str(jid),'-o'],text=True,capture_output=True,check=True).stdout
        fields=dict(re.findall(r'(\w+)=(\S+)',raw))
        assert fields['JobState'] in {'COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY'},'Wait for allocation release'
        h,m,s=map(int,fields['RunTime'].split(':'));elapsed=h*3600+m*60+s
        jobs.append(dict(job_id=jid,state=fields['JobState'],node=fields['NodeList'],gpus=1,
            elapsed_seconds=elapsed,allocated_GPUh=elapsed/3600,scontrol=raw))
    return dict(at=dt.datetime.now(dt.timezone.utc).isoformat(),jobs=jobs,
        total_allocated_GPUh=sum(j['allocated_GPUh'] for j in jobs),ceiling_GPUh=2,
        source='Final scontrol runtime; sacct storage is disabled. Includes failed startup and engine reloads.',
        scientific_GPUh=0,all_jobs_released=True)


def run():
    tasks=json.loads((ROOT/'spec/technical_calls_v1.json').read_text())['rows'];records=[];repeats=[];pairs=[]
    missing=[];failure=[]
    for task in tasks:
        folder=ROOT/'raw/technical_v1'/task['task_id']
        if not (folder/'result.json').exists():missing.append(task['task_id']);continue
        result=json.loads((folder/'result.json').read_text())
        assert result['input_sha256']==sha(folder/'input.json')
        assert result['generation_sha256']==sha(folder/'generation.json')
        assert result['attention_audit_sha256']==sha(folder/'attention_audit.json')
        g=json.loads((folder/'generation.json').read_text());a=json.loads((folder/'attention_audit.json').read_text())
        rec=dict(task_id=task['task_id'],model=task['model'],role=task['role'],arm=task['arm'],image_access=task['image_access'],
            tokens=g['tokens'],request_seconds=g['request_seconds'],finish_reason=g['finish_reason'],prompt_tokens=g['prompt_tokens'],
            preserved_input=True,layers=len(a['layers']),source_prefix_bytes_checked=True,
            reference_max_abs_error=max((x.get('reference_max_abs_error',0) for x in a['layers'].values()),default=None),
            masked_query_layer_count=sum(x['masked_queries'] for x in a['layers'].values()),
            original_result=str(folder/'result.json'))
        records.append(rec)
        if task['repeat']=='repeat1':repeats.append(json.loads((folder/'repeat_validation.json').read_text()))
        if task['image_access']=='OFF_FUTURE':
            on_path=ROOT/'raw/technical_v1'/task['task_id'].replace('OFF_FUTURE','ON')
            if not (on_path/'result.json').exists():continue
            on=json.loads((on_path/'attention_audit.json').read_text())
            ong=json.loads((on_path/'generation.json').read_text())
            equal_cache=all(a['layers'][k]['prefill_K_sha256']==on['layers'][k]['prefill_K_sha256'] and
                a['layers'][k]['prefill_V_sha256']==on['layers'][k]['prefill_V_sha256'] for k in a['layers'])
            pair=dict(model=task['model'],role=task['role'],prefill_KV_bitwise_equal=equal_cache,
                prompt_ids_equal=g['prompt_token_ids']==ong['prompt_token_ids'],
                first_sampled_token_equal=g['generated_token_ids'][0]==ong['generated_token_ids'][0],
                masked_all36_layers=g['tokens']>1 and len(a['layers'])==36 and all(x['masked_queries']==g['tokens']-1 for x in a['layers'].values()),
                exact_zero_reference_image_mass=all(x.get('image_attention_mass_max_head')==0 for x in a['layers'].values()),
                cached_prefill_retained=all(x.get('old_KV_preserved',False) for x in a['layers'].values()))
            pairs.append(pair)
    for p in (ROOT/'audit/technical_workers_v2').glob('*/engine_*/failure.json'):
        failure.append(dict(path=str(p),**json.loads(p.read_text())))
    passed=(not missing and not failure and len(repeats)==4 and len(pairs)==4 and
        all(r['first128_or_whole_short_exact'] for r in repeats) and
        all(all(v is True for k,v in p.items() if k not in {'model','role'}) for p in pairs))
    charges=accounting();assert charges['total_allocated_GPUh']<=2
    save(ROOT/'audit/technical_gpu_resource_accounting_v1.json',charges)
    rates={}
    for model in 'IT':
        for mode in ['ON','OFF_FUTURE']:
            group=[r for r in records if r['model']==model and r['image_access']==mode]
            if group:rates[model+'_'+mode]=dict(calls=len(group),tokens=sum(x['tokens'] for x in group),
                request_seconds=sum(x['request_seconds'] for x in group),
                tokens_per_request_second=sum(x['tokens'] for x in group)/sum(x['request_seconds'] for x in group),
                median_seconds=statistics.median(x['request_seconds'] for x in group))
    validation=dict(at=dt.datetime.now(dt.timezone.utc).isoformat(),status='PASS_TECHNICAL_ONLY' if passed else 'FAIL_HOLD',
        completed_checks=len(records),planned_calls=24,missing=missing,failures=failure,records=records,
        fresh_engine_repeat_comparisons=repeats,image_access_pairs=pairs,request_throughput=rates,
        technical_sources=4,technical_prefixes=8,main300_source_reviews_complete=False,main420_anchors_complete=False,
        scientific_outputs_generated=0,answers_or_accuracy_inspected=False,main_release=False)
    save(ROOT/'audit/technical_preflight_validation_v1.json',validation)
    print(json.dumps(dict(status=validation['status'],completed=len(records),missing=len(missing),
        gpu_hours=charges['total_allocated_GPUh'],rates=rates),indent=2))


if __name__=='__main__':run()
