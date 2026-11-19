"""Paired image-level sufficiency/necessity transitions and the frozen Gate A."""
import os
import numpy as np
import pandas as pd
from scripts.stage10a.common import ROOT,OLD,DATA,load,save,sha,now
from scripts.stage10a.protocol import gate_a


def summary(rows):
    images=sorted({r['image_id'] for r in rows});anchors=('pre','emit','post')
    conditions=('text_only','image_off')
    ix=np.random.default_rng(920260927).integers(0,len(images),size=(4000,len(images)))
    result=dict(n_images=len(images),images=images,independent_unit='image',seed=920260927,bootstrap_draws=4000)
    for condition in conditions:
        values=[];full=[]
        for image in images:
            rr=[r for r in rows if r['image_id']==image and r['condition']==condition]
            assert len(rr)==3 and len({r['anchor'] for r in rr})==3
            values.append([float(next(r['correct'] for r in rr if r['anchor']==a)) for a in anchors])
            full.append(float(rr[0]['full_correct']))
        values=np.array(values);full=np.array(full);draws=values[ix].mean(1);means=values.mean(0)
        differences=values[:,2]-values[:,0];bd=draws[:,2]-draws[:,0]
        result[condition]=dict(accuracy={a:float(means[j]) for j,a in enumerate(anchors)},
            accuracy_ci95={a:np.quantile(draws[:,j],[.025,.975]).tolist() for j,a in enumerate(anchors)},
            post_minus_pre=dict(point=float(differences.mean()),ci95=np.quantile(bd,[.025,.975]).tolist(),
                images_improved=int((differences>0).sum()),images_worsened=int((differences<0).sum()),images_tied=int((differences==0).sum())),
            emit_minus_pre=dict(point=float((values[:,1]-values[:,0]).mean()),ci95=np.quantile(draws[:,1]-draws[:,0],[.025,.975]).tolist()),
            full_accuracy=float(full.mean()),damage={a:float(full.mean()-means[j]) for j,a in enumerate(anchors)},
            damage_ci95={a:np.quantile((full[:,None]-values)[ix].mean(1)[:,j],[.025,.975]).tolist() for j,a in enumerate(anchors)})
    return result


def main():
    assert os.environ.get('SLURM_JOB_ID')
    mp=ROOT/'audit/gate_a_manifest.json';manifest=load(mp)
    pp=ROOT/'audit/gate_a_review_packet.json';packet=load(pp);review=load(ROOT/'audit/gate_a_review.json')
    assert review['sealed'] and review['packet_sha256']==sha(pp) and packet['manifest_sha256']==sha(mp)
    reviewed={r['task_id']:r for r in review['rows']}
    events={r['query_id']:r for r in load(ROOT/'stage10a_event_selection.json')['rows']}
    gold={r['query_id']:r for r in load(DATA/'stage9a3_synthetic_dataset_manifest.json')['queries']}
    baseline={r['query_id']:r for r in load(OLD/'stage9a5_thinking_full_baseline.json')['rows']}
    rows=[]
    for r in manifest['rows']:
        d=reviewed[r['task_id']];e=events[r['query_id']];g=gold[r['query_id']]
        assert sha(r['generation_path'])==d['generation_sha256'] and sha(r['result_path'])==d['result_sha256']
        rows.append(dict(r,option=d['option'],raw_option=d['raw_option'],answer=g['answer'],source_count=g['count'],
            emitted_count=e['emitted_count'],fact_correct=e['emitted_count']==g['count'],full_correct=baseline[r['query_id']]['correct'],
            correct=d['option']==g['answer'],raw_correct=d['raw_option']==g['answer'],
            unscorable=d['option'] is None,at_length_cap=d['at_length_cap'],normal_eos=d['normal_eos'],
            tokens=d['tokens'],continuation_tokens=d['continuation_tokens'],post_contains_option_binding=e['post_contains_option_binding']))
    assert len(rows)==144
    save(ROOT/'audit/gate_a_scored.json',dict(at=now(),rows=rows,review_sha256=sha(ROOT/'audit/gate_a_review.json')))
    for condition,name in [('text_only','stage10a_text_prefix_sufficiency.parquet'),('image_off','stage10a_visual_necessity.parquet')]:
        path=ROOT/name;assert not path.exists();pd.DataFrame([r for r in rows if r['condition']==condition]).to_parquet(path,index=False)
    result=summary(rows)
    result['by_attribute']={a:summary([r for r in rows if r['attribute']==a]) for a in ('color','shape')}
    result['without_post_option_binding']=summary([r for r in rows if not r['post_contains_option_binding']])
    result['correct_emitted_fact_stratum']=summary([r for r in rows if r['fact_correct']])
    result['raw_sensitivity']=summary([dict(r,correct=r['raw_correct']) for r in rows])
    v=result['image_off']['post_minus_pre'];t=result['text_only']['post_minus_pre']
    result.update(at=now(),gate_a_pass=gate_a(v['point'],t['point']),
        H1_supported=v['point']>=.10-1e-12 and v['ci95'][0]>0,H2_supported=t['point']>=.10-1e-12 and t['ci95'][0]>0,
        gate_definition='Either primary transition point>=10pp permits edits; neither means STOP. Full claim requires both substantial transitions with95% lower>0.',
        completion={f'{c}/{a}':dict(n=24,correct=sum(r['correct'] for r in rows if r['condition']==c and r['anchor']==a),
            unscorable=sum(r['unscorable'] for r in rows if r['condition']==c and r['anchor']==a),
            capped=sum(r['at_length_cap'] for r in rows if r['condition']==c and r['anchor']==a))
            for c in ('text_only','image_off') for a in ('pre','emit','post')})
    save(ROOT/'audit/gate_a_inference.json',result)
    print('GATE_A',result['gate_a_pass'],'H1',v,'H2',t,flush=True)
    print('COMPLETION',result['completion'],flush=True)


if __name__=='__main__':main()
