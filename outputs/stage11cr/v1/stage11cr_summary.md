# Stage11C-R — technical repair reproduced; nonprimary gate STOP

Stage11C-R restored the historical execution recipe but did not establish a completion-valid regime for the unchanged Stage11C assay. The prescribed nonprimary gate failed before any primary or oracle rerun. P1/P2/P3 remain unestimated. This is not a scientific null or evidence for an upstream/downstream mechanism.

## Reconstruction and repair
Two historical execution sources were audited: Stage9A and Stage8B-v2. Both used the same pinned2B checkpoints/native image format and sampled decoding at temperature1.0,top-p.95,top-k20,repetition penalty1.0, with eager language/SDPA vision attention and a common40960 generated-token budget. Stage11C forced greedy decoding, used SDPA language attention and4096/8192 caps. Historical per-call RNG/rope reset and wrapper differences were recorded; unrecorded TF32/default-cache fields remain UNKNOWN.

All12 fixed known-good cases (six Thinking/six Direct, no primary overlap) reproduced their full historical token sequences exactly. All reached EOS and a committed final without cap hits. Prompt tokens, image tensors and chat templates match exactly. No historical logits were available. Reproduction does not certify answer correctness.

The fixed two-case SDPA diagnostic isolated sampling: both greedy calls repeated and capped at8192; restoring historical sampling reached EOS and terminal answers in both. This supports a decoding contribution on those cases, not a universal root-cause claim. SDPA sampled traces differ from the historical eager traces; the exact historical protocol wins the predeclared selection priority. No accuracy or T-D gap selected the repair.

The initial local specification unnecessarily proposed4096/8192 cap selection. Before any nonprimary/primary output, a versioned correction applied approved plan section12: use the recovered common40960 historical budget. Initial spec/config and hashes remain preserved, with the correction in stage11cr_cap_protocol_amendment_v1.md. There was no longer-cap search or mode-specific cap.

## Fixed nonprimary validation
The original12 Stage11C technical cases and original item seeds were rerun in both modes under the single repaired historical protocol. None came from the80 primary or opened40 reserve. No correctness scoring occurred.

| Arm | Calls | Cap hits | Committed final | Repetition pathology |
|---|---:|---:|---:|---:|
| Thinking |12|1|11|0|
| Direct |12|4|8|4|

Total cap rate 20.8%. Required: total<15%,each arm<20%,each committed-final>=75%,no severe repetition imbalance. The sealed gate is STOP. The twelve-case pool was not replaced, decoding was not tuned further, and no new benchmark/model search was launched.

All 24/24 validation generations also match their historical token sequences exactly, including capped outputs. Reproducing the implementation therefore does not establish completion validity for this frozen assay. Direct cap rate 33.3% and final rate 66.7% are reported independently; capped guesses were inspected for retraction rather than automatically treated as missing finals.

## Scientific design preserved
All120 eligible families,80 primary/40 reserve, E* and sufficiency judgments, neutral24/CoT48/native-state32 subsets, endpoints and statistical rules are unchanged. All160 repaired native conditions are explicitly NOT_RUN (correctness unknown), not incorrect. Oracle, neutral, CoT, reserve and downstream annotation did not run. Original Stage11C generations remain separate invalid-run evidence and are not pooled.

Figures: R1 documents technical completion and repair; R4 explicitly records unestimated localization. R2/R3/R5 are omitted because their required scientific branches did not execute. Raw generations, input hashes, literal completion reviews, Slurm receipts and the full discrepancy matrix are retained.

## Resources and limitations
Total allocated 5.875278 GPU-hours across 14 finite Slurm jobs; all GPUs released, hard 9 GPU-hour limit respected. The original nonprimary <0.5 GPU-hour planning estimate was contradicted by the recovered historical recipe (5.0803 GPU-hour historical forecast); this was disclosed before launch. Actual accounting includes startup, diagnostics and any failed/partial attempts. No downloads or global environment changes. Reviews are by the execution agent, not independent human annotation. Known-good selection used historical completion only. No correctness scoring or accuracy-based protocol selection occurred; historical metadata was available, so this is not a claim of fully blinded review.

## Recommendation
Close the Thinking-performance mechanism branch and finalize the paper around Claims 1 and 2.

STOP. No recommended follow-on action was executed.
