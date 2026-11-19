# Stage14B user-approved GPU OOM skip amendment v1

Timestamp: 2026-10-05T09:42:40.566200+00:00

The user requested: “if oom happens, the worker should skip that sample and continue on to the next one.” This supersedes the old retry-first behavior for an identifiable GPU-OOM sample. Original protocol and completed evidence remain immutable; this is an execution/missingness amendment during generation, without scientific outcome inspection or selection.

Healthy current workers remain running. A finite CPU supervisor watches jobs136129–136136 and launches at most one replacement per terminal GPU-OOM worker, using the project scheduler, authorized nodes, and the existing eight-GPU ceiling. An attributable OOM sample receives a final TECHNICAL_MISSING record and is skipped. If a shared-engine failure cannot identify one sample, interrupted requests are resumed once at singleton concurrency rather than arbitrarily blamed or discarded. Recovery workers restart a fresh engine inside their allocation after each identifiable OOM, then continue the remaining queue. A replacement allocation can wait in Slurm.

Prompts, checkpoint revisions, pixel limits, seeds, precision, caps, sampling, cohorts, scoring, and all completed results stay unchanged. Original files/seals are retained; the amendment and recovery implementation have a separate hash seal. Non-OOM failures, cancellations, wall limits, host-memory OOM, and startup failures without a request remain explicit holds. No correctness scoring or new phase is launched by the supervisor.

Validation:42 Stage14B CPU tests passed, including14 new recovery tests and subprocess fault injection (fatal OOM followed by successful next-sample completion). No live GPU OOM was induced. Four supervisor tests passed after a final error-isolation change. No Git metadata is present; versioned files and SHA256 seals provide provenance.
