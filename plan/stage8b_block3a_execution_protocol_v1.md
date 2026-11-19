# Block3A execution protocol v1

Frozen before supplemental routing measurement or new sampling, 2026-09-19 UTC.
Authority: user requests the supplied Block3A plan and exactly two GPUs on node02.
Original plan and all Block0/1/2 evidence remain immutable. No Block3B authorized.

## Observable completion and dependencies

1. Verify upstream freezes, preserve all 117 source-localizable Block2 records, freeze native routing subtypes, and complete missing native T/X routing measurements.
2. Freeze 32 distinct item/image families and one exact semantic subgoal per item before sampling. Generate exactly four new seeds per item (1235–1238), up to 128 trajectories. Do not adaptively add seeds/items. Canonical 2B Thinking BF16, T=1, top-p=.95, top-k=20, repetition=1, presence=0, max_new_tokens=40960 and unchanged image preprocessing.
3. Review each new trajectory for the frozen subgoal; seal semantic/local/source labels before opening new source-routing measurements. Then replay eligible events and form same-item pairs.
4. Apply the plan's yield and replication gates. Stop if either fails. Only after both pass freeze causal doses, verified heads, readout contrasts and controls; run weakening, rescue and selectivity assays in that order with the original stopping rules.
5. Produce all eight specified outputs and five figures (explicitly unperformed panels if gated out), exactly one recommendation, accounting and state updates; release GPUs; stop.

## Native routing taxonomy (fixed before new measurements)

Use the unchanged Block2 source mapping: any-pixel ROI grid, shared cells removed from every source. Reuse existing replay measurements; measure only missing resolved T events with nonempty T and X token sets. Retain unavailable records explicitly rather than inventing sources.

Top source is the highest mean source attention share across the frozen 64 observational heads (layers 19–22, all 16 heads); ties within 1e-8, an I winner, unresolved local labels, absent source inventory or absent T/X measurement imply R4. R2 is X top. When T is top, a QK T-minus-X log-mean-exp margin <=1.0 nat defines low margin (R1); larger margins are high. High-margin L- is R3; high-margin L+ is separately labelled SELECTIVE_LPLUS. The threshold is an operational split, not a previously established causal boundary. Never tune it from rollout/causal outcomes. R1/R2 among L+ are control strata, not failure claims.

All original 117 records and labels/geometry are retained verbatim. The original 21 replay results are references, not rewritten. Original optional subtype omissions remain missing in Block2. A new semantic matching category may be assigned in the new anchor review with explicit provenance, before rollout results.

## Fixed cohort selection and compute boundary

Select all 11 distinct families having a resolved source-localizable Block2 L- and nonempty T/X. One anchor per family: earliest reviewed L- (not largest effect). Fill to 32 families with eligible Block2 L+ anchors ranked by increasing native QK T-X margin, then review order. If a family has multiple controls use its lowest-margin anchor. Exclude unresolved/unmeasurable routing from selection. Preserve selection scores and hashes. This is phenotype-enriched sampling, not a population failure-rate estimate.

Four NEW seeds/item, 128 trajectories maximum; original seed1234 is a reference only. Primary replication uses only new-new pairs to avoid conditioning a paired contrast on the discovery outcome/routing score. Original-new contrasts are secondary. No hidden additional rollout budget. Maximum 5,242,880 new tokens. Initial operational estimate 12–24 hours on two A6000s including native capture, up to 48 GPU-hours; refine from measured throughput without changing scientific membership. Batch hard time limit 36 hours (72 GPU-hour upper bound); no automatic rerun of completed trajectories or expansion. Model/layout verification uses only bounded short technical probes.

All CUDA through project scheduler and Slurm, node02 only, two GPUs, <=100G host memory. Start with one process/GPU unless a same-node exact-parity, memory and throughput benchmark certifies two. Do not hold idle GPUs for annotation; allocations terminate after their work. Existing model/dataset only, no downloads.

## Semantic review and pairing

Frozen anchor includes the demanded subgoal, T/X identities, unchanged ROI geometry, source-supported correct interpretation and specific local error distinction. Review uses the image, question and text, with new routing values hidden. Identify the first fresh committed claim addressing that exact subgoal; a tentative alternative, mere repetition, algebraic inference or another visual subgoal is not a matched local read. Missing/unresolved claims are retained as exclusions. Do not select a later error after an earlier correct read.

Use the frozen detector and gap4 episode definition. The claim must match an active episode's original association window [start-16,end+128] inclusive; where multiple episodes qualify, nearest onset then earliest onset. Keep claim alignment and episode identities. Source geometry cannot change across seeds. Seal L+/L-/L?, source identities, exact readout span and exclusion reasons before source measurement. Single-agent annotation is disclosed.

For each item/subgoal, sort new L+ and L- by seed, pair disjointly in order (at most two pairs/item). No repeated seed in primary pairs; item is the independent bootstrap unit. Minimum 20 pairs/16 items; preferred 32/24. If the finite cohort cannot meet the minimum, report yield and stop.

## Statistics and causal gate

Primary metrics are QK T-X and attention-share T-X. Compute L+ minus L- for each pair, median within item, then median over items. Use 10,000 paired item bootstrap draws (seed1234), percentile 95% CIs, exact sign test and Wilcoxon robustness; report paired standardized effect and all unavailable denominators. Gate requires positive median and strictly positive lower CI for at least one primary, plus positive item-median contrasts in at least two frozen semantic categories with >=2 independent items/category. Report both primary tests and Holm-adjusted sign-test p-values; do not substitute a secondary outcome for a failed gate.

If yield/replication fails, no causal intervention; causal artifacts must state not run, no fabricated zero effects. If it passes, freeze a separate causal manifest before assays, including target weakening, equalization and bounded confuser bias; generic sharpening and oracle boost; all required sham, irrelevant-source, timing, high-margin L+ and R2 controls. Assess C1/C2/C3 exactly as the supplied plan; no automatic new doses/windows after nulls. Observational all-head averages do not certify every head as causal.

## Interpretation constraint

The source plan says activation was similar. Block2's actual evidence is an interval including zero, not a test of equivalence. Preserve that limitation. A replication failure does not prove the original descriptive association false; causal claims require replication plus C1, C2 and C3. No benchmark/model/prompt change and no automatic Block3B.
