# Stage9A completion checklist

Verified 2026-09-24T06:07:45.492795+00:00. Original plan and execution protocol preserved.

- [x] Frozen128-family cohort and native three-arm protocol; all-arm parity preflight.
- [x]384 native trajectories preserved; all underlying artifact hashes verified.
- [x]700 masked semantic,610 masked source/readout,384 masked extraction reviews completed.
- [x]50 outcome-independent frozen causal events replayed, all native-prefix/capture/sham gates passed.
- [x]Four primary endpoints, fixed-caliper matching, family-clustered regression, demand controls and sensitivities.
- [x]Secondary accuracy, subtype support limitations and resource burden documented.
- [x]All13 required artifacts and five figures in PNG/PDF verified;18 focused tests passed.
- [x]All scheduler workers terminal, all GPUs released. Remaining compute: zero.
- [x]Exactly one recommendation and STOP; no follow-on or rescue experiment.

[Final report](../outputs/stage9a/v1/stage9a_summary.md) · [Validation](../outputs/stage9a/v1/audit/final_validation.json)

## Historical checklist and resource estimates

# Stage9A execution checklist

- [x] Read policies, plan and relevant prior state.
- [x] Locate existing data/checkpoints; avoid downloads.
- [x] Freeze scientific definitions and implement/test arm-specific runner.
- [x] Seal128-family cohort/config/model hashes.
- [x] GPU preflight all arms: native tokens/logits unchanged; raw Stage8A feature parity.
- [x] Generate384 native trajectories, verify receipts and completion.
- [ ] Build and complete masked bounded semantic demand/source reviews; freeze annotations.
- [ ] Freeze up to32 eligible causal events/arm; record feasibility and matching.
- [ ] Run source-sensitive fixed-history controls; validate parity and oriented readouts.
- [ ] Family-paired P1–P4, normalized time, fixed-caliper matching, adjusted regression, raw panel and secondary accuracy.
- [ ] All13 outputs/5 figures, resource accounting and exactly one recommendation; STOP.

Initial budget:25–55 GPU-hours native plus2–6 causal, measured ETA pending. Two available node02 GPUs observed; maximum4 available authorized GPUs total. Causal/review time is additional to native ETA.

Resource amendment: node07 authorized, but first preflight cancelled for startup RPC I/O wait. Recovery coordinator awaits healthy node02/node03/node06 capacity (maximum4 GPUs), then gates384 native trajectories on preflight. No reliable start ETA while capacity is unavailable. No native scientific evidence yet.

Progress 2026-09-23T11:08:15.601863+00:00: recovery succeeded, four GPUs active on node06/node02, 39/384 native complete. Native-only ETA14–20h; review/causal/analysis additional.

Native completed September24,12:14KST; verified 2026-09-24T04:42:48.908068+00:00. All three exported table hashes match;384 masked packets present. GPUs released; semantic/causal/analysis steps remain unchecked.
