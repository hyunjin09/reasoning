# Stage12W-S — Distributed reasoning-state construction

Decision: **UNRESOLVED**.

420 unique image-free Instruct condition–seed slots; 416 saved continuations, 411 scoreable, 9 missing (including 4 interrupted without output). Total allocation time is bounded 7.6983–11.3019 GPU-hours because historical cleanup end times were lost; resumption upper bound 1.1736 GPU-hours. All scientific allocations are released. Seven identical family-specific seeds across conditions; four selected independent families.

| Family | Full | Question only | Advantage (net / 7) | A eligible | Derived-state signature | Distributed necessity | Order sensitive |
|---|---:|---:|---:|---|---|---|---|
|2975|7/7|0/7|7/7|True|True|None|False|
|798|7/7|5/7|2/7|False|False|None|False|
|750|6/7|0/7 (2 missing)|[4, 6]/7|True|False|False|False|
|2908|7/7|2/7|5/7|True|True|None|False|

Confirmed family counts: full-state advantage 3/4; derived state 2/4; distributed necessity 0/4; order sensitivity 0/4. None denotes unresolved or untested, not a negative observation.
## Family 2975
FULL: 7/7 · Q: 0/7 · MINUS_B1: 7/7 · MINUS_B2: 7/7 · MINUS_B3: 7/7 · MINUS_B4: 7/7 · MINUS_B5: 7/7 · MINUS_B6: 7/7 · MINUS_B7: 6/7 · ESTAR: 0/7 · ESTAR_D: 7/7 · MINUS_D: 3/7 · ORDER: 7/7 · CTRL_MINUS_D: 7/7
Block deletion effects (FULL minus deletion, numerator /7): MINUS_B1=[0, 0], MINUS_B2=[0, 0], MINUS_B3=[0, 0], MINUS_B4=[0, 0], MINUS_B5=[0, 0], MINUS_B6=[0, 0], MINUS_B7=[1, 1]
Bounded elimination: STOP_LOSS; candidate retained blocks [7]. No global minimality claim.
## Family 798
FULL: 7/7 · Q: 5/7 · ESTAR: 0/7 (2 missing) · ESTAR_D: 3/7 · MINUS_D: 6/7 (1 missing) · ORDER: 6/7 (1 missing)
## Family 750
FULL: 6/7 · Q: 0/7 (2 missing) · MINUS_B1: 7/7 · MINUS_B2: 7/7 · MINUS_B3: 6/7 · MINUS_B4: 6/7 · MINUS_B5: 6/7 · MINUS_B6: 7/7 · MINUS_B7: 5/7 · ESTAR: 4/7 (3 missing) · ESTAR_D: 4/7 · MINUS_D: 6/7 · ORDER: 6/7 · P299: 4/7 · P448: 5/7 · P598: 6/7
Block deletion effects (FULL minus deletion, numerator /7): MINUS_B1=[-1, -1], MINUS_B2=[-1, -1], MINUS_B3=[0, 0], MINUS_B4=[0, 0], MINUS_B5=[0, 0], MINUS_B6=[-1, -1], MINUS_B7=[1, 1]
Bounded elimination: D_NOT_ELIGIBLE; candidate retained blocks not searched. No global minimality claim.
## Family 2908
FULL: 7/7 · Q: 2/7 · MINUS_B1: 7/7 · MINUS_B2: 6/7 · MINUS_B3: 6/7 · MINUS_B4: 7/7 · MINUS_B5: 6/7 · MINUS_B6: 7/7 · MINUS_B7: 5/7 · MINUS_B8: 6/7 · ESTAR: 2/7 · ESTAR_D: 7/7 · MINUS_D: 1/7 · ORDER: 7/7 · CTRL_MINUS_D: 7/7
Block deletion effects (FULL minus deletion, numerator /7): MINUS_B1=[0, 0], MINUS_B2=[1, 1], MINUS_B3=[1, 1], MINUS_B4=[0, 0], MINUS_B5=[1, 1], MINUS_B6=[0, 0], MINUS_B7=[2, 2], MINUS_B8=[1, 1]
Bounded elimination: STOP_LOSS; candidate retained blocks [7]. No global minimality claim.
Family750 frozen Pa299/Pb448/Pc598: 4/7, 5/7, 6/7; interference [-1, -1]/7; repair [1, 1]/7. Joint signal=False. F1=Pa, F2=F4=Pb, F3=Pc:21 unique calls, not four independent confirmations.
Every selected matched deletion, excluded-control reason and length ratio is retained in audit/matched_controls_execution_map.json; composite and natural-control effects are in primary_inference.json. No control means the corresponding length explanation remains unresolved.
## Main comparisons
| Family | Raw evidence E* | E* + derived blocks | Full trace | Full minus derived blocks |
|---|---:|---:|---:|---:|
|2975|0/7|7/7|7/7|3/7|
|798|0/7 (2 missing)|3/7|7/7|6/7 (1 missing)|
|750|4/7 (3 missing)|4/7|6/7|6/7|
|2908|2/7|7/7|7/7|1/7|
Matched deletion length ratios (control/target): 2975 MINUS_D: 0.371, 2908 MINUS_D: 0.567. The frozen adequate range is0.8–1.25; an inadequate or unavailable control leaves length confounding unresolved.
The derived-state count must reach3/4 for the global derived-state decision. Local positive effects below that count are retained and are not recoded as a null. A candidate retained block set comes from one fixed elimination order, not an exhaustive minimality search.
All 420 condition–seed slots passed artifact-chain checks; 101 same-agent second-pass checks agreed. Literal enumeration independently reproduced the reported missingness bounds. Figure whiskers show unresolved missing outcomes, not sampling confidence intervals.
## Interpretation boundaries
These are four production-selected families, not a prevalence estimate. Roles summarize mixed source reasoning, including errors, raw restatements and repeated deductions; they do not certify clean derived propositions. Missing outcomes are bounded rather than counted incorrect. Sparse block effects are preserved even when the cross-family mechanism is unresolved. No hidden-state mechanism is established.
All 6,709 prior artifacts and frozen source hashes verified unchanged. Own-response extraction was followed by a separate same-agent QC pass; no independent-rater claim. Exact inputs, generated token IDs and raw responses are retained for completed outputs. Four interrupted calls have input receipts but no fabricated continuation, EOS, cap or token-count claims. Historical cleanup uncertainty is reported separately from newly verified job receipts.
[Source blocks and all responses](../../../reports/stage12ws/v1/index.md) · [Five figure pairs](../../../reports/stage12ws/v1/figures/)
## Exactly one recommendation
Retain Stage12U-S as the strongest supported production result and stop fine externalized-state localization while the block-level mechanism remains unresolved.
Recommendation status: **NOT_LAUNCHED**. Stage12W-S is complete; STOP.