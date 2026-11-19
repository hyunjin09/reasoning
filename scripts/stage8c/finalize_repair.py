"""Assemble bounded-repair evidence and stop if the unchanged V3 still fails."""
import json
import os
import subprocess
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from scripts.stage8c.prepare import save,sha
from scripts.stage8c.prepare_repair import ROOT


def main():
    at=datetime.now(timezone.utc).isoformat()
    summaries={p:json.loads((ROOT/'audit'/f'{p}_summary.json').read_text()) for p in ['forensic','candidate']}
    frames=[pq.read_table(ROOT/'audit'/f'{p}_forensic_metrics.parquet') for p in summaries]
    pq.write_table(pa.concat_tables(frames,promote_options='default'),ROOT/'stage8c_v3_forensic_metrics.parquet')
    raw={p:[json.loads(line) for f in sorted((ROOT/p/'items').glob('*/forensic_rows.jsonl'))
            for line in f.read_text().splitlines()] for p in summaries}
    manifest=json.loads((ROOT/'stage8c_repair_prefix_manifest.json').read_text())
    preservation=json.loads((ROOT/'audit/original_scientific_freeze.json').read_text())
    assert all(sha(p)==h for p,h in preservation['sha256'].items())
    assert sha('code/visual_reasoning/stage8c/gain.py')==preservation['original_gain_sha256']
    source=dict(at=at,all_pass=all(s['partition_pass'] for s in summaries.values()),
        visual_definition='Actual image patch placeholder KV positions from frozen preprocessing.',
        nonvisual_definition='Every other valid attended KV position, including multimodal boundary/system/user/assistant prompt and prior reasoning tokens.',
        masked_and_padding='Explicitly excluded from K; these unpadded last-query cases have none.',
        token_index_manifests={str(p):sha(p) for phase in summaries for p in (ROOT/phase/'items').glob('*/token_index_manifest.json')},
        partition_manifests={str(p):sha(p) for phase in summaries for p in (ROOT/phase/'items').glob('*/source_partitions.json')},
        per_case={phase:{c['case_id']:dict(valid_kv=next(r['valid_kv'] for r in raw[phase] if r['case_id']==c['case_id'] and r['token_index']==c['anchor']),
            visual=next(r['visual_count'] for r in raw[phase] if r['case_id']==c['case_id']),
            overlap=sum(r['overlap_count'] for r in raw[phase] if r['case_id']==c['case_id']),
            uncovered=sum(r['uncovered_count'] for r in raw[phase] if r['case_id']==c['case_id'])) for c in manifest['cases']} for phase in summaries})
    save(ROOT/'stage8c_source_partition_audit.json',source)
    for name,keys in [('prewo_reconstruction',['pre_native_replay','pre_legacy','pre_bf16_sum','pre_fp32_diagnostic']),
                      ('postwo_reconstruction',['post_native_reproject','post_legacy','post_bf16_separate','post_bf16_joint']),
                      ('residual_reconstruction',['residual_native_replay','residual_separate','residual_left_associative','residual_joint'])]:
        save(ROOT/f'stage8c_{name}.json',dict(at=at,thresholds=dict(relative_l2=.02,max_abs=.125),
            implementations={p:{k:s['metrics'][k] for k in keys} for p,s in summaries.items()},
            per_case={p:{c:{k:v[k] for k in keys} for c,v in s['per_case'].items()} for p,s in summaries.items()},
            interpretation='First numerical failure is pre-W_O. Later-stage values are required forensic observations, not evidence overruling that failure. FP32 references cannot certify BF16 science.'))
    save(ROOT/'stage8c_gqa_audit.json',dict(at=at,pass_check=all(s['gqa_pass'] for s in summaries.values()),
        query_heads=16,kv_heads=8,replication_factor=2,query_to_kv=[i//2 for i in range(16)],
        native_tensor_replication_equal=True,rotary_and_cache='Exact Q/K/V received by native eager attention; Q/K already rotary-applied; complete updated native cache.',
        attention_probabilities='Exact native returned BF16 probabilities; never recomputed for decomposition.',
        native_full_attention_replay_exact=all(s['metrics']['pre_native_replay']['max_abs']==0 for s in summaries.values())))
    save(ROOT/'stage8c_projection_bias_audit.json',dict(at=at,actual_module_bias_exists=False,bias_norm=0.,
        count=0,all_measured_layers=[19,20,21,22],verified_every_row=not any(s['projection_bias_present'] for s in summaries.values()),
        native_projection_replay_exact=all(s['metrics']['post_native_reproject']['max_abs']==0 for s in summaries.values())))
    save(ROOT/'stage8c_dtype_accumulation_audit.json',dict(at=at,
        scientific_weights_q_k_v_probabilities_and_outputs='torch.bfloat16',
        native_softmax='Native implementation accumulates softmax in FP32 and casts to query BF16, unchanged.',
        bmm_internal_accumulation='Not directly exposed by the PyTorch API; BF16 inputs/output and allow_bf16_reduced_precision_reduction flags recorded per row/environment. No unsupported exact accumulator-dtype claim.',
        legacy_split_cast_order='Each source BMM rounds to BF16 independently; original audit then promotes both outputs to FP32 before addition. Separate W_O calls also round independently before addition.',
        candidate_cast_order='Complete native KV axis, BF16 zero-masked source weights; BF16 BMM parts, BF16 combination, native BF16 W_O and residual order. No scientific FP32 conversion.',
        diagnostic_fp32='Captured native BF16 weights/values promoted to FP32, TF32 disabled locally, partition BMMs combined before a single native-dtype cast. Diagnostic only.',
        measurement_reduction_dtype='FP32 norms, differences and maxima; largest values/indices retained.',
        native_framework_source='Installed transformers/models/qwen3_vl/modeling_qwen3_vl.py',
        native_framework_sha256=sha('.venv/lib/python3.12/site-packages/transformers/models/qwen3_vl/modeling_qwen3_vl.py'),
        production_code_changed=False,candidate_not_certified=True))
    required=['pre_bf16_sum','post_bf16_joint','post_bf16_separate','residual_joint']
    passed=all(summaries['candidate']['metrics'][m]['all_pass'] for m in required)
    if passed:
        raise RuntimeError('V3 candidate passed: full V1–V6 is required before a success report; do not use this stop finalizer.')
    save(ROOT/'stage8c_v1_v6_revalidation.json',dict(at=at,status='STOP_V3_REPAIR_FAILED',all_pass=False,
        V1=dict(status='not_run',reason='No certified repaired decomposition; fresh joint bundle prerequisite unmet'),
        V2=dict(status='not_run',reason='V3 repair failed'),
        V3=dict(status='failed',thresholds=dict(relative_l2=.02,max_abs=.125),
                source=str(ROOT/'audit/candidate_summary.json'),cases=8,families=4,
                individual_prefix_failures={c:[k for k in required if not values[k]['all_pass']] for c,values in summaries['candidate']['per_case'].items()}),
        V4=dict(status='not_run',reason='V3 repair failed; prior assertions not reused as a fresh pass'),
        V5=dict(status='not_run_as_joint_bundle',supporting_observation='Both forensic implementations reproduce stored native R exactly across all replayed prefixes; this does not replace fresh complete V1–V6.'),
        V6=dict(status='not_run_as_joint_bundle',reason='Scientific inference not resumed'),
        scientific_resume=False,selected_dose=None,recommendation='stop intervention branch'))
    jobs=[]
    queue=json.loads(Path('state/gpu_experiment_queue.json').read_text())
    for jid in ['stage8c_repair_forensic_v1','stage8c_repair_candidate_v1']:
        entry=next(x for x in queue['jobs'] if x['id']==jid)
        result=subprocess.run(['scontrol','show','job',entry['slurm_job_id'],'-o'],capture_output=True,text=True)
        log=ROOT/'audit'/f"slurm_{entry['slurm_job_id']}_final.txt"
        with log.open('x') as stream:stream.write(result.stdout+result.stderr)
        import re
        match=re.search(r'RunTime=(?:(\d+)-)?(\d+):(\d+):(\d+)',result.stdout)
        seconds=(int(match[1] or 0)*86400+int(match[2])*3600+int(match[3])*60+int(match[4])) if match else None
        timing_source='Slurm RunTime'
        if seconds is None:
            phase='candidate' if 'candidate' in jid else 'forensic'
            last_result=max(datetime.fromisoformat(json.loads(p.read_text())['at'])
                            for p in (ROOT/phase/'items').glob('*/result.json'))
            seconds=(last_result-datetime.fromisoformat(entry['created_at'])).total_seconds()
            timing_source='Approximate launch-to-last-result wall time; Slurm record expired and accounting is disabled. Includes startup, excludes final teardown.'
        jobs.append(dict(id=jid,slurm_job_id=entry['slurm_job_id'],node='node02',gpus=2,elapsed_seconds=seconds,
                         gpu_hours=2*seconds/3600,timing_source=timing_source,log=str(log)))
    active=subprocess.run(['squeue','-u','hyunjin','-h','-o','%i %T %N %b'],capture_output=True,text=True,check=True)
    assert not any(j['slurm_job_id'] in active.stdout for j in jobs)
    (ROOT/'audit/final_squeue.txt').write_text(active.stdout)
    save(ROOT/'audit/resources.json',dict(at=at,jobs=jobs,total_gpu_hours=sum(j['gpu_hours'] for j in jobs) if all(j['gpu_hours'] is not None for j in jobs) else None,
         remaining_stage_allocations=0,scientific_trajectories=0))
    baseline=summaries['forensic']['metrics'];candidate=summaries['candidate']['metrics']
    root_cause=f'''# Stage8C-R root cause

Supported diagnosis: **independently rounded BF16 source reductions do not
reconstruct the jointly reduced native attention within the fixed absolute-error
bound.** The first failing stage is pre-W_O. This is supported by exact native
replay, complete source partitions, exact GQA/head layout and a large reduction
of error when the diagnostic retains higher precision until the final cast.
This localizes the discrepancy to split reduction/cast order. It does not prove
the exact internal CUDA accumulator implementation or impossibility of every
other mathematically equivalent implementation.

All8 cases/4 families are retained, including2579/2433,3 triggered and5 nontrigger
anchors, and cached lengths through8192. Both implementations replayed the same
saved tokens with exact stored retrieval scores. There are2064 layer-query
records per implementation. Partition overlap/uncovered counts are zero; native
head, native projection and native residual replay errors are exactly zero.
Actual o_proj bias is absent on all measured layers.

Original split max absolute error:{baseline['pre_legacy']['max_abs']}; BF16
combined source output:{baseline['pre_bf16_sum']['max_abs']}. Maximum allowed:.125.
The FP32 diagnostic with a single BF16 cast reaches
{baseline['pre_fp32_diagnostic']['max_abs']} and passes these pre-W_O comparisons.
That reference changes intermediate precision and is **not** the certified
scientific intervention.

The one bounded repair candidate retained the complete native KV axis, zeroed
the complementary BF16 attention weights and preserved the original source
scope/post-W_O gain. It removes gathered-layout/reduction-shape differences.
Its pre-W_O max absolute error remains{candidate['pre_bf16_sum']['max_abs']};
separate projected contributions reach{candidate['post_bf16_separate']['max_abs']};
native-order residual reconstruction reaches{candidate['residual_joint']['max_abs']}.
Per-case failures are retained in the audits and Parquet; no average overrides
an individual failure. Later-stage errors are downstream forensic observations,
not independently diagnosed new defects while pre-W_O remains invalid.

No tolerance was widened; no scientific FP32 switch, native-minus-visual
definition of nonvisual contribution, or replacement cohort was used to force
an identity. The candidate is preserved but not promoted to scientific use.
The bounded repair failed; full V1–V6 and dev128 are not run.
'''
    (ROOT/'stage8c_repair_root_cause.md').write_text(root_cause)
    lines=['# Stage8C-R — bounded repair completed; STOP intervention branch','',f'Updated {at}.','',
        '**The BF16-preserving candidate failed the unchanged V3 bound. Dev128 was not launched.**','',
        'Diagnosis is supported: splitting the native source reduction introduces independent BF16 rounding. '
        'Source membership, masks, GQA, concatenation and bias handling pass; the first discrepancy is before W_O. '
        'Exact native reconstruction passes, while a higher-precision diagnostic improves agreement. '
        'This establishes a technical limitation of the tested implementations, not a null efficacy result.','',
        '| Quantity | Original | Full-KV BF16 candidate | Limit |','|---|---:|---:|---:|']
    for label,key in [('Pre-W_O BF16 source sum','pre_bf16_sum'),('Separate BF16 projected contributions','post_bf16_separate'),('Native-order residual reconstruction','residual_joint')]:
        lines.append(f"|{label} max abs|{baseline[key]['max_abs']:.6g}|{candidate[key]['max_abs']:.6g}|0.125|")
    lines.extend(['','Eight fixed cases cover4 independent families,3 triggered/5 nontriggered anchors and '
        'short/medium/long cached lengths. Original failing short traces were fully logged through255 decode '
        'queries each;4,128 total layer-query records across two implementations are preserved. '
        'Every row was written before numerical gating. Relative L2 and maximum absolute bounds are both enforced.',
        '', 'One candidate was tested. No gate or scientific setting changed; the original implementation, '
        'failed jobs and all frozen Stage8C cohorts remain byte-identical. '
        'The final V1–V6 bundle explicitly records V3 failure and the remaining fresh checks as not run. '
        'No false revalidation pass is assembled from historical checks.',
        '', '**Exactly one recommendation: stop intervention branch.** No dev128, held-out run, '
        'precision switch or Block3B was launched. The evidence does not invalidate retrieval observability '
        'or Value-rich transport, and it does not prove all possible BF16 decompositions impossible.',
        '', 'Both node02 allocations are released. Resource accounting is in [resources](audit/resources.json). '
        'There is no scientific ETA under the failed gate.',
        '', '[Root-cause evidence](stage8c_repair_root_cause.md) · '
        '[Full forensic metrics](stage8c_v3_forensic_metrics.parquet) · '
        '[Final gate status](stage8c_v1_v6_revalidation.json) · '
        '[Candidate diff](stage8c_repaired_implementation_diff.txt).'])
    (ROOT/'stage8c_repair_summary.md').write_text('\n'.join(lines)+'\n')
    plot(raw,manifest)
    print(json.dumps(dict(status='STOP_V3_REPAIR_FAILED',rows=sum(len(x) for x in raw.values()),
                         scientific_runs=0,recommendation='stop intervention branch')))


def plot(raw,manifest):
    os.environ['MPLCONFIGDIR']=str(ROOT/'audit/matplotlib_cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    dest=ROOT/'figures';dest.mkdir(exist_ok=True)
    keys=['pre_bf16_sum','post_bf16_separate','residual_joint']
    labels=['Before W_O','After W_O (separate)','Residual']
    colors={'forensic':'#315c9b','candidate':'#c47826'}
    names={'forensic':'Original BF16 split','candidate':'Full-KV BF16 candidate'}
    fig,axes=plt.subplots(1,3,figsize=(12,3.6),constrained_layout=True)
    for ax,key,label in zip(axes,keys,labels):
        for phase,rows in raw.items():
            y=[max(r[key]['relative_l2'] for r in rows if r['layer']==l) for l in [19,20,21,22]]
            ax.plot([19,20,21,22],y,'o-',color=colors[phase],label=names[phase])
        ax.axhline(.02,color='black',ls='--',label='Frozen limit');ax.set_title(label)
        ax.set_xticks([19,20,21,22]);ax.set_xlabel('Layer');ax.set_ylim(bottom=0)
    axes[0].set_ylabel('Maximum relative L2 across all cases');axes[-1].legend(fontsize=7)
    fig.suptitle('Relative error is small; absolute-error failures still invalidate V3')
    for suffix in ['png','pdf']:fig.savefig(dest/f'figure1_error_by_layer.{suffix}',dpi=160)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,3.7),gridspec_kw={'width_ratios':[1,2]},constrained_layout=True)
    partition_counts=[max(r[k] for rows in raw.values() for r in rows)
                      for k in ['overlap_count','uncovered_count','invalid_visual_count']]
    axes[0].bar(['Overlap','Uncovered','Invalid V'],partition_counts,color='#315c9b');axes[0].set_ylim(0,1)
    axes[0].set_title('Partition errors: all zero');axes[0].set_ylabel('Position count')
    x=np.arange(3)
    for offset,(phase,rows) in zip([-.18,.18],raw.items()):
        axes[1].bar(x+offset,[max(r[k]['max_abs'] for r in rows) for k in keys],.36,color=colors[phase],label=names[phase])
    axes[1].axhline(.125,color='black',ls='--',label='Frozen absolute limit')
    axes[1].set_xticks(x,labels);axes[1].set_ylabel('Maximum absolute error');axes[1].legend(fontsize=7)
    fig.suptitle('Every failed position is retained; no averaging for gate decisions')
    for suffix in ['png','pdf']:fig.savefig(dest/f'figure2_max_absolute_by_stage.{suffix}',dpi=160)
    plt.close(fig)
    cases=manifest['cases'];rows=raw['forensic'];v=[];n=[]
    for c in cases:
        row=next(r for r in rows if r['case_id']==c['case_id'] and r['token_index']==c['anchor'])
        v.append(row['visual_count']);n.append(row['nonvisual_count'])
    fig,ax=plt.subplots(figsize=(10,4),constrained_layout=True);x=np.arange(len(cases))
    ax.bar(x,v,label='Visual patch KV',color='#315c9b');ax.bar(x,n,bottom=v,label='Nonvisual valid KV',color='#aaa')
    ax.set_xticks(x,[c['case_id'].replace('_','\n') for c in cases],fontsize=8)
    ax.set_ylabel('Valid attended KV positions');ax.set_title('Source partition covers every valid position, without overlap');ax.legend()
    for suffix in ['png','pdf']:fig.savefig(dest/f'figure3_source_coverage.{suffix}',dpi=160)
    plt.close(fig)


if __name__=='__main__':main()
