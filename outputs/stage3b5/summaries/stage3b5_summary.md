# Stage 3B.5 — Sequential Residual-Stream Mediation and State-Dependent Recompute

Technical status: **PASS**. Recommendation: **GO — Attention head/path localization**.

The independent eight-base A5000 gate passed before primary scoring. The primary analysis uses the exact 37 paired numeric base problems, two frozen coordinates, W4/F28_29 and W5/F32_33, both individual layers, and five prospectively defined block boundaries. All 1480 rows and 40/40 corrected tests are present; 26/40 met the frozen Holm/CI/bidirectionality/render/self robustness rule.

GPU execution used 16 recorded A5000 Slurm jobs (validation 106912--106919; primary 106923--106930). Peak primary allocation was 8.745 GiB. Exact commands, logs, result paths, job IDs, and statuses are preserved in `config/gpu_job_manifest.json`.

## Primary boundary profile

| Coordinate/window | first h_pre | first h_post_attn | second h_post_attn | frozen two-layer Block | first h_pre / Block | Frozen category |
|---|---:|---:|---:|---:|---:|---|
| Ed_minus_1/W4 | 0.3461 | 0.6001 | 1.0024 | 0.9969 | 0.264 | Attention (first) |
| Ed_minus_1/W5 | 1.0880 | 1.2912 | 0.7188 | 1.3718 | 0.786 | Attention (first) |
| Ed/W4 | 2.0076 | 3.2813 | 6.0621 | 6.0635 | 0.365 | Attention (second) |
| Ed/W5 | 7.5592 | 8.6712 | 9.1677 | 9.1730 | 0.808 | upstream |

The frozen decision rule identified qualifying post-Attention gains in 3/4 cells: both W4 coordinates and W5 at `E_d-1`. W5 at `E_d` was the only cell satisfying the upstream-state rule (`h_pre`/Block = 0.808); W5 at `E_d-1` was close but remained below the frozen 0.80 cutoff at 0.786. No MLP-gain or cross-layer-sequential category qualified.

Patching only the RMS-normalized Attention or MLP input while retaining the recipient raw residual produced much smaller restoration than patching the corresponding raw residual state. This distinguishes normalized-input sufficiency from raw residual-state carriage; it does not assign a unique information fraction to RMSNorm, Attention, or MLP.

## State-dependent recomputation

| Coordinate/window | h_pre - Joint / Block | h_post_attn - MLP / Block | first h_pre - second h_pre / Block |
|---|---:|---:|---:|
| Ed_minus_1/W4 | -0.210 | 0.646 | -0.330 |
| Ed_minus_1/W5 | 0.435 | 0.847 | -0.254 |
| Ed/W4 | -0.150 | 0.547 | -0.201 |
| Ed/W5 | 0.376 | 0.806 | -0.162 |

`h_pre` plus natural recomputation exceeded frozen Stage 3B.4 Joint-output restoration in both W5 cells but not W4. However, first-layer entry restoration did not exceed the second-layer `h_pre` arm, so the preregistered cross-layer-necessity rule did not pass. In contrast, source `h_post_attn` plus natural MLP recomputation exceeded the frozen precomputed MLP-output arm in all four cells by median 0.548--0.847 Block units. This supports state-dependent recomputation as an explanation for part of the Stage 3B.4 module/block gap, while not identifying a unique information fraction.

## Exact implementation equivalences

The first-layer `h_pre` arm is also the requested two-layer entry-recompute intervention. It was executed once and reported in both the boundary and sequential analyses; it was not double-counted as an additional hypothesis test. First-layer `h_post_block` and second-layer `h_pre` were exact at the captured interface and in every patched score, validating the cross-layer implementation.

Across all 296 base/coordinate/window/layer cases, `h_post_attn` plus natural MLP recomputation and direct `h_post_block` restoration produced exactly identical public scores. This is expected because the MLP is deterministic and positionwise once the raw source post-Attention residual is fixed. Therefore the zero `G_mlp` is a structural equivalence of these interventions, not evidence that MLP computation is globally irrelevant.

The post-Attention boundary gain meets the frozen robust gain and dominance rule in at least two fixed cells. Complete boundary, increment, state-vs-precomputed, cross-layer, coordinate, and window results plus 10 figures are in `outputs/stage3b5/analysis/`.

These interventions localize evidence-specific restoration at current-position block states. They do not identify an attention head, ROI path, Q/R carrier, MLP feature, multi-evidence refresh process, or failure mechanism. Attention magnitude was not used as causal evidence. Stage 3B.5 stops here.
