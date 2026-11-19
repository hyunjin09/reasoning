# Phase 8A: 2B retrieval proxy and transport calibration

## Current Objective

Execute the user-approved Stage8A plan on Qwen3-VL-2B-Thinking/MathVerse: validate the platform, calibrate and confirm passive retrieval and weak-transport observability, test usable Value semantics where eligible, report the gates and STOP before reinjection.

## Active Constraints

- ACCESS_POLICY first; project/allowed dataset/model roots only. HF cache aliases remain read-only. Download only if needed and record inventory/provenance first.
- Completed within user-authorized115046/node02/tmux10:1, two A6000 GPUs,16 CPUs,100G. Released at2026-09-16 22:00:42KST immediately after GPU validation; no current allocation or further GPU work.
- New 2B-native traces; BF16/temp.6/top-p.95/top-k20/seed1234/cap40960/EOS. Discover the2B window; no transfer of4B head indices.
-48 discovery and48 disjoint confirmation families; target80–120 semantic events each. Hard mention-only, nearby and nonvisual negatives. No ROI/Value features in primary deployable R. Discovery-only threshold fitting, frozen confirmation, family bootstrap.
- No reinjection or next stage. Completed Stage7A-Bench v2 results and its previous recommendation remain preserved.

## Current State

- COMPLETE / STOP.96 fresh native traces (71 EOS/25 caps),96 prefix reviews (93,749 tokens;4 whole trajectories),113 discovery and114 confirmation events,36 unique Value assays.
- Gate0 PASS; Gate1 PASS (AUROC0.9776, M-FPR0.1277); Gate2 FAIL (19 states/18 families vs24/12 required); Gate3 PASS for16 evaluable states/15 families,16/16 positive, family median8.3125nats [7.1314,10.2163]. Missing3 wrong claims remain unavailable;4 evaluable states are mention-only negatives.
- Cheap transport candidates do not generalize (held-out AUROCs0.346–0.425); no cheap online weakness gate established. High-R/low-G is relative to frozen layers19–22/readouts, not a certified failure/MIRAGE state.
-115046 cancelled immediately after final validation; verified queue absence. CPU report complete, no remaining execution. Final evidence: `outputs/stage8a/summaries/stage8a_summary.md` and `.json`.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Exact-path controls prevent false causal contrasts | D-051/D-068, `workspace/decision_log.md` | Compare every arm on a validated2B partition; distinguish dense/backend parity | confirmed |
| Source/routing and downstream behavior can dissociate | `workspace/phase_memory/phase_3c10_retrieval_trigger.md` | Do not equate high attention with causal transport | confirmed on4B |
| Sparse controls limited captured failure yield | D-069, `workspace/decision_log.md` | Prepare source/readout/semantic-sham eligibility before effects | confirmed |
| Existing allocation114923/node03 | `runs/allocations/node03_2gpu_20260916/replacement_verified.json` | Resource ceiling and expiry | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Slurm calibration step and minimal CPU step | Socket timeout from node03.localdomain:6818 before Python | cause unknown; infrastructure rather than model execution | Restore node03 Slurm/project access before retry | No unchanged model relaunch or extra GPU request |
| Bare tmux target | Allocation window was6:10 instead of session10 | supported by exact pane metadata | Moved existing pane%23 to10:1; use explicit session separator | No ambiguous bare numeric new-window target |

## Open Candidates

| Candidate | Result | Status |
|---|---|---|
| Passive retrieval observability | Held-out AUROC0.9776; beats lexical/position with positive paired family CIs; probability calibration poor | supported in selected prefixes |
| High-R/low-G dissociation |19 states/18 families,9 held-out; below required24 | Gate2 failed; no expansion |
| Usable Value semantics |16/16 eligible weak states positive;3 wrong-state exclusions | conditional Gate3 PASS |
| Cheap transport gating | All five held-out AUROCs below.5 in frozen orientation | not validated |

## Next-Step Decision

- Current bottleneck: the full reinjection prerequisite is not met (Gate2 and cheap gate), despite positive retrieval/Value evidence.
- Relevant evidence: frozen-confirmation and Value summaries, exact GPU completion proof, release verifiedv2. Do not relax the gate, substitute25 JS-only states, flip cheap classifier signs or expand the cohort after effects.
- Exactly one recommendation: stop the Value-reinjection branch under the current calibration and preserve this mechanistic boundary.
- Authorized action is complete. STOP for user review. No recommendation/next experiment is launched; no GPUs retained.

### Historical initial action result

- Action taken: user-authorized node02 reallocation and unchanged calibrationv2 retry after a successful Slurm/project-read probe.
- Result: two distinct2B/BF16 GPU workers verified; both128-token repeatability checks pass;8/12 normal-EOS traces complete at2026-09-16T02:04:15.050321+00:00.13 CPU checks pass.
- Evidence saved: `outputs/stage8a/audit/node02_resume_checkpoint.json`, `outputs/stage8a/summaries/stage8a_node02_resume_checkpoint.md`.
- Remaining uncertainty: actual-GPU capture/streaming/Value mechanics and functional localization; every scientific gate remains pending.
- Next implication: mechanicsv2 automatically follows successful native calibration within115046; review/freeze source-local events and complete Gate0 before the main cohort.

### Infrastructure checkpoint — 2026-09-15T15:37:56.921040+00:00

0 native2B traces and0 causal events; Gate0 remains untested. Full checkpoint: `outputs/stage8a/summaries/stage8a_calibration_checkpoint.md`; evidence: `outputs/stage8a/audit/calibration_infrastructure_block_v1.json`. Allocation preserved in actual tmux10:1. No new allocation or scientific null claim.

### Calibration implementation checkpoint — 2026-09-16T02:26:27.262600+00:00

Nine of12 native traces complete, all normal EOS; worker0 finished, worker1 is on210. Seven semantic/readout-eligible prefix reviews and asset/tokenization preflights pass.19 CPU checks pass cumulatively. Mechanicsv1 was cancelled before any GPU task after code review; reviewedv2 waits in tmux10:3/pane%27. Evidence: `outputs/stage8a/audit/mechanics_prelaunch_review_v2.json`, `calibration_code_review_v1.json`.

Localization protocolv2 separates full-visual Value-carrier effects from ROI-only effects before any causal score;v1 and both preflight receipts remain preserved. This avoids assuming pixel-local edits imply spatially local contextualized Values. No main-cohort data or scientific thresholds have been fit. A single-head V-versus-N QK LSE contrast is mathematically the log-odds of visual attention mass before quantization; later feature comparisons must not treat this pair as independent evidence.

### Native/mechanics action result — 2026-09-16T02:45:32+00:00

Native12/12 saved:11EOS, one40960-token cap (210). The capped early prefix has a valid localAB12 event and remains separate from EOS accounting. All actual-GPU mechanics pass on both GPUs, including every one of128 raw-logit comparisons, all28-layer exact capture/cache and fixed-route self tests. Technical synthetic JS values are operation checks, not semantic evidence. Ten reviewed local-value events are frozen in `outputs/stage8a/localization/requests_v1.json`;752/185 are excluded from clean localization for source-binding validity, with explicit prefix-only review receipts.19 CPU tests pass. Profilev1 source56-file snapshot/config is frozen; no localization result viewed.

### Localization profile result — 2026-09-16T02:53:29+00:00

10/10 events and all28 individual layers complete, exact per-event native/self checks pass. Frozen rule selects zero-based19–22/all16heads: family-median sum8.2255nats, positive in10/10 calibration families. This sum is not a joint effect or a held-out scientific gate. Next: joint fixed-routing confirmation of this one frozen window, same10 events/controls. Evidence: `outputs/stage8a/localization/analysis_profile_v1/summary.json`, profile figures and raw per-token controls. No alternate window search is selected.

### Gate0 result — 2026-09-16T03:02:33.310769+00:00

Gate0PASS, jointS positive10/10, median10.199nats; targetVSD positive9/10 but small median2.02e-5nats.96 main families and48 reserves frozen with conservative known-family alias exclusions. Main source hashes remain identical to validated native calibration. See `outputs/stage8a/summaries/stage8a_gate0_main_checkpoint.md`.

### Main execution checkpoint — 2026-09-16T03:24:02.404088+00:00

Main nativev1 active in115046.9/node02/tmux10:2, distinct GPUs and both128-token repeats verified.2/96 normalEOS responses saved; both workers continue.2 source/prefix reviews seal6 events (2T,2M,2nearby); semantic/readout/asset preflight verifies4 eligible matched contrasts. No main passive/causal score inspected.30 unique CPU tests pass cumulatively (19 calibration+3cohort+4measurement+2schedule+2probes); main measurement/probe code still needs actual-model extension checks and release review. The8 live native dependencies remain unchanged. Read-only activity receipt confirms utilization within the existing allocation.

### Measurement extension result — 2026-09-16T03:31:32.312392+00:00

Actual2B/BF16 extension smoke PASS on both GPUs with calibration243/264: exact capture/self,32 strict-past queries, nine feature variants,2048-dimensional shallow output, raw decoder residual and full visual-off measurements. About14–15seconds per worker; brief overlap uses only existing GPUs. No main effects examined. Evidence: `outputs/stage8a/audit/measurement_extension_pass_v1.json`, `main_measurement_review_v1.json`. Finite fitting/CI details recorded in `plan/stage8a_analysis_protocol_v1.md` before main scoring.

### Source-scope clarification — 2026-09-16T03:50:42.050338+00:00

Fresh2B prefixes265/3 show visible-label source binding/type errors. They remain semanticT/M observations with local correctnessfalse and no eligibleS readout under the current reviewed contrast; do not convert them into faithful controls or causalwrong-source states. Main request preparation records `source_role=candidate_label_source` versus `demanded_source`. Raw targetedROI-minus-irrelevant suppression on a candidate label is not certified demanded-sourceVSD. Discovery/report analysis preserves this distinction. This input-only clarification precedes every main effect.

### Annotation checkpoint — 2026-09-16T03:57:59.632865+00:00

7 main source/prefix reviews seal24 candidates: {'T': 7, 'M': 7, 'nearby': 5, 'nonvisual': 5}. Only base53 has a full-trajectory review; other coverage is explicitly bounded to the complete selected-event prefixes. Base9 revision2 adds its planned nonvisual control and preserves the original three events/review. Repeated quote in3 is disambiguated by explicit reviewed occurrence0; guard/test preserves ambiguous-default rejection.33 unique CPU tests pass. No main effects viewed. Current source/readout preflight is input-only; first12 extra controls per class are selected in frozen manifest order, independent of generation finish order. See `outputs/stage8a/audit/annotation_checkpoint_v1.json`.

### Annotation/measurement validity update — 2026-09-16T04:14:50.374084+00:00

Main protocolv2 corrects the nearby-control interpretation before effects: arithmetic must follow a selectedT within256native tokens. Distant computations in204/3/287 are reclassifiednonvisual via preserved reviewv2 records; extra negatives are capped at one/class/base and first12eligible bases/class in frozen manifest order. Candidate sourceROI and demanded sourceROI are distinguished. `outputs/stage8a/audit/annotation_temporal_repair_v1.json` records input-only corrections. Measurement smokev2 passes on both GPUs and all feature/shallow/log-probability/JS/CE values are exactly identical to technicalv1; only native-prompt assertions and source-scope reporting changed. Source snapshots and both receipts remain preserved.8main source/prefix reviews are sealed; no main feature/causal outcome seen.

### Annotation/evaluation checkpoint — 2026-09-16T04:38:02.236785+00:00

12 main reviews sealed, including11T candidates; base97 has no eligible freshT because source binding is ambiguous. Bare numerals in answer choices are not source bindings. Base218 retains its wrong diameter→radius demand and does not substitute a later clean read for it.35 unique CPU tests pass, including frozen-confirmation prediction and family-overlap rejection. No main passive/causal result viewed. Evidence: `outputs/stage8a/audit/annotation_checkpoint_v2.json`.

### Active native checkpoint — 2026-09-16T04:42:20.935729+00:00

Both allocated GPUs remain busy;12/96 native traces saved and12prefix reviews complete.36unique CPU checks pass after repairing the secondary sink ablation to augment exactly the selected primary features. Main8native source hashes remain unchanged. Discovery measurement cannot launch until its48reviews are complete and the80–120event request set is frozen. Next dependent steps remain discovery fitting/Gfreeze, held-out confirmation, eligibleValue assays and finalgates; none runs automatically from the native wrapper. No reinjection authorized. See `outputs/stage8a/audit/node02_main_checkpoint_v2.json`.

### User-approved native tail rebalance — 2026-09-16T11:29:22.421741+00:00

Current19continues untouched on original115046.9.92completed traces are protected by a460-file SHA ledger. Three unstarted examples are reassigned under the same allocation: tailrank1runs345then425on the previously idle GPU; tailrank0waits for19and the original guard exit, then runs375. The original no-overwrite assertion at the reserved345directory is a deliberate handoff boundary, not an OOM/model failure. Preserve that original wrapper/exit; the new `outputs/stage8a/native/tail_v1/wrapper.json` will reconcile exactly96canonical results after all workers finish. No completed sample is regenerated. Generation/model/preparation/termination calls are AST-identical to the frozen runner; one reservation/overwrite test passes (37unique CPU tests total). Newstep115046.16/tmux10:3; source/config and planned assignments are frozen in `outputs/stage8a/audit/native_tail_handoff_v1.json` and `outputs/stage8a/config/main_native_tail_v1.json`. No new allocation, dataset, native protocol or scientific cohort change.

Tail launch verified 2026-09-16T11:32:31.679319+00:00: original19and helper345 are both generating on distinct allocated GPUs; helper128-token repeatPASS. Upcoming425and375are automatically assigned. Native progress reader recognizes tail workers and final reconciliation. Evidence: `outputs/stage8a/audit/native_tail_launch_verified_v1.json`.

### Native main completion — 2026-09-16T12:13:20.485813+00:00

All96unique native traces are saved,48discovery+48confirmation;71normalEOSand25token-cap completions. Last generation finished2026-09-16 21:01:34KST. Tail reconciliationPASS and all96result hashes reverified; the92pre-handoff completed records remain unchanged. Original19finished safely, followed by its planned guard exit;375/345/425completed in the new step. No missing/duplicate examples or completed-example reruns. Scientific interpretation remains pending.12reviews exist;36discovery and48confirmation reviews remain. Next dependency: finish discovery semantic review and freeze80–120eligible events, then run approved discovery measurements/fitting and freezeR/Gbefore confirmation. Existing115046allocation is retained; native inference steps have exited. Evidence: `outputs/stage8a/audit/native_main_completion_verified_v1.json`.

### Discovery freeze — 2026-09-16T12:33:38.430293+00:00

48/48discovery source/prefix reviews pass source-asset/native-token preflight:113events ({'nonvisual': 12, 'T': 41, 'nearby': 12, 'M': 48}),60semantic-eligible contrasts. First12eligibleTcausal confirmation subset frozen before main effects.8/48confirmation reviews sealed. Discoverymeasurementv1 launches on existing115046twoGPUs; no main effects seen at freeze. Continue confirmation semantic review while measuring discovery; freeze R/G before confirmation feature evaluation. Receipt: outputs/stage8a/audit/discovery_measurement_launch_v1.json. Native96traces and historical annotations preserved.

### Discovery fit and confirmation freeze — 2026-09-16T12:46:33.475128+00:00

96/96prefix reviews sealed. Discovery113/113measurements complete with exact event capture/selfchecks. Selected joint/max/C.01 R givesOOFAUROC.9211,recall.8293,MFPR.1875; these are model-selection statistics. Frozen transport weakness requires JS<6.149830919e-6 AND absolute full-spanCE<1.169726089e-5, lower quartiles of43OOFhighRdiscovery events.10discovery events qualify; threshold not tuned to24orS. Five scalar cheap-gate candidates fitted with discovery groupedfolds; cancellation has best discovery ranking, but remains exploratory pending heldout. Confirmation114events frozen ({'T': 44, 'M': 47, 'nearby': 11, 'nonvisual': 12}),76semanticeligible; measurement next on115046. User re-emphasized immediate release after requiredGPUassays, before report. No main Sscores examined.

### Final action result — 2026-09-16T13:09:00.777404+00:00

Confirmation114/114 and final Value36/36 complete with exact native/self/off-readout correspondence. Gate1PASS, Gate2FAIL, conditional Gate3PASS;24/24 prespecified eligibleT semantic confirmations are positive.19 state events include15T/4M;16 evaluable (12T/4M),3 locally wrong claims excluded for error-readout validity. Final report preserves cohort/annotation limits and all negative evidence. Recorded worker intervals total18.8121GPU-hours, node02 reservation22.5989GPU-hours (different scopes). User-requested release occurred at22:00:42KST immediately after the completion verifier; Slurm CANCELLED/queue absence subsequently verified. No allocation remains.

Operational observations: the initial30-second release observer saw COMPLETING and wrote false; verifiedv2 records the later terminal state without rewritingv1. A Value snapshot SameFileError was repaired before GPU work by using a project-relative source path. A final CPU resource parser initially assumed smoke runtime was top-level; it now reads the existing base receipts, with no scientific change. Original native handoff guard failure and prior node03 launch failure remain preserved.

Implication: complete/STOP, not a successful end-to-end online controller. Recommendation and evidence are in `outputs/stage8a/summaries/stage8a_summary.md`; no reinjection or further experiment.
