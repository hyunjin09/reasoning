# BlindTest human case audit

Open **`blindtest_case_viewer.html`** in a modern browser. Keep `assets/`, `cases/`, and `images/` beside it. No server, network connection, model, or GPU is required. If using the ZIP, extract the entire ZIP first; opening the HTML from inside a ZIP preview will not load its case files.

This package contains all **300 frozen Stage14C / Stage14C-V BlindTest line-intersection families**. They are previously outcome-observed cases, **not a new independent confirmation sample**. The package is a read-only view of research records plus a separate form for your future annotations. It does not certify E*, change scores, or revise either stage's estimates.

## Start with the image

1. The default **image-first view** displays the original source image and exact benchmark question, including its original answer-format instructions. Click the image to enlarge it; choose **100% pixels** for native resolution. Escape closes the enlargement.
2. Solve the problem before selecting **Reveal gold**. Gold resets to hidden on every case. Both the raw gold and its integer-normalized rendering are shown when revealed.
3. Open **evidence and model comparison** when ready to inspect R0/R1/R2, outputs, visual claims and source construction. This may reveal the answer even if gold remains hidden.
4. Record your own judgments. Blank means **unreviewed**, not uncertain, no, or unknown. All subjective fields in the delivered CSV are empty.
5. Use Previous/Next or Left/Right arrow keys when focus is outside a form/control. ID search also finds representative and alias item IDs. Every queue has a fixed hash order.

Original filenames encode gold (`gt_...`). Packaged images use opaque family hashes. The viewer hides original filenames and gold-bearing metadata until Reveal gold. Opening original provenance files, the index CSV, or the manifest can reveal gold. This is a practical image-first interface, not a secure blinding system.

## What the records mean

**Native image — Stage14C:** the original image plus exact author question. The saved input receipt includes the serialized chat template, image reference/hash and preprocessing parameters, user messages, seed, and sampling settings. The viewer preserves the original image bytes; it never draws a substitute image.

**Historical E* — Stage14C:** the original equal-evidence call. This is shown as its own row, not folded into R0. Historical Instruct native-correct → E*-wrong regressions number **104**.

**Fresh R0 — Stage14C-V:** the fresh call using the original E* serialization. The prompt is byte-identical to historical E* for these cases, but the generations and receipts are separate. Fresh Instruct native-correct → R0-wrong regressions number **103**. This package retains that distinction everywhere.

**R1 / R2 — Stage14C-V:** typed structured fields / entity-explicit prose. Text is sliced directly from the saved supplied prompts, not regenerated from a current renderer. The side-by-side display preserves every character. Amber highlighting is a token/whitespace-preserving **lexical** diff from R0; it does not judge semantic equivalence. Full Instruct and Thinking user/chat prompts are separately expandable for every condition.

**Raw generation:** exact `raw_decoded_response` from the immutable `generation.json`. It may contain tentative or retracted reasoning, repetition, and incomplete output. Nothing is suppressed based on correctness. A full trace remains accessible even when the response is unscorable.

**Raw final quote:** the literal text at an existing original parser span, when one exists. It is distinct from the parser's answer value. If the original parser had no saved span, the viewer says so rather than inventing a final quote. Use the full raw output and any existing semantic review in that case.

**Parser answer:** the saved original extraction, before a response review. **Reviewed answer:** a saved separate response review, if present; otherwise “No separate response review.” **Scored answer/status:** the existing final correctness record. The index preserves all three answer fields. No new answer extraction, adjudication or scoring is performed.

**Reasoning trace:** the exact prefix before the final `</think>` delimiter where present. The opening `<think>` may be in the input chat template. If there is no explicit delimiter, the viewer does not manufacture a reasoning/final split. Expand the complete Instruct raw output to see any prose it generated. All 1,500 Thinking native/historical-E/R generations have their delimited traces, as do the 100 Thinking D1 probes.

## Visual claims: four different provenance types

- **Native self-generated text:** exact excerpts from native raw outputs. The excerpt index is a deterministic sentence/line-like lexical search for blue, red, intersection/crossing/touching, vertex, line, or segment words. It is navigation assistance, **not a new set of evidence labels**. An excerpt can be a hypothesis, derivation, retraction, paraphrase of the task, or factual assertion. Character ranges are zero-based, end-exclusive Unicode code-point offsets in the saved `raw_decoded_response`; line numbers are one-based. Full raw text is authoritative.
- **D1 separately elicited evidence:** 100 families × two models. D1 used a different prompt asking for visible facts. Its complete inputs, raw reasoning/response, and existing two-pass source-claim reviews are preserved. Existing `contradictory` classifications, exact quotes and reviewer source bindings are displayed alongside the researcher E* and original image. They are historical same-agent assessments, not new human verification. D1 is not evidence that the native solver used those statements.
- **Researcher-provided oracle E*:** the R descriptions, underlying ledger and source-QC history. These are precisely what you are auditing, not privileged truth.
- **Inferred/reconstructed wrong claims:** none created. A wrong final answer cannot be reverse-engineered into a visual premise.

No exhaustive existing native-claim truth adjudication was recovered. Thus native “wrong visual fact” remains **NOT OBSERVED / UNKNOWN** pending your inspection, even when the lexical index contains suspicious text. This means no adjudicated wrong-fact record is available; it does not assert that the raw generation has no wrong fact. Missing D1 probes for the other 200 families are explicit.

The existing D1 review inventory contains 13 `contradictory`, 11 `accurate_irrelevant`, and 1 `derived` claim across nine families. Only the existing `contradictory` label is presented as a prior wrong-claim assessment. Each has exact quote locations and its saved reviewer binding. Corresponding E* remains researcher-provided evidence subject to this audit.

## Source geometry and the checker limitation

All 300 cases have saved **image-derived pixel y samples** for the red and blue paths at approximately 1%, 50%, and 99% image width. The samples come from `stage14c/audit/line_pixel_order_qc_v2.json`; the sampling code is linked. Coordinates use a top-left image origin.

The viewer independently repeats only the arithmetic on those existing samples: count sign changes of `blue_y - red_y` between adjacent positions. The calculation does not use gold or model answers. It is shown separately from original gold and assumes two straight-segment paths sharing their three horizontal vertex positions, plus correct endpoint/bend sampling.

**This is not an independent geometric ground-truth checker.** The saved values are approximate pixel samples used in the prior annotation pipeline, not the original generator's six vertex coordinates. The official generator export saves unsigned distances, image parameters and gold, without the per-instance vertices; its preserved source code is linked. We do not reconstruct missing vertices, re-read pixels to label cases, or replace gold. Agreement of the conditional calculation with gold does not prove source fidelity, task sufficiency or answer safety.

Some nested historical records retain labels such as `NOT_REVIEWED` or `G0_PROPOSAL_NOT_G1_QC_SEAL`. They are displayed unchanged as provenance from an earlier point in the pipeline. The final eligibility record and G1 seal are separately linked; no historical field is silently rewritten.

## Review queues and deterministic ordering

Order is ascending SHA256 of:

```
blindtest-human-audit-v1-20261010|<family_id>
```

The same order applies within every filter. “Either model” takes the union across models and counts each family once. Queues overlap and are not independent samples. The R transition queues use **fresh Stage14C-V R0**, never historical E*. Wrong requires the saved `WRONG` label; unscorable responses are not relabeled wrong.

| Queue | Either model | Instruct | Thinking |
|---|---:|---:|---:|
| Native correct → R0 wrong → R2 correct | 107 | 56 | 56 |
| Native correct → R0/R1/R2 wrong | 6 | 3 | 3 |
| Native correct → R1 wrong, with R0 or R2 correct | 171 | 142 | 77 |
| Native wrong → R0/R1/R2 correct | 38 | 11 | 27 |
| Unscorable / incomplete / extraction revised | 23 | 6 | 17 |

Additional queues:

- **Instruct / Thinking disagree: 272.** At least one of native/R0/R1/R2 differs in saved status or final scored answer. For comparison only, braces and whitespace are removed from saved answer strings; correctness labels stay unchanged.
- **All conditions and both models agree: 2.** All eight native/R0/R1/R2 cells agree in answer and status. This strict control definition excludes historical E*. There are only two such families, so the “up to 12” hash-selected control queue includes both, without relaxing the rule.
- **E* / geometry / leakage considerations: 300.** Every family lacks the full original generator coordinates and uses a relation-based textual reduction. This is a broad invitation to audit, **not 300 verified source errors or leakage cases**.
- **Historical pixel QC changed prior order: 0** in the saved v2 record's `prior_orders` versus `orders`. This does not certify all earlier annotation history.
- **Existing contradictory D1 claim: 9.** Membership comes only from the existing pass-2 records and is independent of the selected native-model filter.

The output-issue queue includes any unscorable/technical-missing saved status, cap or saved repetition flag, or an existing response-review answer differing from its original parser value. A review difference is not automatically a scoring error. There are two unscorable fresh R2 Instruct outputs; the other included cases can be fully scored after prior adjudication.

Suggested order: inspect the two strict agreement controls, then all-format regressions, R0-to-R2 reversals, R1-specific regressions, all-format rescues, disagreements and output issues. Stay in hash order within each queue. Review E* quality before interpreting the model transitions, and inspect the original image before the supplied evidence. This order is navigation guidance, not case selection for a new analysis.

## Your annotations

The delivered template has 300 identity rows and nine empty judgment fields:

- `image_gold_correct`, `E_star_source_faithful`, `E_star_task_sufficient`, `E_star_answer_leakage`, `R0_R1_R2_semantically_equivalent`: yes / no / uncertain.
- `native_wrong_visual_fact_observed`, `model_evidence_misread`: yes / no / unknown.
- `apparent_reason_for_failure`: visual misread / textual representation issue / downstream reasoning / scoring issue / unclear.
- `reviewer_notes`: free text. Specify the model/condition, exact claim and image location when useful.

The browser saves annotations only in its own local storage. **Export CSV and back up JSON regularly.** Browser file-origin storage behavior varies; if storage is unavailable, a visible warning explains that entries are in memory only. Restoring a JSON backup asks before replacing matching local entries. It never writes research artifacts. The CSV escapes quotes/newlines and prefixes spreadsheet formula-like values with an apostrophe; JSON retains exact note strings. Browser-test annotations were confined to disposable test profiles and are not present in the delivered template or data.

## Files and provenance

- `blindtest_case_viewer.html`, `assets/`, `cases/`, `images/`: fully offline viewer and exact exported content.
- `blindtest_case_manifest.json`: all 300 identities, source mappings/image hashes, exact R evidence/prompts, model revisions, per-call stage/condition/replicate/seed, answer/status fields, source paths and SHA256 hashes.
- `blindtest_case_index.csv`: compact 300-row answer/status/transition index. Contains gold.
- `blindtest_review_template.csv`: all identity rows, no subjective judgments.
- `blindtest_audit_summary.md`: availability and preservation summary.
- `validation/data_validation.json`, `availability_counts.json`, `browser_validation.json`: validation evidence.
- `validation/consumed_artifact_hashes.json`: hashes of every consumed research artifact, checked unchanged after export.
- `build_package.py`: deterministic read-only exporter. It is an audit utility, not an inference or scoring runner.

Every model record links its original input, generation, result receipt, task manifest, parser extraction, response review if any, and final score. Exact scoring/adjudication versions are identified by those artifact paths and hashes plus the linked stage scoring seals, rather than a guessed uniform version number. Canonical completed attempts are used; incomplete attempts and Stage14C-V context-recovery replays are not merged into primary outcomes. Raw token arrays remain in their original generation artifacts; all requested raw text is copied into the portable case files.

Original artifact links resolve in the original repository layout. If this folder is moved to a different computer, those links may be unavailable; paths and hashes remain visible, while the copied images, exact prompts, raw text, scores, reviews and source annotations work offline. Keep the whole extracted package together.

No new model calls, GPU work, source labels, score changes, benchmark repair, or follow-on experiment was performed.
