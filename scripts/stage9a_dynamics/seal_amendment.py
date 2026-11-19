"""Seal the amendment record/config after safe stop and immutable accounting."""
import json
from pathlib import Path
from scripts.stage8c.prepare import save,sha
from scripts.stage9a.run_native import now

ROOT=Path('outputs/stage9a_dynamics/amendment_v1');OLD=Path('outputs/stage9a_dynamics/v1')


def main():
    stamp=now();status=json.loads((ROOT/'stage9a_old_manifest_status.json').read_text())
    selection=json.loads((ROOT/'stage9a_amended_family_selection.json').read_text())
    manifest=json.loads((ROOT/'stage9a_amended_condition_manifest.json').read_text())
    estimate=json.loads((ROOT/'stage9a_amended_resource_estimate.json').read_text())
    reuse=json.loads((ROOT/'audit/reused_results.json').read_text())['rows']
    doc=f'''# Stage9A compute amendment v1

User-approved amendment sealed {stamp}. Family selection frozen {selection['at']}.

## Reason and preserved scientific question

This is a prospective compute reduction before scientific analysis, not
outcome-dependent adaptation. The old exhaustive manifest contained9,874
distinct masked continuations and10,571 condition rows, with an initial
estimate of1,371 GPU-hours. It is superseded for future free-rollout execution.
This remains the primary Stage9A causal visual-access dynamics experiment;
it is not reclassified as a pilot or exploratory-only study.

The question is unchanged: Do Qwen3-VL-2B Instruct-Direct, Instruct-CoT and
Native Thinking differ in when direct image-token access is functionally
necessary during reasoning?

All128 MathVision families,384 native trajectories and their existing answer
review,539 accepted semantic annotations,50 local readout annotations, source
hashes, native-use characterization and V1–V6 validation remain unchanged.
BF16 models, prompts, sampling/seeds, total40960-token cap, repository layers
19–22, time indexing, prefill/cache preservation and attention-mask semantics
are unchanged. No native regeneration, relabeling or model/data download.

## Safe stop and preservation

Coordinator121713 stopped after its STOP_DISPATCH file was created. Workers
121703–121706 were allowed to finish their active rollout and stopped only
after generation/result receipts were durable. Their old code lacked a graceful
stop flag: a preserved progress-log inode and a FIFO at its append path held each
worker after receipt creation and before the next rollout. The blocked state
was verified before Slurm cancellation; normal progress logs were then restored.
Raw generations and receipts were never overwritten. Proofs are linked from
stage9a_old_manifest_status.json. The amended worker has an ordinary
STOP_WORKERS check between rollouts, so this barrier is no longer needed.

Exactly{status['completed_preserved']} completed old continuations are preserved.
{len(reuse)} exactly matching main rows are reused by verified references to the
original immutable artifacts. Remaining completed superseded rows stay in the
old namespace as pre-amendment exploratory evidence and are excluded from the
amended primary analysis. Unexecuted old rows are cancelled, not silently deleted.

## Deterministic allocation

Select exactly64 of128 independent conservative visual families with recursive
Hamilton largest-remainder quotas by subject, difficulty(level), then answer
format. Resolve quota ties and within-cell ordering by SHA256 with seed
`{selection['seed']}`. Input order does not affect selection. Metadata columns
are only family/item identity, subject, level and answer format. The main cohort
has34 free-response and30 multiple-choice families; every subject receives its
floor/ceiling half allocation. Native correctness, masked outputs, damage,
divergence, causal effects and completion changes are not selection inputs.

The complementary64 families are a frozen reserve. Applying the identical
selection rule to them freezes the next32 eligible extension families and the
final32 separately. No reserve family enters main free-rollout execution.

## Conditions

For every main family and each of the three arms:

- Cumulative cutoffs0,128,512,2048,FULL.
- Five native-reasoning windows[0,.2],[.2,.4],[.4,.6],[.6,.8],[.8,1].
- At most one accepted explicit demand with a full valid33-token radius16
  window: prefer the earliest eligible event strictly after25% native reasoning,
  otherwise choose the earliest eligible event.
- Exactly one equal-width shifted control per selected event. Use a prior
  precomputed control if valid and within10% normalized position; otherwise the
  closest valid shift with hash ties. Conservatively exclude all accepted
  demand±32 neighborhoods. This is a window without annotated demand, not a
  claim that no latent demand exists there.

There are109 paired selected events across192 family/arm trajectories. All539
accepted annotations remain preserved. Missing demands remain missing; they
do not become zero effects. No additional event or radius32 free rollout runs.

The main manifest has{len(manifest['rows'])} logical rows:1,904 distinct masked
continuations and234 exact native identities (including FULL). There are87
additional null-sink controls on8 preselected main families, all three arms:
one early20% window, one late20% window, cutoff128 and the selected demand when
available. These controls remain deferred until main64 results exist. Thus the
maximum currently frozen free-rollout inventory is1,991, below3,000.

All50 previously frozen local readout events run under their original
teacher-forced radius16/radius32 demand/control specification. They do not add
reserve families to primary free-rollout inference. No inventory expansion.

## Three primary scientific groups

P1: Thinking−CoT damage at cutoffs512 and2048, each relative to FULL.
P2: Thinking−CoT difference in the mean damage of[.6,.8] and[.8,1].
P3: Thinking−CoT difference in demand-minus-matched-control damage.

Other windows/cutoffs and Direct ordering are descriptive. Keep family-equal
paired comparisons and4,000 family-cluster bootstrap draws, seed920260924.
Report effect sizes, paired direction,95% intervals and simultaneous intervals:
Bonferroni across P1's two specified components plus the single P2 and P3
components (four numerical components within three scientific groups). Retain
the existing minimum20 paired families and95% valid draws for inferential
intervals; preserve actual support and subject/length/completion uncertainty.

## Extension and control gates

Do not automatically run reserve families. At most the frozen next32 can be
considered only if P2 or P3 has a positive hypothesized point estimate, its
interval includes zero or support is clearly inadequate, the effect survives
subject checks, implementation/controls are valid, and evidence is precision
limited rather than null. Conditions remain unchanged. A triggered extension
uses64+32 for final analysis; final32 requires a new user authorization. Enforce
the3,000-distinct-continuation ceiling before any expanded execution.

The87 null-sink controls are the bounded preselected control set, executed only
after main64 results. Query-text bypass remains conditional on a positive
Thinking-specific late-necessity effect. No full control grid, Stage9B, new
experiment or automatic scientific pivot may be launched by the coordinator.

## Compute and execution

Reuse{len(reuse)} matching main rows; launch only{estimate['main_unfinished']}
unfinished main continuations. Estimated remaining compute including prefixes,
the87 deferred controls and50 local readouts is
{estimate['estimated_total_remaining_gpu_hours']:.1f} GPU-hours, with planning
range{estimate['planning_range_gpu_hours'][0]:.0f}–{estimate['planning_range_gpu_hours'][1]:.0f} GPU-hours
({estimate['days_at_four_gpus']:.1f} days atfour continuously available GPUs).
The estimate fits observed token timing versus context and integrates over
frozen native lengths; length changes, queueing and review remain uncertainty.
Full method, observed timing coverage and all-cap scenario are preserved in
stage9a_amended_resource_estimate.json. This range is not a confidence interval.

Use only available authorized node02/node03/node06/node07 GPUs through the
project scheduler and Slurm; at mostfour simultaneous GPU allocations, including
pending reservations. The amended coordinator can launch only main rows and
the unchanged50 local readouts. It stops at the review/control boundary and on
runtime failure or user cancellation. Workers release GPUs upon completion.

## No-outcome-use attestation

The selection/manifest builder opens only the pre-intervention cohort metadata,
native task metadata and frozen annotation-derived condition inventory. It
does not open masked generations or receipts. After selection was sealed,
accounting accessed only condition IDs, hashes, execution status, timing and
token-throughput fields to identify exact reuse and estimate compute. No
masked answer, accuracy, damage, local causal score or divergence was inspected
to construct this amendment. No aggregate scientific analysis has been opened.
'''
    save(ROOT/'audit/sealing_record.json',dict(at=stamp,old_status_sha256=sha(ROOT/'stage9a_old_manifest_status.json'),resource_estimate_sha256=sha(ROOT/'stage9a_amended_resource_estimate.json'),selection_sha256=sha(ROOT/'stage9a_amended_family_selection.json'),manifest_sha256=sha(ROOT/'stage9a_amended_condition_manifest.json')))
    for p in [ROOT/'stage9a_compute_amendment_v1.md',Path('plan/stage9a_compute_amendment_v1.md')]:
        assert not p.exists();p.write_text(doc)
    (ROOT/'stage9a_mask_backend_validation.json').write_bytes((OLD/'stage9a_mask_backend_validation.json').read_bytes())
    cfg=json.loads((OLD/'config.json').read_text())
    cfg.update(root=str(ROOT),manifest_sha256=sha(ROOT/'audit/interventions.json'),tasks_sha256=sha(ROOT/'audit/tasks.json'),reused_results=reuse,
        amendment='stage9a_compute_amendment_v1',main_families=64,main_tasks=192,main_unique=1904,control_launch_gate='after main results only',readout_root=str(OLD))
    for p in [ROOT/'stage9a_compute_amendment_v1.md',ROOT/'stage9a_amended_family_selection.json',ROOT/'stage9a_amended_condition_manifest.json']:
        cfg['source_sha256'][str(p)]=sha(p)
    save(ROOT/'config.json',cfg)
    save(ROOT/'audit/ready_to_launch.json',dict(at=stamp,pass_all=True,source_sha256={str(p):sha(p) for p in [ROOT/'config.json',Path('scripts/stage9a_dynamics/run_worker.py'),Path('scripts/stage9a_dynamics/dispatch.py'),Path('scripts/stage9a_dynamics/run_readouts.py')]},
        scientific_outcomes_used=False,main_unfinished=estimate['main_unfinished'],controls_deferred=True,extension_automatic=False))
    print(json.dumps(dict(sealed_at=stamp,preserved=status['completed_preserved'],main_unique=1904,deferred_controls=87,reused=len(reuse),unfinished=estimate['main_unfinished'],estimated_gpu_hours=estimate['estimated_total_remaining_gpu_hours'],days_four=estimate['days_at_four_gpus']),indent=2))


if __name__=='__main__':main()
