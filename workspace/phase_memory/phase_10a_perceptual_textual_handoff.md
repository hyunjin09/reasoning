# Phase 10A: causal perceptual-to-textual handoff

## Current Objective
Completed the approved bounded Stage10A plan. STOP; no next experiment authorized.

## Active Constraints
- Native Qwen3-VL-4B-Thinking; original32 images/64 FULL traces unchanged.
-24 independent primary images, balanced12 color/12 shape;8 frozen reserve unused.
- BF16, TF32 off, greedy, native Thinking/DeepStack,512 total tokens including prefix.
- Fresh text-only replay and cached image-off remain distinct interventions.
- User ceiling is now **up to8 GPUs**, through scheduler/Slurm on authorized
  nodes02/03/06/07. This permission persists; no GPUs are currently allocated.
- No cap/anchor rescue, CoT comparison, Stage10B or automatic follow-on.

## Current State
- Complete:32 semantic annotations,24 primary/8 reserve, frozen anchors/protocol.
- Complete:144 Gate-A continuations;96 logical text-edit conditions (72 new,
 24 reused originals);48 post2×2 continuations on12 images.264 new generations.
- Complete: sealed native final review;16 focused CPU tests;8 initial technical
  cases and2 fresh-image-prefix technical cases; independent final audit.
- Complete:11 requested artifacts, including optional-not-run records;4 PNG/PDF
  figures; resource accounting; all26 scheduler jobs terminal (one resolved
  failed preflight,25 successes). All17 GPU jobs terminal, GPUs released.
- Outcome **C**: emitted text causally influences image-free continuations;
  full perceptual-to-textual handoff and phase termination are not established.

## Evidence That Matters
| Observation | Evidence | Implication |
|---|---|---|
| Text-only16/24 pre→20/24 post; +16.67pp [4.17,33.33] | audit/gate_a_inference.json | H2 supported;2 gains resolve missing finals and2 valid wrong answers |
| Image-off20/24 at every anchor; necessity decrease0 [0,0] | same | H1 fails; no full handoff, reserve or bridge |
| Edited-count following13/24 CF versus0/24 original/sham | audit/gate_b_inference.json | Causal text influence;8 CF missing finals remain explicit |
| CF−sham score+1.417 [1.125,1.667]; deletion−sham accuracy−16.67pp | same | H3 and Gate B pass, including correct-fact and attribute checks |
| Post text−image effect−0.333 [−0.833,0.083] | audit/dominance_v2_inference.json | No post text dominance; no measured reversal |
|264 unique outputs, source/receipt hashes and paired inference pass | audit/final_validation.json | Evidence complete and auditable |

Paths above are relative to outputs/stage10a/v1. Primary report:
outputs/stage10a/v1/stage10a_summary.md.

## Failed Attempts and Lessons
- Initial technical job124857 failed on an unrecognized text-only processor field.
  One CPU diagnostic identified all-zero mm_token_type_ids. The repair preserves
  and extends these text-modality zeros, rejects nonzero modality, and passed a
  regression test plus all8 actual-model checks on retry124861. Failed receipt
  and original code remain under audit/. No scientific condition changed.
- Before2×2 outcomes, visual review found the initial "upright square" selector
  inverted the renderer angle convention. v2 changes only image007's source
  object: blue circle→upright blue square, count1→2. Original v1 manifests,
  code, images and successful technical receipts remain immutable. Runtime
  validation was reused with explicit hash linkage; no unnecessary GPU rerun.
- Pre-text already enumerates objects. Image-off retains earlier visual state.
  A null H1 does not diagnose when/where latent transfer occurred.
- Ten primary post anchors contain option binding. Without those, H2 is
  +14.29pp [0,35.71] on14 images. Four emitted facts are source-wrong; the20
  correct-fact stratum still supports text influence. Do not erase these limits.
- The post2×2 edits only the first fact, leaving later native recounts intact.
  Its result does not compare all textual carriers jointly against vision.

## Open Candidates
None selected. Reserve, MathVision bridge and CoT follow-on were not triggered.

## Next-Step Decision
- Authorized action is complete; no further experiment selected.
- Exactly one recommendation: retain causal text-carrier influence as a bounded
  result alongside native visual-use findings; do not promote a perceptual-to-
  textual phase-handoff claim.
- STOP. User chooses any subsequent research action.

## Resource Closure
0.401667 allocated GPU-hours (including failed preflight and startup),0.193
continuation GPU-hours; peak8 concurrent GPUs;8.738GiB peak reserved VRAM.
No package/model/dataset download, tmux allocation or keepalive. All GPUs released.
