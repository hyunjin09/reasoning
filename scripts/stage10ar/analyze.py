"""Frozen paired localization endpoints; no selection from intervention outcomes."""
import os
import numpy as np
import pandas as pd
from scripts.stage10ar.common import ROOT,PRIOR,load,save,sha,now
from scripts.stage10ar.protocol import contrasts,earliest_transition,multiplicity_interval

ASSAYS=('image_off','text_only')
ANCHORS=tuple(f'A{i}' for i in range(5))


def panel(rows):
    images=sorted({r['image_id'] for r in rows});x=np.full((len(images),2,5),np.nan)
    for r in rows:x[images.index(r['image_id']),ASSAYS.index(r['condition']),ANCHORS.index(r['anchor'])]=float(r['correct'])
    assert np.isfinite(x[:,:,[0,1,3,4]]).all()
    return images,x


def summarize(rows):
    images,x=panel(rows);n=len(images);ix=np.random.default_rng(920260927).integers(0,n,size=(4000,n))
    delta=contrasts(x);boot=delta[ix].mean(1);adjusted=multiplicity_interval(boot);ordinary=np.quantile(boot,[.025,.975],axis=0)
    result=dict(n_images=n,images=images,primary={})
    for j,name in enumerate(('P1','P2','P3','P4')):
        d=delta[:,j];result['primary'][name]=dict(point=float(d.mean()),ci95=ordinary[:,j].tolist(),
            familywise95_ci=adjusted[:,j].tolist(),positive=int((d>0).sum()),negative=int((d<0).sum()),tied=int((d==0).sum()))
    result['curves']={}
    for k,assay in enumerate(ASSAYS):
        result['curves'][assay]={}
        for j,a in enumerate(ANCHORS):
            values=x[:,k,j];values=values[np.isfinite(values)];m=len(values)
            if not m:result['curves'][assay][a]=None;continue
            indices=np.random.default_rng(920260927).integers(0,m,size=(4000,m));bd=values[indices].mean(1)
            result['curves'][assay][a]=dict(n=m,accuracy=float(values.mean()),accuracy_ci95=np.quantile(bd,[.025,.975]).tolist(),
                necessity=float(1-values.mean()) if assay=='image_off' else None,
                necessity_ci95=np.quantile(1-bd,[.025,.975]).tolist() if assay=='image_off' else None)
    avail=np.isfinite(x[:,0,2])
    result['A2_secondary']=None
    if avail.any():
        y=x[avail];d=np.column_stack((y[:,0,3]-y[:,0,2],y[:,1,3]-y[:,1,2]));m=len(y)
        indices=np.random.default_rng(920260927).integers(0,m,size=(4000,m));bb=d[indices].mean(1)
        result['A2_secondary']=dict(n_images=m,visual_point=float(d[:,0].mean()),text_point=float(d[:,1].mean()),
            visual_ci95=np.quantile(bb[:,0],[.025,.975]).tolist(),text_ci95=np.quantile(bb[:,1],[.025,.975]).tolist())
    return result


def robustness(rows):
    images,x=panel(rows);d=contrasts(x);by={r['image_id']:r for r in rows}
    groups={}
    for i in images:
        r=by[i]
        for key in (f"count:{r['source_count']}",f"{r['attribute']}:{r['target']}"):groups.setdefault(key,[]).append(i)
    removals={f'image:{i}':[i] for i in images}
    removals.update({k:v for k,v in groups.items() if 2<=len(v)<=6})
    values={k:dict(removed=v,points=d[[i not in v for i in images]].mean(0).tolist()) for k,v in removals.items()}
    return dict(all_directions_positive=all(min(v['points'])>0 for v in values.values()),leave_out=values)


def main():
    assert os.environ.get('SLURM_JOB_ID')
    frozen=load(ROOT/'audit/analysis_freeze.json');assert frozen['source_sha256']==sha(__file__)
    mp=ROOT/'audit/primary_manifest.json';m=load(mp);pp=ROOT/'audit/primary_review_packet.json';packet=load(pp);review=load(ROOT/'audit/primary_review.json')
    assert review['sealed'] and review['packet_sha256']==sha(pp) and packet['manifest_sha256']==sha(mp)
    reviewed={r['task_id']:r for r in review['rows']};events={r['query_id']:r for r in load(ROOT/'stage10ar_anchor_annotations.json')['rows']};rows=[]
    for r in m['rows']:
        d=reviewed[r['task_id']];e=events[r['query_id']]
        assert sha(r['generation_path'])==d['generation_sha256'] and sha(r['result_path'])==d['result_sha256']
        compact={k:v for k,v in r.items() if k!='prefix_ids'}
        rows.append(dict(compact,option=d['option'],raw_option=d['raw_option'],source_count=e['source_count'],answer=e['source_answer'],
            correct=d['option']==e['source_answer'],raw_correct=d['raw_option']==e['source_answer'],
            unscorable=d['option'] is None,at_length_cap=d['at_length_cap'],normal_eos=d['normal_eos'],tokens=d['tokens']))
    save(ROOT/'audit/primary_scored.json',dict(at=now(),rows=rows,review_sha256=sha(ROOT/'audit/primary_review.json')))
    for assay,name in [('image_off','stage10ar_visual_necessity.parquet'),('text_only','stage10ar_text_sufficiency.parquet')]:
        path=ROOT/name;assert not path.exists();pd.DataFrame([r for r in rows if r['condition']==assay]).to_parquet(path,index=False)
    result=summarize(rows);result['by_attribute']={a:summarize([r for r in rows if r['attribute']==a]) for a in ('color','shape')}
    complete={r['image_id'] for r in rows if r['anchor']=='A2'}
    result['complete_anchor_sensitivity']=summarize([r for r in rows if r['image_id'] in complete])
    result['raw_sensitivity']=summarize([dict(r,correct=r['raw_correct']) for r in rows])
    result['robustness']=robustness(rows)
    points=all(v['point']>0 for v in result['primary'].values())
    early_intervals=all(result['primary'][p]['familywise95_ci'][0]>0 for p in ('P1','P2'))
    attributes=all(v['point']>0 for s in result['by_attribute'].values() for v in s['primary'].values())
    old=load(PRIOR/'audit/gate_b_inference.json');oldqueries=set(load(PRIOR/'stage10a_event_selection.json')['primary_ids'])
    selected=set(m['query_order']);overlap=sorted(selected&oldqueries)
    applies=old['H3_supported'] and old['correct_emitted_fact_stratum']['cf_minus_sham']['ci95'][0]>0
    robust=result['robustness']['all_directions_positive'];main_pass=points and early_intervals and attributes and robust and applies
    reserve=points and not early_intervals and attributes and robust
    before=sum(events[q]['anchors']['A3']['native_tokens']<events[q]['anchors']['A4']['native_tokens'] for q in selected)
    optional=main_pass and before>=12
    visual=result['primary']['P1']['familywise95_ci'][0]>0 and result['primary']['P3']['point']>0
    textual=result['primary']['P2']['familywise95_ci'][0]>0 and result['primary']['P4']['point']>0
    outcome='A' if main_pass else 'B' if textual and not visual else 'C' if visual and not textual else 'D' if not visual and not textual else 'non-A: mixed robustness/uncertainty'
    result.update(at=now(),outcome=outcome,main_gate_pass=main_pass,reserve_gate_pass=reserve,optional_a3_edit_gate_pass=optional,
        gate_components=dict(all_four_points_positive=points,early_pair_adjusted_CI_positive=early_intervals,both_attributes_positive=attributes,
            leave_one_and_small_group_robust=robust,prior_text_causality_applicable=applies),A3_before_A4=before,
        text_causality=dict(prior_inference_sha256=sha(PRIOR/'audit/gate_b_inference.json'),overlapping_queries=overlap,
            overlap_n=len(overlap),same_model_aggregate_count_regime=True,correct_fact_stratum_n=20,
            limitation='The prior text-edit effect is not a new per-item causal certificate for every selected query.'),
        independent_unit='image',seed=920260927,bootstrap_draws=4000,multiplicity='Bonferroni across4 primary contrasts:98.75% marginal percentile intervals, family-wise95%.',
        completion={f'{c}/{a}':dict(n=sum(r['condition']==c and r['anchor']==a for r in rows),
            correct=sum(r['correct'] for r in rows if r['condition']==c and r['anchor']==a),
            unscorable=sum(r['unscorable'] for r in rows if r['condition']==c and r['anchor']==a),
            capped=sum(r['at_length_cap'] for r in rows if r['condition']==c and r['anchor']==a)) for c in ASSAYS for a in ANCHORS})
    images,x=panel(rows);states=[]
    for i,image in enumerate(images):
        pairs=[None if not np.isfinite(x[i,:,j]).all() else x[i,:,j].astype(bool).tolist() for j in range(5)]
        state=earliest_transition(pairs);h=int(state['H'][1]) if state['H'] else None
        states.append(dict(image_id=image,**state,assay_correct_by_anchor={a:p for a,p in zip(ANCHORS,pairs)},
            H_relative_to_A3=None if h is None else h-3,at_or_adjacent_to_A3=h is not None and abs(h-3)<=1))
    save(ROOT/'stage10ar_item_transition_states.json',dict(at=now(),rows=states,identifiable_H=sum(r['H'] is not None for r in states),
        H_distribution={a:sum(r['H']==a for r in states) for a in ANCHORS},nonmonotonic_images=sum(bool(r['later_reversals']) for r in states),
        definition='Earliest available anchor with both assays correct; later reversals are retained; missing A2 is not a failure.'))
    save(ROOT/'stage10ar_primary_inference.json',result)
    for name,value in result['primary'].items():print(name,value,flush=True)
    print('MAIN_GATE',main_pass,'RESERVE',reserve,'OPTIONAL_EDIT',optional,'OUTCOME',outcome,flush=True)
    print('GATE_COMPONENTS',result['gate_components'],flush=True)


if __name__=='__main__':main()
