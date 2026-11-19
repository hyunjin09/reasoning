"""CPU-Slurm: verify native evidence, materialize metrics and masked answer packets."""
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from scripts.stage8c.prepare import save,sha
from visual_reasoning.stage9a.protocol import ARMS,TAU,episode_metrics
from visual_reasoning.stage8b.v2_scoring import extract_answer

ROOT=Path('outputs/stage9a/v1')
SPECIAL={'<|im_end|>','<|endoftext|>','<think>','</think>'}


def aligned(active,token,start,end,width=16):
    return bool(active[max(start,token-width):min(end,token+width+1)].any())


def summarize(scores,span,events,tokens,*,common=False):
    start=span['start'];end=span['common_end'] if common else span['end']
    coords=np.array([t for t in range(start,end) if tokens[t]['decoded_token'] not in SPECIAL],dtype=int)
    m=episode_metrics(scores[coords],0,len(coords))
    active=np.zeros(len(scores),dtype=bool);active[coords]=scores[coords]>TAU
    onset=np.zeros(len(scores),dtype=bool)
    for ep in m['episodes']:
        ep.update(native_start=int(coords[ep['start']]),native_end=int(coords[ep['end']-1])+1)
        onset[ep['native_start']]=True
    demands=[e for e in events if e['semantic_label']=='accepted' and start<=e['demand_token']<end]
    controls=[e for e in events if e['semantic_label']=='rejected' and start<=e['demand_token']<end]
    mean=lambda x:float(np.mean(x)) if len(x) else None
    m.update(P2=m['late_fractions']['0.5'],P3=m['episodes_per_1k'],P4=m['long_gap_probability'],
             reviewed_demands=len(demands),reviewed_nondemands=len(controls),mean_R=mean(scores[coords][np.isfinite(scores[coords])]))
    for w in (16,32):
        values=[aligned(active,e['demand_token'],start,end,w) for e in demands]
        m['P1' if w==16 else 'alignment32']=mean(values)
        full=[v for e,v in zip(demands,values) if e['demand_token']-w>=start and e['demand_token']+w<end]
        m[f'alignment{w}_full_window']=mean(full);m[f'full_window{w}_n']=len(full)
    m['alignment16_onset']=mean([aligned(onset,e['demand_token'],start,end) for e in demands])
    m['nondemand_alignment16']=mean([aligned(active,e['demand_token'],start,end) for e in controls])
    shifted=[]
    for fraction in (.25,.5,.75):
        values=[aligned(active,start+(e['demand_token']-start+int(fraction*(end-start)))%(end-start),start,end) for e in demands] if end>start else []
        m[f'shift_{fraction}']=mean(values);shifted.extend(values)
    m['shift_control_alignment16']=mean(shifted)
    m['demand_minus_shift']=m['P1']-m['shift_control_alignment16'] if demands else None
    m['demand_minus_nondemand']=m['P1']-m['nondemand_alignment16'] if demands and controls else None
    onsets=np.array([e['start'] for e in m['episodes']])
    m['median_onset_gap']=mean([]) if len(onsets)<2 else float(np.median(np.diff(onsets)))
    m['mean_episode_duration']=mean([e['end']-e['start'] for e in m['episodes']])
    peri={}
    for offset in range(-64,65):
        observations=[bool(active[e['demand_token']+offset]) for e in demands if start<=e['demand_token']+offset<end]
        peri[str(offset)]=dict(mean=mean(observations),events=len(observations))
    m['peri_demand']=peri
    return m,coords,active,onset


def main():
    assert os.environ.get('SLURM_JOB_ID'),'Resource-heavy extraction must use CPU Slurm'
    frozen=json.loads((ROOT/'annotations/causal_selection_frozen.json').read_text());assert frozen['frozen']
    tasks=json.loads((ROOT/'audit/native_tasks.json').read_text())['rows']
    cohort={r['item_id']:r for r in json.loads((ROOT/'stage9a_cohort_manifest.json').read_text())['rows']}
    packet={r['task_id']:r['packet_id'] for r in json.loads((ROOT/'annotations/packet_index.json').read_text())['rows']}
    semantic=json.loads((ROOT/'annotations/semantic_review_complete.json').read_text())['rows']
    by_packet={p:[] for p in packet.values()}
    for r in semantic:by_packet[r['packet_id']].append(r)
    selected={r['task_id']:r for r in frozen['rows']};eligible=set(frozen['eligible_event_ids'])
    writer=None;episodes=[];annotations=[];summaries=[];answer_packets=[];integrity=[]
    feature_path=ROOT/'stage9a_retrieval_features.parquet';assert not feature_path.exists()
    for k,task in enumerate(tasks):
        d=ROOT/'native/examples'/task['task_id'];receipt=json.loads((d/'result.json').read_text())
        for path,expected in receipt['provenance_sha256'].items():assert sha(path)==expected,path
        integrity.append(dict(task_id=task['task_id'],all_artifact_hashes_match=True))
        tokens=[json.loads(line) for line in (d/'tokens.jsonl').read_text().splitlines()];gen=json.loads((d/'generation.json').read_text())
        with np.load(d/'passive.npz') as z:
            features=z['features'];focus=z['visual_focus'];scores=z['retrieval_score'];keys=z['feature_keys'].tolist()
        assert len(tokens)==len(scores)==features.shape[0]==focus.shape[0]
        assert np.isnan(scores[0]) and np.isfinite(scores[1:]).all()
        n=len(scores);span=receipt['reasoning_span'];events=by_packet[packet[task['task_id']]]
        primary,coords,active,onset=summarize(scores,span,events,tokens)
        common,_,_,_=summarize(scores,span,events,tokens,common=True)
        prefix=dict(task_id=task['task_id'],item_id=task['item_id'],family_id=task['family_id'],arm=task['arm'])
        for scope,metrics in [('primary',primary),('common_assistant',common)]:
            for i,e in enumerate(metrics['episodes']):episodes.append(dict(**prefix,scope=scope,episode_index=i,**e))
        for e in events:
            t=e['demand_token']
            reviewed=dict(e,causal_eligibility='eligible_discrete_local_readout' if e['event_id'] in eligible else 'not_eligible_in_bounded_discrete_readout_review')
            annotations.append(dict(**prefix,**reviewed,source_readout_eligible=e['event_id'] in eligible,
                selected_for_causal=task['task_id'] in selected and selected[task['task_id']]['event_id']==e['event_id'],
                retrieval_active16=aligned(active,t,span['start'],span['end']),retrieval_onset16=aligned(onset,t,span['start'],span['end']),
                retrieval_active32=aligned(active,t,span['start'],span['end'],32),window16_truncated=t-16<span['start'] or t+16>=span['end']))
        total=focus.sum(-1);normalized=focus/np.maximum(total[:,None],1e-30)
        focus_entropy=-(normalized*np.log(np.maximum(normalized,1e-30))).sum(-1)/np.log(focus.shape[1])
        cols=dict(token_index=np.arange(n,dtype=np.int32),retrieval_score=scores,in_primary_reasoning=np.isin(np.arange(n),coords),
            normalized_reasoning_position=np.full(n,np.nan),episode_active=active,episode_onset=onset,
            spatial_mean_focus_entropy=focus_entropy,spatial_mean_focus_top4_share=np.partition(normalized,-4,axis=-1)[:,-4:].sum(-1),
            source_target_share=np.full(n,np.nan,dtype=np.float32),source_donor_share=np.full(n,np.nan,dtype=np.float32),source_irrelevant_share=np.full(n,np.nan,dtype=np.float32))
        cols['normalized_reasoning_position'][coords]=np.arange(len(coords))/max(len(coords),1)
        for j,key in enumerate(keys):cols[key]=features[:,j]
        if task['task_id'] in selected:
            for kind in ('target','donor','irrelevant'):cols['source_'+kind+'_share']=normalized[:,selected[task['task_id']][kind+'_local']].sum(-1)
        cols={key:pa.array(value) for key,value in cols.items()}
        for key,value in prefix.items():cols[key]=pa.array([value]*n)
        table=pa.table(cols)
        if writer is None:writer=pq.ParquetWriter(feature_path,table.schema,compression='zstd')
        writer.write_table(table)
        row=cohort[task['item_id']]
        raw={key:float(np.nanmean(features[coords,j])) if len(coords) else None for j,key in enumerate(keys)}
        summary=dict(**prefix,subject=row['subject'],difficulty=row['level'],answer_format=row['answer_format'],question_length=len(task['question'].split()),
            problem_type=row['problem_type'],visual_density=row['visual_density'],entity_count=row['entity_count'],
            completion=receipt['completion'],boundary=span['boundary'],boundary_certain=span['certain'],generated_tokens=n,
            primary=primary,common=common,raw_mean=raw,runtime_seconds=receipt['runtime']['elapsed_seconds'])
        summaries.append(summary)
        text=gen['raw_decoded_response'];extraction=extract_answer(text,row['options']);offset=extraction['span']
        evidence=text[max(0,offset[0]-180):min(len(text),offset[1]+100)] if offset else text[-700:]
        answer_packets.append(dict(packet_id=packet[task['task_id']],extraction=extraction,options=row['options'],
            extraction_context=evidence,tail=text[-650:],normal_eos=receipt['normal_eos'],at_length_cap=receipt['at_length_cap']))
        if k%16==0:print(json.dumps(dict(event='analysis_extracted',trajectories=k+1,total=len(tasks))),flush=True)
    writer.close()
    pd.DataFrame(episodes).to_parquet(ROOT/'stage9a_retrieval_episodes.parquet',index=False)
    pd.DataFrame(annotations).to_parquet(ROOT/'stage9a_demand_events.parquet',index=False)
    save(ROOT/'audit/trajectory_metrics.json',dict(rows=summaries,feature_path=str(feature_path),causal_manifest_sha256=sha(ROOT/'annotations/causal_selection_frozen.json')))
    save(ROOT/'audit/all_native_hashes_verified.json',dict(rows=integrity,verified=True))
    save(ROOT/'annotations/answer_extraction_packets.json',dict(rows=sorted(answer_packets,key=lambda r:r['packet_id']),masking='No arm, gold/correctness, routing or causal outcomes; full source text retained natively'))
    save(ROOT/'audit/extraction_complete.json',dict(completed=True,trajectories=len(summaries),features_sha256=sha(feature_path),slurm_job_id=os.environ['SLURM_JOB_ID']))


if __name__=='__main__':main()
