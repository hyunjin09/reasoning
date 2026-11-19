# Stage8A complete — retrieval observable, selective reinjection not justified

Completed 2026-09-16T13:06:48.451497+00:00. Qwen3-VL-2B-Thinking / MathVerse. Execution is complete; the overall scientific controller criterion is **not met**. The retrieval proxy passes held-out confirmation and eligible weak-transport states retain Value semantics, but the frozen cohort misses Gate2 and cheap transport gating does not generalize.

The two node02 GPUs in tmux10 were cancelled at **2026-09-16 22:00:42 KST**, immediately after final GPU validation. Slurm subsequently confirmed CANCELLED and no queued/running allocation. The original tmux10:0 shell remains. [Verified release](../audit/allocation_released_verified_v2.json). No new allocation, reinjection, controller or next experiment is running.

## Gate decision

| Gate | Result | Evidence |
|---|---|---|
| 0: technical validity | PASS | Exact cached BF16/native, capture, cache, self and fixed-routing checks; 2B functional layers19–22/all16heads |
| 1: retrieval proxy | PASS | Held-out AUROC0.9776; mention FPR0.1277; positive paired advantages over lexical/position |
| 2: weak-transport cohort | FAIL | 19 events /18 families; requires24 events /12 families;9 held-out events persist |
| 3: usable Value semantics | PASS, conditional | 16/16 evaluable events positive /15 families; family median8.3125nats,95%CI[7.1314,10.2163] |

Gate3 covers16/19 frozen states (84.2%). Three locally wrong claims lack an appropriately oriented semantic contrast and are excluded, not scored zero. Gate3 does not override Gate2. Four of the16 evaluable states are semantic mention-only negatives, rather than true retrieval-required events.

## Cohort, annotation and technical validity

Twelve separate calibration traces produced11 normalEOS and one cap; ten source/readout-eligible events localized the model's own functional late window. Joint calibration Value-semantic effects were positive10/10, median10.199nats. Calibration is not held-out replication. Target-relative suppression was positive9/10 but tiny (median2.02e-5nats).

The main cohort has48 discovery and48 disjoint confirmation families,96 fresh native traces,71 normalEOS and25 length-cap completions,1,507,425 generated tokens. All96 bases received source/prefix review:93,749 tokens examined, only4 complete trajectories. The remaining review coverage ends after explicitly recorded prefixes. Missing events are unavailable within that coverage, not certified absent from the full trajectory. One primary-agent annotator; no independent agreement estimate or active labor timer. Final-answer accuracy was not evaluated by this local-state study.

| Split | T | Mention-only | Nearby | Nonvisual | Total |
|---|---:|---:|---:|---:|---:|
| Discovery |41|48|12|12|113|
| Confirmation |44|47|11|12|114|

Labels and source/readout eligibility were sealed independently of main features/effects. Some M controls reuse text-given or previously unbound numerical information and precede the selected T; they are not all later matched mentions. Nearby controls must follow T within256 tokens. Local source/type errors remain wrong semantic candidates; candidate-label ROIs are not certified demanded-source ROIs. All main native/self/off readouts reproduce exactly across measurement and Value runs. [GPU completion proof](../audit/gpu_work_complete_v1.json), [annotation coverage](../audit/all_annotations_complete_v1.json).

Inference used BF16, temperature0.6/top-p0.95/top-k20/seed1234, max40960, EOS stopping, text eager/visionSDPA. Raw logits are converted to FP32 for log-probabilities and higher precision for distribution/statistical calculations; this is not FP32 model inference. Fresh native cached query-by-query prefixes were retained. No model or dataset download was needed. The original plan and historical runs/manifests are preserved.

## Retrieval proxy: held-out results

Discovery chose joint QK/attention, max aggregation, C0.01, tauR=0.5478025981 (strict greater-than). The nominal window4 variant contains no temporal features in this chosen joint model. Grouped five-fold normalization/model selection used discovery only. Its selected OOF AUROC0.9211 is a selection statistic. Features, models and R/G thresholds were frozen at12:45:40UTC before confirmation measurement/evaluation; no S effect informed selection. [Frozen rule](../analysis/discovery_freeze_v1/freeze.json).

| Model | AUROC all | AUROC T/M | AUPRC all | T recall | M FPR |
|---|---:|---:|---:|---:|---:|
| attention | 0.975 | 0.963 | 0.965 | 0.841 | 0.064 |
| extended | 0.981 | 0.971 | 0.973 | 0.795 | 0.043 |
| joint | 0.978 | 0.967 | 0.969 | 0.864 | 0.128 |
| lexical | 0.650 | 0.563 | 0.553 | 0.432 | 0.277 |
| position | 0.712 | 0.703 | 0.641 | 0.386 | 0.149 |
| qk | 0.979 | 0.969 | 0.971 | 0.864 | 0.128 |
| shallow | 0.719 | 0.665 | 0.579 | 0.227 | 0.149 |
| visual_word | 0.662 | 0.589 | 0.488 | 0.795 | 0.617 |
| sink_secondary | 0.977 | 0.966 | 0.968 | 0.864 | 0.128 |

Primary AUROC95%CI[0.9536,0.9931], T/M AUROC95%CI[0.9314,0.9898]. At the frozen threshold, recall38/44=86.4% and M false positives6/47=12.8%; their95%CIs are[75.6%,95.6%] and[4.2%,23.4%]. Gate1 uses the preregistered point thresholds; the upper M-FPR interval exceeds20%. Recall at empirical confirmation FPR10%/20% is90.9%/97.7%; these curve summaries do not replace the frozen operating point.

Paired family-bootstrap AUROC advantages: lexical+0.3271 [0.2480,0.4053], position+0.2656 [0.1806,0.3369]. All intervals use4000 family resamples/seed1234. Primary ECE(5 equal-width bins)=0.2971 and Brier=0.1557: ranking is strong, probability calibration is poor. Attention/QK perform similarly; their algebraic relation means they are not independent mechanistic replications. The extended alternative's held-out score does not authorize replacing the selected model.

The prespecified source-eligible T causal subset is24 events/24 families,12 per split; semantic Value exceeds sham24/24, family median8.1647nats [6.6250,11.3750]. This supports label validity in the eligible subset, not every annotated T. The primary R uses no ROI, Value magnitude or future-token feature. Continuous whole-trajectory false alarms, online implementation latency and deployment robustness remain untested. [Full metrics](../analysis/confirmation_v1/retrieval_confirmation.json), [ROC/PR figure](../analysis/confirmation_v1/retrieval_confirmation.png).

## Native transport and the frozen state

Discovery G is broad, continuous/skewed, without a certified mixture. Weakness requires **JS<6.149830919e-6 AND |mean full-span CE effect|<1.169726089e-5**, the lower quartiles among43 discovery OOF high-R events. This is relative weakness of the tested layers/readout, not absence of grounding. The absolute CE guard excludes both strong positive and negative influence; a common leading token alone cannot certify full-span weakness.

| Split | High R | High R / low G | Families | Fraction of high R | T / M | S eligible |
|---|---:|---:|---:|---:|---:|---:|
| Discovery |43|10|9|23.3%|8 /2|8|
| Confirmation |44|9|9|20.5%|7 /2|8|
| Combined |87|19|18|21.8%|15 /4|16|

T-only states number15 from15 families. The JS-only secondary screen yields11 discovery +14 confirmation events, but its25 cannot replace the frozen dual criterion to rescue Gate2. Families/events remain nested in [transport analysis](../analysis/transport_v1/transport_analysis.json). Target-relative suppression among eligible weak states has median4.47e-7nats, positive10/16; these very small BF16-path effects should not be inflated into strong native source dependence.

Cheap transport models were fitted only on discovery high-R events. Held-out results use44 high-R events,9 weak; lower-than-chance AUROCs are reported in their frozen learned orientation, without post hoc flipping.

| Cheap metric | Weakness AUROC | AUPRC | Recall | FPR | Spearman JS / signed CE / composite G |
|---|---:|---:|---:|---:|---:|
| alphaV_ratio | 0.416 | 0.195 | 0.000 | 0.000 | 0.157 / 0.240 / 0.235 |
| postWO_ratio | 0.384 | 0.184 | 0.000 | 0.000 | 0.150 / 0.248 / 0.244 |
| residual_ratio | 0.346 | 0.169 | 0.000 | 0.000 | 0.202 / 0.254 / 0.262 |
| head_cancellation_ratio | 0.425 | 0.283 | 0.222 | 0.371 | 0.064 / -0.019 / 0.029 |
| head_cosine_disagreement | 0.422 | 0.219 | 0.000 | 0.057 | -0.069 / -0.050 / -0.068 |

The discovery-selected cancellation candidate does not generalize (AUROC0.425, recall22.2%, FPR37.1%). It remains exploratory. None supplies a validated cheap online weakness gate. No new causal threshold, model, sign flip or cohort expansion was selected after these results.

## Value semantics and interpretation

Thirty-six unique assays cover the union of24 prespecified T controls and16 eligible weak states, with4 overlapping events. They patch semantic versus matched sham Values at fixed native routing/history in layers19–22. All self/no-op checks pass. Full-visual semantic-minus-sham is primary; ROI-only is secondary, because contextualized visual Values need not remain spatially local.

Within the16 weak states, all effects are positive; family median8.3125nats [7.1314,10.2163]. Discovery8 events/7 families: median9.6875 [7.4686,11.6875]; confirmation8/8:7.2238 [1.5000,14.2500]. T-only12/12 positive, median9.2812 [7.4218,12.9687]. ROI-only effects also positive16/16 (event median7.3933nats; secondary). Missing main265/main218/main743 are locally wrong claims requiring separate error-oriented controls; their semantics remain unresolved. The observed positives are locally correct eligible claims, not certified unfaithful failures or demonstrated correction opportunities. [Value summary](../analysis/value_v1/value_summary.json), [semantic/sham figure](../analysis/value_v1/value_semantics.png).

- **H1:** supported for selected MathVerse prefixes by held-out passive discrimination and eligible T causal validation.
- **H2:** a pure mention-only explanation is disfavored here, but annotation/source selection and absence of whole-trajectory evaluation limit generality.
- **H3:** uniform tight coupling is not established;9 held-out relative-weak states exist. Conversely, a relative quantile-defined state does not prove a natural bimodal failure regime.
- **H4:** supported at the eligible case level by retained Value semantics, but the required cohort size and deployable cheap gate are not achieved.

Counterfactual sensitivity does not establish that amplification of native Values improves accuracy, that extraction is intact for wrong claims, or that these events are MIRAGE/PRIOR_FILL. No intervention benefit was tested.

## Resources, preserved failures and reproducibility

| Recorded worker interval | GPU-hours |
|---|---:|
| calibration_native | 1.2048 |
| main_native | 16.9347 |
| localization_profile | 0.0816 |
| localization_joint | 0.0236 |
| discovery_measurements | 0.2084 |
| confirmation_measurements | 0.2228 |
| value_assays | 0.1126 |
| mechanics_v2 | 0.0075 |
| measurement_smoke_v1 | 0.0081 |
| measurement_smoke_v2 | 0.0080 |

Recorded worker intervals total **18.8121 GPU-hours**; node02 allocation reservation was **22.5989 GPU-hours**, including CPU review/idle/loading overhead. These are alternative accounting scopes, not additive. Prior blocked node03 reservation is excluded. Main native inference alone took16.9347 workerGPU-hours. Active annotation labor was not timed. [Resource ledger](stage8a_resource_final.json).

Preserved failures: node03 pre-Python socket timeouts (cause unresolved); deliberate original-native no-overwrite exit during the approved tail handoff (not OOM), with all96 canonical results reconciled; prelaunch snapshot SameFileError repaired by making the snapshot path project-relative (no scientific work ran); release observer timed out at30 seconds while Slurm was COMPLETING, followed by confirmed CANCELLED/queue absence. The v1 release observation remains historical, superseded by verifiedv2. No scientific artifact was discarded to hide these failures.

Thirty-nine distinct CPU checks passed cumulatively, plus actual-model controls on both GPUs. Completed raw measurement, Value and active annotation hashes were reverified by this compiler. Primary analysis source/config snapshots remain unchanged. Final reporting is CPU-only. Figures and source code retain PNG/PDF/SVG and JSON evidence. [Machine-readable final result](stage8a_summary.json).

## Exactly one recommendation

**Stop the Value-reinjection branch under the current Stage8A calibration and preserve this mechanistic boundary.** Gate2 fails and no cheap transport rule generalizes, despite positive retrieval and conditional semantic evidence. Preserve those positives and limitations together. STOP for user review; do not launch reinjection or another experiment.
