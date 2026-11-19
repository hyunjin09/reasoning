"""Secondary A3 carrier test; frozen before any new edit outcomes."""
import os
from scripts.stage10ar.common import ROOT,load,save,sha,now
from scripts.stage10a.analyze_b import paired


def main():
    assert os.environ.get('SLURM_JOB_ID')
    mp=ROOT/'audit/optional_manifest.json';m=load(mp)
    assert m['source_sha256']['scripts/stage10ar/analyze_optional.py']==sha(__file__)
    pp=ROOT/'audit/optional_review_packet.json';review=load(ROOT/'audit/optional_review.json')
    assert review['sealed'] and review['packet_sha256']==sha(pp) and load(pp)['manifest_sha256']==sha(mp)
    reviewed={r['task_id']:r for r in review['rows']}
    events={r['query_id']:r for r in load(ROOT/'stage10ar_anchor_annotations.json')['rows']};rows=[]
    for r in m['rows']:
        d=reviewed[r['task_id']];e=events[r['query_id']]
        assert sha(r['generation_path'])==d['generation_sha256'] and sha(r['result_path'])==d['result_sha256']
        count=e['task']['options'].get(d['option']);original=count==r['original_count'];cf=count==r['counterfactual_count']
        rows.append(dict(task_id=r['task_id'],image_id=r['image_id'],query_id=r['query_id'],attribute=r['attribute'],condition=r['condition'],
            option=d['option'],answer_count=count,original_count=r['original_count'],counterfactual_count=r['counterfactual_count'],
            follows_original=original,follows_counterfactual=cf,semantic_score=int(cf)-int(original),unscorable=d['option'] is None,
            at_length_cap=d['at_length_cap'],tokens=d['tokens']))
    def summary(rs):
        images=sorted({r['image_id'] for r in rs});by={(r['image_id'],r['condition']):r for r in rs}
        return dict(n_images=len(images),
            cf_minus_original=paired([by[i,'counterfactual']['semantic_score']-by[i,'original']['semantic_score'] for i in images]),
            cf_minus_sham=paired([by[i,'counterfactual']['semantic_score']-by[i,'sham']['semantic_score'] for i in images]),
            completion={c:dict(n=len(images),follow_original=sum(by[i,c]['follows_original'] for i in images),
                follow_counterfactual=sum(by[i,c]['follows_counterfactual'] for i in images),unscorable=sum(by[i,c]['unscorable'] for i in images),
                capped=sum(by[i,c]['at_length_cap'] for i in images)) for c in ('original','counterfactual','sham')})
    result=summary(rows);result.update(at=now(),executed=True,rows=rows,independent_unit='image',bootstrap_draws=4000,seed=920260927,
        by_attribute={a:summary([r for r in rows if r['attribute']==a]) for a in ('color','shape')},
        manifest_sha256=sha(mp),review_sha256=sha(ROOT/'audit/optional_review.json'),
        interpretation_boundary='Secondary12-image local-inventory edit; not an extra primary endpoint. Prior repeated evidence can conflict with the edit.')
    save(ROOT/'stage10ar_a3_text_edit.json',result)
    print({k:v for k,v in result.items() if k in ('cf_minus_original','cf_minus_sham','completion')},flush=True)


if __name__=='__main__':main()
