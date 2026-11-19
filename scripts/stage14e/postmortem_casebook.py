"""Complete retrospective provenance packet; preserves distinct annotation versions."""
import csv,json
from scripts.stage14e.common import P, load, rows, save, sha, now


def main():
    joined=load(P/'analysis/sava72_joined.json')
    taxonomy={r['item_id']:r for r in load(P/'analysis/postmortem_family_taxonomy_v1.json')}
    supplement=load(P/'annotations/postmortem_remaining20_source_review_v1.json')['records']
    source={r['item_id']:r for r in rows('outputs/stage14d0/inventory/source_and_raw_output_manifest.jsonl')}
    print('source fields',list(source[joined[0]['item_id']]))
    old_table=list(csv.DictReader((P/'analysis/postmortem_stage_matrix_v1.csv').open()))
    full=[];book=['# All72 SAVA retrospective source casebook','One AI reviewer; condition-visible retrospective development evidence. Existing52 source reviews and new20 supplementary reviews use distinct rubrics. No harmonized pooled new-evidence rate is claimed. Unmentioned/ambiguous evidence is not an acquisition failure. Exact causal mediation of final changes is not identified.']
    for r in joined:
        i=r['item_id'];meta=taxonomy[i]
        reviews=r['readout_review']['records'] if r['readout_review'] else [s for s in supplement if s['item_id']==i]
        assert len(reviews)==5,(i,len(reviews))
        version='historical52' if r['readout_review'] else 'supplement20_v1'
        qi=next(q for q in reviews if q.get('arm',q.get('condition'))=='QI')
        tab=dict(next(t for t in old_table if t['item_id']==i),source_review_version=version,source_review_exact=json.dumps(qi,ensure_ascii=False))
        full.append(tab)
        book.extend([f'\n## Family {i}',f"Source: `{r['image']}`; SHA256 `{r['image_sha256']}`. Family `{r['family_id']}`.",
            'Question:\n\n'+r['question'],'Frozen prefix:\n\n```text\n'+r['prefix']+'\n```',
            f"Observable state: **{meta['observable_prefix_state']}**. {meta['rationale']}",
            'Controller and predicted address:\n\n```json\n'+json.dumps({k:r['acquisition'].get(k) for k in ['query','compiled_query','address','views','query_generation','locator_generation']},ensure_ascii=False,indent=2)+'\n```',
            'Source annotation and exact reference provenance:\n\n```json\n'+json.dumps({k:v for k,v in source[i].items() if k in ['E_star_atoms','image','source_path','source_annotation_path','family_id','item_id']},ensure_ascii=False,indent=2)+'\n```',
            f'Source review version: `{version}`. Full source judgments with readout quotes/paths:\n\n```json\n'+json.dumps(reviews,ensure_ascii=False,indent=2)+'\n```',
            'Final outcomes (historical, already observed):\n\n| Arm | Correct | Status | Exact raw continuation |\n|---|---|---|---|'])
        for s in r['solver_rows']:
            book.append(f"| {s['arm']} | {s['correct']} | {s['final_status']} | `{s['generation_path']}` |")
        book.append(f"Any-arm regression: {meta['any_regression']}; primary QI rescue: {meta['QI_rescue']}. Acquisition record `{r['acquisition_path']}`, SHA256 `{r['acquisition_sha256']}`.")
    assert len(full)==72 and len({r['item_id'] for r in full})==72
    path=P/'analysis/postmortem_stage_matrix_v2.csv'
    with path.open('x') as f:
        writer=csv.DictWriter(f,fieldnames=list(full[0]));writer.writeheader();writer.writerows(full)
    path=P/'reports/sava_all72_casebook_v1.md'
    with path.open('x') as f:f.write('\n\n'.join(book)+'\n')
    save(P/'audit/postmortem_full_coverage_v1.json',dict(at=now(),families=72,logical_helper_reviews=360,
         historical_review_families=52,supplementary_review_families=20,table_sha256=sha(P/'analysis/postmortem_stage_matrix_v2.csv'),
         casebook_sha256=sha(path),pooled_relabeling=False,raw_historical_artifacts_modified=False))

if __name__=='__main__':main()
