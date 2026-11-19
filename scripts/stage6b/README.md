# Stage6B execution

Run from the project root with `PYTHONPATH=code:.` and `.venv/bin/python`.
All GPU commands run inside the existing Slurm110860 allocation in tmux9 pane%20.
`launch_existing.py` records project queue bookkeeping and sends the command to
that shell; it never requests an allocation or changes CUDA_VISIBLE_DEVICES.

C2 is frozen and complete. Keep its worker and kernel hashes unchanged.

C1 fixed-prefix: `prepare_c1_stress.py`, `analyze_c1.py protocol`, phase-specific
mechanics using `run_events.py`, `audit_events.py`, discovery, `analyze_c1.py freeze`,
confirmation, `audit_c1_replays.py`, `analyze_c1.py analyze`.
The first mechanics failure is preserved; the second independently verifies
text-only implicit positions against the Stage6B identity-offset adapter.

Dynamics: `prepare_dynamics.py`, `repair_dynamic_anchor_sources.py`, mechanics,
discovery, `analyze_dynamics.py freeze`, confirmation, `analyze_dynamics.py analyze`.
Use `exact_anchor_manifest_v2.jsonl`. V1 was never scored; v2 adds the current
source for adjacent latency anchors without changing panel membership or pairs.
The exact panel fails its minimum gate and must remain descriptive.

Native C1: `prepare_native.py`, initial dense mechanics and `audit_dense.py`.
The first primary run encountered a long-context OOM. The v2 worker retains the
inactive checkpoint on the CPU; a focused allocator diagnostic and ten long
canonical controls validate `expandable_segments:True` on both A6000s. Use
`run_dense_v2.py` through `run_dense_v2_tmux.sh`, the
`native_dense_residency_mechanics.json` gate, and
`native_endpoint_manifest_v3_schedule.jsonl` for `native_primary_02`.
V3 changes only the execution order to balance token-length-derived work; all
1,199 entries and 14,906 endpoints are identical to V2. The original workers,
failed logs and original signatures are preserved. Programmatic demand remains
separate from manual review. Analyze with `analyze_trajectory.py` after completion.

C3: `prepare_c3.py`, mechanics, discovery, `analyze_c3.py freeze`, confirmation,
`analyze_c3.py analyze`. Existing polygons/RLEs are projected; absent query targets
are never fabricated. C4: `prepare_c4.py` and the validated dense worker on its
20 frozen case/control traces and predeclared wrong-claim boundaries, then
`analyze_c4.py analyze`. The controlled descriptor directions were frozen from
C1 discovery before inspecting C4 features.

Synthesis: `analyze_robustness.py`, `analyze_sink.py`, `audit_completion.py`.
Figures: `figures_controlled.py`, `figures_dynamics.py`,
`figures_native_validation.py all`. `figure_support.py` sets a project-local
Matplotlib cache before importing Matplotlib. Full raw results are required;
missing causal readouts remain unmeasured rather than being imputed from PCA.

`finish_stage.py` waits for both existing native completion records, updates the
queue record, and runs trajectory, sink, geometry figures, final audit and report
generation in that order. It requests no compute allocation and stops on the
first failed command. Progress and per-step logs are preserved in
`audit/completion_pipeline.json` and `runs/stage6b/completion_*.log`.
Review the generated artifacts and update compact research state afterward.

For CPU tests, explicitly use `-o cache_dir=outputs/stage6b/audit/pytest_cache`.
The original successful test command and cache-path exceptions are preserved in
`audit/cpu_checks_final.json` and `audit/cache_configuration.json`; do not modify
the existing project-root `.pytest_cache` under the current access policy.

Every run writes two rank signatures, model/environment records, raw per-event
results, exact replay checks and completion summaries under `outputs/stage6b/raw/`.
Do not interpret partial runs as complete. Discovery freezes must precede their
confirmation runs. No next-stage rescue or extension is authorized here.
