# Stage14E2: deliberative source reading and continued method development

The user explicitly continued the active goal after the first bounded cycle's negative result. This is a prospective continuation under the **same 24 additional GPU-hour ceiling**, not a budget reset. Stage14E v1 remains sealed. Its 32 evaluation families are outcome-observed and cannot serve as fresh evaluation again. The preceding goal turn was progress: completed experimental evidence and resource closure changed the next decision. The broad methodology goal remains unachieved.

## Evidence and competing actions

The ledger recovered useful evidence in 0/32 versus 1/32 for the SAVA-style reader. Accepted targets were often incomplete, 12 ledgers were rejected, and correct helper statements often repeated known facts. However, the runtime explicitly appended `</think>` before every helper response. This is a confirmed implementation choice, **not a newly discovered bug or established explanation**. The result concerns compact helper reading. Relaxing provenance alone would not address accepted-but-unhelpful reads; another crop is not supported by prior development. The smallest decision-changing action is a matched reader-mode test before another integrated design.

## Action 1: frozen matched reader diagnostic

- Reuse the original 24 development families, original images, frozen 512-token prefixes and family seeds. No final-answer correctness is used for selection or tuning.
- Reuse original model targets O (18 QUERY, 6 NONE). Preserve NONE as 12 logical absent reads across O conditions.
- Freeze new source-informed target names T for all24. They specify what to inspect, with no observed values, relation assertions, corrective hints or answer steps. Explicitly diagnostic; never a deployable method input.
- Conditions: `O_C`, `O_T`, `T_C`, `T_T`, `T_N`. C closes the thinking channel; T leaves it open; N is the matched T target/read prompt with no fresh image. All use the same source-reader instruction and unverified prefix. The same T query is held fixed in all three T conditions.
- Matched C/T conditions use **unconstrained decoding in both**, the same8192-output-token cap and the pinned temperature1/top-p.95/top-k20/rep1/presence0 recipe. Thus the principal changed factor is the supplied thinking boundary, not a simultaneous grammar or cap change. Historical2048-token constrained outputs are context only, not the matched comparator.
- Expect120 logical/108 physical scientific reads, plus bounded replay checks. No long solver continuations in this diagnostic.
- Parse only the committed final section. Never mine the reasoning trace for a successful evidence record after an invalid final. Permit one JSON object with the original four fields; preserve malformed, capped, absent and unknown results.
- Primary diagnostic contrast: useful source-correct acquisition `T_T − T_C`; also report complete requested-source coverage, explicit source errors, O_T−O_C and T_T−T_N. The no-image arm measures source-correct textual responses, not visual acquisition. Preserve partial/reinspection/known distinctions from the existing source rubric. Family-equal4000 stratified bootstrap, seed20261022. No final accuracy selection.
- Source review uses original pixels and existing source references offline; no gold/E*/humanROI enters model-selected runtime. Source-informed T is the explicit diagnostic exception and is labeled at every call.

## Implementation tasks and verification

1. **Boundary/parser contracts (two files):** failing tests for open/closed boundary, missing closing tag, JSON ambiguity, duplicate keys, extra fields and cap preservation; implement minimal pure functions. Verify tests before GPU.
2. **Runtime and worker (two files):** version the established engine in a separate module, add explicit helper-mode transport, retain pixel/token receipts and fresh repeated native continuation checks. Verify matched prompts differ only by the declared closing suffix; input image hashes and seeds identical.
3. **Freeze and launch (preparation/launcher):** exact family/condition manifests, source-target QC, hashes, old-seal verification and resource carry-forward. Two single-GPU shards when available;48h Slurm limits. Actual allocation billing remains cumulative. Expected1–2GPUh; reserve up to6GPUh for the finite diagnostic, leaving at least10.85GPUh initially unreserved for method evaluation. Do not shorten scientific rollouts to hit an arbitrary wall-clock estimate.
4. **Review and decide:** inspect all outputs/source evidence, not only successes; distinguish engineering failures from method behavior. Preserve all attempts. Decide the next method action from acquisition evidence and record it before implementing it.

## Continued research, not a diagnostic stop

After Action1, select a deployable revision only from development evidence. Consider deliberative relation-complete source reading and source-inventory-before-demand-selection; at most two deliberate new candidates initially. Do not supply T targets at deployment. Freeze a new disjoint method-evaluation cohort and common metrics before viewing its intervention outputs. Reserve compute for matched native/old-reader/new-method outcomes; adapt cohort size prospectively to the measured cost, never after accuracy inspection. A second scientific revision requires a new evaluation group. Do not recycle the prior32 as held-out evidence.

The objective is demonstrable acquisition improvement with downstream accuracy evaluated separately. Do not declare goal completion from technical gates or a small in-sample improvement. Preserve null results. Continue under the active goal while meaningful, scientifically valid work remains within the ceiling. If the remaining resources cannot support a valid next action, document the precise constraint; do not exceed24GPUh or manufacture completion. Old Stage14D375GPUh remains HOLD, Stage14C-V remains unfinished.
