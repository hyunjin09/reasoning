# A6000 Calibration v2 Summary

**PASS — A6000 CANONICAL PATH READY**

Calibration v1 remains an immutable FAIL because its full-vs-bounded cross-path parity gate failed. Calibration v2 does not relabel that result; it validates one fixed within-path execution protocol.

## Canonical path

P1 one-shot cached execution was rejected after the frozen longest-prefix case OOMed. P2 therefore selected the largest fixed repaired chunk that passed all six frozen stress cases: **2,048 generated tokens**, with allocator-cache release between chunks. Selection used memory feasibility only. No per-example chunk switching is permitted.

## Readiness results

| # | Criterion | Status |
|---:|---|:---:|
| 1 | P1/P2 choice frozen from memory feasibility | PASS |
| 2 | One execution path for every Stage 3C.9 causal condition | PASS |
| 3 | No per-example chunk-size switching | PASS |
| 4 | Deterministic replay | PASS |
| 5 | Self patches | PASS |
| 6 | Intervention selectivity | PASS |
| 7 | GQA/RoPE/cache indexing | PASS |
| 8 | W8/W16 mechanics | PASS |
| 9 | Event/neighbor cache patching | PASS |
| 10 | Local/final readout scoring | PASS |
| 11 | All outputs finite | PASS |
| 12 | >=90% strong/medium historical causal-sign agreement | PASS |
| 13 | No systematic sign reversal | PASS |
| 14 | Target-vs-control ordering preserved | PASS |
| 15 | Long-prefix stress fits frozen A6000 path | PASS |
| 16 | No silent truncation or backend fallback | PASS |
| 17 | Intended A6000 device pool passes cross-device replay | PASS |

## Numerical characterization

Multimodal prefill tensors matched exactly in all three first-divergence probes. Divergence began only after different continuation execution shapes entered the BF16 language stack (layers 2–3), consistent with deterministic shape-dependent drift rather than a prefill, RoPE, or cache-indexing defect. Absolute cross-path D equality is diagnostic, not a readiness gate.

## Internal validity

The authoritative 12-base run passed 96/96 deterministic arm checks, 192/192 cache self-patch checks, and 48/48 residual self-patch checks. W8/W16, event/neighbor, and local/final mechanics each covered 8 validation bases.

## Scientific continuity

Strong/medium bridge effects retained 24/24 suppression/KV-rescue/residual-rescue signs. Target suppression exceeded matched irrelevant-ROI suppression on 8/8 bases. Threshold-adjacent classifications are reported at 0.025, 0.05, 0.10, and 0.15 nats/token; the frozen primary threshold remains 0.05.

## Hardware

All six frozen stress cases fit below the 90% reserved-VRAM ceiling. Devices 0–3 in Slurm allocation 108085 each passed the strong, medium, small-effect, and 30,574-token long-prefix probes with no OOM, truncation, or backend fallback; short-probe results were exactly identical across devices.

## Boundaries

Earlier `smoke`, `run`, and `run_v2` trees are preserved as implementation diagnostics and are excluded from readiness evidence. No Stage 3C.9 result may mix A5000 and A6000 trajectories. Stage 3C.9 must restart from 0/600 and use this fixed path for every causal arm.
