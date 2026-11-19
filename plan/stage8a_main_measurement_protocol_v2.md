# Stage8A main measurement protocol v2

Operationalizes the approved plan before any main-cohort feature or causal score is examined. Gate0 freezes layers19–22 and all16 logical heads. Native generation/configuration and the96-family input-only manifest are already frozen. Calibration families are excluded.

## Semantic annotation and blinding

Review the native prompt, source image, complete reasoning prefix through each proposed event and the upcoming local claim. Record exact review coverage; a prefix review is not a claim to have reviewed the whole trajectory. Labels are T, M, nearby, nonvisual, or excluded/ambiguous. No attention, Value, causal score or final accuracy selects an event.

T requires an upcoming visual fact not sufficiently supplied by the prompt or preceding reasoning. M requires a reference to a visual entity whose needed content is already available. Nearby events perform arithmetic/integration on available facts; nonvisual events use text/history without visual demand. Ambiguous binding or freshness is excluded. Correctness is recorded separately from retrieval demand; a wrong read can be T when demand/source/readout remain identifiable. No automatic conversion of accuracy errors into causal failures.

Aim for one earliest eligible T and one earliest clear later M per family, plus12 nearby and12 nonvisual controls per split, for up to120 events each. If a category is unavailable, record the reason; do not manufacture it. Up to two distinct source-demand events per family can contribute within the80–120 target when needed for coverage. Additional events and input-only reserves are used for semantic yield only, before their effects. Retain family clustering and all exclusions. Known-family aliases identified during review must be grouped conservatively before fitting; preserve the original manifest.

The primary query predicts the first token of the reviewed evidence/readout span. For all categories, preserve this literal native boundary; unlike the calibration's differing-suffix localization, do not advance over a common counterfactual numeric prefix. Complete readout token probabilities handle multi-token values. Where one readout is a strict token prefix of another, use a separately reviewed shared terminator or mark the semantic contrast unavailable. The same native boundary defines R, G and S.

## Passive features

Use the exact q1 cached native path. Capture current query and up to32 preceding queries, with recent-window candidates4,16,32. Only past queries enter a temporal median. Per head: total visual mass, scaled QK logsumexp visual-minus-nonvisual and visual-minus-generated-history, top4/max visual mass, normalized entropy, effective visual count, sink mass. If visual mass numerically underflows to0, define entropy/effective count as0 and retain the zero mass explicitly. QK and attention are related coordinates, not independent corroboration.

Discovery aggregation variants: median,10% trimmed mean, max across the64 selected layer/head pairs. Logistic regression with standardized features; compare attention only, QK only, joint, and joint plus concentration/temporal features. Sink-release is secondary. No ROI, Value, future token, total trajectory length or final outcome in primary R. Baselines use only the preceding32 token text, absolute log query position, and visual-word indicators. A small shallow-state baseline is optional and must be described accurately if omitted.

Use grouped/family-separated discovery validation to select variants and operating point; fit normalization inside every training fold. Freeze model/features/normalization/window/threshold before any confirmation feature evaluation. Report AUROC/AUPRC, T-versus-M and all-negative comparisons, recall at fixedFPR, mentionFPR, calibration and family bootstrap intervals. Do not retune after confirmation.

## Native transport and semantic tests

G1 is raw-distribution JS(native, visual-off) at the selected query; visual-off removes all visual alphaV contributions in the frozen late window without renormalizing attention. G2 is mean CE(off)-CE(native) on the full upcoming evidence span. Each teacher-forced readout query uses a native, isolated history. G3 compares sourceROI removal against an image-geometry/ink-matched irrelevantROI; it is unavailable when source controls are missing, never imputed to zero.

Cheap diagnostics are visual/total alphaV norm, visual/total postWO norm, visual-postWO/raw incoming decoder residual norm, and projected-head norm-of-sum/sum-of-norms plus cosine disagreement. Record denominators and numerical conventions. These are G candidates, not primary R features.

Inspect discovery G distribution before selecting its low threshold. Do not tune to later S or force the24-event gate. Freeze threshold and definition before confirmation. Report all highR/lowG events, semantic-label composition, eligible-source coverage, and T-only counts separately. Relative lowG does not imply absent visual grounding.

Value semantics use original/counterfactual/sham image prompt Values with unchanged native query/routing/history. Primary patch uses all visual Value carriers; sourceROI-only is a secondary diagnostic because spatially local pixel edits can alter contextualized Values elsewhere. S is the semantic-minus-sham change in upcoming counterfactual-versus-original mean log-probability preference. Run exact capture/self and fixed-routing checks; report unavailable controls explicitly. A prespecified semantic confirmation subset for T is distinct from highR/lowG selection and never defines event labels by its effect.

No reinjection, rollback, controller, new model, new benchmark or next-stage execution. Apply the original Gates1–3 and preserve negative results. All scientific confirmation comparisons cluster by independent problem family.

## Input-only annotation clarification — 2026-09-16T04:10:29.596318+00:00

The plan's nearby arithmetic control must be temporally close to a selectedT, not merely repeat an old image value. Operationally require the arithmetic query to follow a selectedT in the same native trace by at most256 native tokens. Distant computations on available history remain eligible nonvisual controls. Keep at most one nearby and one nonvisual extra control per base, then the first12 eligible bases per class in the frozen manifest order. Within a class/base choose the earliest reviewed query. Preserve all unselected candidates and superseded reviews. This clarification follows a token-coordinate audit, before any main feature or causal score: the originally tagged arithmetic controls in204,3,287 are1363,328,268tokens after their selectedT, respectively. The originalv1 protocol is preserved.

For wrong source/entity/type bindings, a localizable visible label does not establish the source for the demanded entity. Record source_role as candidate_label_source; its targetedROI contrast is not called demanded-sourceVSD. Such locally incorrect claims retain semantic demand labels but have no eligibleS contrast under the current review. Full visual-offG remains defined.
