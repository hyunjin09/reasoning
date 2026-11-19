"""Image-equal factorial marginal effects, with unchanged semantic score."""
import os
import pandas as pd
from scripts.stage10a.common import ROOT,OLD,load,save,sha,now
from scripts.stage10a.analyze_b import paired


def summary(rows):
    images=sorted({r['image_id'] for r in rows});ix={(r['image_id'],r['condition']):r for r in rows}
    assert len(ix)==4*len(images)
    et=[];ei=[];interaction=[]
    for i in images:
        a,b,c,d=[ix[i,k]['semantic_score'] for k in ('I0T0','I1T0','I0T1','I1T1')]
        et.append(((c-a)+(d-b))/2);ei.append(((b-a)+(d-c))/2);interaction.append(d-b-c+a)
    return dict(n_images=len(images),images=images,E_text=paired(et),E_image=paired(ei),
        text_minus_image=paired([t-i for t,i in zip(et,ei)]),interaction=paired(interaction),
        completion={c:dict(n=len(images),follow_original=sum(ix[i,c]['follows_original'] for i in images),
            follow_counterfactual=sum(ix[i,c]['follows_counterfactual'] for i in images),
            correct_current_image=sum(ix[i,c]['correct_current_image'] for i in images),
            unscorable=sum(ix[i,c]['unscorable'] for i in images),capped=sum(ix[i,c]['at_length_cap'] for i in images))
            for c in ('I0T0','I1T0','I0T1','I1T1')})


def main():
    assert os.environ.get('SLURM_JOB_ID')
    mp=ROOT/'audit/dominance_manifest.json';m=load(mp);pp=ROOT/'audit/dominance_review_packet.json';packet=load(pp)
    review=load(ROOT/'audit/dominance_review.json');assert review['sealed'] and review['packet_sha256']==sha(pp) and packet['manifest_sha256']==sha(mp)
    reviewed={r['task_id']:r for r in review['rows']};rows=[]
    for r in m['rows']:
        d=reviewed[r['task_id']];assert sha(r['generation_path'])==d['generation_sha256'] and sha(r['result_path'])==d['result_sha256']
        count=r['task']['options'].get(d['option']);raw_count=r['task']['options'].get(d['raw_option'])
        compact={k:v for k,v in r.items() if k not in ('task','prefix_ids','prefix_text')}
        rows.append(dict(compact,option=d['option'],answer_count=count,
            follows_original=count==r['original_count'],follows_counterfactual=count==r['counterfactual_count'],
            correct_current_image=count==(r['counterfactual_count'] if r['image_cf'] else r['original_count']),
            semantic_score=int(count==r['counterfactual_count'])-int(count==r['original_count']),
            raw_semantic_score=int(raw_count==r['counterfactual_count'])-int(raw_count==r['original_count']),
            unscorable=d['option'] is None,at_length_cap=d['at_length_cap'],normal_eos=d['normal_eos'],tokens=d['tokens']))
    save(ROOT/'audit/dominance_scored.json',dict(at=now(),rows=rows,review_sha256=sha(ROOT/'audit/dominance_review.json')))
    dest=ROOT/'stage10a_image_text_2x2.parquet';assert not dest.exists();pd.DataFrame(rows).to_parquet(dest,index=False)
    result=summary(rows);result.update(at=now(),seed=920260927,bootstrap_draws=4000,independent_unit='image',anchor='post',
        pre_measured=False,effect_definition='E_text=.5[(I0T1-I0T0)+(I1T1-I1T0)]; E_image=.5[(I1T0-I0T0)+(I1T1-I0T1)] on signed answer-count score.')
    result['by_attribute']={a:summary([r for r in rows if r['attribute']==a]) for a in ('color','shape')}
    result['raw_sensitivity']=summary([dict(r,semantic_score=r['raw_semantic_score']) for r in rows])
    d=result['text_minus_image'];result['post_text_dominance_supported']=d['point']>=.10-1e-12 and d['ci95'][0]>0
    save(ROOT/'audit/dominance_inference.json',result)
    print('POST_DOMINANCE',result['post_text_dominance_supported'],'TEXT',result['E_text'],'IMAGE',result['E_image'],'DIFFERENCE',d,flush=True)
    print('COMPLETION',result['completion'],flush=True)


if __name__=='__main__':main()
