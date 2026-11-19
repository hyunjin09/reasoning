# Stage14D-0 supplement: native answer × observable visual evidence

Completed from sealed annotations only. **No inference, GPU work, reannotation, source repair or historical score change.** I = Qwen3-VL-4B-Instruct; T = Qwen3-VL-4B-Thinking. The existing audit is preserved.

## Definitions and denominator

The primary status uses each required **source-valid subfact's last recorded claim state across the whole native output**:

1. **All correct:** every required source-valid subfact is explicitly STATED_CORRECT.
2. **Explicit error:** at least one required source-valid subfact is STATED_INCORRECT or MISBOUND; this takes precedence over incomplete coverage elsewhere.
3. **Incomplete/ambiguous:** no qualifying explicit error, but not all required facts are explicitly correct. Unmentioned, vague, unstable and other unresolved statements are retained here. This is **not an acquisition-failure label**.

Earlier errors that were corrected do not force category 2 in the primary last-state table. An ever-error sensitivity is supplied separately. Four source-invalid subfacts in 276, 604 and 2869 remain withheld; their families remain, using their nonempty source-valid references. All 300 families have both native outputs. Each model has its own CORRECT/WRONG denominator; UNSCORABLE is excluded from primary rates and association estimates, never converted to WRONG.

Cells below are **exact n (unweighted row %)**, conditional on the native answer status. Percentages can differ slightly from 100 after rounding. The panels remain separate: R is source-selected from the 1,000-family E*-eligible frame; F is outcome-enriched; combined tables are descriptive only.

## Main observations

In the source-selected R panel, explicit last-state evidence errors occur in 52/73 wrong Instruct answers and 50/69 wrong Thinking answers, but also in 13/63 and 15/80 correct answers. Observable source errors are strongly associated with wrong answers without being necessary or sufficient for them.

Conversely, all required source-valid facts are explicitly correct in 9/73 wrong Instruct answers and 5/69 wrong Thinking answers in R; the descriptive combined counts are 15/128 and 20/156. This is not automatically a diagnosis of purely downstream error because the required reference is minimal and other visual claims can be wrong.

R weighted accuracy is 80.8% versus 19.9% for Instruct and 90.8% versus 23.0% for Thinking, comparing all-correct with explicit-error evidence. The corresponding accuracy differences are +60.9 pp [45.7, 75.4] and +67.9 pp [55.5, 80.1]. These are within-model associations; they do not isolate a causal effect of evidence or a Thinking advantage.


## R: source-selected representative panel

| Model | Native answer | n | 1: All correct | 2: Explicit error | 3: Incomplete/ambiguous |
|---|---|---:|---:|---:|---:|
| Instruct | CORRECT | 63 | 38 (60.3%) | 13 (20.6%) | 12 (19.0%) |
| Instruct | WRONG | 73 | 9 (12.3%) | 52 (71.2%) | 12 (16.4%) |
| Thinking | CORRECT | 80 | 50 (62.5%) | 15 (18.8%) | 15 (18.8%) |
| Thinking | WRONG | 69 | 5 (7.2%) | 50 (72.5%) | 14 (20.3%) |

R **source-stratified weighted row percentages [95% family-bootstrap intervals]** follow. Counts remain the observed sample counts above; weighted values are not integer counts.

| Model | Native answer | n | 1: All correct | 2: Explicit error | 3: Incomplete/ambiguous |
|---|---|---:|---:|---:|---:|
| Instruct | CORRECT | 63 | 60.4% [48.3, 72.4] | 20.5% [10.9, 30.9] | 19.1% [9.6, 29.4] |
| Instruct | WRONG | 73 | 12.4% [5.4, 20.6] | 71.2% [60.7, 81.2] | 16.5% [8.4, 25.4] |
| Thinking | CORRECT | 80 | 62.6% [52.1, 73.1] | 18.6% [10.5, 27.0] | 18.8% [10.7, 27.4] |
| Thinking | WRONG | 69 | 7.3% [1.6, 13.8] | 72.4% [61.7, 82.5] | 20.3% [11.3, 30.3] |

## F: outcome-enriched discovery panel

| Model | Native answer | n | 1: All correct | 2: Explicit error | 3: Incomplete/ambiguous |
|---|---|---:|---:|---:|---:|
| Instruct | CORRECT | 56 | 35 (62.5%) | 12 (21.4%) | 9 (16.1%) |
| Instruct | WRONG | 55 | 6 (10.9%) | 38 (69.1%) | 11 (20.0%) |
| Thinking | CORRECT | 63 | 42 (66.7%) | 12 (19.0%) | 9 (14.3%) |
| Thinking | WRONG | 87 | 15 (17.2%) | 50 (57.5%) | 22 (25.3%) |

## Combined: descriptive R + F, not prevalence

| Model | Native answer | n | 1: All correct | 2: Explicit error | 3: Incomplete/ambiguous |
|---|---|---:|---:|---:|---:|
| Instruct | CORRECT | 119 | 73 (61.3%) | 25 (21.0%) | 21 (17.6%) |
| Instruct | WRONG | 128 | 15 (11.7%) | 90 (70.3%) | 23 (18.0%) |
| Thinking | CORRECT | 143 | 92 (64.3%) | 27 (18.9%) | 24 (16.8%) |
| Thinking | WRONG | 156 | 20 (12.8%) | 100 (64.1%) | 36 (23.1%) |

## Unscorable finals — separate from primary rates

### R

| Model | Native answer | n | 1: All correct | 2: Explicit error | 3: Incomplete/ambiguous |
|---|---|---:|---:|---:|---:|
| Instruct | UNSCORABLE | 14 | 1 (7.1%) | 10 (71.4%) | 3 (21.4%) |
| Thinking | UNSCORABLE | 1 | 0 (0.0%) | 1 (100.0%) | 0 (0.0%) |

### F

| Model | Native answer | n | 1: All correct | 2: Explicit error | 3: Incomplete/ambiguous |
|---|---|---:|---:|---:|---:|
| Instruct | UNSCORABLE | 39 | 6 (15.4%) | 23 (59.0%) | 10 (25.6%) |
| Thinking | UNSCORABLE | 0 | 0 (NA) | 0 (NA) | 0 (NA) |

### COMBINED_DESCRIPTIVE

| Model | Native answer | n | 1: All correct | 2: Explicit error | 3: Incomplete/ambiguous |
|---|---|---:|---:|---:|---:|
| Instruct | UNSCORABLE | 53 | 7 (13.2%) | 33 (62.3%) | 13 (24.5%) |
| Thinking | UNSCORABLE | 1 | 0 (0.0%) | 1 (100.0%) | 0 (0.0%) |

## Association: answer correctness conditional on evidence status

These tables reverse the conditioning: **P(native correct | evidence status, scoreable final)**. They describe an association, not a causal effect of correcting evidence. Status codes are 1/2/3 as defined above.

### R

| Model | Evidence status | Correct / scored | Raw accuracy | Weighted accuracy [95% CI] |
|---|---|---:|---:|---:|
| Instruct | 1 | 38/47 | 80.9% | 80.8% [69.4, 91.5] |
| Instruct | 2 | 13/65 | 20.0% | 19.9% [10.9, 30.3] |
| Instruct | 3 | 12/24 | 50.0% | 49.9% [29.1, 70.3] |
| Thinking | 1 | 50/55 | 90.9% | 90.8% [82.7, 98.0] |
| Thinking | 2 | 15/65 | 23.1% | 23.0% [13.5, 32.7] |
| Thinking | 3 | 15/29 | 51.7% | 51.8% [33.4, 69.9] |

### F

| Model | Evidence status | Correct / scored | Raw accuracy | Descriptive accuracy [95% CI] |
|---|---|---:|---:|---:|
| Instruct | 1 | 35/41 | 85.4% | 85.4% [73.3, 95.5] |
| Instruct | 2 | 12/50 | 24.0% | 24.0% [12.3, 36.5] |
| Instruct | 3 | 9/20 | 45.0% | 45.0% [23.5, 66.7] |
| Thinking | 1 | 42/57 | 73.7% | 73.7% [61.9, 84.6] |
| Thinking | 2 | 12/62 | 19.4% | 19.4% [10.3, 30.0] |
| Thinking | 3 | 9/31 | 29.0% | 29.0% [13.5, 46.5] |

### COMBINED_DESCRIPTIVE

| Model | Evidence status | Correct / scored | Raw accuracy | Descriptive accuracy [95% CI] |
|---|---|---:|---:|---:|
| Instruct | 1 | 73/88 | 83.0% | 83.0% [74.7, 90.5] |
| Instruct | 2 | 25/115 | 21.7% | 21.7% [14.4, 29.5] |
| Instruct | 3 | 21/44 | 47.7% | 47.7% [32.7, 62.7] |
| Thinking | 1 | 92/112 | 82.1% | 82.1% [74.6, 89.1] |
| Thinking | 2 | 27/127 | 21.3% | 21.3% [14.2, 28.6] |
| Thinking | 3 | 24/60 | 40.0% | 40.0% [27.9, 52.6] |

Accuracy differences compare evidence categories within each model. All-correct minus explicit-error is positive when answers are more often correct in category 1. Intervals come from the same family resamples.

| Panel | Model | All-correct − explicit-error accuracy | Incomplete − explicit-error accuracy |
|---|---|---:|---:|
| R | Instruct | +60.9 pp [+45.7, +75.4] | +30.0 pp [+6.6, +52.6] |
| R | Thinking | +67.9 pp [+55.5, +80.1] | +28.8 pp [+7.5, +49.6] |
| F | Instruct | +61.4 pp [+44.3, +77.0] | +21.0 pp [-4.0, +47.7] |
| F | Thinking | +54.3 pp [+38.8, +68.8] | +9.7 pp [-8.2, +29.2] |
| COMBINED_DESCRIPTIVE | Instruct | +61.2 pp [+50.1, +71.9] | +26.0 pp [+9.1, +42.8] |
| COMBINED_DESCRIPTIVE | Thinking | +60.9 pp [+50.4, +70.6] | +18.7 pp [+4.7, +33.0] |

## Pre-answer sensitivity and its identification limit

The completed annotations do **not** provide an exhaustive time-indexed state for every fact. Reusing the old `has_pre_answer_anchor` together with a last-state label could leak final exposition: that flag only checks an excerpt's start. A last pre-answer state therefore cannot be recovered reliably without prohibited reannotation.

The permitted sensitivity uses the **recorded first-claim state** only when an existing source-linked quotation starts exactly at `t_claim` and its **entire span ends before the answer boundary**. Thinking's cutoff is the start of `</think>`; Instruct's is its manually recorded answer/exposition-region start. These boundaries have different semantics. No new boundary or semantic label is inferred. Other subfacts are temporally unresolved; category 3 here includes that uncertainty. A later pre-answer correction or corruption is not reconstructed.

This is a **pre-answer anchored first-claim sensitivity**, not a last-pre-answer-state analysis. All scoreable outputs have boundaries, so its primary answer denominators match the main tables. Boundary-unavailable unscorable traces are excluded only from this sensitivity and listed in `sensitivity_coverage.csv`.


### R: pre-answer anchored first claims

| Model | Native answer | n | 1: All correct | 2: Explicit error | 3: Incomplete/ambiguous |
|---|---|---:|---:|---:|---:|
| Instruct | CORRECT | 63 | 32 (50.8%) | 18 (28.6%) | 13 (20.6%) |
| Instruct | WRONG | 73 | 7 (9.6%) | 50 (68.5%) | 16 (21.9%) |
| Thinking | CORRECT | 80 | 38 (47.5%) | 16 (20.0%) | 26 (32.5%) |
| Thinking | WRONG | 69 | 4 (5.8%) | 29 (42.0%) | 36 (52.2%) |

### F: pre-answer anchored first claims

| Model | Native answer | n | 1: All correct | 2: Explicit error | 3: Incomplete/ambiguous |
|---|---|---:|---:|---:|---:|
| Instruct | CORRECT | 56 | 32 (57.1%) | 14 (25.0%) | 10 (17.9%) |
| Instruct | WRONG | 55 | 5 (9.1%) | 37 (67.3%) | 13 (23.6%) |
| Thinking | CORRECT | 63 | 34 (54.0%) | 4 (6.3%) | 25 (39.7%) |
| Thinking | WRONG | 87 | 12 (13.8%) | 22 (25.3%) | 53 (60.9%) |

### COMBINED_DESCRIPTIVE: pre-answer anchored first claims

| Model | Native answer | n | 1: All correct | 2: Explicit error | 3: Incomplete/ambiguous |
|---|---|---:|---:|---:|---:|
| Instruct | CORRECT | 119 | 64 (53.8%) | 32 (26.9%) | 23 (19.3%) |
| Instruct | WRONG | 128 | 12 (9.4%) | 87 (68.0%) | 29 (22.7%) |
| Thinking | CORRECT | 143 | 72 (50.3%) | 20 (14.0%) | 51 (35.7%) |
| Thinking | WRONG | 156 | 16 (10.3%) | 51 (32.7%) | 89 (57.1%) |

### R: weighted pre-answer row percentages [95% CI]

| Model | Native answer | n | 1: All correct | 2: Explicit error | 3: Incomplete/ambiguous |
|---|---|---:|---:|---:|---:|
| Instruct | CORRECT | 63 | 50.9% [38.7, 62.9] | 28.5% [17.6, 40.0] | 20.6% [11.2, 31.2] |
| Instruct | WRONG | 73 | 9.6% [3.6, 16.9] | 68.5% [57.9, 78.9] | 21.9% [13.0, 31.6] |
| Thinking | CORRECT | 80 | 47.6% [37.0, 58.5] | 19.9% [11.4, 29.0] | 32.5% [23.0, 42.6] |
| Thinking | WRONG | 69 | 5.8% [1.4, 11.5] | 42.0% [30.6, 53.9] | 52.2% [40.9, 63.5] |

### Pre-answer association contrasts

| Panel | Model | All-correct − explicit-error accuracy | Incomplete − explicit-error accuracy |
|---|---|---:|---:|
| R | Instruct | +55.7 pp [+39.5, +71.0] | +18.4 pp [-2.8, +39.3] |
| R | Thinking | +55.0 pp [+38.0, +71.5] | +6.5 pp [-11.9, +24.4] |
| F | Instruct | +59.0 pp [+41.2, +75.1] | +16.0 pp [-7.6, +40.3] |
| F | Thinking | +58.5 pp [+38.6, +76.4] | +16.7 pp [-1.2, +33.5] |
| COMBINED_DESCRIPTIVE | Instruct | +57.3 pp [+45.6, +68.7] | +17.3 pp [+1.0, +33.0] |
| COMBINED_DESCRIPTIVE | Thinking | +53.6 pp [+39.6, +66.5] | +8.3 pp [-5.4, +21.4] |

A matched **whole-output anchored first-state** comparison (identical span rule, no answer cutoff) and an **ever-error** sensitivity are in the CSVs. The former separates the boundary restriction from first-versus-last changes; it should be read alongside this sensitivity.

### Separating first-state and boundary restrictions

Exact family counts with category 2 evidence below use the same answer denominators. A decline is not a new semantic judgment or proof that an error first occurred in final exposition.

| Panel | Model | Answer | Denominator | Whole-output last state | Whole-output anchored first state | Pre-answer anchored first state |
|---|---|---|---:|---:|---:|---:|
| R | Instruct | CORRECT | 63 | 13 | 18 | 18 |
| R | Instruct | WRONG | 73 | 52 | 50 | 50 |
| R | Thinking | CORRECT | 80 | 15 | 21 | 16 |
| R | Thinking | WRONG | 69 | 50 | 42 | 29 |
| F | Instruct | CORRECT | 56 | 12 | 14 | 14 |
| F | Instruct | WRONG | 55 | 38 | 37 | 37 |
| F | Thinking | CORRECT | 63 | 12 | 5 | 4 |
| F | Thinking | WRONG | 87 | 50 | 32 | 22 |
| COMBINED_DESCRIPTIVE | Instruct | CORRECT | 119 | 25 | 32 | 32 |
| COMBINED_DESCRIPTIVE | Instruct | WRONG | 128 | 90 | 87 | 87 |
| COMBINED_DESCRIPTIVE | Thinking | CORRECT | 143 | 27 | 26 | 20 |
| COMBINED_DESCRIPTIVE | Thinking | WRONG | 156 | 100 | 74 | 51 |

For example, among R wrong Thinking answers, explicit-error counts change from 50/69 (last state) to 42/69 (anchored first state) to 29/69 (pre-answer anchored first state). Thus first-versus-last/anchor eligibility and the answer boundary both matter. The remaining cases are not certified free of pre-answer errors. Absence of an admissible quote is temporal uncertainty, not absent acquisition.

## Estimation, uncertainty and preservation

R estimates use sealed inverse-inclusion weights N_h/n_h in four source strata. We resample all selected family IDs within their original source strata, then recompute the conditional ratio; we do not resample subfacts or treat them as independent observations. There are 4,000 draws with fixed seed 20261012. Model and estimand resamples share family IDs. Intervals are 95% percentile intervals, without finite-population or multiplicity correction. Undefined denominator draws are counted in the CSVs. F and combined intervals use unweighted family resampling and remain cohort-descriptive.

The frozen family IDs are retained. The previously flagged geometry-equivalent 751/1744 pair crosses two source strata; original-ID intervals do not resolve that source dependence. R represents the eligible source frame only; pooled R+F is not a probability sample. First-claim restrictions can disproportionately move longer or weakly anchored traces into category 3.

All semantic judgments inherit the original single-AI audit. Bootstrap intervals describe sampling variation, not annotation reliability. Correct stated minimal E* does not establish that all other visual claims are correct, that facts were visually acquired rather than inferred, or that a wrong answer must be a purely downstream failure. Checkpoints, output contracts, caps and trace lengths differ across models.

Files: `family_evidence_status.csv` (600 family/model rows), `answer_by_evidence_crosstab.csv` (exact counts, raw percentages, weighted/descriptive estimates and intervals), `answer_accuracy_by_evidence.csv`, `association_risk_differences.csv`, `pre_answer_support.csv`, `sensitivity_coverage.csv`, `spec.md`, `analyze.py`, and `validation_and_provenance.json`.

**STOP — analysis only; no follow-on experiment.**
