"""Descriptive diagnostic tables and exhaustive casebook, without method selection."""
import json
from collections import Counter
import numpy as np
from scripts.stage14e2.common import P, load, save, sha, now


def pct(x): return f'{100*x:.2f}'


def main():
    result = load(P/'analysis/diagnostic_results_v1.json')
    audit = load(P/'audit/completed_execution_audit_v1.json')
    records = load(P/'analysis/source_review_complete_v1.json')['rows']
    packets = [r for file in sorted((P/'analysis').glob('source_packet_*_v1.json')) for r in load(file)['families']]
    (P/'reports').mkdir(exist_ok=True)
    report = ['# Stage14E2 matched reader-mode diagnostic', '',
        'This experiment is complete; further method development and the frozen fresh32 evaluation are paused at the user’s request. '
        'These are24 outcome-observed development families, not a fresh confirmation cohort. No downstream solver continuation or final-answer accuracy experiment was run.', '',
        '## Frozen design', '',
        'O=original model-selected query; T=source-informed target identity, diagnostic only. '
        'C=closed helper thinking boundary; T suffix=open helper thinking boundary. '
        'T_N uses the same diagnostic target and open thinking boundary without a fresh image. '
        'A correct T_N response is not visual acquisition. All readouts receive the same unverified solver prefix. '
        'Same family seed, sampling settings and8192-token cap; no constrained JSON grammar in either reader mode. '
        'The original targets are absent on6families, retained as12logical absent O records.', '',
        '## Acquisition outcomes', '',
        'Useful=U(new correct task-critical fact) or R(valid reinspection), including partial source coverage. '
        'K=already-known/given; W=explicit task-critical source error; ?=uncertain/incomplete; I=irrelevant/derived; '
        'A=absent original query; X=capped/malformed/uncommitted. No capped reasoning was mined for a replacement final.', '',
        '| Condition | Physical / assigned | Useful U+R | U | R | Known K | Wrong W | Unknown ? | Other I | Invalid X | Full task-source coverage |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for a, r in result['arms'].items():
        n=r['labels'];c=r['coverage']
        report.append(f"| {a} | {r['attempted']}/{r['assigned']} | {r['useful']} | "+
            ' | '.join(str(n.get(k,0)) for k in ['U','R','K','W','?','I','X'])+
            f" | {c.get('full_task_source',0)} |")
    report += ['', '| Contrast | Difference (pp) |95% family bootstrap CI (pp)| Gains | Losses |',
               '|---|---:|---|---|---|']
    for name, r in result['pairs'].items():
        report.append(f"| {name} | {pct(r['difference'])} | [{pct(r['ci95'][0])}, {pct(r['ci95'][1])}] | "+
            ', '.join(r['gains'])+' | '+', '.join(r['losses'])+' |')
    report += ['', 'The cube family436 relies on the source’s solid-pile/hidden-support convention. '
        'Its partial reinspections do not certify individually visible hidden cubes. '
        'A descriptive sensitivity excluding this family is reported below; it was added during source review, '
        'does not replace the frozen primary analysis, and has no separate inferential claim.', '']
    by={(r['item_id'],r['condition']):r for r in records}
    remaining=sorted({r['item_id'] for r in records}-{'436'})
    for treatment, base in [('T_T','T_C'),('O_T','O_C'),('T_T','T_N')]:
        delta=[int(by[f,treatment]['label'] in ['U','R'])-int(by[f,base]['label'] in ['U','R']) for f in remaining]
        report.append(f'- Excluding436: {treatment}−{base} = {pct(np.mean(delta))}pp across23families.')
    report += ['', 'Primary contrast: T_T−T_C. Secondary: O_T−O_C and T_T−T_N. '
        'Family-equal, inherited source-context strata,4000 bootstrap draws, seed20261022. '
        'Zero-event degenerate intervals do not prove a zero population rate. One stochastic seed per family; '
        'uncertainty does not separately estimate repeated-seed variation.', '', '## Execution and resource use', '',
        f"Completed{audit['physical']}physical/{audit['logical']}logical scientific reads;4/4 repeated-native gates pass. "
        'All matched C/T prompts, token prefixes, image pixels, family seeds and generation settings passed exact transport checks. '
        'Prior sealed records are unchanged. Both finite queues exited; no further experiment launched.', '',
        f"This diagnostic: **{audit['diagnostic_gpu_hours']:.4f}charged GPU-hours**. "
        f"Cumulative authorized cycle: **{audit['cumulative_gpu_hours']:.4f}/24GPU-hours**, including failed jobs, startup and idle allocation. "
        'Historical SAVA expenditure remains separate (21.365278GPU-hours).', '',
        '| Arm | Generated tokens | Median tokens | Cap hits | Summed request seconds |',
        '|---|---:|---:|---:|---:|']
    for a in result['arms']:
        rs=[r for r in audit['records'] if r['condition']==a]
        report.append(f"| {a} | {sum(r['tokens'] for r in rs)} | {np.median([r['tokens'] for r in rs]):.1f} | "
            f"{sum(r['cap_hit'] for r in rs)} | {sum(r['latency_seconds'] for r in rs):.1f} |")
    report += ['', 'Request latency is descriptive and is not substituted for allocation billing.', '',
        '## Interpretation limits and pause', '',
        'Source-informed T targets are diagnostic oracle identities, not deployable method outputs. '
        'The source review is a single AI review with condition visible, using original pixels and offline source references. '
        'Source-reference ambiguity and partial coverage remain explicit in the casebook. '
        'A source-correct fact repeated from the prefix is not newly acquired evidence. '
        'No final-answer improvement can be inferred from this reader-only experiment. '
        'No candidate is selected or evaluated after this diagnostic while paused.', '',
        'The frozen fresh32 evaluation inputs remain unused. Old Stage14D375GPU-hour work remains HOLD; '
        'Stage14C-V remains unfinished.', '',
        'Provenance: `analysis/source_review_complete_v1.json`, `analysis/diagnostic_results_v1.json`, '
        '`audit/completed_execution_audit_v1.json`, `audit/resource_ledger.json`, '
        '`protocol/source_review_rubric_v1.json`, and `reports/casebook_v1.md`.']
    with (P/'reports/diagnostic_tables_v1.md').open('x') as out: out.write('\n'.join(report)+'\n')
    casebook=['# Exhaustive Stage14E2 source review', '', 'All24families and120logical conditions; raw reasoning remains in each immutable generation artifact.', '']
    for p in packets:
        casebook += ['## Family '+p['item_id'], '', '![Original source]('+p['image']+')', '',
            '**Question:** '+p['question'], '', '**Frozen source reference (offline only):** '+json.dumps(p['E_star_atoms'],ensure_ascii=False), '',
            '**Prefix:**', '', '```text',p['prefix'],'```','']
        for r in [r for r in records if r['item_id']==p['item_id']]:
            casebook += ['### '+r['condition'], '', f"{r['label']} / {r['coverage']} / {r['status']}", '', r['notes'], '',
                '```json', json.dumps(r.get('parsed'), ensure_ascii=False, indent=2), '```', '',
                'Raw: '+str(r['generation_path']), 'SHA256: '+str(r.get('generation_sha256')), '']
    with (P/'reports/casebook_v1.md').open('x') as out: out.write('\n'.join(casebook)+'\n')
    save(P/'audit/report_provenance_v1.json', dict(at=now(), files={
        str(P/'reports'/f):sha(P/'reports'/f) for f in ['diagnostic_tables_v1.md','casebook_v1.md']},
        no_new_method_or_follow_on=True))


if __name__ == '__main__': main()
