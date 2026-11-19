"""Source-only casebook with exact helper quotes and separate review panels."""
import json
from collections import Counter
from scripts.stage14d1_pilot.common import P, load, rows, save, sha, now


def main():
    fixed={r['item_id'] for r in load(P/'protocol/offline_review_selection.json')['selected']}
    flagged=set(load(P/'annotations/flagged_readout_selection_v8.json')['item_ids'])
    source={r['item_id']:r for r in rows(P/'inference/families.jsonl')}
    cases=[]
    for path in sorted((P/'annotations/readouts').glob('*.json'), key=lambda p:int(p.stem)):
        r=load(path);item=r['item_id']
        panel='fixed_24' if item in fixed else 'source_flagged_17' if item in flagged else 'additional_technical_5'
        cases.append(dict(item_id=item,family_id=r['family_id'],panel=panel,image=source[item]['image'],
            query_review=load(P/'annotations/query_only'/f'{item}.json'),
            address_review=load(P/'annotations/address_only'/f'{item}.json'),
            readout_review=r,annotation_path=str(path),annotation_sha256=sha(path)))
    save(P/'analysis/source_casebook_v8.json',dict(at=now(),cases=cases,
        no_solver_outcomes_opened=True,panels=dict(Counter(r['panel'] for r in cases))))
    lines=['# Source-only SAVA casebook','',
        'These reviews were sealed before scientific final-answer inspection. The fixed 24-family panel supports the planned sample summary. The additional 17 source-flagged and five technical cases are descriptive. One AI reviewer inspected original images; no independent reliability estimate is available.','',
        'Correctness here concerns explicitly stated source facts, not latent acquisition or final-answer correctness. Abstentions, unavailable targets and ambiguous coordinates are not counted as explicit visual errors. Q helper receives no additional image; the Q solver retains the original image-conditioned context.','']
    for r in cases:
        lines += [f"## Item {r['item_id']} — {r['panel']}",'',f"Family: `{r['family_id']}`. Original image: `{r['image']}`.",'',
            f"Query: **{r['query_review']['label']}**. {r['query_review']['notes']}",'',
            f"Address: **{r['address_review']['label']}**. {r['address_review']['notes']}",'']
        for x in r['readout_review']['records']:
            lines += [f"### {x['arm']}: {x['status']}",'',x['note'],'',
                'Exact helper record:','```json',json.dumps(x['readout'],ensure_ascii=False,indent=2),'```','',
                f"Raw artifact: `{x['generation_path']}`; SHA256 `{x['generation_sha256']}`; helper alias `{x['alias_of']}`.",'']
    p=P/'reports/source_casebook_v8.md'
    with p.open('x') as f:f.write('\n'.join(lines))
    print('Source casebook:',len(cases),'families; no solver outcomes loaded')

if __name__=='__main__':main()
