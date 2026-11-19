# Stage8A technical localization specification

Implementation detail of the approved Stage8A plan, recorded2026-09-16 before
any2B causal score. Calibration alone determines the2B layer window; discovery
and confirmation remain unseen. No4B causal score or head index is used.

Use the twelve frozen calibration bases. Review each source image and the
entire native prefix preceding an annotated event. Prefer the first clean,
source-bound reading of an editable local value that is not already supplied by
the question or prior reasoning. Record wrong/ambiguous bindings separately;
they are not silently reclassified as clean localization controls. Native EOS
accounting retains every base. The annotation record distinguishes reviewed
prefixes from whole-trajectory review. Freeze at most one eligible event per
base before scores; use all eligible bases, with at least four independent
families needed for a functional window claim.

At the exact upcoming value boundary, compare the native value with the edited
value using their context-consistent token continuations. Candidate prefixes
must match the native token history exactly. A changed tokenization is an
explicit unavailable readout, not an approximate prefix. Preserve per-token
log-probabilities and mean evidence-span log-probability contrasts.

Keep any common native numeric prefix in history and anchor the contrast just
before the first differing subtoken (for example,10↔12 keeps the native1 and
contrasts0↔2). The complete source value is still unavailable at that boundary.
Record both the literal start and the shifted causal query. Identical candidates
or a strict-prefix candidate without a reviewed terminator are unavailable.
Every suffix prediction uses an isolated native-history checkpoint; an arm does
not contaminate the teacher-forced history used for later suffix positions.

The primary replay path is the exact native multimodal prefill followed by
one-token cached queries. It must match raw Hugging Face native logits at every
one of128 calibration positions on both GPUs. Each intervention starts from an
independent clone. A broader chunk path is not assumed equivalent in BF16.

Map reviewed edit ROIs to the actual2B processor grid; do not inherit4B token
indices. For each native event, capture source Values from original, matched
semantic-counterfactual and matched-sham image conditions. Reuse reviewed edit
assets with hashes and identical prompts/token layouts. First verify the
original asset equals the native image. Patch only target visual positions,
holding native selected-layer probabilities, other Values and native history
fixed. The self-Value arm must reproduce logits and caches exactly. Technical
synthetic Value offsets are operation checks only, never semantic evidence.

Profile all28 individual language layers and all16 logical heads jointly per
layer. For each layer, report the shift toward the counterfactual value under
semantic versus sham Values. Also report target removal versus a cardinality-
matched irrelevant visual region, with controls chosen from image geometry
before scoring. These are calibration diagnostics only.

Candidate late windows are four consecutive layers starting at14 through24
(zero-based), fixed before scores. Rank them by the family median of summed
single-layer semantic-minus-sham effects. Break ties toward the earlier start.
Confirm the winning four-layer window with one joint fixed-routing contrast on
the same calibration events. All16 heads remain included; no head-specific
selection is claimed. Report the entire profile, including early layers.

A functional late-window claim requires positive family-median joint semantic-
minus-sham effect and positive signed effects on at least two thirds of eligible
families, with the source-specific removal control reported alongside it. If
the calibration is inconclusive, do not label a noise maximum causal or proceed
as if Gate0 passed. Preserve the result and diagnose only if it changes whether
the platform or biological hypothesis failed. This calibration criterion does
not replace the main plan's held-out scientific gates.
