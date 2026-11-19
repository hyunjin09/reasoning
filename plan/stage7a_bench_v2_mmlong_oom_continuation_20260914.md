# MMLong per-sample OOM continuation amendment

User authorization, 2026-09-14 16:31 KST: skip samples that encounter OOM and continue the remaining native screen, keeping the existing four GPUs working while eligible work remains. This supersedes the stop-entire-dispatch behavior for a verified native sample CUDA OOM only.

Preserve the original 200-row cohort, all pages, the five preflight exclusions, decoding settings, successful outputs, failed attempts and historical manifests. Record runtime OOM separately from model errors and causal states, with the original denominator retained. Do not retry an OOM sample, reduce pages/caps, or proactively exclude other long documents. Other errors and failed mechanics checks remain fatal.

Implement versioned continuation files without altering the 35 dependencies of the live v8 workers. Let existing generations finish. Replacement workers wait for any predecessor batch on their Slurm-assigned GPU to exit before loading a model. A shared queue assigns unfinished batches without duplicating predecessor work; original successful artifacts are hash-verified and reused. Historical pending scheduler records are superseded explicitly.

A native sample CUDA OOM must save its event identity, traceback, elapsed time and an unavailable result, then exit the model subprocess. The parent restarts a clean subprocess on the same allocated GPU, verifies forward progress, skips terminal results and continues the batch. No unchanged retry of the failed sample. No new GPU allocation, benchmark, dataset or causal pilot.

Acceptance: focused CPU tests cover OOM continuation, non-OOM fail-closed behavior, ownership, predecessor handoff and preservation; unchanged generation/input settings verified; four replacement workers registered within allocation113280; existing and replacement GPU ownership does not overlap; native progress after the preserved OOM is observed. Then leave only the finite MMLong dispatcher running and return a concise handoff.
