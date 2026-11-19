# Phase 2: PIQD Query Extraction Memory

## Current Objective
Implement and run Phase 2 teacher-forced CQ/CFQ query extraction on the 10 Phase 1 smoke samples.

## Active Constraints
- Stop after Phase 2; do not implement Phase 3, full-bank retrieval metrics beyond sanity checks, behavioral continuation, full MathVerse, dataset download, or model substitution.
- Use existing `.venv`, local MathVerse at `/data/dataset/MathVerse`, and local Qwen3-VL-8B-Thinking cache with `local_files_only=True`.
- Use Phase 1 retained visual indices exactly; do not recompute or change FastV pruning.
- CQ and CFQ must use identical stored generated token IDs and event generated-token indices.
- Do not silently re-tokenize generated text if generated token IDs are missing.
- No cross-condition KV reuse: CQ and CFQ each start from `past_key_values=None`.
- Store all heads for selected layers; do not average heads in Phase 2.
- Store `K_full` from CFQ/full visual condition for later Phase 3 same-bank scoring.
- Heavy model execution must use `infra/gpu_scheduler.py` with node memory caps respected.
- Generated Python/shell files must stay organized under `scripts/`; reusable code under `code/`.

## Current State
- Done: Phase 2 pre-flight validation, query extraction implementation, GPU diagnostic, final 10-sample extraction, output validation, and global state updates.
- In progress: None.
- Blocked:
- Most recent useful observation: Final validation passed and required Phase 2 state files are updated.

## Evidence That Matters
| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Phase 1 final smoke run succeeded with 10/10 samples | `outputs/piqd/phase1/phase1_summary.md` | Phase 2 should use existing smoke outputs, not regenerate Phase 1 | confirmed |
| Event logs are active-bank qK over retained tokens, not full-bank RVIS | `outputs/piqd/phase1/phase1_event_logs.jsonl` | Phase 2 must preserve event convention and avoid retrieval claims | confirmed |
| FastV status is approximate static pruning | `outputs/piqd/phase1/phase1_fastv_status.md` | Phase 2 must preserve this label and not fix FastV | confirmed |
| Prompt pack path in prompts may use stale `plan/` prefix | Phase 1 memory and local listing | Use `piqd_agent_specs_v4/` in this workspace | confirmed |
| Phase 1 artifacts pass Phase 2 strict pre-flight | `code/piqd/phase2/artifacts.py`, `scripts/piqd/phase2_self_test.py` | Exact prompts, images, token IDs, retained indices, visual counts, event indices, and decoding config are available | confirmed |
| Phase 2 replay and q/K capture helpers pass local tests | `code/piqd/phase2/replay.py`, `code/piqd/hooks/query_key_capture.py`, `scripts/piqd/phase2_self_test.py` | Token appending, event keys, stable prefix hashes, and tensor stacking are ready for GPU runner | confirmed |
| Phase 2 runner compiles | `scripts/piqd/phase2_query_extraction.py`, `scripts/piqd/phase2_run_query_extraction.sh` | Ready for small GPU diagnostic before full 10-sample extraction | confirmed |
| One-sample Phase 2 diagnostic succeeded | `outputs/piqd/phase2_diag/phase2_summary.md` | Model load, CQ/CFQ full-prefix forwards, q/K hooks, and sanity outputs work on GPU | confirmed |
| Final 10-sample Phase 2 extraction succeeded | `outputs/piqd/phase2/phase2_summary.md` | Required Phase 2 tensors and sanity files exist for 20 events | confirmed |
| Global Phase 2 state files updated | `outputs/piqd/work_state.md`, `outputs/piqd/todo.md`, `outputs/piqd/implementation_log.md` | Required dashboard, todo, and implementation log reflect Phase 2 completion | confirmed |
| Final validation passed | validation command over `outputs/piqd/phase2` | Required files exist; row counts and tensor shapes match expectations | confirmed |

## Failed Attempts and Lessons
| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Phase 1 strict event threshold | Fallback event despite visible local minimum | Smoke-level event naming should not be hidden by arbitrary threshold | Use saved Phase 1 event indices as artifacts; do not regenerate Phase 1 | Do not change Phase 1 pruning or generation in Phase 2 |
| Phase 1 broad source scans | Noisy output from generated/cache/vendor paths | Scans included generated or cloned third-party paths | Keep searches targeted to `code/`, `scripts/`, `infra/`, prompts, and PIQD outputs | Do not broad-scan `workspace/third_party`, `.venv`, or `workspace/uv_cache` |
| Prior Phase 1 Slurm jobs requested 96G on one A100 | Exceeded new node memory policy | Scheduler now enforces node memory caps | Use `--mem <= 60G` on node01/A100 | Do not request 96G for one GPU |

## Open Candidates
| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Phase 1 artifacts may already contain all pre-flight fields | Final validation checked rows but not every Phase 2 field | Build strict pre-flight table and fail to `phase2_blockers.md` if missing | confirmed |
| Query extraction can reuse Phase 1 Qwen prefill/pruning helpers | Phase 1 runner already builds full/pruned prefill embeddings and retained visual mapping | Add Phase 2 replay/helper tests before GPU execution | confirmed |
| Hooking self-attention forward can capture q/k without modifying Transformers | Phase 1 active logger used non-invasive wrapping | Implement a teacher-forced capture hook for selected layers | confirmed |
| Full-prefix forward may be simpler and safer than chunking for 10-sample smoke | Prefix length is short in Phase 1 logs and chunking adds indexing risk | Run one-sample diagnostic on GPU first | confirmed |

## Next-Step Decision
- Current bottleneck: None for Phase 2.
- Relevant memory item used: Final validation passed and the Phase 2 prompt says to stop after Phase 2.
- Chosen next action: Stop and report completion to the user.
- Why this action: All required Phase 2 outputs are present and Phase 3 is not approved.
- What not to repeat: Do not modify installed Transformers; do not recompute Phase 1 retained visual indices.
- Stop condition: Phase 2 complete.

### Step Result
- Action taken: Implemented and ran Phase 2 artifact pre-flight validation.
- Result: `scripts/piqd/phase2_self_test.py` passed 5 tests; real Phase 1 artifacts produced 10 valid rows, 0 blockers, and 20 candidate events.
- Evidence saved: `code/piqd/phase2/artifacts.py`, `scripts/piqd/phase2_self_test.py`, terminal validation output.
- Failure or issue: `pre_answer_selection_step` is not present in Phase 1 artifacts and is not processed in Phase 2; this is not a blocker because the prompt only requires it if available.
- Lesson learned: Phase 2 can use exact stored generated token IDs and retained visual indices without re-tokenizing or regenerating Phase 1.
- Next implication: Implement teacher-forced replay/capture helpers and a GPU runner.

### Step Result
- Action taken: Implemented Phase 2 replay and q/K capture helpers and expanded self-tests.
- Result: `scripts/piqd/phase2_self_test.py` passed 10 tests; syntax compilation passed.
- Evidence saved: `code/piqd/phase2/replay.py`, `code/piqd/hooks/query_key_capture.py`, terminal test output.
- Failure or issue: None.
- Lesson learned: The Phase 2 runner can build exact prompt+stored-prefix inputs and use non-invasive attention hooks without touching installed Transformers.
- Next implication: Implement the GPU runner and output writers.

### Step Result
- Action taken: Implemented `scripts/piqd/phase2_query_extraction.py` and `scripts/piqd/phase2_run_query_extraction.sh`.
- Result: Python compilation passed, shell syntax passed, and `scripts/piqd/phase2_self_test.py` passed 10 tests.
- Evidence saved: Runner scripts and terminal verification output.
- Failure or issue: None.
- Lesson learned: The GPU runner is ready for a one-sample model-facing diagnostic.
- Next implication: Submit the one-sample diagnostic through Slurm.

### Step Result
- Action taken: Submitted one-sample Phase 2 diagnostic through Slurm on A100 with `--mem 60G`.
- Result: Diagnostic succeeded; 1 sample and 2 events processed; q tensors have shape `[4, 32, 128]`; K_full has shape `[4, 32, 70, 128]`.
- Evidence saved: `outputs/piqd/phase2_diag/phase2_summary.md`, `outputs/piqd/phase2_diag/phase2_event_queries.pt`, `outputs/piqd/phase2_diag/phase2_visual_keys.pt`, `runs/piqd_phase2_diag/slurm.log`.
- Failure or issue: None.
- Lesson learned: Whole-prefix teacher forcing works for Qwen3-VL Phase 2 and keeps CQ/CFQ cache contexts separate.
- Next implication: Run the final 10-sample extraction.

### Step Result
- Action taken: Submitted final 10-sample Phase 2 extraction through Slurm on A100 with `--mem 60G`.
- Result: 10 samples and 20 events processed; all sanity checks passed; q tensors are `[4, 32, 128]`; K_full tensors are `[4, 32, num_visual_tokens, 128]`.
- Evidence saved: `outputs/piqd/phase2/phase2_summary.md`, `phase2_event_queries.pt`, `phase2_visual_keys.pt`, metadata/check JSONL files, `runs/piqd_phase2_extract_10/slurm.log`.
- Failure or issue: Phase 2 does not compute retrieval metrics or behavioral continuation by design.
- Lesson learned: Same-prefix CQ/CFQ query extraction is now instrumented for the 10-sample smoke set.
- Next implication: Update global state files and stop after Phase 2.

### Step Result
- Action taken: Updated global state files, reran final validation, and cleaned generated Python bytecode caches under `code/` and `scripts/`.
- Result: Phase 2 deliverables are complete; tests and validation passed; no `__pycache__` directories remain under source/script trees.
- Evidence saved: `outputs/piqd/work_state.md`, `outputs/piqd/todo.md`, `outputs/piqd/implementation_log.md`, final validation terminal output.
- Failure or issue: None.
- Lesson learned: Phase 2 is internally consistent and ready for review before any Phase 3 work.
- Next implication: Stop after Phase 2.
