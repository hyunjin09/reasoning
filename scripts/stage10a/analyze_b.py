"""Frozen directional text-causality contrasts, with image-level uncertainty."""
import os
import numpy as np
import pandas as pd
from scripts.stage10a.common import ROOT,DATA,load,save,sha,now
from scripts.stage10a.edits import gate_b


def paired(values):
    x=np.asarray(values,dtype=float);assert len(x)
    ix=np.random.default_rng(920260927).integers(0,len(x),size=(4000,len(x)))
    return dict(point=float(x.mean()),ci95=np.quantile(x[ix].mean(1),[.025,.975]).tolist(),
                positive=int((x>0).sum()),negative=int((x<0).sum()),tied=int((x==0).sum()))


def summary(rows):
    images=sorted({r['image_id'] for r in rows});conditions=('original','counterfactual','delete','sham')
    indexed={(r['image_id'],r['condition']):r for r in rows};assert len(indexed)==4*len(images)
    def difference(c,d,field):return paired([float(indexed[i,c][field])-float(indexed[i,d][field]) for i in images])
    return dict(n_images=len(images),images=images,
        semantic_score={c:paired([indexed[i,c]['semantic_score'] for i in images]) for c in conditions},
        cf_minus_original=difference('counterfactual','original','semantic_score'),
        cf_minus_sham=difference('counterfactual','sham','semantic_score'),
        cf_minus_delete=difference('counterfactual','delete','semantic_score'),
        delete_minus_sham_accuracy=difference('delete','sham','correct'),
        completion={c:dict(n=len(images),correct=sum(indexed[i,c]['correct'] for i in images),
            follow_original=sum(indexed[i,c]['follows_original'] for i in images),follow_counterfactual=sum(indexed[i,c]['follows_counterfactual'] for i in images),
            unscorable=sum(indexed[i,c]['unscorable'] for i in images),capped=sum(indexed[i,c]['at_length_cap'] for i in images)) for c in conditions})


def main():
    assert os.environ.get('SLURM_JOB_ID')
    mp=ROOT/'audit/gate_b_manifest.json';manifest=load(mp);pp=ROOT/'audit/gate_b_review_packet.json'
    packet=load(pp);review=load(ROOT/'audit/gate_b_review.json')
    assert review['sealed'] and review['packet_sha256']==sha(pp) and packet['manifest_sha256']==sha(mp)
    reviewed={r['task_id']:r for r in review['rows']}
    events={r['query_id']:r for r in load(ROOT/'stage10a_event_selection.json')['rows']}
    gold={r['query_id']:r for r in load(DATA/'stage9a3_synthetic_dataset_manifest.json')['queries']};rows=[]
    for r in manifest['rows']:
        d=reviewed[r['task_id']];e=events[r['query_id']];g=gold[r['query_id']]
        assert sha(r['generation_path'])==d['generation_sha256'] and sha(r['result_path'])==d['result_sha256']
        count=e['task']['options'].get(d['option']);raw_count=e['task']['options'].get(d['raw_option'])
        compact={k:v for k,v in r.items() if k not in ('prefix_ids','prefix_text')}
        rows.append(dict(compact,option=d['option'],answer_count=count,answer=g['answer'],source_count=g['count'],
            fact_correct=r['original_count']==g['count'],correct=d['option']==g['answer'],
            follows_original=count==r['original_count'],follows_counterfactual=count==r['counterfactual_count'],
            semantic_score=int(count==r['counterfactual_count'])-int(count==r['original_count']),
            raw_semantic_score=int(raw_count==r['counterfactual_count'])-int(raw_count==r['original_count']),
            raw_correct=d['raw_option']==g['answer'],unscorable=d['option'] is None,at_length_cap=d['at_length_cap'],
            normal_eos=d['normal_eos'],tokens=d['tokens'],continuation_tokens=d['continuation_tokens']))
    assert len(rows)==96
    save(ROOT/'audit/gate_b_scored.json',dict(at=now(),rows=rows,review_sha256=sha(ROOT/'audit/gate_b_review.json')))
    dest=ROOT/'stage10a_text_counterfactual_results.parquet';assert not dest.exists();pd.DataFrame(rows).to_parquet(dest,index=False)
    result=summary(rows);result.update(at=now(),independent_unit='image',seed=920260927,bootstrap_draws=4000)
    result['by_attribute']={a:summary([r for r in rows if r['attribute']==a]) for a in ('color','shape')}
    result['correct_emitted_fact_stratum']=summary([r for r in rows if r['fact_correct']])
    result['raw_sensitivity']=summary([dict(r,semantic_score=r['raw_semantic_score'],correct=r['raw_correct']) for r in rows])
    result['gate_b_pass']=gate_b(result['cf_minus_original'],result['cf_minus_sham'])
    noise=result['cf_minus_delete'];deletion=result['delete_minus_sham_accuracy']
    result['noise_criterion']=noise['point']>=.10-1e-12 and noise['ci95'][0]>0
    result['deletion_criterion']=deletion['point']<0 or deletion['ci95'][0]>0 or deletion['ci95'][1]<0
    strata=[result['correct_emitted_fact_stratum'],*result['by_attribute'].values()]
    result['direction_agrees_across_strata']=all(s['cf_minus_original']['point']>0 and s['cf_minus_sham']['point']>0 for s in strata)
    result['H3_supported']=result['gate_b_pass'] and result['noise_criterion'] and result['deletion_criterion'] and result['direction_agrees_across_strata']
    save(ROOT/'audit/gate_b_inference.json',result)
    print('GATE_B',result['gate_b_pass'],'H3',result['H3_supported'],flush=True)
    for k in ('cf_minus_original','cf_minus_sham','cf_minus_delete','delete_minus_sham_accuracy','completion'):print(k,result[k],flush=True)


if __name__=='__main__':main()
