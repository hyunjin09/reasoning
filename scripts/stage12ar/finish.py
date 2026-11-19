"""Produce technical-only artifacts after a terminal predeclared gate."""
from pathlib import Path
import re
from scripts.stage12ar.common import ROOT, load, save, sha, now
from scripts.stage12ar.decision import decide
from scripts.stage12ar.resources import account


def main():
    dev = load(ROOT / 'stage12ar_development_manifest.json')
    val = load(ROOT / 'stage12ar_validation_manifest.json')
    d = load(ROOT / 'audit/development_D_review.json')
    c_path = ROOT / 'audit/development_C_review.json'
    v_path = ROOT / 'audit/validation_review.json'
    c = load(c_path) if c_path.exists() else None
    v = load(v_path) if v_path.exists() else None
    state = decide(d['gates']['D'], c['gates'] if c else None, v['gates'] if v else None)
    selection_path = ROOT / 'stage12ar_candidate_selection.json'
    if state == 'D_INVALID':
        assert c is None and v is None and not selection_path.exists()
        save(selection_path, dict(at=now(), correctness_opened=False, D_development_pass=False,
            selected_C=None, candidate_gates=None, status='NOT_RUN_D_DEVELOPMENT_FAILED',
            reason='Plan section15 stops immediately on D failure; no further D wording or C/validation generation.'))
    selection = load(selection_path)
    chosen = selection['selected_C']
    if state == 'C_INVALID':
        assert chosen is None and v is None
    if v:
        assert chosen in ['C0','C1'] and set(v['gates']) == {'D', chosen}
    reviews = [r for r in [d,c,v] if r is not None]
    assert all(r['correctness_opened'] is False for r in reviews)
    decisions = {row['task_id']: row for review in reviews for row in review['rows']}
    resources = account('closure', final=True)

    import pandas as pd
    def result(t):
        p = ROOT / 'generations' / t['task_id'] / 'generation.json'
        row = dict(task_id=t['task_id'], item_id=t['item_id'], family_id=t['family_id'],
            arm=t['arm'], answer_type=t['answer_type'], cap=t['cap'], status='NOT_RUN',
            format_valid=None, visible_reasoning=None, committed_final=None,
            cap_hit=None, severe_repetition=None, tokens=None, normal_stop=None,
            finish_reason=None, stop_reason=None, raw_decoded_response=None,
            generation_path=None, generation_sha256=None, quote=None, reason=None,
            request_latency_seconds=None, correctness_status='NOT_SCORED_TECHNICAL_ONLY')
        if p.exists():
            g = load(p)
            receipt = load(p.parent / 'result.json')
            assert sha(p) == receipt['generation_sha256'] == decisions[t['task_id']]['generation_sha256']
            r = decisions[t['task_id']]
            row.update({k:r[k] for k in ['format_valid','visible_reasoning','committed_final','cap_hit','severe_repetition','tokens','normal_stop','quote','reason']})
            row.update(status='COMPLETED_REVIEWED', raw_decoded_response=g['raw_decoded_response'],
                finish_reason=g['finish_reason'], stop_reason=str(g['stop_reason']),
                request_latency_seconds=g['request_latency_seconds'],
                generation_path=str(p), generation_sha256=sha(p))
        return row
    development = [result(t) for t in dev['rows']]
    validation_tasks = [t for t in val['prospective_tasks'] if t['arm'] in ['D', chosen]]
    validation = [result(t) for t in validation_tasks]
    if chosen is None:
        for i in val['ids']:
            src = next(t for t in val['prospective_tasks'] if t['item_id'] == i and t['arm'] == 'C0')
            t = dict(src, task_id=f'validation_C_UNSELECTED_{i}', arm='C_UNSELECTED')
            validation.append(result(t))
    assert len(development) == 36 and len(validation) == 24
    if v is None:
        assert all(r['status'] == 'NOT_RUN' for r in validation)
    for name, rows in [('development', development), ('validation', validation)]:
        path = ROOT / f'stage12ar_{name}_results.parquet'
        assert not path.exists()
        pd.DataFrame(rows).to_parquet(path, index=False)
    completed = sum(r['status'] == 'COMPLETED_REVIEWED' for r in development + validation)
    assert completed == len(decisions) <= 60
    endings = dict(CONTRACT_VALID='CONTRACT_VALID — Stage12A scientific rerun is justified',
        D_INVALID='D_INVALID — do not rerun Stage12A', C_INVALID='C_INVALID — do not rerun Stage12A',
        CONTRACT_UNSTABLE='CONTRACT_UNSTABLE — do not rerun Stage12A')
    components = {} if not v else {a: ('VALID' if r['pass'] else 'D_INVALID' if a == 'D' else 'C_INVALID') for a,r in v['gates'].items()}
    save(ROOT / 'stage12ar_contract_decision.json', dict(at=now(), decision=state,
        final_line=endings[state], correctness_opened=False, selected_C=chosen,
        development_D=d['gates']['D'], development_C=c['gates'] if c else None,
        validation=v['gates'] if v else None, validation_component_status=components,
        source_families_preserved=61, frozen_facts_preserved=157,
        E_calls=0, actual_calls=completed, scientific_endpoints='NOT_EVALUATED',
        scientific_rerun_launched=False, future_scientific_sensitivity='If separately authorized, exclude all24 technical families in a sensitivity analysis.'))

    comparison = Path('reports/stage12ar/v1')
    comparison.mkdir(parents=True, exist_ok=True)
    index = ['# Stage12A-R full technical responses', '',
             'Exact prompts and complete responses. Technical labels only; correctness is unscored.', '',
             '| Phase / case | Outputs |', '|---|---|']
    for phase, tasks in [('development',dev['rows']), ('validation',validation_tasks)]:
        for i in sorted({t['item_id'] for t in tasks}, key=int):
            actual = [t for t in tasks if t['item_id'] == i and t['task_id'] in decisions]
            if not actual:
                continue
            body = [f'# {phase}: case {i}', '']
            for t in actual:
                p = ROOT / 'generations' / t['task_id'] / 'generation.json'
                g = load(p)
                s = g['raw_decoded_response']
                fence = '`' * max(3, 1 + max([len(x) for x in re.findall(r'`+', s + t['prompt'])] or [0]))
                body += [f"## {t['arm']}", '',
                    f"{g['tokens']} tokens; stop={g['finish_reason']}; no correctness score.", '',
                    'Exact prompt:', '', fence + 'text', t['prompt'], fence, '',
                    'Full response:', '', fence + 'text', s, fence, '',
                    f"[Original image]({t['image']}) · [Raw JSON]({p.resolve()})", '']
            name = f'{phase}_{i}.md'
            with (comparison / name).open('x') as f:
                f.write('\n'.join(body))
            index.append(f'| {phase} / {i} | [Full responses]({name}) |')
    with (comparison / 'index.md').open('x') as f:
        f.write('\n'.join(index) + '\n')

    def table(gates, arms):
        lines = ['| Arm | Format | Visible reasoning | Finals | Caps | Severe repetition | Median tokens | Gate |',
                 '|---|---:|---:|---:|---:|---:|---:|---|']
        for a in arms:
            if not gates or a not in gates:
                lines.append(f'| {a} | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | — | NOT_RUN |')
                continue
            r = gates[a]; s = r['summary']
            cells = [str(s[k]) + '/12' for k in ['format_valid','visible_reasoning','committed_final','cap_hit','severe_repetition']]
            lines.append('| ' + ' | '.join([a,*cells,str(s['median_tokens']),'PASS' if r['pass'] else 'FAIL']) + ' |')
        return lines
    gates = dict(d['gates'], **(c['gates'] if c else {}))
    why = ('D failed development; C0/C1 and untouched validation were not run under section15.' if state == 'D_INVALID'
        else 'Neither predeclared C candidate passed; untouched validation was not run.' if chosen is None
        else f'{chosen} selected using the frozen completion/format/length priority; no correctness or answer quality used.')
    summary = ['# Stage12A-R contract validation', '', f'**{state}**. This is a technical result; the Lost-Keys hypothesis remains untested.', '',
        'The original61 families,157 E* facts, questions/images/source answers, E requests and scientific thresholds '
        'remain unchanged. Stage12A artifacts were not modified. No E, task correctness, evidence correctness, rescue '
        'or scientific GO/NO-GO endpoint was evaluated.', '',
        '## 1–3. Development: D, C0 and C1', '', *table(gates, ['D','C0','C1']), '',
        'One exact D suffix with64-token cap; exactly two predeclared conditional C candidates with32768-token cap. '
        'All arms retain the same pinned2B Instruct checkpoint, BF16/vLLM backend, image preprocessing, '
        'sampling(.7/.8/top20/repetition1/presence1.5) and Stage12A per-family seed policy. '
        'No additional prompt or budget search was performed.', '',
        'Format and commitment are distinct. D fails format if it shows intermediate calculations even when a '
        'final exists. C requires substantive reasoning and terminal commitment. C0 has no literal final-marker '
        'requirement; C1 requires its requested terminal line. Severe repetition is a semantic cycle review '
        'supported by exact32-gram metrics, including outputs that eventually stop normally. No answer correctness '
        'enters these labels.', '',
        '## 4. Selected C contract', '', why, '',
        'Priority: fewer severe repetitions, fewer caps, more finals, more strict format-valid responses, '
        'shorter median generated length, then C0. Numerical gates are unchanged.', '',
        '## 5. Untouched validation', '',
        'The12 validation families were frozen before any new generation using SHA256(stage12ar-validation-v1|family_id): '
        'five MC and seven open-ended, disjoint from the fixed12 development families. Selection used only identity '
        'and answer type, with no difficulty, subject or model behavior.', '',
        'Validation IDs: ' + ', '.join(val['ids']) + '.', '',
        *table(v['gates'] if v else None, ['D', chosen or 'C_UNSELECTED']), '',
        'No prompt modification is allowed after validation. A failure after passing development is reported '
        'as CONTRACT_UNSTABLE, with D/C component failures preserved in the decision JSON.', '',
        '## Resources and provenance', '',
        f'{completed} actual generation calls; **{resources["allocated_gpu_hours"]:.6f} allocated GPU-hours** '
        'including startup, failures and teardown. All stage allocations released. Target<1.5, hard2.5GPUh. '
        'No model/dataset download or environment installation required.', '',
        'Exact prompts/manifests and prospective hashes are saved alongside this report. '
        '`audit/prospective_draft1/` preserves an unused pre-generation draft whose inherited Stage12A '
        'configuration metadata was corrected before launch; prompts, cases and requested Stage12A-R gates did not change. '
        'Completed raw text, token IDs, actual chat inputs and receipts are under `generations/`. '
        '[Read all responses](../../../reports/stage12ar/v1/index.md). '
        'Parquet NOT_RUN/null entries are unexecuted conditions, never incorrect answers.', '',
        '## 6. Decision', '',
        'No scientific rerun was launched. Technical success would justify a separately authorized61-family '
        'Stage12A scientific rerun, including sensitivity excluding all24 technical families. Technical failure '
        'does not establish absence of Lost Keys, reasoning benefits or visual-access bottlenecks.', '', endings[state]]
    with (ROOT / 'stage12ar_summary.md').open('x') as f:
        f.write('\n'.join(summary) + '\n')
    print('STAGE12AR_CLOSED', state, completed, resources['allocated_gpu_hours'])


if __name__ == '__main__': main()
