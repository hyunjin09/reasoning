# Stage14E2: reader-mode diagnostic completed; research paused

Allowing the helper to reason did **not improve the primary acquisition yield** under the frozen diagnostic-target protocol: **4/24 useful reads in both modes**, difference **0.00 percentage points**, 95% family-bootstrap interval **[−16.67, +12.50]**. There were two gains and two losses. These are partial source reads or reinspections; **no condition produced a new or validly reinspected complete task-source representation**.

This completes the experiment requested before the pause. Both Slurm jobs ended normally and released their GPUs. No method revision, downstream solver experiment or fresh-32-family evaluation was launched. The broader methodology goal remains unachieved and is paused at the user's request.

## What was tested

The same 24 previously observed development families were evaluated under five conditions. Original images, frozen reasoning prefixes, family seeds, checkpoint and sampling settings were preserved. All readers had an 8,192-token output cap and unconstrained decoding. The matched compact/reasoning comparison changed only whether the helper's thinking section was explicitly closed before generation.

| Condition | Target | Helper mode | Fresh image | Useful source-correct responses / 24 |
|---|---|---|---|---:|
| O_C | Original model-selected query | Compact | Yes | 3 |
| O_T | Same original query | Reasoning | Yes | 5 |
| T_C | Source-informed diagnostic target | Compact | Yes | 4 |
| T_T | Same diagnostic target | Reasoning | Yes | 4 |
| T_N | Same diagnostic target | Reasoning | No | 1 |

The source-informed targets identify what to inspect; they are **diagnostic oracle targets**, not a deployable target-selection method. Six original queries were NONE, retained as six absent records in each O condition. Thus there are **120 logical conditions and 108 physical scientific reads**, plus eight short technical calls.

“Useful” follows the frozen rubric: a new correct task-critical source fact, or a valid reinspection of an unsettled premise, without an explicit wrong task-critical source statement. Partial coverage is allowed and reported. Correct but already-established facts do not count. A source-correct T_N response is not visual acquisition.

## Paired results and their limits

| Contrast | Difference | 95% family-bootstrap interval | Gains / losses |
|---|---:|---:|---:|
| **T_T − T_C, primary** | **0.00 pp** | **[−16.67, +12.50]** | **2 / 2** |
| O_T − O_C | +8.33 pp | [0.00, +20.83] | 2 / 0 |
| T_T − T_N | +12.50 pp | [0.00, +25.00] | 3 / 0 |

The analysis uses conservative families as the independent unit, equal family weights, inherited source-context strata (6 local-sufficient, 12 global-required, 6 local-plus-global), 4,000 paired bootstrap draws and seed 20261022. These intervals do not quantify annotation uncertainty or repeated-seed variability. This is a small development diagnostic, with one AI reviewer who could see conditions, not independent confirmation.

The primary gains were **487** (hexagon rows) and **1305** (triangular-grid size). Their compact diagnostic-target outputs failed JSON parsing, so the gains include output-format validity. In 487, the no-image reader also supplied the correct row counts; the fresh image was not necessary for that observed source-correct response.

The primary losses were **333**, where the compact reader correctly supplied the number of grey components but the reasoning reader misdescribed their boundaries, and **2471**, where the compact reader confirmed the overlap's rectangular shape but the reasoning reader hit the cap.

The original-target gain is limited to **436** and **1305**, both partial reinspections. Family 436 depends on the solid-pile/hidden-support convention in the source reference. Excluding it in a clearly descriptive sensitivity leaves the primary difference at zero and reduces O_T − O_C to +4.35 pp over 23 families. This sensitivity does not replace the frozen primary analysis.

Complete source records did occur, but only for facts already established in the prefix: T_C had three, T_T two and T_N two. These are controls for source correctness, not successful new acquisition.

## What the case review shows

- Extra helper reasoning can confirm a partial fact, but it did not reliably recover the required source structure. Correct shape names often omitted the endpoint, incidence or connectivity information needed by the task.
- Existing wrong assumptions sometimes persisted despite a fresh image. For example, 2702 retained a checkerboard pattern even though the image has solid black separator rows and columns; 999 invented a 4-by-11 board instead of the connected block layout.
- Mathematical answers were kept separate from visual evidence. The area returned in 292 and transformed fish counts in 641 were not used to infer an unobserved visual misread.
- Unknown, ambiguous and capped responses were preserved. The unbound count in 1207 was not forced into a source-error label, and internal reasoning was never mined to replace an invalid committed final.

These observations do not establish that closing the helper's thinking section caused the earlier SAVA failures. Under this matched prompt, prefix and cap, opening it alone did not improve the primary endpoint. The intervals remain wide, and target selection, source binding, output validity and source reading remain distinct unresolved issues.

## Technical validity and cost

All 108 physical reads and 120 logical assignments are accounted for. Both workers passed their two repeated-native checks (4/4 family-worker gates). Completed receipts verify identical C/T image pixels, prompt-token prefixes, seeds, sampling parameters and caps, with only the declared thinking-boundary difference. The pinned Qwen3-VL-4B-Thinking revision, BF16 execution, vLLM 0.11.0 and disabled prefix cache were verified. Prior sealed artifacts are unchanged.

Reasoning was substantially more expensive: T_C generated 2,340 tokens in total, while T_T generated 114,501. T_C had three malformed finals and no cap hits; T_T had five cap hits. O_T had four cap hits. T_N had eight cap hits and one schema failure. These remain assigned failures in the acquisition denominator.

Slurm jobs **150977** and **150978** completed in **43:59** and **56:08**, respectively, each with one GPU. The diagnostic used **1.6686 charged GPU-hours**. Cumulative expenditure under the current 24-hour allowance is **8.8175/24 GPU-hours**, including the preceding cycle and failed/startup/idle allocation time. Historical SAVA expenditure remains separately recorded as **21.365278 GPU-hours**.

No downstream answer-accuracy claim is possible from this reader-only experiment. The fresh 32-family evaluation remains frozen and unused. The old Stage14D 375-GPU-hour experiment remains HOLD; Stage14C-V remains unfinished.

## Saved evidence

- [Detailed tables](diagnostic_tables_v1.md)
- [All 24 cases and exact committed readouts](casebook_v1.md)
- [All 120 source-review records](../analysis/source_review_complete_v1.json)
- [Paired estimates](../analysis/diagnostic_results_v1.json)
- [Completed execution and provenance audit](../audit/completed_execution_audit_v1.json)
- [Allocation accounting](../audit/resource_ledger.json)
- [User-requested pause boundary](../protocol/pause_after_diagnostic_v1.json)

**Status: PAUSED after the completed diagnostic. No follow-up experiment launched.**
