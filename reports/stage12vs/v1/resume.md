# Stage12V-S execution checklist

Stage completed and verified. Read stage12vs_summary.md for results. STOP; no
subsequent experiment is authorized by this completed plan. The historical
execution instructions below are retained for reproducibility, not for rerunning.

## Frozen preparation

- [x] Four primary production-support families: 2975, 798, 750, 2908.
- [x] Fifth family 991 preserved descriptively; no new calls.
- [x] Exact source prefixes split losslessly into 2,036 steps, with role tags
  and six coarse anchors frozen before generation.
- [x] 72 coarse replay tasks and seeds frozen; all CPU input checks pass.
- [x] Nine protocol/inference tests pass; source and analysis hashes sealed.
- [x] Two finite 36-call Slurm workers submitted: 129295 and 129296.
- [x] CPU-only receipt observer 129299 submitted; no scientific launches.
- [x] Phase A outputs complete, reviewed, and score extraction QC sealed.
- [x] Full-prefix replication gate evaluated: all four pass.
- [x] Deterministic fine localization completed:2975 stable29→30,2908 stable735→736;798 missing,750 nonmonotonic.
- [x] Adjacent-prefix Thinking checks completed for stable transitions.
- [x] Critical-step edits and matched noncritical controls manually audited
  and frozen before their intervention outputs.
- [x] C1–C5 completed and scored; optional evidence-plus-step only if mandatory
  conditions are complete and remaining compute permits.
- [x] Family inference, all required artifacts, four figures, resource
  accounting, and historical-evidence verification completed.
- [x] Exactly one recommendation recorded; STOP, no follow-on experiment.

## Review and advancement

Use the project CPU environment with `PYTHONPATH` containing `code`, project
root, and `infra`. Do not rerun `prepare.py` or overwrite existing receipts.

1. Check actual Slurm state and `workers/<job>/exit.json`, then verify every
   completed task using `scripts.stage12vs.review.checked`. Raw outputs are in
   `outputs/stage12vs/v1/generations/<task>/generation.json`.
2. Run `python -m scripts.stage12vs.review phaseA` to create and display
   continuation-only review packets. Extract committed outcomes manually with
   `review.record` before correctness. Inspect more than the displayed tail
   wherever needed. Unfinished cap hits stay missing; no credit from a prefix.
3. Run `scoring first phaseA`, `scoring freeze phaseA`, and
   `scoring show_second phaseA` via `python -m scripts.stage12vs.scoring`.
   Complete the separate extraction pass using `scoring.second`, preserve and
   adjudicate any disagreements, then `scoring close phaseA`. This is same-agent
   QC, not independent inter-rater reliability.
4. Run `python -m scripts.stage12vs.advance gate` once. More than one failed
   full-prefix replication triggers the plan's stop before content ablations.
   Missing or unspecified patterns remain unresolved, not forced failures.
5. If eligible, run `advance fine --phase phaseB1`. Launch only that newly
   frozen manifest using `scripts.stage12vs.launch` with an appropriate finite
   time limit. Review/QC/close the wave before materializing phaseB2, and so on.
   No new seeds at an already-tested boundary. Stop each family on the frozen
   stability/nonmonotonic/missingness rules. The actual source lengths imply a
   worst-case 75 fine calls; the plan's 48 was an approximate estimate. The hard
   seven allocated GPU-hour limit remains unchanged.
6. After fine localization closes, `advance adjacent` freezes the prescribed
   before/after Thinking checks. `interventions.py` consumes prospectively
   authored `audit/manual_intervention_edits.json`; inspect its required fields
   before writing the edits. It must never choose text from intervention
   outcomes. A non-propositional critical step or an unidentifiable matched
   control is a scientific limitation, not permission to invent an edit.
7. Review/QC each new wave using the same procedure. Report all seed outcomes,
   family counts and exact descriptive intervals. Counterfactual-following,
   if used, needs a prospectively specified semantic readout and an explicit
   response audit; do not infer it from correctness alone.

## Resource and reporting safeguards

`launch.account` reads preserved terminal receipts and includes remaining
wall-time commitments before every new launch. Keep total committed allocation
at or below seven GPU-hours. Finite workers exit and release GPUs on completion;
the observer only saves receipts. Neither launches the next scientific wave.

Final reporting/figure assembly is complete; final decision is
PORTABILITY_NONMONOTONIC. The following verification safeguards were applied. Represent plan-gated omitted
panels explicitly rather than fabricating rows. Verify all 5,219 previously
snapshotted historical files against `audit/preserved_history.json` at closure.

The short 798 trace received a full manual primary-role review. The longer
traces use frozen source-cue tags with explicit uncertainty; they were not
exhaustively independently semantically certified. Carry that limitation into
the report and do not infer a common mechanism from uncertain tags.

Scheduler updates regenerate `reports/index.md`. Restore the curated Recent
research reports section from `audit/reports_index_before.md` after the last
update and add the Stage12V-S report link without deleting historical links.

## Concurrent follow-up submission — 2026-10-01T08:20:08.259588+00:00
Fine114 calls reviewed/QC closed. Adjacent Thinking jobs129900/129901 (12 calls)
and Instruct C1–C5 jobs129902/129903 (30 calls) are independent and submitted;
review entire `adjacentT` and `contentC` waves using the frozen review/scoring
procedures. See `audit/manual_intervention_edits.json` for prospective CF-following
readouts; record explicit response-based labels before final inference. OptionalE
six calls are only prepared, not launched; do not launch before all mandatory
controls complete and the cumulative budget is checked. No concurrent duplicate
task IDs;all prefixes/questions/recipes/seeds remain frozen. Source semantic
novelty caveat:both critical steps repeat earlier content. Next CPU observer129904
is24h/zeroGPU and depends on129710 to preserve overnight Slurm receipts.

## Final closure — 2026-10-01T10:13:16.824965+00:00
All162 calls reviewed,16 artifacts,4 PNG/PDF figure pairs,162 full responses;5,219 historical files unchanged.2.405556GPUh,all science GPUs released. Pending CPU successor129904 cancelled; active observer129710 exits on STOP. Exactly one recommendation recorded,not launched. No remaining execution task.
