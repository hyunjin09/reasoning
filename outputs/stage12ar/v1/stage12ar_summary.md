# Stage12A-R contract validation

**D_INVALID**. This is a technical result; the Lost-Keys hypothesis remains untested.

The original 61 families, 157 E* facts, questions/images/source answers, E requests and scientific thresholds remain unchanged. Stage12A artifacts were not modified. No E, task correctness, evidence correctness, rescue or scientific GO/NO-GO endpoint was evaluated.

## 1–3. Development: D, C0 and C1

| Arm | Format | Visible reasoning | Finals | Caps | Severe repetition | Median tokens | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| D | 0/12 | 6/12 | 3/12 | 9/12 | 0/12 | 64.0 | FAIL |
| C0 | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | — | NOT_RUN |
| C1 | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | — | NOT_RUN |

One exact D suffix with a 64-token cap; exactly two predeclared conditional C candidates with a 32,768-token cap. All arms retain the same pinned 2B Instruct checkpoint, BF16/vLLM backend, image preprocessing, sampling (temperature0.7, top-p0.8, top-k20, repetition penalty1.0, presence penalty1.5) and Stage12A per-family seed policy. No additional prompt or budget search was performed.

Format and commitment are distinct. D fails format if it shows intermediate calculations even when a final exists. C requires substantive reasoning and terminal commitment. C0 has no literal final-marker requirement; C1 requires its requested terminal line. Severe repetition is a semantic cycle review supported by exact 32-gram metrics, including outputs that eventually stop normally. No answer correctness enters these labels.

Visible reasoning was counted conservatively: five responses contain only problem restatement or announced analysis, so they were format-invalid but not counted as substantive reasoning. Four show explicit arithmetic; two externalize intermediate constraints or a working variable/diagram representation. The gate fails independently on format, final commitment and cap counts. The input audit found no prompt/image mismatch; the cause of noncompliance remains unknown.

## 4. Selected C contract

D failed development; C0/C1 and untouched validation were not run under section 15.

Priority: fewer severe repetitions, fewer caps, more finals, more strict format-valid responses, shorter median generated length, then C0. Numerical gates are unchanged.

## 5. Untouched validation

The 12 validation families were frozen before any new generation using SHA256(stage12ar-validation-v1|family_id): five MC and seven open-ended, disjoint from the fixed 12 development families. Selection used only identity and answer type, with no difficulty, subject or model behavior.

Validation IDs: 2273, 2448, 1789, 1476, 2143, 372, 1478, 990, 2996, 2908, 1974, 1430.

| Arm | Format | Visible reasoning | Finals | Caps | Severe repetition | Median tokens | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| D | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | — | NOT_RUN |
| C_UNSELECTED | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | — | NOT_RUN |

No prompt modification is allowed after validation. A failure after passing development is reported as CONTRACT_UNSTABLE, with D/C component failures preserved in the decision JSON.

## Resources and provenance

12 actual generation calls; **0.123333 allocated GPU-hours** including startup, failures and teardown. All stage allocations released. Target: <1.5; hard limit: 2.5 GPU-hours. No model/dataset download or environment installation required.

Exact prompts/manifests and prospective hashes are saved alongside this report. `audit/prospective_draft1/` preserves an unused pre-generation draft whose inherited Stage12A configuration metadata was corrected before launch; prompts, cases and requested Stage12A-R gates did not change. Completed raw text, token IDs, actual chat inputs and receipts are under `generations/`. [Read all responses](../../../reports/stage12ar/v1/index.md). Parquet NOT_RUN/null entries are unexecuted conditions, never incorrect answers.

## 6. Decision

No scientific rerun was launched. Technical success would justify a separately authorized 61-family Stage12A scientific rerun, including sensitivity excluding all 24 technical families. Technical failure does not establish absence of Lost Keys, reasoning benefits or visual-access bottlenecks.

D_INVALID — do not rerun Stage12A
