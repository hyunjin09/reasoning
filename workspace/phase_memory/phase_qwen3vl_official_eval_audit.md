# Qwen3-VL official MathVision baseline audit

## Current Objective
Audit current official benchmark code, compare Stage11C/11C-R, then validate identical12 nonprimary cases under official model-specific recipes. No Claim3 rerun.

## Active Constraints
User-approved prompt 2026-09-28T15:45:47.706454+00:00; frozen12 unchanged; no accuracy-based selection; primary official scripts outrank README/root defaults. Sanity target<1.5GPUh, optional diagnostic target<1.5additional, hard3 allocatedGPUh. Slurm/project scheduler only, authorized nodes02/03/06/07, up to8 GPUs. Preserve old stages. Exactly nine requested deliverable names (ablation conditional), source/raw evidence in subdirectories.

## Current State
Complete / STOP: OFFICIAL_PROTOCOL_STILL_INVALID. Official fixed12 sanity: Direct 7/12 committed finals, 5 caps, 5 repetition pathologies; Thinking 12/12 finals, 0 caps, 0 pathologies. Allocated 0.571111 GPUh; all stage GPUs released.
Conditional ablation NOT_RUN.
All requested deliverables and closure checks saved under outputs/qwen3vl_official_eval/v1. No scientific rerun.

## Evidence That Matters
Stage11CR12 exact historical known-good replays passed but fixed nonprimary Direct4/12cap,8/12final,4loops. Historical replay was not proof of official benchmark faithfulness. Sources retained under outputs/qwen3vl_official_eval/v1/sources.

## Failed Attempts and Lessons
Jobs126162/126163 failed before generation due to an overlong Unix socket path. Shortening only project TMPDIR repaired startup; retry126167/126168 used unchanged frozen scientific settings. All failed allocations counted. MathVision-specific recipes differ from root generic Thinking defaults and from the historical project prompt/decoding. Historical token replay alone did not establish official benchmark faithfulness.

## Open Candidates
None within this completed action. Any Claim3 scientific rerun requires separate user instruction; do not automatically launch.

## Next-Step Decision — 2026-09-28T15:45:47.706454+00:00
Complete pinned primary-source/prompt/runtime audit and field diff; validate exact dataset correspondence. Then freeze24-call sanity manifest and resource envelope before GPU execution. No scientific primary/oracle/CoT/reserve work.

### Step Result
Audit in progress.

## Next-Step Decision — 2026-09-28T16:04:11.679855+00:00
Official source audit confirms both prompt and decoding mismatch. Run only24 fixed technical calls through unmodified official run_inference, with case filtering and observational recording. Two finite40minute singleGPU jobs have1.3333GPUh maximum commitment, within3hard. Gate10finals/at-most1cap/at-most1pathology unchanged. Conditional three variants already frozen. No Claim3.

### Runtime failure and repair — 2026-09-28T16:08:02.362705+00:00
Jobs126162/126163 failed before inference: project temp path plus UUID exceeds Unix socket107-byte limit. Source logs directly identify cause. Preserved original manifest/wrapper under audit/manifest_versions. Shortened TMPDIR to allowed runs/qvtmp; CPU Unix socket bind succeeds. No model outputs existed, no decoding/prompt/case changes. Retry only same24 calls within revised allocated budget.

## Final Result — 2026-09-28T16:27:34.723462+00:00
OFFICIAL_PROTOCOL_STILL_INVALID. Official fixed12 sanity: Direct 7/12 committed finals, 5 caps, 5 repetition pathologies; Thinking 12/12 finals, 0 caps, 0 pathologies. Allocated 0.571111 GPUh; all stage GPUs released.
Conditional ablation NOT_RUN.
Preserved Stage11C/11C-R hashes, source commits, canonical input hashes, raw official outputs and technical reviews. Fair native comparison uses each variant's validated intended decoding recipe, not forced identical hyperparameters.

## Next-Step Decision — 2026-09-28T16:27:34.723462+00:00
STOP. Return the technical validation result to the user; no new scientific action selected or launched.
