"""Read-only joins of sealed source judgments and completed final responses."""
import csv
import json
from pathlib import Path
from scripts.stage14e.common import P, load, rows, save, sha, now
from scripts.stage14e.reporting import markdown_blocks


def link(path, label=None):
    return f'[{label or Path(path).name}]({Path(path).resolve()})'


def block(value):
    return '```json\n' + json.dumps(value, ensure_ascii=False, indent=2) + '\n```'


def main():
    registry = load(P / 'manifests/final_execution_registry_v1.json')
    states_path = Path(registry['acquisition_root']) / 'acquisition_states.json'
    states = load(states_path)
    families = {r['item_id']: r for r in rows(P / 'inference/evaluation_families.jsonl')}
    refs = {r['item_id']: r for r in load(P / 'offline/evaluation_source_references_v1.json')}
    qc = {r['item_id']: r for r in load(P / 'annotations/evaluation_source_QC_v1.json')['rows']}
    acquired = load(P / 'annotations/evaluation_source_review_v1.json')['records']
    scored = load(P / 'analysis/final_scored_rows_v1.json')['records']
    acq = {(r['item_id'], r['condition']): r for r in acquired}
    finals = {(r['item_id'], r['arm']): r for r in scored}
    assert len(acq) == len(finals) == 96 and len(families) == 32
    records, table = [], []
    book = ['# Stage14E: all32 final-evaluation source/output casebook',
        'Frozen hash order; every family included. Source judgments were sealed before new solver finals were opened. '
        'Single AI reviewer, condition-visible; these are qualitative source audits, not independent human labels. '
        'The original image, offline E* reference, model claims and final scores remain distinct. '
        'No-image helper outputs are not new visual acquisition. Native aliases are not successful helper executions. '
        'N=native; S=original SAVA-style reader; M=Source-Premise Ledger. '
        'No ROI or localization module is used in this final experiment; predicted regions are therefore not applicable. '
        'Earlier localization records remain in the diagnostic and SAVA casebooks.']
    for i in registry['families']:
        family, ref = families[i], refs[i]
        assert sha(family['image']) == ref['image_sha256']
        a = {c: acq[i, c] for c in ['S', 'M', 'M_noimage']}
        f = {c: finals[i, c] for c in ['N', 'S', 'M']}
        provenance = {}
        for c in ['S', 'M']:
            p = states[i][c]['query_generation_path']
            provenance[c + '_controller'] = dict(path=p, sha256=sha(p),
                raw_output=load(p)['raw_decoded_response'])
        for c, r in a.items():
            if r['generation_path']:
                assert sha(r['generation_path']) == r['generation_sha256']
        for c, r in f.items():
            assert sha(r['generation_path']) == r['generation_sha256']
        record = dict(item_id=i, family_id=family['family_id'], source=ref,
            prefix_qc=qc[i], runtime_family=family, acquisition_state=states[i],
            acquisition_judgments=a, solver_results=f, controller_provenance=provenance,
            predicted_region=None, region_not_applicable_reason='Final selected method uses original full image only')
        records.append(record)
        flat = dict(item_id=i, family_id=family['family_id'], image=family['image'],
            prefix_state=qc[i]['prefix_state'], structured_source=ref['has_structured_atom'])
        for c in ['S', 'M', 'M_noimage']:
            flat[c + '_evidence_label'] = a[c]['label']
        for c in ['N', 'S', 'M']:
            flat[c + '_answer'] = f[c]['reviewed_answer']
            flat[c + '_correct'] = f[c]['correct']
            flat[c + '_execution'] = f[c]['status']
        table.append(flat)
        book.extend([f'\n## Family {i}',
            f"Family `{family['family_id']}`; source {link(family['image'], 'original image')}; "
            f"SHA256 `{ref['image_sha256']}`. Source annotation {link(ref['source_receipt'])}.",
            '**Original question**\n\n' + family['question'],
            '**Offline source reference — never a runtime input**\n\n' + block(ref['E_star_atoms']),
            '**Frozen512-token prefix**\n\n```text\n' + family['prefix'] + '\n```',
            '**Prospective prefix/source review**\n\n' + block(qc[i]),
            '**Controller, provenance, validation and selected targets**\n\n' +
                block({c: states[i][c] for c in ['S', 'M']}),
            '**Exact controller outputs**\n\n' + block(provenance)])
        for c in ['S', 'M', 'M_noimage']:
            r = a[c]
            book.extend([f'### {c} acquisition', block(r)])
            if r['generation_path']:
                book.append('Exact runtime prompt, image preprocessing and token records: ' +
                    link(Path(r['generation_path']).with_name('input.json'), 'input') + '; ' +
                    link(r['generation_path'], 'generation') + '.')
        book.append('| Arm | Reviewed final | Correct | Execution | Exact input / generation |\n|---|---|---|---|---|')
        for c in ['N', 'S', 'M']:
            r = f[c]
            answer = str(r['reviewed_answer']).replace('|', '\\|').replace('\n', ' ')
            book.append(f"| {c} | {answer} | {r['correct']} | {r['status']} | " +
                link(Path(r['generation_path']).with_name('input.json'), 'input') + ' / ' +
                link(r['generation_path'], 'raw continuation') + ' |')
        book.append('Parser/review separation, gold, seeds, aliases, suffix and output hashes:\n\n' + block(f))
    save(P / 'analysis/final_casebook_v1.json', dict(at=now(), records=records,
        source_review_sha256=sha(P / 'annotations/evaluation_source_review_v1.json'),
        final_scoring_sha256=sha(P / 'analysis/final_scored_rows_v1.json'), new_annotations=False))
    with (P / 'analysis/final_case_index_v1.csv').open('x') as out:
        w = csv.DictWriter(out, fieldnames=list(table[0])); w.writeheader(); w.writerows(table)
    with (P / 'reports/final32_casebook_v1.md').open('x') as out:
        out.write(markdown_blocks(book))
    print('All32 source/output cases joined;96 helper judgments,96 logical solver outcomes')


if __name__ == '__main__':
    main()
