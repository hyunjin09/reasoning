# Phase 1: PIQD Smoke Pipeline Memory

## Current Objective
Build and run a minimal Phase 1 smoke pipeline for local MathVerse + local Qwen3-VL-8B-Thinking with FastV-style 33.3% static pruning and active-bank event logging.

## Active Constraints
- Do not implement Phase 2, CQ/CFQ teacher-forced replay, behavioral continuation, DSTP, dynamic token swapping, oracle analysis, or full MathVerse.
- Use existing `.venv`; do not recreate environment.
- Use local MathVerse at `/data/dataset/MathVerse`; do not download MathVerse.
- Use local Qwen cache under `/home/hyunjin/.cache/huggingface/hub/models--Qwen--Qwen3-VL-8B-Thinking`; do not substitute models.
- Use Slurm for GPU work; no heavy model work on login node.
- Keep generated code organized under `scripts/piqd/` and `code/piqd/`; use `workspace/third_party/FastV` for the reference clone to stay inside allowed write roots.
- Exclude `.venv`, `workspace/uv_cache`, and `outputs` from source scans.

## Current State
- Done: Phase 0 verified `.venv`, PyTorch CUDA on A4000, and absence of existing PIQD/model/FastV code; Phase 1 10-sample smoke generation completed.
- In progress: None.
- Blocked:
- Most recent useful observation: Final validation passed for all required Phase 1 files, row counts, event names, and active-bank definitions.

## Evidence That Matters
| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| `.venv` has torch `2.7.1+cu118`, transformers `5.12.1`, datasets `5.0.0`, qwen-vl-utils `0.0.14` | `workspace/env_state.md` | Existing environment should be reused | confirmed |
| No existing model/generation/FastV implementation | `outputs/piqd/phase0_repo_inspection.md` | Phase 1 must create scaffolding | confirmed |
| Qwen3-VL hooks should wrap installed Transformers code | `outputs/piqd/phase0_repo_inspection.md` | Avoid modifying third-party internals | confirmed |
| Generated dependency cache polluted a previous scan | `outputs/piqd/work_state.md` | Future scans must exclude cache/env paths | confirmed |
| MathVerse local path exists with `testmini.json`, `testmini.parquet`, and image directories | `/data/dataset/MathVerse` inspection | Loader can use local JSON without downloads | confirmed |
| Active local Qwen snapshot is `92f3c4b4feadd3a016ef468d103bb5f58b2a2c6b` | HF `refs/main` | Model loader should use this snapshot with `local_files_only=True` | confirmed |
| FastV reference cloned at commit `d165972` | `workspace/third_party/FastV` | Reference top-k attention pruning is available | confirmed |
| Loader and event helper tests pass | `scripts/piqd/phase1_self_test.py` | Data subset and pure FastV/event logic are usable | confirmed |
| Phase 1 Python sources compile | `python -m py_compile` over `code/` and `scripts/piqd/` | New Qwen wrapper/logger/runner are syntactically valid | confirmed |
| Processor-only Qwen path works on one local MathVerse sample | `processor_inputs` check | Prompt/image schema is compatible before GPU model loading | confirmed |
| Requested `/home/hyunjin` Qwen cache resolves to `/data/dataset/huggingface/hub/.../92f3c4...` | `resolve_hf_snapshot` output | Phase 1 uses local files only, but reports should show both requested and resolved roots | confirmed |
| Resource inspection report written | `outputs/piqd/phase1/resource_inspection.md` | Required Phase 1 output documents local dataset/model/FastV resources | confirmed |
| Model-load-only job succeeded on A100 | `outputs/piqd/phase1/phase1_model_loading.md` | Local Qwen model can be loaded without substitution before generation | confirmed |
| One-sample diagnostic generation succeeds | `outputs/piqd/phase1_diag/phase1_summary.md` | Prefill, FastV-style pruning, greedy decode, and active-bank logging execute on GPU | confirmed |
| Event-selection helper now uses first active-bank local minimum | `code/piqd/fastv/fastv_adapter.py`, `scripts/piqd/phase1_self_test.py` | Required event name is not hidden by an arbitrary threshold | confirmed |
| Final 10-sample smoke run succeeded | `outputs/piqd/phase1/phase1_summary.md` | Phase 1 required generation/event outputs were produced | confirmed |
| Global Phase 1 state files updated | `outputs/piqd/work_state.md`, `outputs/piqd/todo.md`, `outputs/piqd/implementation_log.md`, `workspace/dataset_inventory.md` | Required state/report updates are in place | confirmed |
| Final validation passed | validation command over `outputs/piqd/phase1` | Required files exist and logs contain 10 ok generation/event rows | confirmed |

## Failed Attempts and Lessons
| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Phase 0 broad `rg` after dependency install | Huge irrelevant output from `workspace/uv_cache` | Generated cache was included | Exclude generated cache/env/output paths | Do not source-scan `.venv` or `workspace/uv_cache` unless intentionally inspecting installed packages |
| Strict `0.75` event threshold in diagnostic | Event fell back to `minimum_active_similarity_step` even though the active-bank curve had a local minimum | Threshold was too strong for smoke-level shift logging | Use first active-bank local minimum as `first_active_attention_shift`; keep fallback only when no local minimum exists | Do not require an arbitrary similarity threshold for Phase 1 shift naming |

## Open Candidates
| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Exact FastV may not map cleanly to Qwen3-VL DeepStack embeddings | Phase 0 noted Qwen3-VL visual insertion/deepstack complexity | Implement adapter and mark status explicitly | testing |
| Qwen3-VL-8B may OOM on 16GB A4000 | 8B bf16 likely exceeds A4000 memory | Prefer A6000/A100 for model smoke; stop on OOM | unchecked |
| Local MathVerse schema may not match assumptions | Dataset path is external local directory | Inspect file layout and parse a small sample | confirmed |

## Next-Step Decision
- Current bottleneck: None for Phase 1.
- Relevant memory item used: Final validation passed and the Phase 1 prompt says to stop after Phase 1.
- Chosen next action: Stop and report completion to the user.
- Why this action: All required Phase 1 outputs are present and Phase 2 is not approved.
- What not to repeat: Do not edit installed Transformers or clone/write root `third_party`.
- Stop condition: Phase 1 complete.

### Step Result
- Action taken: Inspected local MathVerse, Qwen snapshot cache, and FastV reference.
- Result: Required local resources exist; FastV reference cloned to workspace-local path.
- Evidence saved: To be summarized in `outputs/piqd/phase1/resource_inspection.md`.
- Failure or issue: Prompt-suggested root `third_party/FastV` conflicts with allowed write organization, so reference was cloned under `workspace/third_party/FastV`.
- Lesson learned: FastV reference keeps top visual tokens by attention from the last token and uses static KV-cache pruning as a known variant.
- Next implication: Phase 1 implementation should be explicitly marked approximate unless Qwen3-VL integration exactly matches the modified FastV forward.

### Step Result
- Action taken: Implemented pure IO/env helpers, MathVerse loader, FastV retention/event helpers, and local unit checks.
- Result: `PYTHONPATH=code python scripts/piqd/phase1_self_test.py` passes 5 tests.
- Evidence saved: Test output in terminal; code under `code/piqd/` and `scripts/piqd/phase1_self_test.py`.
- Failure or issue: None.
- Lesson learned: `round(729 * 0.333)` gives the intended 243 retained visual tokens.
- Next implication: Proceed to model wrapper and active attention logger with the loader/selection primitives stable.

### Step Result
- Action taken: Ran local syntax compilation and reran `scripts/piqd/phase1_self_test.py`.
- Result: Compilation passed; 5 unit tests passed.
- Evidence saved: Terminal output from `python -m py_compile` and `phase1_self_test.py`.
- Failure or issue: None.
- Lesson learned: The newly added Phase 1 files are ready for lightweight import/model-facing checks.
- Next implication: Verify local Qwen loader imports and processor-only path before Slurm GPU model loading.

### Step Result
- Action taken: Imported Qwen loader utilities and built one processor-only local MathVerse input batch.
- Result: `Qwen3VLProcessor` produced expected tensors (`input_ids`, `attention_mask`, `mm_token_type_ids`, `pixel_values`, `image_grid_thw`).
- Evidence saved: Terminal output; to be summarized in `outputs/piqd/phase1/resource_inspection.md`.
- Failure or issue: Requested cache root resolves through local storage to `/data/dataset/huggingface/hub/...`.
- Lesson learned: Keep output reports explicit about requested cache path versus resolved local snapshot.
- Next implication: Write resource inspection output, then submit GPU model loading through Slurm.

### Step Result
- Action taken: Wrote `outputs/piqd/phase1/resource_inspection.md`.
- Result: Local MathVerse, local Qwen snapshot, processor-only batch shapes, and FastV reference commit are documented.
- Evidence saved: `outputs/piqd/phase1/resource_inspection.md`.
- Failure or issue: None.
- Lesson learned: Requested `/home/hyunjin` model cache is a local symlink target; this is acceptable as long as local-files-only loading is retained.
- Next implication: Submit a Slurm model-load-only job on a larger GPU partition to test the real model without running generation yet.

### Step Result
- Action taken: Submitted `piqd_phase1_model_load` through `infra/gpu_scheduler.py` on A100.
- Result: Job succeeded; `Qwen3VLForConditionalGeneration` loaded in bf16 with eager attention on `NVIDIA A100-PCIE-40GB`.
- Evidence saved: `outputs/piqd/phase1/phase1_model_loading.md`, `outputs/piqd/phase1/phase1_fastv_status.md`, `runs/piqd_phase1_model_load/slurm.log`.
- Failure or issue: None.
- Lesson learned: A100 has enough memory for the model-load-only check (`~17.5GB` allocated after load).
- Next implication: Run the 10-sample Phase 1 smoke generation on A100 with bounded `max_new_tokens`.

### Step Result
- Action taken: Submitted one-sample/four-token diagnostic generation through Slurm.
- Result: Generation succeeded and active-bank similarity records were written.
- Evidence saved: `outputs/piqd/phase1_diag/phase1_summary.md`, `outputs/piqd/phase1_diag/phase1_generation_logs.jsonl`, `runs/piqd_phase1_diag/slurm.log`.
- Failure or issue: Strict `0.75` threshold caused fallback naming even with an active-bank local minimum.
- Lesson learned: Phase 1 shift logging should define `first_active_attention_shift` as the first active-bank local minimum, not a thresholded event.
- Next implication: Patch event selection, rerun local tests, then launch the required 10-sample smoke generation.

### Step Result
- Action taken: Patched event selection and reran local checks.
- Result: `py_compile` passed; `scripts/piqd/phase1_self_test.py` passed 5 tests.
- Evidence saved: Updated `code/piqd/fastv/fastv_adapter.py` and `scripts/piqd/phase1_self_test.py`; terminal test output.
- Failure or issue: None after patch.
- Lesson learned: Active-bank shift event naming can remain deterministic without an arbitrary threshold.
- Next implication: Launch the final 10-sample Phase 1 smoke generation.

### Step Result
- Action taken: Submitted `piqd_phase1_smoke_10` through Slurm on A100.
- Result: 10/10 samples succeeded; generation logs and event logs each contain 10 rows; all event rows use `first_active_attention_shift` with active-bank retained-token qK definition.
- Evidence saved: `outputs/piqd/phase1/phase1_summary.md`, `outputs/piqd/phase1/phase1_generation_logs.jsonl`, `outputs/piqd/phase1/phase1_event_logs.jsonl`, `runs/piqd_phase1_smoke_10/slurm.log`.
- Failure or issue: Exact FastV remains approximate for Qwen3-VL and is documented as static top-k visual token deletion.
- Lesson learned: The smoke path is viable for 10 local MathVerse samples under A100 memory.
- Next implication: Update global state files and stop after Phase 1.

### Step Result
- Action taken: Updated required global state files and dataset inventory.
- Result: `work_state.md`, `todo.md`, `implementation_log.md`, and `workspace/dataset_inventory.md` now reflect Phase 1 completion and gated future work.
- Evidence saved: Updated markdown files.
- Failure or issue: None.
- Lesson learned: The Phase 1 reports should explicitly distinguish completed smoke work from future Phase 2 replay work.
- Next implication: Run final validation and stop after Phase 1.

### Step Result
- Action taken: Ran final validation over Phase 1 outputs and reran `scripts/piqd/phase1_self_test.py`.
- Result: Validation passed; 8 required Phase 1 files exist; samples/generation/events are `10/10/10`; all event rows are `first_active_attention_shift` with active-bank non-RVIS definitions.
- Evidence saved: Terminal validation output and existing Phase 1 artifacts.
- Failure or issue: None.
- Lesson learned: Phase 1 deliverables are internally consistent.
- Next implication: Stop after Phase 1.
