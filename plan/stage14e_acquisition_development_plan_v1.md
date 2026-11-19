# Stage14E bounded visual-acquisition methodology development

Authorized by the user's autonomous research instruction on 2026-10-22. This is a new development cycle, not a rewrite of the completed Stage14D-1 pilot. All existing sealed artifacts remain immutable. The old Stage14D exhaustive experiment remains HOLD; Stage14C-V remains unfinished.

## Objective and success criteria
Improve acquisition of source-resolvable task-critical visual evidence by the pinned Qwen3-VL-4B-Thinking model. Primary endpoint: source-correct, demand-relevant evidence, with novelty/reinspection distinguished from already supplied facts. Final-answer accuracy is a separate downstream endpoint. Null/harmful results are valid. No gold, E* values or human ROIs enter deployable runtime inputs.

## Ordered work and verification
1. **Failure postmortem:** Join all72 source/query/address/solver records; inspect source images and exact prefixes/readouts. Analyze the frozen24 panel, all9 regressions and3 QI rescues. Preserve provenance and distinguish supported observations from causal hypotheses. Verify72 unique families and original seals.
2. **Hypotheses and prior art:** Compare demand identification, target translation, localization, readout and timing. Review the requested primary literature. Select at most two mechanisms with a discriminating diagnostic; do not claim novelty from generic query/crop/lookback.
3. **Controlled diagnostic:** Freeze source-only target identities without values, matched conditions and evaluation rubric before generation. Use old development families. Separate target selection from reading and prefix influence; include no-image reading and bounded context controls where applicable. Evidence acquisition is primary; do not use final correctness for method selection. CPU contracts/tests before GPU.
4. **Development:** Freeze each scientific revision before its test, allow at most two deliberate method versions. Repair genuine engineering defects with regression tests; retain all failed outcomes. Methods may abstain. Freeze the selected method before held-out evaluation.
5. **Evaluation:** Deterministically select disjoint fresh method-evaluation families using source metadata only. These may have historical benchmark exposure; they are not a new independent benchmark confirmation. Freeze IDs, strata, inputs, seeds, scoring, 512-token anchors and paired baseline/treatment before outcomes. One evaluation per selected method, no tuning on its results. Use original images and the validated model/solver recipe; retain incomplete and unscorable outcomes.
6. **Closure:** Source/evidence casebook, paired family bootstrap (4000 draws), rescue/regression/missingness, allocation accounting, code/tests and final recommendation answering the six requested questions. Release all allocations. No large follow-on campaign.

## Resource envelope
New work has a hard **24 additional GPU-hour** ceiling, separate from historical SAVA21.365278GPUh. Planning allocation: diagnostic≤3h; development/technical≤3h; final evaluation target≤12h;6h reserve. These are reallocatable planning targets, not permission to exceed24h. Record actual Slurm elapsed×allocatedGPUs including startup/failure/idle. Reserve a conservative upper bound before each allocation; use admission/accounting safeguards for this explicit budget. Slurm limits48h; finite queues exit promptly. Do not impose arbitrary short rollout deadlines. Up to8 concurrent GPUs through the project scheduler only. Inspect live capacity before launch.

## Runtime and integrity
Pinned4B Thinking checkpoint; BF16; temperature1/top-p.95/top-k20/repetition1/presence0. Retain VLLM_ENABLE_V1_MULTIPROCESSING=0, prefix cache off, consistent scheduling, original image preprocessing. Freeze helper caps and solver cap prospectively. Runtime manifests exclude source answers and evaluation labels; diagnostic oracle-target inputs explicitly tagged and never counted as deployable. Preserve raw prompts, images/hash, token IDs, outputs and receipt hashes.

## Initial action
Complete the source-grounded postmortem and competing-hypothesis assessment, then freeze the smallest diagnostic that can distinguish target-selection failure from reading failure. The user's latest instruction already authorizes the complete cycle and ordinary revisions; no routine approval checkpoint is introduced.
