"""Record the actual V3 stop; never manufacture scientific results."""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage8c.prepare import ROOT, save, sha


def main():
    at=datetime.now(timezone.utc).isoformat()
    cfg=ROOT/'audit/technical_config_v3.json'
    config=json.loads(cfg.read_text())
    assert all(sha(p)==h for p,h in config['source_sha256'].items())
    failures=[]
    for rank,item in [(0,'2579'),(1,'2433')]:
        p=ROOT/'technical_v3'/f'worker{rank}'/'failure.json'
        r=json.loads(p.read_text())
        assert 'V3 decomposition outside frozen BF16 tolerance' in r['traceback']
        failures.append(dict(rank=rank,item_id=item,path=str(p),sha256=sha(p),at=r['at']))
    jobs=[]
    for job,seconds,kind in [('118514',81,'harness_onset_coverage'),('118515',57,'manual_cached_position_ids'),('118518',57,'V3_decomposition_tolerance')]:
        status=subprocess.run(['scontrol','show','job',job,'-o'],text=True,capture_output=True)
        path=ROOT/'audit'/f'slurm_{job}_final.txt'
        with path.open('x') as stream:stream.write(status.stdout+status.stderr)
        jobs.append(dict(slurm_job_id=job,node='node02',gpus=2,allocated_seconds=seconds,
                         gpu_hours=2*seconds/3600,status='FAILED',reason=kind,status_capture=str(path)))
    queue=subprocess.run(['squeue','-u','hyunjin','-h','-o','%i %T %N %b'],text=True,capture_output=True,check=True)
    with (ROOT/'audit/final_squeue.txt').open('x') as stream:stream.write(queue.stdout)
    assert not any(j['slurm_job_id'] in queue.stdout for j in jobs)
    validation=dict(at=at,status='STOP_TECHNICAL_V3',pass_checks=False,scientific_runs=0,
        failures=failures,config_sha256=sha(cfg),thresholds=dict(relative_l2_max=.02,absolute_max=.125),
        measured_error_values=None,
        measurement_limitation='The failed assertion did not serialize max_rel/max_abs or intermediate arrays. At least one bound failed on each tested item; which bound and magnitudes are unavailable. No quantitative decomposition-effect claim.',
        checks=dict(V1='Preceding native/gain1 token, committed-logit, RNG, feature/score assertions passed on two initial prefixes by code-path evidence; all-four coverage incomplete.',
                    V2='Preceding never-trigger gain2 exactness assertions passed on those two prefixes by code-path evidence; full audit incomplete.',
                    V3='FAILED on2579 and2433; no tolerance change or further GPU retry.',
                    V4='Independent replay, earlier-cache identity, later-layer cache change and continuation assertions returned successfully before V3 failure; standalone metrics not serialized.',
                    V5='Online/offline onset and passive feature comparisons passed on two initial prefixes; remaining-prefix coverage incomplete.',
                    V6='Final formal audit not reached; inference API was designed without oracle fields.'),
        diagnosis='unknown',implication='Cannot start development or interpret gain efficacy. Preserve cohorts and all attempts.')
    save(ROOT/'stage8c_v2_technical_validation.json',validation)
    notrun=dict(at=at,status='not_run_technical_gate',reason='Required V3 decomposition check failed',
                scientific_observations=0,technical_validation=str(ROOT/'stage8c_v2_technical_validation.json'))
    for name in ['dev_dose_results','dose_freeze','test_primary_accuracy','family_clustered_inference',
                 'subtype_heterogeneity','timing_control256','rescue_collateral_review']:
        save(ROOT/f'stage8c_v2_{name}.json',dict(notrun,dose=None) if name=='dose_freeze' else notrun)
    schema=pa.schema([('item_id',pa.string()),('arm',pa.string()),('event_index',pa.int64()),
                      ('T_M_U',pa.string()),('L_plus_minus_unknown',pa.string()),('review_status',pa.string())],
                     metadata={b'status':b'not_run_technical_gate',b'reason':b'V3 failure; zero annotated observations'})
    pq.write_table(pa.Table.from_pylist([],schema=schema),ROOT/'stage8c_v2_local_read_audit128.parquet')
    resources=dict(at=at,jobs=jobs,allocated_gpu_hours=sum(j['gpu_hours'] for j in jobs),
         remaining_active_allocations=0,remaining_authorized_gpu_work_under_failed_gate=0,
         scientific_runtime_overhead=None,
         provisional_preflight_estimate='40–100GPUh dev;150–350GPUh initial full conditional stage; withdrawn as ETA because technical gate failed',
         eta='No scientific completion ETA until validity is established')
    save(ROOT/'stage8c_v2_runtime_overhead.json',resources)
    family=json.loads((ROOT/'stage8c_v2_family_manifest.json').read_text())
    report=f'''# Stage8C v2 — STOP at technical validation

Updated {at}.

**The required V3 visual-decomposition validation failed. No development,
held-out, timing-control or intervention efficacy experiment was launched.**
This is an implementation-validity stop, not a null or harmful scientific result.

## Completed preparation

- User-approved plan and machine policies read; original plan preserved.
- Existing3040-item MathVision test data/images and pinned Qwen3-VL-2B-Thinking
  reused; no dataset/model download, no environment installation.
- Conservative input-only family audit:575 prior MathVision item IDs excluded,
  then full connected-family exclusion including prior external images.
  {family['eligible_representatives']} eligible independent representatives.
- Frozen128 development and512 test items; one item per identified family;
  disjoint from each other and identified prior-use families. Frozen256 timing
  and128 local-read subsets selected before outcomes.
- Both cohorts cover15 subjects, all5 difficulty levels and choice/free-response
  formats. Topology has4 eligible representatives and was not sampled under
  proportional allocation. Fine problem type, visual density/entity counts are
  missing; they were not invented.
- Family rules combine exact/rescaled image signatures, conservative perceptual
  candidates, specific repeated templates and known1707/1245 alias. They may
  overmerge; independent redraws may still escape. This is not exhaustive
  semantic family certification.
- Online gain/cache wrapper, CPU tests and guarded execution/scoring scaffolding
  written. The scientific runner remains unvalidated and must not be launched.

## Technical evidence and stop

Three short two-A6000 node02 jobs, with no tmux allocation:

| Slurm job | Duration | Result |
|---|---:|---|
|118514|81s|Harness incorrectly required every prefix to contain an onset. Existing native traces distinguished triggered and nontriggered audit prefixes.|
|118515|57s|Manual independent cache-validation call omitted suffix position IDs. Source inspection and a CPU regression reproduced the shape error; existing repository helper reused.|
|118518|57s|V3 reconstruction exceeded the frozen BF16 tolerance on both audited initial items2579 and2433. **STOP.**|

The first two repairs changed validation callers only; gain/detector/cohorts and
numerical bounds remained unchanged. The final V3 bounds were relative L2<=.02
and max absolute error<=.125. The failing assertion did **not** save individual
error magnitudes or which bound failed. Cause remains **unknown**. Do not
attribute the failure to BF16 rounding or to the intervention formula without
additional evidence.

Control-flow evidence shows preceding gain1 and non-trigger token/logit/RNG
equalities, detector comparisons and independent cache replay assertions passed
on those two prefixes. Their complete metric records and the remaining two
prefixes were not finalized. Formal V6 was not reached. Thus the six-check gate
has **not** passed.

Raw evidence: [final validation](stage8c_v2_technical_validation.json),
[worker0 failure](technical_v3/worker0/failure.json),
[worker1 failure](technical_v3/worker1/failure.json),
[original coverage diagnostic](audit/technical_coverage_diagnostic.json),
[resource record](stage8c_v2_runtime_overhead.json).

## Scientific work not run

Dev512 dose trajectories, dose selection, test1024 paired trajectories, random
timing256, semantic audit128, rescue/collateral review and optional extension
are all unmeasured. Required downstream JSON/Parquet files explicitly record
not-run status; the annotation table has zero rows. Seven scientific figures
are not generated because no corresponding data exist. There is no accuracy,
dose-response, timing or generality conclusion, and no chosen dose.

## Resources and next decision

All three allocations are released: approximately{resources['allocated_gpu_hours']:.4f}
GPU-hours total. No current stage GPU work remains allowed past the failed gate.
The earlier compute ranges are provisional estimates, **not a current ETA**.

Exactly one recommendation: **diagnose and repair visual-contribution
decomposition, preserving these cohorts and the failed attempts, then revalidate
V1–V6 before resuming Stage8C.** This report does not launch that follow-up or
Block3B. No tolerance relaxation, dose change or cohort replacement was made.
'''
    with (ROOT/'stage8c_v2_summary.md').open('x') as stream:stream.write(report)
    artifacts={str(p):sha(p) for p in ROOT.glob('stage8c_v2_*') if p.is_file()}
    support={str(p):sha(p) for p in ROOT.glob('audit/*') if p.is_file()}
    support.update({str(p):sha(p) for p in ROOT.glob('technical*/*/*.json')})
    save(ROOT/'audit/technical_stop_freeze.json',dict(at=at,artifacts_sha256=artifacts,support_sha256=support,
         scientific_gate_pass=False,stop_enforced=True,original_configs_unchanged=True))
    print(json.dumps(dict(status='STOP_TECHNICAL_V3',scientific_runs=0,gpu_hours=resources['allocated_gpu_hours'],
                         active_stage_allocations=0,report=str(ROOT/'stage8c_v2_summary.md'))))


if __name__=='__main__':main()
