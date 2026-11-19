# Stage13A: confirmatory equal-evidence Thinking advantage

Decision: **EQUAL_EVIDENCE_THINKING_ADVANTAGE_CONFIRMED**.

Exact96 source-frozen MathVision families;576 fresh primary calls,three per checkpoint/family. Both variants received identical Q+E* without images or added reasoning instructions.

Primary complete paired families: **84/96**. Thinking minus Instruct: **11.11111111111111 percentage points**,95% family-bootstrap interval **[5.555555555555555, 17.063492063492063]**. Median family difference 0.0pp; positive/zero/negative families 23/56/5.
10,000 family resamples; seeds are repeated measurements within families. Frozen confirmation requires at least80 complete families,+5pp,CI lower>0,and the scoreability safeguard.

Scoreability: Instruct 94.79%,Thinking 99.65%; difference 4.86pp. Full96 missingness bounds: [9.722,15.278]pp. Technical missingness is never scored as incorrect.

Majority transitions: {'BOTH_CORRECT': 61, 'THINKING_ONLY': 10, 'INSTRUCT_ONLY': 1, 'BOTH_WRONG': 18, 'UNRESOLVED': 6}. Net Thinking-only families: 9; descriptive exact discordant-family p=0.01171875.

32k-comparable: n=82,effect=11.382113821138212pp,95% interval=[6.097560975609756, 17.479674796747968]. Optional cap-matched panel executed: False.

Stage12Y descriptive estimate: 13.98pp,95% interval=[6.451612903225806, 22.58064516129032]. The same96 families are reused; these estimates are not independent and were not pooled. Stage13A supersedes Stage12Y for the cohort-level Claim1C estimate.

Interpretation is limited to deployed4B variants under their intended recipes. Checkpoints,sampling settings and output budgets differ. A positive result does not isolate a pure Thinking switch or establish state construction as universal. Negative/partial evidence does not erase selected-case portability; insufficient coverage is a technical limitation.

All Instruct scoring/QC closed before Thinking outputs were reviewed. All ambiguous cases and a frozen20% random sample were second-reviewed by the same agent; this is not independent-rater reliability. Cap-after-unretracted-final remains scoreable; pre-outcome caps remain missing; normal-stop refusal/no-answer is scientific failure.

Resources: 576 completed logical calls;589 submitted attempts including13 interrupted by the Slurm wall-time limit,8.569 allocatedGPUh,target<10/hard14. All allocations released. 15807 historical artifacts and source/input seals unchanged. Four PNG/PDF figure pairs saved.

Exactly one recommendation: Run a cross-scale image-vs-equal-evidence study at 2B/4B/8B to test whether the functional role of Thinking changes with model size.

STOP. Recommendation not launched.
