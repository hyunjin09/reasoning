# Phase11A: visual-evidence bottleneck census

## Current Objective
COMPLETE / STOP — describe whether matched Thinking/CoT outcome differences coincide
with explicit evidence recoverability, observable native evidence access, or downstream failure.

## Active Constraints
- All128 Stage9A MathVision families reviewed before mode correctness is opened.
- E*1–4 image-derived atoms, sufficient with question text; two independent passes.
- Preserve384 native traces; no new full benchmark generation or model comparison.
- At most64 families ×3 short probes; optional12-family oracle pilot only after gates.
- Slurm only, authorized ceiling8 GPUs, hard stage cap<2.5GPUh; no automatic Stage11B.

## Current State
- Done: approved plan, policies and D110–D114 read; existing model/data located.
- Done:128 image/question-only packets and384 native source hashes; no native accuracy opened.
- Done: two independent128-item construction passes (A60/B67 eligible proposals), originals preserved.
- Done: common65-set review plus two versioned exact-set repairs;61 eligible families sealed before outcomes.
- Done:183 native traces sealed after101/103/75 raw reviews, seven shared state disagreements adjudicated, and12 fixed quality audits. All96 shared reviews remain in the raw32-family agreement calculation. Sources: annotations/native_final.json and annotations/native_adjudication.json.
- Done:183 short mode-blinded probe reviews sealed,61 each to main/A/B. Native labels sealed before probe response export; probe labels sealed before correctness/mode join. Independent32-family localization rule reviews agree completely.
- Done: all183 frozen512-token probes completed. Jobs125491/125492 completed and both GPUs released. Allocated GPU time including initial import failures:0.450278GPUh; peak2 GPUs.
- Done: paired census and4000 family bootstrap draws. Frozen decision NO_GO:12 Thinking-correct/CoT-failed families,4 unique localizations (A1/B1/C2),8 mixed;4<8 required informative families. Reverse4/4 mixed. Eligibility and agreement pass; no optional pilot.
- Done:14 required artifacts, four PNG/PDF figure pairs, completion audit and separate numeric/seal-order/presentation review. All originals retained; no Stage11B or new experiment launched.
- Twelve focused protocol/statistical/denominator/import/annotation-validation checks pass; primary allocation target<1.5GPUh and hard stage cap<2.5GPUh.
- Blocked: none.
- No model accuracy or probe outcomes were opened for Stage11A selection; joins occurred only after annotation seals.

## Evidence That Matters
| Evidence | Source | Relevance | Status |
|---|---|---|---|
| Passive access and native-text NLL did not suffice for reopening | D114 | Separate measurements and claims | confirmed |
| Correct final answer need not imply correct local evidence | prior failure stages | Independent evidence/answer annotation | confirmed |
| Matched128 families,384 original trajectories | Stage9A manifest | Reuse, no outcome-based selection | confirmed |
| Only4/12 Thinking-gain families uniquely localize | stage11a_go_nogo_decision.json | Fails frozen minimum8; STOP | confirmed |
| Native fine kappa0.886; coarse1.0; localization1.0 | stage11a_annotation_agreement.json | Agreement passes; low yield is not caused by a failed reliability gate | confirmed |
| Thinking57/61,CoT24/61,Direct0/61 probes hit512-token cap | stage11a_resource_accounting.json | Recoverability is bounded by the prompt and budget | confirmed |

## Failed Attempts and Lessons
First GPU launch failed before model/sample execution: local statistics.py shadowed stdlib statistics.median. Both logs and a failing import regression confirm the cause; renamed the helper to census_statistics.py,10 tests pass. Frozen worker/manifest hashes unchanged, zero claims/results. Retry is justified by removal of the naming collision. Evidence: outputs/stage11a/v1/audit/import_repair.json.

Prior collector dependency failure counsels explicit job-state checks before
downstream work; do not assume environment-only Slurm dependencies were applied.

## Open Candidates
None authorized. Optional feasibility pilot skipped under NO_GO; no Stage11B.

## Next-Step Decision
- Bottleneck: insufficient uniquely localizable mode-discordant families under the frozen measurement budget.
- Memory used: D114 local evidence and native outcomes remain distinct;4 informative families do not meet Stage11A's frozen8-family minimum.
- Chosen action: STOP after the completed census; no optional pilot or new research action.
- Why: NO_GO is the prospectively specified decision. Thinking accuracy25/61 versus CoT17/61 does not itself localize the mechanism; probe recovery16/61 versus18/61 is strongly budget-limited.
- Do not repeat: treating probe recovery as internal encoding, or absent text as
  absent hidden state; selecting evidence from successful model answers.
- Stop condition: met. Exactly one recommendation: stop the bottleneck branch and finalize the paper around the already-established causal retrieval and visual-to-text lifecycle claims. Recommendation not executed automatically.
