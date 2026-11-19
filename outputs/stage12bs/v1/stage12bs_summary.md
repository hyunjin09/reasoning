# Stage 12B-S — full scientific failure profiling

**PROFILE_INFORMATIVE**. Completed 2026-09-29T12:03:48.793686+00:00. The frozen full-cohort gate passed; labels are sealed and no follow-on experiment was launched.

61 independent families (24 multiple choice, 37 open-ended), 157 frozen E* facts, and 183 E/N/O calls. Reused 72 calls on 24 families; generated exactly 111 on the remaining 37 without retries. Model, prompts, evidence, BF16/vLLM recipe, seeds and caps were unchanged. All 407 historical artifacts remain hash-preserved.

## Validity and denominators

| Arm | Input-valid | Scoreable | Pre-outcome caps | Cap after outcome |
|---|---:|---:|---:|---:|
| E | 61/61 | 60/61 | 0 | 0 |
| N | 61/61 | 57/61 | 4 | 0 |
| O | 61/61 | 55/61 | 5 | 3 |

Denominators were sealed before gold was opened: N-scoreable=57, complete E/N/O profiles=51, technical unresolved=10. Four native outputs are unscoreable, not wrong. There are 29 native failures overall, of which 26 have complete profiles. O528 ended normally but answered a subsidiary fact rather than the task; E372 retained a placeholder. These remain technical missingness.

## Frozen primary results

All intervals below are family-level Wilson 95% intervals.

| Endpoint | Count, estimate [95% CI] |
|---|---|
| P1 — Native failure prevalence | 29/57 = 50.9% [38.3%, 63.4%] |
| P2 — Oracle-rescuable fraction | 12/26 = 46.2% [28.8%, 64.5%] |
| P3 — B1: evidence recovery / availability | 11/26 = 42.3% [25.5%, 61.1%] |
| P4 — B2: task-context access/use | 1/26 = 3.8% [0.7%, 18.9%] |
| P5 — B3: downstream reasoning | 3/26 = 11.5% [4.0%, 29.0%] |
| P6 — B4: mixed / unresolved | 11/26 = 42.3% [25.5%, 61.1%] |

Native accuracy: 28/57 = 49.1% [36.6%, 61.7%]. Oracle accuracy: 38/55 = 69.1% [56.0%, 79.7%]; these marginal denominators differ, so use the paired contrast for direct comparison. All requested evidence atoms were correct in 20/60 = 33.3% [22.7%, 45.9%].

The profile meets the frozen informative rule because there are 29 scoreable native failures and B1 contains 11 families; both integrity gates pass. B2 has only one family and B3 only three. This does **not** support a substantial Lost-Keys prevalence claim or precise comparisons of the small categories.

**Evidence-scoring qualification:** E− means at least one INCORRECT or UNRESOLVED atom under the frozen all-atoms-correct rule. Of the 11 B1 families, seven have an explicitly incorrect atom and four have unresolved/underspecified evidence without an explicitly incorrect atom. The same 7+4 split occurs in B4. B1 therefore supports incomplete demonstrated evidence recovery; it must not be described as 11 proven visual misreads. The short E contract can understate recoverability when a response omits a required binding.

## Oracle contrasts and reasoning behavior

Oracle rescue given E+: 1/4 = 25.0% [4.6%, 69.9%]; given E−: 11/22 = 50.0% [30.7%, 69.3%].

- rescue_Eplus_minus_Eminus: -0.2500; family-bootstrap 95% interval [-0.6666666666666666, 0.4342677345537757]; 3917/4000 defined draws.
- paired_oracle_minus_native: +0.2157; family-bootstrap 95% interval [0.09803921568627451, 0.35294117647058826]; 4000/4000 defined draws.

Bootstrap seed 120220260929; one equally weighted independent family per row. Rescue-by-E is descriptive, not a causal effect of probing. Paired oracle-minus-native accuracy is evaluated on the 51 complete profiles.

Among the 38 families with N R1/R2/R3 behavior, oracle behavior resolved in 12, shared a pathology type in 21, and was unscoreable in five; none changed to a disjoint pathology type. N scientific failures:26 LOOP_OR_REOPEN,3 WRONG_CONVERGED. O scientific failures:13 LOOP_OR_REOPEN,4 WRONG_CONVERGED. R4 describes advancing computation and is not a pathology exclusion.

E+ with pathological O failure occurs in items 2214, 1942, 3011 and 2013. The first three are B3; 2013 lacks a scoreable native answer and remains TECHNICAL_UNRESOLVED. This secondary set is not silently added to the primary profile. Per-label native-pathology rescue IDs are preserved in primary_inference.json.

## Prespecified sensitivities

| Analysis | N failure | Complete-profile failures | B1 / B2 / B3 / B4 | Oracle rescue | Yield rule |
|---|---|---:|---|---|---|
| S1_exclude_development | 25/45 | 22 | 10 / 1 / 3 / 8 | 11/22 | PROFILE_INFORMATIVE |
| S2_exclude_all_technical | 18/34 | 16 | 9 / 1 / 1 / 5 | 10/16 | PROFILE_SPARSE |

The 37 previously untouched families alone yield only18 scoreable native failures and are PROFILE_SPARSE. This limits standalone fresh-cohort precision; it does not replace the preregistered 61-family main analysis. P1–P6 and intervals for both sensitivities are in the sensitivity artifact.

## Scoring and resource audit

All183 first scores were preserved. Second review covered94 mandatory ambiguity cases plus9 calls from3 randomly selected otherwise-unambiguous families (ceil20% of11). E agreement:81/84 atoms,33/34 whole-E outcomes; N41/41 and O28/28 task labels. The three E disagreements and own-arm adjudications remain logged. Random-audit agreement:E8/8 atoms,N3/3,O3/3. This is single-agent, separate-pass quality control, with other-arm outcomes and first labels absent from packets; it is not independent human reliability or a fresh reviewer unaware of prior context.

New compute: 1.467222 allocated GPU-hours including initialization, below target5/hard7. Slurm127732–127735 all COMPLETED0:0 and released. Prior reused technical-stage costs were0.389167(Stage12B)+0.602778(Stage12B-R)GPUh, reported separately, never double-counted as new compute. No model/dataset download or environment mutation was needed.

No mechanistic hidden-state claim follows from these behavioral categories. B2 does not show that the native trajectory internally held correct evidence; B3 does not prove perfect perception. Oracle evidence and prior sufficiency reviews remain frozen. Negative and unscoreable outcomes are preserved.

## Figures and evidence

- [Assay schematic](figures/figure1_assay.png) · [PDF](figures/figure1_assay.pdf)
- [Native-failure composition](figures/figure2_failure_composition.png) · [PDF](figures/figure2_failure_composition.pdf)
- [Oracle rescue by E](figures/figure3_oracle_rescue.png) · [PDF](figures/figure3_oracle_rescue.pdf)
- [Reasoning behavior by bottleneck](figures/figure4_pathology.png) · [PDF](figures/figure4_pathology.pdf)
- [Deterministic examples](figures/figure5_examples.png) · [PDF](figures/figure5_examples.pdf)

[All 61 families and full E/N/O responses](../../../reports/stage12bs/v1/index.md). Detailed machine-readable tables and all first/second/adjudication records are alongside this report.

## Exactly one recommendation

Freeze the Stage 12B-S bottleneck labels and run prompted CoT plus native Thinking on the same families to test selective rescue by failure type.

**STOP. This recommendation has not been executed.**
