# Stage 12C — technical sanity stop

**TECHNICAL_STOP.** The approved 12-family sanity check is complete. Thinking failed the frozen pre-outcome truncation gate. The remaining 98 calls were not launched, and correctness remains unopened.

## Approved protocol and preservation

The prospective user clarification was recorded before generation. Both conditions retain their pinned checkpoints, original images/questions, image processing, family seeds, and sealed sanity-family IDs:

| Setting | C: prompted CoT | T: native Thinking |
|---|---|---|
| Checkpoint | Qwen3-VL-4B-Instruct | Qwen3-VL-4B-Thinking |
| Revision | `ebb281ec70b05090aa6165b016eac8ec08e71b17` | `1de27d8c51f12e819435303b9e84c4e25ba8401e` |
| Prompt | Original N prompt plus ` Let's think step by step.` | Original N prompt, no added suffix |
| Temperature / top-p / top-k | 0.7 / 0.8 / 20 | 1.0 / 0.95 / 20 |
| Repetition / presence penalty | 1.0 / 1.5 | 1.0 / 0 |
| Maximum output tokens | 32,768 | 40,960 |

Both used BF16 and the existing project-local vLLM environment. The synthetic-counting greedy 512-token recipe was not inherited. Hash checks confirm that all 1,742 preserved historical files, 14 frozen specification files, and 13 generation-source files remain unchanged. The original 61 families, 157 E* facts, and Stage 12B-S labels are preserved.

## Sealed technical result

Each arm requires 12/12 valid inputs, at least 10/12 scoreable answers, and at most 1/12 pre-outcome truncation. There is **no repetition threshold**.

| Arm | Valid inputs | Scoreable | Pre-outcome caps | Normal stops | Gate |
|---|---:|---:|---:|---:|---|
| C: prompted CoT | 12/12 | 11/12 | 0/12 | 12/12 | PASS |
| T: native Thinking | 12/12 | 10/12 | 2/12 | 10/12 | FAIL |

The unscoreable responses are:

- **T, item 2198:** 40,960 tokens. No closing `</think>` or final-answer channel. A provisional option is followed by renewed vertex bindings and an unfinished derivation.
- **T, item 3011:** 40,960 tokens. No closing `</think>` or final-answer channel. Several provisional volumes are reopened, and the trace ends mid-discussion of tetrahedra.
- **C, item 2013:** normal stop at 3,767 tokens. An explicit Across-3 single-digit value and the terminal grid's middle entry do not resolve to one unambiguous task commitment.

Scratchpad candidates are not promoted to final answers because a cap was reached. These responses were never graded as incorrect.

| Descriptive behavior | C | T |
|---|---:|---:|
| Median generated tokens | 4,500.5 | 23,577 |
| Token IQR (Q1–Q3) | 2,224.25–7,823.25 | 10,477.75–29,768 |
| Maximum tokens | 13,716 | 40,960 |
| R1: severe repetition | 9/12 | 12/12 |
| R2: reopening | 7/12 | 11/12 |
| R3: nonconvergent reasoning | 8/12 | 11/12 |
| R4: long advancing computation | 3/12 | 7/12 |
| R5: terminal ambiguity | 1/12 | 0/12 |

R1–R5 were reviewed independently of correctness and do not replace the gate. Long advancing computations can coexist with repetitive passages. Missing final answers from truncation do not automatically receive R5.

## Resources and deliverable status

Exactly 24 new calls were generated, with no retries. Slurm jobs 128009 on node02 and 128010 on node03 both completed with exit code 0:0 and released their GPUs. Total allocated compute, including startup: **0.703611 GPU-hours**. No package, model, or dataset download was needed.

A vLLM teardown warning appeared after all Thinking outputs and the complete worker receipt had been saved. The two capped responses have explicit `length` stop receipts; no generation interruption from the later teardown warning was observed. The cause of the completion behavior remains unknown.

All raw responses, token IDs, input/pixel hashes, runtime receipts, and technical annotations are saved. The 17 required artifact paths exist. The two result tables contain 12 sanity rows each; correctness, rescue-transition, trace, and pathology-transition tables are schema-bearing empty tables marked `NOT_RUN_TECHNICAL_STOP`. P1–P4 are null, not zero. The five scientific figures were not generated because their underlying scientific comparisons were not reached.

This result does not establish either sparse rescue or a negative scientific effect. No correctness, rescue comparison, visible-evidence inference, prompt search, or decoding search was performed.

[Read the complete C/T responses for all 12 sanity families](../../../reports/stage12c/v1/index.md).

## Exactly one recommendation

Suspend Stage 12C scientific rescue profiling and obtain separate approval for technical validation of the 4B Thinking MathVision completion regime before a rerun.

**STOP. The recommendation has not been executed.**
