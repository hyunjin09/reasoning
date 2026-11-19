# Stage14A — completed source construction

Completed source-only construction under the approved plan and structured-atom clarification. No evaluated-model calls, external annotator calls, model-outcome inspection, or GPU computation.

| Deliverable | Final count |
|---|---:|
| MATH-Vision native problems | 3,040 |
| Known conservative MATH-Vision families | 2,104 |
| Frozen-order representatives reviewed | 1,727 |
| Final E* families, all second reviewed | 1,000 |
| Final-cohort complete source rereads | 250 |
| MathVerse native families / versions | 788 / 4,728 |
| MathVerse primary / scheduled second reviews | 788 / 197 |
| Confirmation subsets | 300 + 300 |

The preserved first 16 cases were rechecked under the user clarification. Final evidence has 1,448 primary atoms: 985 structured layouts and 463 scalar relations. 797 families contain a structured atom. Every structured atom records internal size, unit, coherent source object and minimality; primary atom count is not an information-volume measure. Atom counts by family are 708 with one, 173 with two, 82 with three and 37 with four. The cohort includes 650 open-ended and 350 multiple-choice problems; source difficulty levels 1–5 contain 77, 274, 181, 263 and 205 families. Full subject and evidence-type distributions are in [source statistics](stage14a_source_statistics.json).

QC rejected item1174 as text-sufficient after a source-only exact geometry check. Its original acceptance and the original 250-family QC selection remain immutable. The next frozen candidate, rank1727/item879, passed primary and second review. Recomputing the same QC hash rule selected879, which received its complete reread. Thus251 complete rereads are preserved, including the rejected case; exactly250 belong to the final cohort. Two other accepted source receipts are aliases and do not increment the independent-family count.

| Final exclusion reason | Count |
|---|---:|
| TEXT_SUFFICIENT | 487 |
| AMBIGUOUS_VISUAL_SOURCE | 10 |
| MORE_THAN_FOUR_ATOMS | 194 |
| UNDERSPECIFIED_SOURCE | 16 |
| CORRUPT_SOURCE | 1 |
| ANSWER_LEAKAGE_UNAVOIDABLE | 8 |
| MATERIAL_SOURCE_CONTRADICTION | 9 |

The CORRUPT_SOURCE exclusion is the documented native gold conflict for2524, not an unreadable image. The broad census retains all original records and golds with source-issue provenance. Original ordering, first-pass decisions, rejected records, aliases and QC corrections remain available through the revision-aware eligibility log and audit receipts.

MathVerse has complete files and six native versions for every family. Semantic validity is separate from this structural completeness:

| Source check | PASS | FAIL | Documented ambiguity |
|---|---:|---:|---:|
| same_task | 693 | 63 | 32 |
| gold_consistency | 788 | 0 | 0 |
| text_only_sufficient | 398 | 353 | 37 |
| visual_versions_sufficient | 718 | 35 | 35 |
| answer_safe | 782 | 6 | 0 |
| unique_ids | 788 | 0 | 0 |

350 families pass all recorded source checks;390 have at least one source failure and48 have documented ambiguity without an explicit failure. These are retained source-validity findings, not model results or unfinished review disagreements. Gold consistency means literal agreement across versions, not proof the gold is mathematically correct. VD/VO sufficiency is scoped to those two versions; separate Vision Intensive losses remain in review notes. Fourteen source rereads corrected earlier flags that had mixed those scopes. Native prompts, all image variants and golds were preserved. Requirement metadata uses null when source defects prevent a defensible visual-binding judgment.

All QC is same-agent review; no independent inter-rater reliability is claimed. The frozen MathVerse confirm300 manifest remains byte-for-byte unchanged; its historical PENDING semantic fields describe the pre-review freeze, and current status joins through the final788 manifest/QC records.

The historical identity audit examined138,143 files and retained34,160 identity-bearing artifacts. One unreadable nonresearch scheduler-status file is documented. Source catalogs had already listed every family, so strictly historically untouched size is0 for both datasets and for E*-1000. Catalog exposure, generation/technical use, trace/outcome-review evidence, and unclassified appearances remain separate. Outcome-review evidence is inferred from artifact provenance, without inspecting outcome values. Alias-expanded provenance does not prove direct per-item use.

The3,828 total denotes native benchmark problem IDs, not3,828 verified independent tasks. MATH-Vision conservative aliases and16 observed MathVerse repeat groups are explicit. Exact RGB comparison found no cross-benchmark image matches, but does not prove task independence.

All5,429 source files and25,511 prior Stage12/13 files match their snapshots; original plan/specification/sampling code also match. Twenty source/projection tests passed. Final contract checks are recorded in [validation](audit/final_validation.json), and final files/receipts in [preservation manifest](stage14a_preservation_manifest.json). Five source-report figures are available as PNG and PDF in [the figure manifest](audit/source_figure_manifest.json).

Resources:0GPU-hours, no downloads or installations. Three CPU-only scheduler jobs completed. Known allocated CPU time is1.9756CPU-hours for the first and final audits; exact elapsed for the four-CPU identity repair was unavailable after Slurm expired its record (one-hour command timeout, at most4additional allocatedCPU-hours). Bounded local CPU work was not separately metered. [Accounting](stage14a_resource_accounting.json) records the limits and review counts.

Recommendation: Launch the preregistered large-scale math phenomenon study: broad Instruct-vs-Thinking census on all3,828 native problems, visual-evidence/equal-evidence profiling on the1,000-family MATH-Vision E* cohort, and paired-modality analysis on MathVerse, retaining the frozen source-validity and provenance flags.

STOP. The recommended study has not been launched.
