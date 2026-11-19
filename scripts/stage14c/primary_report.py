"""Primary-only tables from the sealed Stage14C estimands, before diagnostics."""
from scripts.stage14c.common import *


def number(x):return 'not estimable' if x is None else f'{x:.2f}'
def span(x):return 'not estimable' if x is None else f'[{x[0]:.2f}, {x[1]:.2f}]'
def counts(x):return '/'.join(str(x[k]) for k in ['CORRECT','WRONG','UNSCORABLE','TECHNICAL_MISSING'])


def main():
    seal=load(ROOT/'audit/primary_analysis_seal.json')
    for p,h in seal['files'].items():assert sha(p)==h,p
    results=load(ROOT/'analysis/primary_results.json')['tasks'];contrasts=load(ROOT/'analysis/cross_task_contrasts.json')
    lines=['# Stage14C primary-only results','',
        'This summary precedes subgroup and D1 diagnostic interpretation. The math panel reuses the sealed Stage14B reference; it is not a new independent math replication. No math answer was regenerated or regraded.','',
        '## Source coverage','',
        '| Panel | Native items | E* items | Interpretation |','|---|---:|---:|---|',
        '| MATH-Vision | 3,040 | 1,000 | Existing math anchor; conservative known-family clustering |',
        '| MMStar | 1,000 | 280 | Mixed VQA, including mathematics; source-only eligible subset |',
        '| BlindTest | 714 | 300 | Native covers nine task labels; E* covers line intersections only |','',
        'Source-only selection and two-pass same-agent QC were completed before model generation. Same-agent review does not establish independent annotation reliability. Semantic native gold validity was not independently certified for every item. Ineligible items remain in the native panel and never enter fabricated oracle denominators.','',
        '## Primary evidence-supply rescue','',
        '| Panel | Rescued/scored native-wrong follow-ups | Rescue % [95% CI] | Unresolved follow-ups | Conservative bounds % |',
        '|---|---:|---|---:|---|']
    for b,p in results.items():
        r=p['I_supply']['rescue']
        lines.append(f"| {b} | {r['numerator']}/{r['scored_denominator']} | {number(r['estimate_pp'])} {span(r['ci95_pp'])} | {r['unresolved_followups']} of {r['native_wrong']} native wrong | {span(r['bounds_pp'])} |")
    lines+=['','## Primary post-evidence variant gap','',
        '| Panel | Paired T−I pp [95% CI] | Scored pairs/items | Conservative bounds pp | I marginal accuracy % | T marginal accuracy % |',
        '|---|---|---:|---|---:|---:|']
    for b,p in results.items():
        r=p['post'];lines.append(f"| {b} | {number(r['difference_pp'])} {span(r['ci95_pp'])} | {r['paired_n']}/{r['n']} | {span(r['difference_bounds_pp'])} | {number(r['marginal_left']['accuracy_pp'])} | {number(r['marginal_right']['accuracy_pp'])} |")
    lines+=['','Marginal accuracies have their own scored denominators. The paired variant gap is not their naive subtraction.','',
        '## Frozen cross-task contrasts','',
        '| Contrast (math minus comparison) | Estimate pp | Unadjusted 95% interval | Missingness bounds pp | Status |',
        '|---|---:|---|---|---|']
    for name,r in contrasts.items():
        endpoint='Instruct rescue' if name in {'C1','C2'} else 'post-evidence gap'
        lines.append(f"| {name}: {endpoint}, {r['benchmark']} | {number(r['estimate_pp'])} | {span(r['ci95_pp'])} | {span(r['bounds_pp'])} | {r['status']} |")
    lines+=['','10,000 family-bootstrap draws, fixed seed120220260929 and independent task streams; family-equal weighting. Intervals are unadjusted descriptive95% intervals for the complete frozen C1–C4 family. No familywise significance claim. Zero denominators remain not estimable.','',
        '## Mandatory supply transitions and residuals','',
        '| Panel/variant | Net E*−native pp [95% CI] | Correct→correct | Correct→wrong | Wrong→correct | Wrong→wrong | Scored pairs/items |',
        '|---|---|---:|---:|---:|---:|---:|']
    for b,p in results.items():
        for m in 'IT':
            r=p[m+'_supply'];tr=r['transitions']
            cs=[tr.get(k,0) for k in ['CORRECT__CORRECT','CORRECT__WRONG','WRONG__CORRECT','WRONG__WRONG']]
            lines.append(f"| {b}/{m} | {number(r['difference_pp'])} {span(r['ci95_pp'])} | "+' | '.join(map(str,cs))+f" | {r['paired_n']}/{r['n']} |")
    lines+=['','All four-way transitions, including unscorable and technical missing cells, are retained in `analysis/complete_pair_transitions.json`. Net supply benefit includes regressions.','',
        '| Panel | I E*: C/W/U/M | T E*: C/W/U/M | I residual wrong % [95% CI] | T residual wrong % [95% CI] |',
        '|---|---|---|---|---|']
    for b,p in results.items():
        r=p['post'];i=r['marginal_left'];t=r['marginal_right']
        lines.append(f"| {b} | {counts(r['counts_left'])} | {counts(r['counts_right'])} | {number(i['residual_error_pp'])} {span(i['residual_error_ci95_pp'])} | {number(t['residual_error_pp'])} {span(t['residual_error_ci95_pp'])} |")
    lines+=['','C/W/U/M denotes correct/wrong/unscorable/technical missing. Neither unscorable nor technical missing is counted as wrong.','',
        '## Native selectivity (secondary endpoint)','',
        '| Panel/stratum | T−I pp [95% CI] | Scored pairs/items | I C/W/U/M | T C/W/U/M |',
        '|---|---|---:|---|---|']
    for b,p in results.items():
        for field in ['native_all','native_eligible']:
            r=p[field];lines.append(f"| {b}/{field} | {number(r['difference_pp'])} {span(r['ci95_pp'])} | {r['paired_n']}/{r['n']} | {counts(r['counts_left'])} | {counts(r['counts_right'])} |")
    lines+=['','## Interpretation limits','',
        'E* supply intervenes on available textual evidence and may also change representation and binding. Rescue is oracle-supply responsiveness; resistance is not automatically a pure reasoning failure. Cross-task contrasts are observational and compare differently selected eligible populations. In particular, the BlindTest E* panel cannot support a claim about all nine native task types. Conditional rescue percentages and paired variant-gap percentage points do not measure comparable shares of upstream and downstream failure.','',
        'The models are distinct pinned4B deployed checkpoints with their validated model-specific recipes and unequal32,768/81,920token caps. This is neither a same-weights Thinking toggle nor an equal-compute comparison. Across changing batch contexts bitwise seed replay is not guaranteed; the bounded matched-context replay passed, with the original mismatch preserved.','',
        'MMStar extraction deliberately uses terminal committed-answer adjudication rather than the upstream first-character matcher; this study is not an official leaderboard replication. Raw outputs, original parser decisions and review provenance remain immutable.','',
        'Next within the already approved stage: prespecified source sensitivities and bounded D1 evidence elicitation. No additional experiment or follow-on stage is authorized by these results.','']
    path=ROOT/'summaries/stage14c_primary_summary.md'
    with path.open('x') as f:f.write('\n'.join(lines))
    save(ROOT/'audit/primary_summary_seal.json',dict(at=now(),summary_sha256=sha(path),
         primary_analysis_seal_sha256=sha(ROOT/'audit/primary_analysis_seal.json'),
         secondary_or_D1_interpreted=False))


if __name__=='__main__':main()
