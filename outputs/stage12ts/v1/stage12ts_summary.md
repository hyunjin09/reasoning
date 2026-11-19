# Stage12T-S Thinking scientific rescue and visual evidence recovery

**THINKING_DOWNSTREAM_SIGNAL**. 2026-09-30T06:50:00.295920+00:00

Frozen61-family MathVision developmental cohort,157 E* facts;24 validated Thinking81920 responses reused unchanged and37 new calls. Prior E/N/O/C outputs and labels preserved. This is a different-checkpoint/native-recipe comparison, not a causal Thinking-on/off intervention. Visible trace evidence does not establish hidden-state retrieval.

Qwen3-VL-4B-Thinking1de27d8c51f12e819435303b9e84c4e25ba8401e; original image/question, no suffix; temperature1/top-p.95/top-k20/repetition1/presence0/cap81920. Same BF16/vLLM runtime, preprocessing and family seeds. No retries or decoding search.

Technical input-valid61/61,scoreable59/61,pre-outcome caps2. R1–R4 are behaviors rather than exclusions. Technical missingness is never an incorrect answer.

| Stratum | Thinking rescue | Frozen total | Missing | Missingness bounds |
|---|---|---:|---:|---|
| B1 | 3/10 (30.0%; Wilson95% 10.8%–60.3%) | 11 | 1 | [0.2727272727272727, 0.36363636363636365] |
| B2 | 1/1 (100.0%; Wilson95% 20.7%–100.0%) | 1 | 0 | [1.0, 1.0] |
| B3 | 1/3 (33.3%; Wilson95% 6.1%–79.2%) | 3 | 0 | [0.3333333333333333, 0.3333333333333333] |
| B4 | 5/11 (45.5%; Wilson95% 21.3%–72.0%) | 11 | 0 | [0.45454545454545453, 0.45454545454545453] |

Interpretation: the frozen decision is a downstream signal, not a demonstrated downstream mechanism. Thinking rescues five B4 families that Native Instruct failed even with correct evidence supplied; all five also fail under prompted CoT. B1 has only three rescues, two Thinking-only successes and one Thinking-only FULL-evidence case, below the visual-recovery thresholds of five/three/three. Thus this stage does not establish improved visible evidence recovery as a substantial source of the variant advantage.

The B1 minus B4 estimate is negative, but its bootstrap interval includes zero. The comparison changes checkpoint, decoding recipe and available output budget (CoT 32,768; Thinking 81,920); none of these contributions is isolated. S1 retains three B4 rescues in eight families; S2 retains only two B4 families and rescues neither, so the main signal is not independently validated by a substantial untouched subset.


T-P3 B1−B4 selectivity: -0.15454545454545454;4000-family-bootstrap95%[-0.5454545454545454, 0.2727272727272727],seed120220260929. Equal-weight independent families; B2/B3 and B1 subtypes are descriptive. B1 means incomplete demonstrated recovery of task-critical visual evidence, not uniformly visual misreading.

Central signature: 1 B1 families are CoT-wrong, Thinking-correct and TRACE_E_FULL(T). Total B1 evidence-linked Thinking rescues: 1.

Primary paired C/T transitions:

```json
{
  "B1": {
    "counts": {
      "BOTH_WRONG": 6,
      "FIRST_ONLY": 0,
      "THINKING_ONLY": 2,
      "BOTH_CORRECT": 1,
      "UNSCOREABLE_TECHNICAL": 2
    },
    "jointly_scoreable": 9,
    "frozen_total": 11,
    "first_accuracy": {
      "numerator": 1,
      "denominator": 9,
      "estimate": 0.1111111111111111,
      "wilson95": [
        0.019890887638544907,
        0.434999705576656
      ]
    },
    "thinking_accuracy": {
      "numerator": 3,
      "denominator": 9,
      "estimate": 0.3333333333333333,
      "wilson95": [
        0.1205838183869109,
        0.6457978644196036
      ]
    },
    "first_arm": "c"
  },
  "B4": {
    "counts": {
      "BOTH_WRONG": 6,
      "FIRST_ONLY": 0,
      "THINKING_ONLY": 5,
      "BOTH_CORRECT": 0,
      "UNSCOREABLE_TECHNICAL": 0
    },
    "jointly_scoreable": 11,
    "frozen_total": 11,
    "first_accuracy": {
      "numerator": 0,
      "denominator": 11,
      "estimate": 0.0,
      "wilson95": [
        0,
        0.2588329669680317
      ]
    },
    "thinking_accuracy": {
      "numerator": 5,
      "denominator": 11,
      "estimate": 0.45454545454545453,
      "wilson95": [
        0.21271271622459764,
        0.719908462590678
      ]
    },
    "first_arm": "c"
  }
}
```

B1 visible evidence and outcome:

```json
{
  "evidence_linked_rescues": 1,
  "thinking_only_evidence_recovery_rescues": 1,
  "qualifying_families": [
    "visual_family_f1cfa5ebb149e8099d56"
  ],
  "by_outcome": {
    "rescued": {
      "n": 3,
      "states": {
        "TRACE_E_WRONG_OR_CONFLICTING": 2,
        "TRACE_E_FULL": 1
      },
      "full": {
        "numerator": 1,
        "denominator": 3,
        "estimate": 0.3333333333333333,
        "wilson95": [
          0.06149194472039621,
          0.7923403991979522
        ]
      }
    },
    "not_rescued": {
      "n": 7,
      "states": {
        "TRACE_E_WRONG_OR_CONFLICTING": 7
      },
      "full": {
        "numerator": 0,
        "denominator": 7,
        "estimate": 0.0,
        "wilson95": [
          5.551115123125783e-17,
          0.35433043506668743
        ]
      }
    },
    "unscoreable": {
      "n": 1,
      "states": {
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
}
```

B1 subtypes:

```json
{
  "B1_EXPLICIT_WRONG": {
    "thinking": {
      "numerator": 2,
      "denominator": 6,
      "estimate": 0.3333333333333333,
      "wilson95": [
        0.09677141110578041,
        0.700006684861608
      ],
      "frozen_total": 7,
      "missing": 1,
      "observed_rescues_over_frozen_total": 0.2857142857142857,
      "missingness_identification_bounds": [
        0.2857142857142857,
        0.42857142857142855
      ]
    },
    "cot_thinking": {
      "counts": {
        "BOTH_WRONG": 3,
        "FIRST_ONLY": 0,
        "THINKING_ONLY": 1,
        "BOTH_CORRECT": 1,
        "UNSCOREABLE_TECHNICAL": 2
      },
      "jointly_scoreable": 5,
      "frozen_total": 7,
      "first_accuracy": {
        "numerator": 1,
        "denominator": 5,
        "estimate": 0.2,
        "wilson95": [
          0.03622410863243014,
          0.6244653702374747
        ]
      },
      "thinking_accuracy": {
        "numerator": 2,
        "denominator": 5,
        "estimate": 0.4,
        "wilson95": [
          0.11762077423264783,
          0.769275718723987
        ]
      },
      "first_arm": "c"
    },
    "evidence": {
      "evidence_linked_rescues": 0,
      "thinking_only_evidence_recovery_rescues": 0,
      "qualifying_families": [],
      "by_outcome": {
        "rescued": {
          "n": 2,
          "states": {
            "TRACE_E_WRONG_OR_CONFLICTING": 2
          },
          "full": {
            "numerator": 0,
            "denominator": 2,
            "estimate": 0.0,
            "wilson95": [
              0,
              0.6576197724933469
            ]
          }
        },
        "not_rescued": {
          "n": 4,
          "states": {
            "TRACE_E_WRONG_OR_CONFLICTING": 4
          },
          "full": {
            "numerator": 0,
            "denominator": 4,
            "estimate": 0.0,
            "wilson95": [
              0,
              0.4898908364545973
            ]
          }
        },
        "unscoreable": {
          "n": 1,
          "states": {
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
    }
  },
  "B1_UNRESOLVED_ONLY": {
    "thinking": {
      "numerator": 1,
      "denominator": 4,
      "estimate": 0.25,
      "wilson95": [
        0.04558726080970055,
        0.6993581574175981
      ],
      "frozen_total": 4,
      "missing": 0,
      "observed_rescues_over_frozen_total": 0.25,
      "missingness_identification_bounds": [
        0.25,
        0.25
      ]
    },
    "cot_thinking": {
      "counts": {
        "BOTH_WRONG": 3,
        "FIRST_ONLY": 0,
        "THINKING_ONLY": 1,
        "BOTH_CORRECT": 0,
        "UNSCOREABLE_TECHNICAL": 0
      },
      "jointly_scoreable": 4,
      "frozen_total": 4,
      "first_accuracy": {
        "numerator": 0,
        "denominator": 4,
        "estimate": 0.0,
        "wilson95": [
          0,
          0.4898908364545973
        ]
      },
      "thinking_accuracy": {
        "numerator": 1,
        "denominator": 4,
        "estimate": 0.25,
        "wilson95": [
          0.04558726080970055,
          0.6993581574175981
        ]
      },
      "first_arm": "c"
    },
    "evidence": {
      "evidence_linked_rescues": 1,
      "thinking_only_evidence_recovery_rescues": 1,
      "qualifying_families": [
        "visual_family_f1cfa5ebb149e8099d56"
      ],
      "by_outcome": {
        "rescued": {
          "n": 1,
          "states": {
            "TRACE_E_FULL": 1
          },
          "full": {
            "numerator": 1,
            "denominator": 1,
            "estimate": 1.0,
            "wilson95": [
              0.20654931437723745,
              1
            ]
          }
        },
        "not_rescued": {
          "n": 3,
          "states": {
            "TRACE_E_WRONG_OR_CONFLICTING": 3
          },
          "full": {
            "numerator": 0,
            "denominator": 3,
            "estimate": 0.0,
            "wilson95": [
              5.551115123125783e-17,
              0.5614970317550454
            ]
          }
        },
        "unscoreable": {
          "n": 0,
          "states": {},
          "full": {
            "numerator": 0,
            "denominator": 0,
            "estimate": null,
            "wilson95": null
          }
        }
      }
    }
  }
}
```

B1 evidence-state transitions:

```json
{
  "TRACE_E_WRONG_OR_CONFLICTING \u2192 TRACE_E_WRONG_OR_CONFLICTING": 10,
  "TRACE_E_WRONG_OR_CONFLICTING \u2192 TRACE_E_FULL": 1
}
```

Secondary common-denominator accuracy and paired transitions:

```json
{
  "common_joint_n": 53,
  "common_joint_missing": 8,
  "accuracies": {
    "n": {
      "numerator": 26,
      "denominator": 53,
      "estimate": 0.49056603773584906,
      "wilson95": [
        0.3612424984784323,
        0.6211647088532004
      ]
    },
    "c": {
      "numerator": 26,
      "denominator": 53,
      "estimate": 0.49056603773584906,
      "wilson95": [
        0.3612424984784323,
        0.6211647088532004
      ]
    },
    "t": {
      "numerator": 35,
      "denominator": 53,
      "estimate": 0.660377358490566,
      "wilson95": [
        0.5259478663754829,
        0.7731296089867581
      ]
    }
  },
  "native_thinking": {
    "counts": {
      "BOTH_WRONG": 17,
      "FIRST_ONLY": 2,
      "THINKING_ONLY": 11,
      "BOTH_CORRECT": 25,
      "UNSCOREABLE_TECHNICAL": 6
    },
    "jointly_scoreable": 55,
    "frozen_total": 61,
    "first_accuracy": {
      "numerator": 27,
      "denominator": 55,
      "estimate": 0.4909090909090909,
      "wilson95": [
        0.36376777849003283,
        0.619237401530278
      ]
    },
    "thinking_accuracy": {
      "numerator": 36,
      "denominator": 55,
      "estimate": 0.6545454545454545,
      "wilson95": [
        0.5225390350756162,
        0.7663729045791027
      ]
    },
    "first_arm": "n"
  },
  "cot_thinking": {
    "counts": {
      "BOTH_WRONG": 16,
      "FIRST_ONLY": 2,
      "THINKING_ONLY": 13,
      "BOTH_CORRECT": 25,
      "UNSCOREABLE_TECHNICAL": 5
    },
    "jointly_scoreable": 56,
    "frozen_total": 61,
    "first_accuracy": {
      "numerator": 27,
      "denominator": 56,
      "estimate": 0.48214285714285715,
      "wilson95": [
        0.3566821941245828,
        0.6098961607582303
      ]
    },
    "thinking_accuracy": {
      "numerator": 38,
      "denominator": 56,
      "estimate": 0.6785714285714286,
      "wilson95": [
        0.5482263990973855,
        0.7859900520744849
      ]
    },
    "first_arm": "c"
  }
}
```

Pathology counts:

```json
{
  "N": {
    "R1": 38,
    "R2": 32,
    "R3": 33,
    "R4": 16,
    "R5": 1
  },
  "O": {
    "R1": 26,
    "R2": 21,
    "R3": 19,
    "R4": 16,
    "R5": 3
  },
  "C": {
    "R1": 43,
    "R2": 36,
    "R3": 42,
    "R4": 20,
    "R5": 1
  },
  "T": {
    "R1": 55,
    "R2": 43,
    "R3": 45,
    "R4": 31,
    "R5": 0
  }
}
```

B4 pathology transitions:

```json
{
  "N": {
    "RESOLVED": {
      "count": 0,
      "rescued": 0
    },
    "PRESERVED": {
      "count": 9,
      "rescued": 4
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
      "rescued": 1
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
      "rescued": 4
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
      "rescued": 1
    },
    "UNSCOREABLE_TECHNICAL": {
      "count": 0,
      "rescued": 0
    }
  },
  "C": {
    "RESOLVED": {
      "count": 0,
      "rescued": 0
    },
    "PRESERVED": {
      "count": 11,
      "rescued": 5
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
      "count": 0,
      "rescued": 0
    },
    "UNSCOREABLE_TECHNICAL": {
      "count": 0,
      "rescued": 0
    }
  }
}
```

Sensitivity analyses use the same definitions and never replace the main decision. S2 includes documented pre-Stage12T-S technical exposures across the lineage, including Stage11C/R and official protocol validation. Scientific generations alone do not count as technical development.

| Sensitivity | Retained families | B1 T rescue | B4 T rescue | T-only B1 | T-only FULL B1 |
|---|---:|---|---|---:|---:|
| S1 | 49 | 3/9 (33.3%; Wilson95% 12.1%–64.6%) | 3/8 (37.5%; Wilson95% 13.7%–69.4%) | 2 | 1 |
| S2 | 17 | 1/2 (50.0%; Wilson95% 9.5%–90.5%) | 0/2 (0.0%; Wilson95% 0.0%–65.8%) | 1 | 0 |

Review:61 T-only first scores;50 separate-pass second reviews. All technical and26evidence-trace annotations sealed before correctness. Same-agent packet-blinded review, not independent inter-rater reliability; per-case coverage and literal evidence are preserved.

Review coverage limitation: long responses were inspected using deterministic excerpts, answer contexts, complete endings and fact-targeted searches. This was not exhaustive reading of every long trace. Positive pathology/evidence labels have quoted witnesses; negative pathology and not-externalized labels mean not established in the inspected passages. These descriptive annotations are not independent human validation. R1–R4 do not change scoreability.

The original cap-validation prefix divergences remain unresolved; no pure-budget explanation is claimed. Any B4 rescue may involve downstream/checkpoint differences and is not attributed solely to visual recovery. Small stratum counts limit precision; no benchmark-wide prevalence claim.

Final new allocated compute: 1.531944 GPU-hours, 37 new calls, 24 reused calls. All three jobs completed exit0 and released their GPUs. No retries or downloads. Resource details: stage12ts_resource_accounting.json. No automatic follow-on experiment.

- [T1_failure_map_rescue](figures/T1_failure_map_rescue.png) · [PDF](figures/T1_failure_map_rescue.pdf)
- [T2_primary_rescue_by_mode](figures/T2_primary_rescue_by_mode.png) · [PDF](figures/T2_primary_rescue_by_mode.pdf)
- [T3_B1_paired_transitions](figures/T3_B1_paired_transitions.png) · [PDF](figures/T3_B1_paired_transitions.pdf)
- [T4_B1_evidence_transitions](figures/T4_B1_evidence_transitions.png) · [PDF](figures/T4_B1_evidence_transitions.pdf)
- [T5_evidence_linked_examples](figures/T5_evidence_linked_examples.png) · [PDF](figures/T5_evidence_linked_examples.pdf)

[Full Thinking responses](../../../reports/stage12ts/v1/index.md).

**Exactly one recommendation:** Run Thinking Equal-Evidence Oracles on rescued B4 families to localize the gain downstream of visual evidence acquisition.

STOP. Recommendation not executed.
