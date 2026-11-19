# Stage12B visual failure bottleneck profile

**TECHNICAL_STOP**. Technical validity failed; no bottleneck proportions or task accuracy are estimated.

All61 independent MathVision families,157 E* facts, questions/images/source answers and earlier Stage12A/12A-R evidence are preserved. Model: Qwen3-VL-4B-Instruct, revision ebb281ec70b05090aa6165b016eac8ec08e71b17, BF16/vLLM0.11.0. E cap256; native N and image-free O cap32768; official Instruct .7/.8/top20/repetition1/presence1.5. N has no appended instruction. O preserves exact facts and original questions; frozen requests provide fact/entity labels.

## Technical sanity

| Arm | Parseable | Committed finals | Caps | Severe repetition | Gate |
|---|---:|---:|---:|---:|---|
| E | 12/12 | 0/12 | 0/12 | 0/12 | PASS |
| N | 12/12 | 12/12 | 0/12 | 4/12 | FAIL |
| O | 12/12 | 11/12 | 0/12 | 3/12 | FAIL |

E commitment is not a task-solving endpoint; E parseability is the relevant gate. Native spontaneous reasoning is permitted. Semantic repetition review is separate from token n-gram diagnostics. No gold correctness entered the technical gate. No prompt/cap adaptation was performed.

Severe-cycle cases: N725,1140,2975,750; O1140,2975,750. These repeatedly reopened the same interpretation/calculation, including after provisional final answers. Long advancing digit enumerations (N1988:13676tokens; O1988:9520tokens) were not counted as severe merely for length. Technical review was a same-agent review: short responses read completely; long responses inspected at head/middle/tail and repeated-cycle passages, with full text retained. No independent rater agreement is claimed.

## Oracle integrity

61 source-only checks and13/61 (21.3%) randomly selected second-pass reviews completed before generation. The second pass used the same agent, not an independent rater. Actual oracle inputs contain no image and generated input receipts verify zero visual tokens. Bare values retain their exact original request labels. Original empty question528 is retained, with target implied by its frozen question-mark-cloud fact; this is an explicit input limitation. Literal image references remain text. Direct-classification item458 requires minimal downstream inference.

## Scientific profile

P1–P6, B1–B4, oracle-rescue contrasts and accuracy: **NOT_ESTIMATED**. Unrun/null rows are not errors. The gate failed before scientific correctness was opened; no remaining49 families were generated. This is not evidence for or against perceptual, access/use or downstream dominance. The cause of the repetitive reasoning remains unresolved; all36 calls stopped normally.

All labels, if estimable, are bottleneck candidates: E−does not establish absent encoding; E+does not establish native retrieval; O+changes evidence representation; O−does not prove perfect perception. This cohort is developmental, not population-wide prevalence.

## Resources and evidence

36/183 calls completed; 147 NOT_RUN. **0.389167 allocated GPU-hours**, including startup and teardown; target<6/hard8. All stage GPUs released. No download/install, CoT, Thinking or further experiment.

[Read complete responses](../../../reports/stage12b/v1/index.md). Exact inputs, text/tokenIDs and receipts are in generations/; reviews, source hashes and statistical specification are preserved. All15 required root artifacts accompany this report. Figure1 is the assay schematic; figures2–4 are explicit NOT_ESTIMATED placeholders because scientific profiling was gated off.

## Exactly one recommendation

Repair the native/oracle assay before any scientific interpretation or additional conditions. This recommendation was not executed.
