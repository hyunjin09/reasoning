# Stage8B MathVision transfer batch — verified results

The32-example batch and its blind transfer review are complete. **Frozen detector transfer passes the specified audit.** The larger Stage8B census and mechanistic comparisons remain unexecuted.

Slurm115741 used two RTX A6000 GPUs on node03, directly through the project scheduler, with no tmux. The wrapper completed successfully on2026-09-17 at07:36:24KST. All32 native receipts and160 artifact hashes match; the original16-file source freeze is unchanged. The current user Slurm queue is empty, confirming that both GPUs have been released. Slurm has purged the detailed job record; successful wrapper completion and the empty live queue are the available evidence, not an accounting-system terminal-state certificate.

| Native outcome | Examples |
|---|---:|
| Final correct, normal EOS | 7 |
| Final wrong, normal EOS | 3 |
| 40,960-token cap, no final-answer section | 22 |
| Total | 32 |

Accuracy is **7/10 =70% among completed answers**. This is not full-sample accuracy. The22 capped traces all lack `</think>`; they cannot supply usable final-correct/final-wrong labels under the frozen protocol. Their cap rate is68.75%. They are preserved separately from wrong answers and are not unresolved formatting cases that an alternative extractor could adjudicate.

The three completed wrong answers are MathVision1833 (21 versus27),2299 (8 versus4), and2730 (1.6 versus4.0). The seven correct items are102,1451,1529,182,2429,2577 and2663. Ground truths and final-section extraction were checked after all semantic reviews were sealed.

| Frozen transfer requirement | Observed | Result |
|---|---:|---|
| Retrieval on>=70% of clearly visually demanding items | 23/23 =100% | Pass |
| Active prediction within±8 tokens of>=70% of annotated T queries | 34/38 =89.47% | Pass |
| High-R at<=20% of exact hard-negative anchors | 1/60 =1.67% | Pass |
| Minimum24 T,24 negative queries across16 items | 38 T,60 negatives,32 reviewed items | Pass |

Mention-only false alarms are1/32 (3.13%); obvious nonvisual false alarms are0/28. The threshold remains0.5478025980771918, with no detector refit or threshold change.

Manual review covered all32 source images and the first1,536 reasoning tokens per trace:49,152 of988,116 reasoning tokens (4.97%). One annotator; no independent agreement estimate. Events were sealed before opening R or final-answer scores. The38 source-read attempts comprise29 locally correct,1 locally incorrect and8 unresolved local-truth events. The single definite local error is the circle diameter3/8 read as a radius in2261. Later errors noted in native prefixes were not added beyond the fixed first-two selection. These counts are an audit description, not failure prevalence or a causal taxonomy. No causal assay has run.

The main limitation is native outcome yield and compute feasibility. Several reviewed prefixes repeat the setup, speculate or reconsider source interpretations; the cause of the high cap fraction is unknown. Technical observer parity does not identify that cause or establish an accuracy-repair opportunity.

The batch produced994,503 tokens in8h24m wall time. Native generation consumed15.55 GPU-hours; the two-GPU allocation consumed approximately16.80 GPU-hours including technical/setup/straggler overhead. Mean native runtime was29.16minutes per example. At this32-item rate, the remaining3,008-example full census projects to30.46days of ideal two-worker native time, or32.90days retaining this batch's efficiency. This is a small-sample throughput projection, not a reliable whole-stage ETA; same-item seeds, annotation and causal work are additional.

Gate0's250-correct/250-wrong target is not yet met; this is the initial32-item batch, not a completed large census. Gate1 passes within the stated audit scope. Gates2–4 remain unevaluated. The next plan step is the census feasibility/continuation decision under the approved two-GPU constraint. No full-census continuation, paired rollout, causal job or intervention was launched during this result check.

Evidence: [completion and release](../audit/transfer32_completion_verified_v1.json), [pre-score annotation freeze](../audit/transfer32_annotations_sealed_v1.json), [transfer gate](../analysis/transfer_gate_v1.json), [native census](../analysis/census_snapshot_v1.json), [capped-output verification](../audit/capped_no_final_answer_verified_v1.json), [local outcome table](../analysis/transfer32_local_outcome_table_v1.json), [resources](../analysis/transfer32_resources_v1.json).
