# Stage14D1 SAVA — final technical recovery report

**Decision: NO-GO for the 72-family pilot. Exact replay passes the bounded validation; the remaining blocker is the query provenance contract. STOP after this report.**

Both Slurm jobs completed successfully: GPU146598 and CPU146599. All five runtime profiles completed. No scientific pilot, final-answer scoring, prompt optimization, new model or old Stage14D grid was run. This technical result does not establish SAVA's effectiveness or ineffectiveness.

## Replay: recovered under deterministic scheduling

All eight original prompt-plus-512-token reconstructions, images and prefix boundaries match. Recovery input checks and all completed receipts pass.

| Runtime profile, prefix cache disabled | Sampled exact pairs | Greedy exact pairs |
|---|---:|---:|
| Default V1 multiprocessing, batch8 | 6/8 | 5/8 |
| Default V1 multiprocessing, batch1 | 8/8 | 8/8 |
| V1 multiprocessing disabled, batch1 | 8/8 | 8/8 |
| V1 multiprocessing disabled, batch8 | 8/8 | 8/8 |
| Independent fresh process, multiprocessing disabled, batch8, original seeds | 8/8 | 8/8 |
| Same independent process, predeclared seed+100003 | 8/8 | 8/8 |

The independently frozen exact-replay gate therefore **passes**, including all eight sampled pairs at each seed set. It was not relaxed. Greedy is diagnostic only; the sampled scientific recipe remains unchanged.

The setting tested is `VLLM_ENABLE_V1_MULTIPROCESSING=0`, documented for offline reproducibility in the pinned [vLLM0.11.0 documentation](https://docs.vllm.ai/en/v0.11.0/usage/reproducibility.html). Model, BF16 precision, seeds and sampling parameters were unchanged. This result validates the observed hardware/runtime and bounded64-token tests; it is not a guarantee across arbitrary hardware, batching or trajectory lengths.

### Root-cause evidence

- **Supported:** scheduling-sensitive numerical execution. Instrumented case33 again diverged at generated-token index30 under default batch8. Its input and first30 generated tokens were identical, and the CUDA generator-state hashes matched both before and after sampling. Raw logits and resulting sampling probabilities differed. Token330's raw logit changed from23.875 to24.0; with identical RNG state the selected token changed from46363 to330.
- Its logged prefill schedules differed between repetitions. One repetition prefills case33 without1477 in that step; the other co-prefills1477. In the multiprocessing-disabled profile, the corresponding schedules and case33 logits matched, and the token sequences matched. The hooks themselves can affect timing, so the evidence identifies a supported scheduling/numerical mechanism, not a specific CUDA kernel defect.
- **Not found:** a prompt/image/prefix reconstruction bug. No RNG-state mismatch was found at the diagnosed case33 divergence; this does not establish RNG parity for every historical failure.
- Case107 did not reproduce its earlier sampled index45 failure in this run. It did diverge under default greedy at index35 and passed the deterministic profiles. The unstable cases/positions can vary; identical sampled seeds alone did not remove the problem.
- Batch1 also passed with default multiprocessing. Cache disablement alone did not suffice at batch8. Greedy default batch8 also failed, ruling out an explanation based solely on random seed selection.

The original design restarts from reconstructed prefixes with fresh frozen family seeds. It never restores the historical generator's advanced state. Historical-future equality and equality of two fresh repeats are different tests; the latter is the retained gate.

Bitwise replay is not mathematically necessary for every stochastic causal design, but changing this gate is unnecessary here. The prospective multi-seed paired-baseline alternative remains unadopted. See [the pre-result gate review](replay_gate_review_v1.md).

## QUERY/NONE: grammar works; full provenance acceptance fails

The automatic report's `synthetic_QUERY_NONE` gate combines branch choice with the full query contract. Its10/12 result must not be described as10/12 syntax-valid outputs or only10/12 correct branches.

| Check | Result |
|---|---:|
| Synthetic expected branch, ignoring provenance acceptance | 12/12 |
| Synthetic committed, JSON-schema-valid output | 12/12 |
| Positive controls generating QUERY | 6/6 |
| No-demand controls generating NONE | 6/6 |
| Synthetic full query-contract acceptance | 10/12 |
| Synthetic cap hits | 0/12 |
| Frozen-family committed, JSON-schema-valid QUERY | 8/8 |
| Frozen-family full query-contract acceptance | 0/8 |
| Frozen-family query cap hits | 0/8 |

The dot-count positive control generated QUERY twice, but included an unsupported provenance entry `"number":"3"` with `"quote":"upper-right compartment"`. The branch and grammar worked; the provenance gate correctly rejected that record under the frozen literal contract. Both branches remained available throughout.

All eight scientific-case replies selected QUERY. Their rejection was **not** NONE behavior or failure to terminate. The literal validator requires an exact quoted span in the claimed question/prefix, the cited digit within that span, and citations for all numeric strings in query fields.

| Family/item | Observed provenance-contract issue |
|---|---|
| 317 | The40/30 values occur in the question, but emitted LaTeX quote strings do not match the source bytes. |
| 760 | Cites digit4 using the source word `four-storey`, while query identifier1 is uncited. |
| 2577 | Cites3 and6 using source spans containing perimeters12 and24; these are not literal source numbers and are not used in its query fields. |
| 107 | Cites4/3 using the words `four`/`three`; the query's12 is uncited. |
| 2274 | Claims question quotes `$ A$ at position 3` and `$ B$ at position 4` that do not occur there; the query itself uses neither number. |
| 33 | Uses rendered Unicode-arrow quotes instead of the question's literal LaTeX arrow spans. |
| 1477 | Cites digit5 using the source word `five`; the1 in `image1` has no citation. |
| 737 | Claims a question quote `last digit in the sequence` that is absent and contains no9, although9 occurs in query fields. |

These include formatting/representation mismatches and unsupported citations. **They are not eight established false visual facts.** In particular, failing a byte-exact citation check does not by itself show that a semantically referenced number is absent. No record was repaired, normalized, reclassified as accepted or regenerated. The numerical gates remain unchanged. Queries' source relevance and correctness are not certified by this audit.

## Bounded acquisition transport and gate outcome

No query was accepted, so **LOCATE and targeted Q/QI/QIA/QGL readouts were not attempted**. The automatic locator Boolean is false because there is no eligible denominator; it is not an observed0% locator success rate.

The eight generic G image readouts passed their JSON contract. Sixteen N/G solver continuations reached the intentional256-token technical cap. They establish bounded transport only, not completed answers or answer accuracy. Targeted arms were aliases to N in this technical transport path, not evidence that targeting had zero effect.

The eight-case gate is therefore still **NO-GO**:0/8 full-contract accepted/actionable queries fails the unchanged6/8 and4/8 requirements, and the strict synthetic full-contract gate also fails. The central remaining bottleneck is between query generation and provenance acceptance. No targeted localization/retrieval efficacy claim is supported.

## Fixes, tests and preservation

The corrected grammar preserves status-first field order for both branches. CPU tests establish both branches are reachable; generation now confirms this. The recovery worker tests supported scheduling settings, records request seeds/input tokens/images/raw logits/scheduler traces, and internally enforces exact replay before scientific-case acquisition transport. Existing four grammar tests and four gate/budget regression tests passed before launch.

New CPU-only final verification independently checks JSON schema validity, replays the unchanged numeric validator, validates268 completed receipts, and confirms original377 package files plus26 code files remain hash-identical. No sealed original code or v1/v2/v3 artifact was overwritten. The frozen72-family cohort is intact. The automatic report is preserved; this separate report clarifies branch/syntax versus provenance and not-attempted versus failed gates.

## Resources and stop

- Recovery: one RTX A6000 onnode03 for1288allocated seconds, **0.357778GPU-hours**.
- Prior attempts:1421GPU-seconds.
- Cumulative technical usage: **2709seconds =0.752500/2GPU-hours**.
- Remaining technical allowance:4491seconds, **not an instruction to launch another diagnostic**.
- Completed recovery requests:268 (240 solver replay/transport,20 QUERY including synthetic controls,8 generic READ).
- Both jobs terminal; no GPU allocation retained. CPU postprocessing used zero GPUs.

No additional inference was launched while checking results. No protocol gate was lowered, no prompts were tuned, and no pilot or follow-on experiment was launched. The old1,674-continuation/375GPU-hour Stage14D experiment remains HOLD.

Evidence: [final verification](../audit/final_result_verification.json), [replay matrix](../audit/replay_matrix_results.json), [RNG/logit comparison](../audit/logit_rng_comparisons.json), [automatic gate results](../audit/technical_revalidation_results.json), [resource accounting](../audit/resource_accounting.json). Full raw outputs/token IDs, seeds and receipts remain under `raw/`; scheduler and full selected logit snapshots are under `traces/`.

**NO_GO_TECHNICAL_QUERY_CONTRACT — exact replay validated; scientific pilot not launched.**
