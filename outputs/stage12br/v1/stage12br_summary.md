# Stage12B-R pathology-aware validity repair

Decision: **VALIDITY_REPAIRED**. This validates input integrity and scoreability only; task/evidence correctness remains unopened and bottleneck proportions are not estimated.

Fresh validation IDs: 1478, 458, 2214, 2448, 991, 798, 2908, 2013, 1974, 1942, 2580, 2273. Exclude the original 12 development cases; rank the remaining 49 by SHA256(`stage12br-validation-v1|family_id`), choose the first 5 multiple-choice and 7 open-ended families, and merge in hash order. Selection used only identity and answer type. The cohort, rules, pathology guide, and exact 36 copied requests were hashed before generation. Manifest SHA256: `d35498521fa3293867961f5deb5e4ab7ae74449598ffdbb927448158ec0a20df`.

E is the image-present evidence probe; N is native image-plus-question Instruct; O is the image-free Equal-Evidence Oracle.

| Arm | Input valid | Scoreable | Truncated before outcome | Cap after outcome | Normal stop |
|---|---:|---:|---:|---:|---:|
|E|12/12|12/12|0/12|0/12|12/12|
|N|12/12|11/12|1/12|0/12|11/12|
|O|12/12|11/12|1/12|2/12|9/12|

Each arm must have 12/12 input-valid, at least 10/12 scoreable, and at most 1/12 pre-outcome truncation. No repetition threshold. Inputs were verified against exact frozen tasks, image hashes/multimodal payloads, oracle text, and the inherited 61-family source-only oracle review. No prompt/model/runtime/cap/seed change. All 192 snapshotted Stage12B artifacts remain unchanged.

| Capped response | Classification | Output-only rationale |
|---|---|---|
|O_2214_v1|Cap after scoreable outcome|The last explicit commitment is boxed33, after reconsidering and superseding the hypothetical trapezoid-area7 branch. The unfinished final generic restart introduces no new incompatible answer or withdrawal. The answer is extractable despite unresolved support and a cap; cap-after-outcome. No proof or answer correctness assessment.|
|O_991_v1|Cap after scoreable outcome|Repeated explicit minimum-move answer2 survives at the cap, including the final I think I have to say2 after rejection of another attempted sequence. Earlier3 speculation is superseded. Move1..4 labels are steps in unsuccessful attempted constructions, not a competing committed minimum. Failed support does not make the expressed task answer unscoreable. Cap-after-outcome; no correctness assessment.|
|N_2013_v1|Truncated before scoreable outcome|Cap interrupts repeated clue interpretation; no concrete task answer or completed grid is committed. Saying it needs to box an answer does not supply one.|
|O_1974_v1|Truncated before scoreable outcome|An earlier intended5:6/C is repeatedly reopened and challenged by newly asserted geometric ratios5:9 and5:8. The terminal segment keeps switching layouts and ratios and is cut off during another reconstruction; it never recommits to C or another ratio after that disagreement. Unlike a final forced guess, option-membership remarks alone do not settle the incompatible terminal derivations. No unique surviving task outcome; pre-outcome truncation. No correctness assessment.|

Cap boundaries were reviewed semantically against the prospectively frozen rules. A still-committed answer does not require a correct or convergent derivation. Conversely, an earlier candidate does not suffice when later incompatible terminal answers remain unresolved. Complete traces and exact quotes support these distinctions.

| Arm | R1 repetition | R2 reopening | R3 nonconvergence | R4 long advancing | R5 terminal ambiguity |
|---|---:|---:|---:|---:|---:|
|N|8/12|7/12|7/12|4/12|0/12|
|O|7/12|5/12|5/12|3/12|1/12|

Labels overlap and cover 24 N/O outputs. R1–R4 do not exclude otherwise scoreable outcomes; R5 is also unscoreable. Long advancing means at least 4096 tokens plus semantic progress, never merely length. One-agent semantic annotation used complete raw traces and supporting quotes. For the four capped traces, exact duplicate paragraphs were collapsed losslessly for review, with all unique text, offsets, duplicate maps, and original-order endings preserved. There is no independent inter-rater reliability claim. These small-set frequencies are technical-validation descriptions, not scientific prevalence or causal attribution.

All 36 raw outputs/token IDs are preserved; [full response pages](../../../reports/stage12br/v1/index.md). Validation parquet includes raw text and output-only extracted outcomes, never correctness. Pathology parquet preserves per-family labels/reasons/quotes. Annotation details: `audit/manual_validation_decisions.json`.

Allocated GPU use: 0.602778 GPU-hours including startup/teardown, against a target below 0.6 and a hard maximum of 1.0. Jobs: 127673/node03/COMPLETED, 127674/node02/COMPLETED. All stage GPU allocations released. No installs/downloads. The original 4B BF16/vLLM recipe was reused.

Full 61-family Stage12B scientific profiling was not launched. Section 21 requires separate authorization; any future authorized profiling must retain the frozen validity rule, original 61 families/157 facts, P1–P6/B1–B4 definitions, and planned sensitivity reports excluding the original 12 and all 24 technical cases. No correctness, bottleneck proportions, CoT, Thinking, or follow-on experiment here. Repetition causes remain unresolved.

VALIDITY_REPAIRED — Stage12B scientific profiling may resume
