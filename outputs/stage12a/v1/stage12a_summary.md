# Stage12A — technical validation stopped

The fixed12-case technical gate failed after the plan’s one bounded wording repair. The61-family Lost-Keys question remains unresolved; this is not a scientific NO-GO.

## Preserved design and specification versions

All61 original families (24 multiple-choice /37 open-ended),157 E* facts, images/questions, E requests, seeds, model/runtime,128/16/8192 caps and numerical gates remain unchanged. The original plan/spec is archived in `audit/spec_versions/`. `output_contract_v2.json` records the user-approved native-answer clarification before any generation. `output_contract_v3_bounded_repair.json` records the later, explicitly plan-permitted, output-only D/C wording repair. It was based on technical failures, with correctness unopened. These are distinct changes; the later repair is not described as pre-outcome.

Initial exact templates remain in `stage12a_prompt_templates.md`; appended repair wording is in `audit/spec_versions/output_contract_v3_bounded_repair.json`. `audit/technical_v1.json` and `audit/technical_v2.json` preserve every exact executed request.

## Technical results

| Version | Arm | Format valid | Committed finals | Cap hits | Severe repetitive cycles | Gate |
|---|---|---:|---:|---:|---:|---|
| Initial | E | 11/12 | n/a | 0/12 | 0/12 | PASS |
| Initial | D | 1/12 | 3/12 | 9/12 | 0/12 | FAIL |
| Initial | C | 6/12 | 7/12 | 4/12 | 7/12 | FAIL |
| After one repair | E | 11/12 | n/a | 0/12 | 0/12 | PASS |
| After one repair | D | 9/12 | 12/12 | 0/12 | 0/12 | FAIL |
| After one repair | C | 8/12 | 8/12 | 4/12 | 6/12 | FAIL |

E was reused unchanged in the second gate. D requires a single native answer, without reasoning; an MCQ letter plus explanatory text/value is invalid. C commitment is distinguished from strict terminal formatting. A literal template placeholder `X` is not a committed answer. Severe repetition was reviewed semantically from actual output cycles; the exact32-gram metric is supporting evidence and can miss differently tokenized loops. Normal stopping does not erase repetition.

## Scope of the result

60 outputs were preserved:36 initial E/D/C calls and24 repaired D/C calls. All12 technical families were retained; the other49 families were not generated. No task correctness or E* recovery was scored, no E+/D− phenotype was assigned, and P1–P4, GO/NO-GO scientific thresholds and bootstrap intervals are NOT ESTIMATED. Parquets preserve both versions and mark the active prompt version; null outcomes mean unscored, not incorrect. The three required figure panels explicitly mark scientific estimates unavailable.

The observed issue is instruction/completion noncompliance under these fixed conditions. Its cause remains unresolved; neither missing visual encoding nor a Lost-Keys mechanism follows from this result.

## Resources and evidence

Allocated GPU time: **0.500278 GPU-hours** including startup/shutdown. All Stage12A allocations released. Slurm127229 saved all36 valid receipts before timing out during shutdown; no completed response was retried. The repair used a longer finite wall allowance. Exact terminal receipts and commands are in `stage12a_resource_accounting.json`.

Raw responses, token IDs and actual input prompts: `generations/<task_id>/`. Readable side-by-side versions: [technical response index](../../../reports/stage12a/v1/index.md). Output-only manual decisions and integrity evidence: `audit/technical_v1_review.json`, `audit/technical_v2_review.json`, and `audit/technical_v1_integrity.json`. No native Thinking, oracle, new benchmark, full-cohort correctness, further wording search or follow-on launched.

## Exactly one recommendation

Do not expand or interpret the Lost-Keys pilot until a separately approved technical repair establishes compliant Answer-Only and completion-valid reasoning on the frozen validation cases.

**TECHNICAL_STOP — scientific gate not evaluable**
