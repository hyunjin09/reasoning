**Resource amendment 2026-09-20T05:09:09.078330+00:00: four node02 GPUs, Slurm118545; see stage8c_v3_four_gpu_resume_v1.md.**

# Stage8C v3 execution checklist

Updated 2026-09-22 KST. **Complete at development no-go.** Active plan: `stage8c_v3_fp32_direct_retrieval_gain_plan.md`.

- [x] Read plan, access/GPU policies and prior phase evidence.
- [x] Implement direct full-FP32 loader; reuse gain, detector and sampling logic.
- [x] Record exact new dose tie-break order; six focused CPU tests passed.
- [x] Verify/copy frozen dev128/test512 and timing/audit subsets; seal source/config.
- [x] Submit two node02 GPUs through project scheduler and Slurm.
- [x] Verify startup and ordinary decoding on both GPUs; FP32 dtype receipts and live VRAM recorded.
- [x] Four-GPU user amendment: cancel118529, preserve two interrupted attempts, resume118545.
- [x] Confirm all512 complete receipts/4608 artifact hashes and preserved frozen sources.
- [x] Complete512 dev trajectories with FP32 dtype receipts and unchanged scoring adapter.
- [x] Seal78 masked extraction reviews; report53 unresolved graded outcomes without credit.
- [x] Apply no-go guards: all gains fail positive accuracy and rescue balance. Dose=null; stop.
- [x] Held-out512 condition evaluated: not permitted by dev no-go; explicit not-run artifact.
- [x] Timing256/local-read128: not run under dev stop; empty status-tagged semantic table.
- [x] Extension criteria: not reached; no extension launched or selected.
- [x] Produce applicable development figures, summary, runtime and one recommendation.
- [x] Release four node02 GPUs automatically after job118545 exits0. Remaining compute0GPU-h.

No BF16 repair, transfer audit, detector recalibration or pre-efficacy V1–V6.
The authorized plan is complete at its development stop boundary. Block3B is a
recommendation for user selection, not an automatically launched next experiment.
