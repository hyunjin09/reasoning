# Stage14D bounded technical calibration

**PASS_TECHNICAL_ONLY.** All24 frozen calls completed and passed their mechanical checks. No scientific main continuation was generated or scored.

Four source images and eight checkpoint-specific early prefixes were actually reviewed. Four fresh-engine B0 pairs match all512 generated tokens, exceeding the preregistered128-token check. All four targeted ON/OFF pairs share exactly the same processed prefix, image and prefill K/V hashes across36language layers; their first sampled token matches. Only subsequent generated queries lose image-key access. Prior visual/text K/V and directive prefill are retained. GPU attention checks compare against an explicit FP32 masked reference at the frozen BF16 tolerance; image probability mass is exactly zero in that reference and compacted keys exclude precisely the image-token positions.

The initial callable-RPC setup failed before any model call. A versioned named-worker-extension repair fixed transport without changing cases, targets, prefixes, seeds, sampling, caps or the mask algorithm. Insecure serialization remains disabled. Both failed startup allocations and both successful allocations are preserved. Total allocated cost: **0.36305556GPU-hours**; all GPUs released. The24-call allowance is exhausted even though its2GPU-hour ceiling was not reached. No additional generation is authorized under that release.

Explicit technical settings: single active request, max_num_seqs18, eager vLLM execution, prefix caching disabled, pinned4B checkpoints, BF16/FlashAttention2, original MathVision image preprocessing and model-specific sampling. All calls used the deliberate512-token technical cap. These cap hits do not diagnose long-form noncompletion. Output correctness was not inspected or used as a gate.

Measured ON request throughput: Instruct25.11 and Thinking44.97tokens/s. OFF:20.34and38.27tokens/s. These serial instrumented measurements do not validate the earlier42.54GPU-hour projection based on historical batched jobs. A full-inventory linear extrapolation at serial rates is239.79GPU-hours; neither that extrapolation nor doubling it establishes an81920-token tail bound. Source/anchor and CF eligibility are still being reviewed. See `../audit/technical_resource_reestimate_v1.json`.

**Main scientific release remains held.** Main300source/420native-anchor reviews and source-specific CF eligibility are incomplete. Stage14C-Vclosure has not been waived. The100GPU-hour full-stage ceiling is still a proposal. No Stage14E/F or other new scientific experiment has been launched.
