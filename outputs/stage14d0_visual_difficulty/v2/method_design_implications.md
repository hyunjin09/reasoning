# Method implications — one priority, no experiment launched

The single recommended priority is **visual rereading tied to a named entity or coordinate, with the full image retained as context**. A future method should resolve a task-critical visual query from the actual image and return the observed value together with its source identity. Oracle E* must not be an inference input.

This recommendation follows the global-structure/context association, the broad competitor association, and concrete examples of row/column or entity misbinding. It does not establish that those features caused the observed errors or that rereading will improve accuracy. The [report](report.md) preserves weak and negative evidence rather than selecting only favorable comparisons.

| Source weakness / observation | Candidate acquisition operation | Testable implication and control | Present evidential limit |
|---|---|---|---|
| A: no small/tiny class under frozen source-pixel rubric; sparse blur/occlusion | Targeted higher-resolution reread | Compare extra local resolution against equal-budget rereading while retaining global context | Tiny-text effect is not estimable; this audit does not prioritize generic zoom |
| B: global structure has higher explicit-error coverage; separated-ROI contrast uncertain | Read the image frame together with named local regions | Compare full image + target region against full image alone, region alone and matched irrelevant region | Association does not prove a multi-ROI benefit; only two families in the three-plus-separated group |
| C: binding errors exist but complexity has no monotonic error ordering | Attach entity ID, row/column or ray endpoints to the reread query and answer | Keep target reference fixed while testing whether explicit source identity reduces misbinding | A direct-attribute fact can involve counting; taxonomy is not a calibrated difficulty scale |
| D: three-plus operations are not reliably worse than one | Sequential queries only when the current source demand calls for them | If studied later, compare sequential vs one-shot acquisition with matched image/token/computation budgets | No depth-based argument currently favors sequential querying |
| E: operation differences are uncertain; tracing has substantial unobservability | Task-specific count/trace/match routines are candidates, not selected methods | Any future specialization must improve source-fact accuracy against equally costly generic rereading | Read comparator only 10 families; all operation-versus-read explicit-error CIs include zero |
| F: competitor presence associates with more explicit errors; two bounded examples have a visible alternative location | Identify the target entity before reading its value; retain coordinates/role | Compare correct reference to adjacent/irrelevant target references, without supplying the correct value | Competitors cover 958/979 facts; no observed-attention or causal wrong-source inference |
| G: predicted global dependence has the clearest shared association | Preserve full-scene context alongside any local view | Test whether region-only loses identity/topology relative to full + region at matched budget | Context labels are judgments; no crop effect has been measured |

## Bounded future question

Does preserving the full image while explicitly identifying the demanded entity improve **observed source-fact correctness and native task correctness** compared with equally costly generic rereading?

A possible future Stage14D-1 comparison would hold the checkpoint, decoding recipe, initial native prompt, output contract and number of reread opportunities fixed. Query triggering and entity references would come from the ongoing reasoning/task and actual image, never from oracle E*, existing gold answers or the current audit's error labels. Human/source annotations could be used after generation for evaluation, not to provide the correct value during inference.

The discriminating controls are full image + target region, full image alone, target region alone and full image + an adjacent/irrelevant region. Match total visual-token and computation budgets where possible and report any unavoidable differences. A matched extra-reasoning budget is useful to distinguish added computation from improved source access. This is a design sketch, not a sealed experimental grid, input manifest or authorization to run one.

Evidence endpoints should separate explicit correct, explicitly wrong/misbound and unobservable/ambiguous states. Also report native task accuracy, wrong→correct and correct→wrong transitions, final scoreability, latency and token/GPU cost. More verbalization alone must not count as better acquisition; conditional error needs coverage alongside it. Preserve source uncertainty and count families, not subfacts, as independent units. An acquisition improvement without task benefit, a task benefit without evidence improvement, and both improving are different outcomes.

The 150 reviewed R families are outcome-observed discovery material. Any later confirmatory claim needs separately authorized evaluation design with independent held-out support. The current casebook is illustrative, not a fresh test set. No sample size, model-scale expansion, new method implementation or resource request is authorized here.

## Claims retained

C1 is a functional visual-to-text handoff observation, not a universal two-stage architecture. C2 says textual E* can rescue failures while changing source representation/binding; it does not measure pure perception failure. C3 remains a future visual acquisition claim and requires both evidence recovery from actual images and downstream benefit without oracle E* at inference. This audit alone establishes none of those intervention effects.

**STOP.** No Stage14D-1/14E, training, inference or visual tool calls by evaluated models were launched. The old Stage14D 1,674 continuations / 375-GPU-hour main proposal remains HOLD; Stage14C-V closure is not waived.
