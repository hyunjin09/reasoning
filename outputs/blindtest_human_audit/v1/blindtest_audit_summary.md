# BlindTest audit package availability

**Complete coverage: 300/300 frozen families and 300/300 unique original source images.** The package is in a separate output directory. It preserves the distinction between historical Stage14C and fresh Stage14C-V calls and leaves human judgments blank.

| Requested field | Availability | Detail |
|---|---|---|
| Original image / source mapping | Full | Original embedded image bytes exported unchanged; byte hash, decoded pixel hash, dimensions and source row verified for all 300. |
| Question, native prompt, raw/normalized gold | Full | Exact question and both serialized native inputs; gold hidden by default, including gold-bearing filenames/metadata. |
| Exact R0/R1/R2 evidence and full prompts | Full | 1,800 saved input receipts, side-by-side evidence, lexical differences and full chat templates. |
| Historical/native/R outputs and statuses | Full | 600 native + 600 historical E* + 1,800 fresh R records; all 3,000 existing final statuses preserved. |
| Raw generation and reasoning | Full where generated | Exact raw text everywhere; all 1,500 main Thinking calls have delimited traces. Instruct prose remains in complete raw output, without an invented reasoning boundary. |
| Raw final quote, parser vs reviewed answer | Partial by design of saved records | Literal original parser spans exist for 2,977/3,000 main calls. 201 have a separate existing response review. Missing spans/reviews are explicit; full raw text is always accessible. |
| Native visual statements | Partial | Exact lexical excerpt navigation finds hits in 326/600 native outputs. Hits are unverified and can include hypotheses/retractions; no exhaustive native truth-label inventory exists. |
| Native incorrect visual evidence | Unknown unless human-verified | No new claim labels or wrong premises inferred from final answers. Marked NOT OBSERVED / UNKNOWN; raw evidence is available for your audit. |
| D1 separate evidence probes | Partial | 100/300 families, both models: 200 raw calls. Existing pass-2 reviews include 13 contradictory claims across nine families, with exact quotations and reviewer source bindings. They do not establish native use. |
| Source geometry / annotation | Partial | All 300 have source ledger, E* atoms, QC history, metadata and saved image-derived pixel y samples. |
| Independent checker from original generator vertices | Absent | Per-instance generator vertices were not saved. A separately labelled conditional arithmetic recheck uses existing approximate pixel samples; it does not verify image truth or replace gold. |
| Queues, review form and exports | Full | Requested filters with counts and fixed hash order; blank nine-field human forms, local persistence, CSV and JSON export. |
| Original immutable artifact provenance | Full | Per-call paths/hashes, stage, condition, canonical attempt, seed, model revision, score/review artifacts and seal links. External original links require original repository layout. |

The historical Instruct E* regression count remains **104**; fresh R0 remains **103**. No outcomes have been merged, rescored or revised.

The broad E* concern queue contains all 300 cases because original generator coordinates are absent and E* reduces the visual task to textual relations. This is **not a new label asserting incorrect evidence or answer leakage**.

Validation checks the exact 300-case cohort membership, source bytes/pixels/questions/golds, all 3,200 exported call mappings including D1, every one of 32,184 quoted text spans, scoring-seal links, and unchanged hashes of 16,232 consumed artifacts. Browser results are in `validation/browser_validation.json`.

No inference, GPU jobs, dataset repairs, sealed-artifact changes, new source labels, or follow-up experiments.
