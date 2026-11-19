# Stage 3B.7-R summary

Technical status: **PASS**.

Fresh validation retained **13** unique disjoint base problems. Target-specific eligibility: **2 / 2** targets passed.

## Fresh validation

- `target_a`: **PASS**; median target BPR `0.636921`, CI `[0.3122844074942652, 0.9531245827670887]`, bidirectional fraction `0.923`, sham-margin median `0.499194`, irrelevant-margin median `0.635106`.
- `target_b_r`: **PASS**; median target BPR `0.155103`, CI `[0.09375000151339918, 0.49999966772338666]`, bidirectional fraction `0.923`, sham-margin median `0.095288`, irrelevant-margin median `0.125`.

## Primary spatial result

- `target_a`: `ROI-Local`; Phase-B gate `True`; median PRRs `{'all_visual': 1.0, 'target_roi': 0.8860268880043086, 'visual_complement': 0.04719518324024655, 'irrelevant_roi': 0.0013013620285216062, 'target_ring': 0.920284672986575}`.
- `target_b_r`: `ROI-Local`; Phase-B gate `True`; median PRRs `{'all_visual': 1.0, 'target_roi': 0.8478256599122588, 'visual_complement': 0.1147845104748609, 'irrelevant_roi': 0.004728695101552608, 'target_ring': 0.8518622520781758}`.

## Conditional K/V result

- `target_a`: `Value-Dominant`; median KVR `{'K': -0.008879321508972863, 'V': 1.1540490754596153, 'KV': 1.0}`.
- `target_b_r`: `Value-Dominant`; median KVR `{'K': 0.005434065281927495, 'V': 1.0436114778639323, 'KV': 1.0}`.

## Historical failure and interpretation boundaries

- The original Stage 3B.7 `E_d-1/W4/Top_2` target remains a failed result (`0.269893` sham/semantic versus the frozen `<0.25` gate). The newly validated Top-4 result does not retrospectively change that decision or prove why Top-2 failed.
- PRR and KVR are unclipped recovery ratios and are not additive information fractions. Values above one can arise from intervention non-additivity.
- `Value-Dominant` means V-only restoration is robust while K-only restoration is not under the frozen late-layer query-head/ROI intervention. It does not establish a general visual-memory mechanism, a vision-encoder location, or causal importance of raw attention magnitude.
- Post-freeze pooled attention-to-V correlation uses one averaged observation per base (`N=37`, Spearman rho `0.16524419155998102`); target-specific relationships are heterogeneous and remain descriptive.

## Recommendation

**GO — Value-content mechanism** — Both ROI-qualified targets show the frozen Value-dominant K/V pattern.

Raw attention was used only in the post-freeze secondary analysis. Attention magnitude is not causal evidence. No later experiment was started.
