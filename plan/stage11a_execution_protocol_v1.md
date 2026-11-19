# Stage11A prospective execution protocol

Authority: stage11a_visual_evidence_bottleneck_census_plan.md. Independent unit is
the exact Stage9A problem/image family. Preserve all128 and all384 native traces.
No native mode correctness is opened during E* eligibility or sufficiency review.

## Review and sealing order

1. Two existing semantic annotation agents independently inspect all128 original
   images/questions and benchmark gold, with trajectories/outcomes withheld. Each
   proposes eligibility and1–4 atomic visual facts. This is independent model-agent
   review, not human inter-rater reliability. Prior-stage exposure is not erased;
   Stage11A packets themselves contain no model answers or modes.
2. Main adjudication compares proposals against images. A common proposed E* is
   independently checked for sufficiency by both reviewers before final sealing.
   Disagreements/too-large/unresolved evidence remain recorded. No packing a large
   inventory or the solved answer into a nominally atomic proposition.
3. Native review sees one anonymized trace at a time, no other mode, probe, or final
   correctness. Full original reasoning is retained; navigation indices are not
   evidence of absence. Every eligible item is reviewed in all three modes; the
   first32 eligible families in fixed hash order receive two independent passes
   for every mode. If fewer32 exist, review all and report the shortfall.
4. Probe review uses sealed facts. Join modes, native correctness and probes only
   after native and probe labels are sealed. Independently apply the frozen
   discordance classification on the same agreement-family set after this join.

## Evidence states

N2 requires every atom correctly present or deducible from the generated text
without consulting the image again. N4 records asserted correct/incorrect versions
or evidence-state changes, including correction over time. Mere questions are not
assertions. N3 requires an asserted wrong critical fact, without a corresponding
correct conflicting version. N1 has some correct atoms but no sufficient set and
no wrong critical assertion. N0 is an inspectable substantive reasoning trace
with no E* evidence. N5 is answer-only/too little observable reasoning to judge.
N5 stays distinct from N0; no inference about unobserved internal state.
Record quotes, character/token position where feasible, per-atom status, review
coverage and rationale. Inspect full text for conflicting/corrected later evidence;
do not label a whole long trace from its first relevant hit alone.

Historical final outcomes use the existing reviewed Stage9A native answer scoring;
valid wrong and no-valid-final remain distinct. Preserve the scoring provenance.
The E4 primary failure rate includes wrong and no-valid-final, reported separately
alongside a wrong-only sensitivity. No-valid-final never itself implies visual error.

## Explicit probes

Probe all eligible families if<=64. Otherwise choose64 by proportional largest-
remainder allocation over (subject, primary evidence type), with fixed SHA256
ordering seeded1120260928 within strata and to break ties. This never uses mode
correctness, native-state labels, or probe outcomes. Eligible families without
probes remain in E1/native-state reports but not the fully observed primary E5.

Original image and preprocessing; original question may contextualize unnamed
visual referents. Ask the same fact attributes/relations without values or solution.
Append exactly Stage9A's CoT instruction for CoT; use native Thinking template for
Thinking and unchanged Direct template. Pinned historical2B model revisions, BF16,
TF32 off; same Stage9A sampling parameters, one fixed item seed shared across modes.
Short cap512 new tokens per mode. No continuation merely to obtain a desired read.
Score fact recovery over all visible probe text, including Thinking reasoning;
report normal EOS and cap status separately. Explicit retractions can be resolved
by a final unambiguous corrected assertion; persistent contradictions are AMBIGUOUS.
All atoms CORRECT=>PROBE_ACCESSIBLE; some=>PROBE_PARTIAL; none=>PROBE_INACCESSIBLE.
This measures recovery under this explicit-demand prompt and budget only.

## Profiles and matched localization

Preserve each plan-defined P1–P4 predicate. If more than one applies (e.g. an
inaccessible probe but sufficient native evidence and a failed answer), classify
P5 mixed and retain both flags; do not silently impose causal precedence. A correct
answer without sufficient observable native evidence is P5, not certified success.
N5 is never counted as N0 or as a clean P2 native-access bottleneck.

E5 primary denominator is the probed eligible family subset with Thinking correct
and CoT wrong/no-valid-final. Preserve A/B/C predicates; exactly one=>that category,
multiple or none=>D mixed. Reverse discordance uses the identical swapped rule.
E1 uses all128; E2 uses probed items; E3/E4 use all eligible native traces, with a
matched-probe-subset view for fair figure comparisons. Every denominator is explicit.

## Statistics, agreement and feasibility

Equal-family weighting,4000 paired bootstrap draws, seed1120260928, ordinary95%
percentile intervals; no token/atom pseudoreplication. Report Thinking−CoT paired
differences and exact two-sided binomial/McNemar discordant counts descriptively.
Report raw Cohen kappa and agreement before adjudication. If fine N0–N5 kappa<.6,
collapse to N2 / observable insufficient(N0,N1,N3,N4) / not-externalized(N5);
do not promote fine-grained state proportions. Coarse kappa must be>=.6 for an
acceptable evidence-state agreement gate. Undefined kappa is not a pass.

Operational GO thresholds are frozen before outcome joins. Strong GO:>=48 eligible,
>=16 primary Thinking-correct/CoT-failed discordant families,>=8 nonmixed informative
discordances, at least two CoT failure profiles among P1/P2/P3 each containing>=8
independent probed families, acceptable native agreement, and mixed fraction<=75%.
Limited GO:>=32 eligible,>=8 informative discordances, acceptable agreement/mixed
fraction, but Strong GO not reached. The thresholds refer to independent families,
not three repeated modes. Otherwise No GO. All component counts are shown; no
post-outcome threshold repair. A>=48 cohort with insufficient category spread can
at most support a limited feasibility pilot, never a Strong GO claim.

## Optional pilot and stop

Only after the census is frozen and GO is plausible: at most12 eligible families,
balanced deterministically across observed candidate CoT failure types, no oracle-
outcome selection. Original question plus identical correct E*, image removed,
CoT and Thinking, cap512; no optional Direct arm needed. Freeze selected IDs and
text before pilot generation. Report feasibility and cap limitations; no full
Stage11B or causal gap-closure claim from this small pilot.

All GPU work through scheduler/Slurm, up to8 authorized A6000 GPUs; request only
useful independent workers. Primary target<1.5GPUh, optional<.5, total hard<2.5
including startup/technical/failure allocations. No downloads expected. Version
failed artifacts rather than overwriting. Required14 artifacts and four figure
pairs, optional pilot/fifth figure only if executed. Exactly one plan recommendation;
STOP before Stage11B or any new experiment.
