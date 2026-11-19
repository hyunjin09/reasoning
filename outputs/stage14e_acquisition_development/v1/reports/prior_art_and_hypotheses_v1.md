# Competing hypotheses and primary-source prior-work assessment

Accessed2026-10-22. This assessment supports experiment design; it does not establish novelty or reproduce the papers' empirical claims on our checkpoint/cohort.

| Work / primary source | Relevant mechanism | Boundary for this cycle |
|---|---|---|
|[Does Reasoning Improve Seeing?](https://proceedings.mlr.press/v306/bi26d.html)|Probes for reasoning helpfulness/desired length; head interventions on meta-cognitive signals|No claim that longer reasoning necessarily improves perception; our target is measured source acquisition|
|[When to Think and When to Look](https://arxiv.org/abs/2511.15613v3)|Uncertainty-triggered lookback and breadth search|Generic lookback/triggering is existing work; our initial diagnostic fixes timing|
|[ReGround](https://arxiv.org/abs/2608.04385v1)|Self-diagnosis followed by image re-injection, trained with diagnostic scaffolding|Neither diagnosis nor re-injection alone is novel; correct diagnosis is a competing bottleneck|
|[PEARL](https://arxiv.org/abs/2511.18437v1)|Perception checklists and perceptual fidelity gates/rewards duringRL|Task-relevant perception questions already exist; this cycle is training-free and evaluates online premise targeting separately|
|[Perceval](https://arxiv.org/abs/2604.24583v1)|Visual-claim error grounding, token-level training penalties and inference correction|Visual claim checking/repair is prior art; no trained critic or answer reranking here|
|[DeepEyes](https://arxiv.org/abs/2505.14362)|RL-induced visual tool use interleaved with reasoning|Crop/search/tool use is prior art; no retraining in this bounded cycle|
|[Active-Look](https://aclanthology.org/2026.findings-acl.745/)|Grounding-expert disagreement, region verification, highlighting and selective zoom|Global/local preservation and uncertainty-based region selection are already proposed; no novelty claim for adding a crop|
|[V*](https://arxiv.org/abs/2312.14135)|LLM-guided visual search and working context|Semantic visual search is prior art; current question is precise source-resolvable demand and reader independence|
|[Visual CoT](https://arxiv.org/abs/2403.16999)|Region-supervised visual reasoning and intermediate boxes|ROI-aware reasoning is established; manual ROI diagnostic cannot represent deployment|
|[Visual Contrastive Decoding](https://arxiv.org/abs/2311.16922)|Contrasts original versus distorted-image output distributions to reduce hallucination|No claim of inventing image-dependence controls; logits intervention would need separate implementation validation|
|[CofactGVR](https://proceedings.mlr.press/v306/zhang26ex.html)|Counterfactual predicted-region perturbation supplies intermediate grounding rewards|Final correctness alone does not validate an evidence mediator; our no-image/source evidence endpoints are narrower diagnostics|

The named ReGround here is the visual re-examination paper, not similarly named reviewer-comment grounding or robotics projects. OpenReview's CofactGVR page was inaccessible behind browser verification; the primary PMLR proceedings page was available and used. No secondary summary overrides primary papers.

## Competing explanations

- **Demand recognition:**A query for an unknown mathematical value cannot be satisfied visually. Test explicit classification of unresolved visual/reinspection versus alreadygiven/derived unknown, includingNONEcontrols.
- **Target translation:**Generic noun+property omits the needed relation/frame. Test relation-complete requests with source references versus the old controller; diagnostic source-valid target identity hides the value.
- **Context contamination:**Solver conjectures and image-unavailable claims may anchor the reader. Test same exact target/read instruction with versus without the512-token prefix. This is a hypothesis, not an established failure cause.
- **Reading limitation:**Even a good target may yield incorrect or incomplete extraction. Test an entity-bound structural observation format at matched target/image; do not force a value on uncertainty.
- **Localization:**Correct targets may be mislocalized. Add a bounded model-predicted source-region condition with original global image; no manual correction/fabricated crop.
- **Timing:**Many512-token prefixes are unsettled, but some already contain sufficient evidence. First test selective demand; changing timing now would confound target/read diagnosis.

## Candidate methods (maximum two initially)

A. **Premise-addressed independent reading:** controller separates unknown visual premise, reinspection, and nonvisual/known states; returns a value-free relational target. A fresh reader receives the original question, target and full image, without the solver's candidate evidence values or conclusions. The solver retains its original image/prefix and resumes with an explicitly unverified record.

B. **Premise-addressed structural reading:** same controller and information separation, but the reader constructs a compact source frame plus observed entity/value/relation bindings. Its goal is to avoid returning an unbound label when the task requires layout/connectivity. It may be verbose, wrong or unnecessarily costly; test these risks.

The proposed contribution to evaluate is the separation of **demand selection information** from **source-value reading information**, with explicit source-resolvability and structured binding contracts. This is an operational hypothesis and measured component comparison, not a proven novel algorithm. Broader priority/novelty requires stronger evidence and a full paper-level review. A positive image-versus-no-image acquisition contrast would support fresh visual contribution, but not prove downstream mediation.
