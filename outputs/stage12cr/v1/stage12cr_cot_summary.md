# Stage12C-R CoT scientific rescue

**COT_RESCUE_SPARSE**. 2026-09-29T16:01:34.837032+00:00

CoT rescued 1 of the 11 frozen B1 families (1 technically missing) and 0 of 11 B4 families. The five-rescue threshold was not reached in either primary stratum. This is a sparse rescue result under the frozen prompt and recipe, not an invalidity finding.

Same frozen61-family MathVision cohort and157 E* facts;12 C responses reused unchanged and49 newly generated. Prior E/N/O labels and original Stage12C artifacts preserved. This is a same-checkpoint prompt intervention; Thinking completion does not gate or enter the scientific analysis.

Pinned Qwen3-VL-4B-Instruct; original image/question plus ` Let's think step by step.`; temperature0.7,top-p0.8,top-k20,repetition1,presence1.5,cap32768. Same BF16/vLLM runtime, preprocessing and per-family seed. No retries.

Technical: 61/61 input-valid, 57/61 scoreable, 3 pre-outcome caps. R1–R4 never automatically exclude; missing outcomes are not wrong answers.

Four responses hit the cap: three lacked an outcome; item1951 retained a unique final commitment despite the truncated final box. Item2013 stopped normally but lacked a unique requested answer. These four missing outcomes and the cap-after-answer case were classified before correctness was opened.

CoT pathology counts: R1=43/61, R2=36/61, R3=42/61, R4=20/61, R5=1/61. Repetition and reopening remain behavior measurements rather than exclusions.

| Endpoint | Estimate | Frozen total | Missing |
|---|---|---:|---:|
| A-P1: B1 CoT rescue | 1/10 (10.0%; Wilson95% 1.8%–40.4%) | 11 | 1 |
| A-P2: B4 CoT rescue | 0/11 (0.0%; Wilson95% 0.0%–25.9%) | 11 | 0 |

A-P3 B1−B4 selectivity: 0.1; bootstrap95% [0.0, 0.3].4000 equal-weight family draws, fixed seed120220260929, stratified B1/B4. Exact observed rescue/frozen-total and missingness bounds are in the inference JSON; missing outcomes are never imputed wrong.

Descriptive only: B2 rescue 1/1 (100.0%; Wilson95% 20.7%–100.0%); B3 rescue 1/3 (33.3%; Wilson95% 6.1%–79.2%). No primary inference is made from these tiny strata.

B1 denotes incomplete demonstrated evidence recovery:7explicit-wrong/4unresolved-only. B2=1/B3=3 are descriptive. Small cells limit precision; this developmental cohort does not estimate benchmark-wide prevalence.

Secondary paired N→C comparison, jointly scoreable families only:

```json
{
  "counts": {
    "RESCUE": 3,
    "REGRESSION": 3,
    "BOTH_CORRECT": 23,
    "BOTH_WRONG": 25,
    "UNSCOREABLE_TECHNICAL": 7
  },
  "jointly_scoreable": 54,
  "native_accuracy": {
    "numerator": 26,
    "denominator": 54,
    "estimate": 0.48148148148148145,
    "wilson95": [
      0.3539397274661188,
      0.6114829980187293
    ]
  },
  "cot_accuracy": {
    "numerator": 26,
    "denominator": 54,
    "estimate": 0.48148148148148145,
    "wilson95": [
      0.3539397274661188,
      0.6114829980187293
    ]
  }
}
```

B1 subtypes (no subgroup significance tests):

```json
{
  "B1_EXPLICIT_WRONG": {
    "numerator": 1,
    "denominator": 6,
    "estimate": 0.16666666666666666,
    "wilson95": [
      0.030053369748306635,
      0.5635028221864702
    ],
    "frozen_total": 7,
    "missing": 1,
    "observed_rescues_over_frozen_total": 0.14285714285714285,
    "missingness_identification_bounds": [
      0.14285714285714285,
      0.2857142857142857
    ],
    "transitions": {
      "BOTH_WRONG": 5,
      "RESCUE": 1,
      "UNSCOREABLE_TECHNICAL": 1
    }
  },
  "B1_UNRESOLVED_ONLY": {
    "numerator": 0,
    "denominator": 4,
    "estimate": 0.0,
    "wilson95": [
      0,
      0.4898908364545973
    ],
    "frozen_total": 4,
    "missing": 0,
    "observed_rescues_over_frozen_total": 0.0,
    "missingness_identification_bounds": [
      0.0,
      0.0
    ],
    "transitions": {
      "BOTH_WRONG": 4
    }
  }
}
```

Visible evidence: all26 complete native-failure traces annotated against frozen E* without correctness or bottleneck labels. Explicit contradictions take precedence over FULL; NOT_EXTERNALIZED does not imply internally absent evidence. Evidence-recovery-consistent rescue is C+ with TRACE_E_FULL; it is not causal proof of hidden retrieval.

The single rescued B1 trace still contains conflicting source bindings; there are zero evidence-recovery-consistent B1 rescues. No B4 family is rescued, so this cohort supplies no successful B4 example with which to establish a convergence-repair bridge.

```json
{
  "rescued": {
    "n": 1,
    "counts": {
      "TRACE_E_WRONG_OR_CONFLICTING": 1
    },
    "full": {
      "numerator": 0,
      "denominator": 1,
      "estimate": 0.0,
      "wilson95": [
        0,
        0.7934506856227626
      ]
    }
  },
  "not_rescued": {
    "n": 9,
    "counts": {
      "TRACE_E_WRONG_OR_CONFLICTING": 9
    },
    "full": {
      "numerator": 0,
      "denominator": 9,
      "estimate": 0.0,
      "wilson95": [
        0,
        0.2991450484195441
      ]
    }
  },
  "unscoreable": {
    "n": 1,
    "counts": {
      "TRACE_E_WRONG_OR_CONFLICTING": 1
    },
    "full": {
      "numerator": 0,
      "denominator": 1,
      "estimate": 0.0,
      "wilson95": [
        0,
        0.7934506856227626
      ]
    }
  }
}
```

B4 pathology transitions retain native and oracle separately plus their union. R4 long advancing computation is descriptive; FigureA5 compares R1–R3.

```json
{
  "N": {
    "RESOLVED": {
      "count": 0,
      "rescued": 0
    },
    "PRESERVED": {
      "count": 9,
      "rescued": 0
    },
    "CHANGED": {
      "count": 0,
      "rescued": 0
    },
    "NO_PRIOR_PATHOLOGY": {
      "count": 0,
      "rescued": 0
    },
    "NEW_PATHOLOGY": {
      "count": 2,
      "rescued": 0
    },
    "UNSCOREABLE_TECHNICAL": {
      "count": 0,
      "rescued": 0
    }
  },
  "O": {
    "RESOLVED": {
      "count": 0,
      "rescued": 0
    },
    "PRESERVED": {
      "count": 9,
      "rescued": 0
    },
    "CHANGED": {
      "count": 0,
      "rescued": 0
    },
    "NO_PRIOR_PATHOLOGY": {
      "count": 0,
      "rescued": 0
    },
    "NEW_PATHOLOGY": {
      "count": 2,
      "rescued": 0
    },
    "UNSCOREABLE_TECHNICAL": {
      "count": 0,
      "rescued": 0
    }
  },
  "NO_union": {
    "RESOLVED": {
      "count": 0,
      "rescued": 0
    },
    "PRESERVED": {
      "count": 10,
      "rescued": 0
    },
    "CHANGED": {
      "count": 0,
      "rescued": 0
    },
    "NO_PRIOR_PATHOLOGY": {
      "count": 0,
      "rescued": 0
    },
    "NEW_PATHOLOGY": {
      "count": 1,
      "rescued": 0
    },
    "UNSCOREABLE_TECHNICAL": {
      "count": 0,
      "rescued": 0
    }
  }
}
```

Review:61 C-only first scores; 47 second reviews covering all ambiguities plus the deterministic20% unambiguous-family audit. Same-agent separate-pass quality control, not independent inter-rater reliability. No Thinking correctness was opened.

Resource accounting: stage12cr_cot_resource_accounting.json (allocated GPU time includes startup; hard5GPUh).

- [A1_failure_map_cot_rescue](figures/A1_failure_map_cot_rescue.png) · [PDF](figures/A1_failure_map_cot_rescue.pdf)
- [A2_primary_cot_rescue](figures/A2_primary_cot_rescue.png) · [PDF](figures/A2_primary_cot_rescue.pdf)
- [A3_native_cot_transitions](figures/A3_native_cot_transitions.png) · [PDF](figures/A3_native_cot_transitions.pdf)
- [A4_B1_visible_evidence](figures/A4_B1_visible_evidence.png) · [PDF](figures/A4_B1_visible_evidence.pdf)
- [A5_B4_pathology_resolution](figures/A5_B4_pathology_resolution.png) · [PDF](figures/A5_B4_pathology_resolution.pdf)

Final allocated compute: 0.880556 GPU-hours, 49 new calls, 12 reused calls. All allocations completed exit0 and were released. No retries or downloads.

[Full unabridged responses](../../../reports/stage12cr/v1/index.md).

**Exactly one scientific recommendation:** Keep Stage12B-S as the main Claim1 and stop the CoT rescue branch.

STOP. Recommendation not executed.
