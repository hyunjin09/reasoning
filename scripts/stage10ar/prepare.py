"""L0 tokenization and immutable inputs; no intervention outcomes are read."""
import os
from pathlib import Path
from transformers import AutoTokenizer
from scripts.stage10ar.common import ROOT,OLD,DATA,PROTOCOL,load,save,sha,now
from scripts.stage10a.prepare import boundaries


def main():
    assert os.environ.get('SLURM_JOB_ID')
    previous=load(OLD/'config.json');review=load(ROOT/'audit/semantic_review.json')
    assert review['sealed'] and review['protocol_sha256']==sha(PROTOCOL)
    for name,d in previous['files_sha256'].items():assert sha(Path(previous['checkpoint'])/name)==d
    tokenizer=AutoTokenizer.from_pretrained(previous['checkpoint'],local_files_only=True)
    inputs=[OLD/'config.json',OLD/'stage9a5_thinking_full_baseline.json',OLD/'audit/inference_tasks.json',
        ROOT/'audit/semantic_review.json',ROOT/'audit/optional_a3_annotations.json',DATA/'stage9a3_synthetic_dataset_manifest.json',
        Path('plan/stage10ar_causal_phase_transition_localization_plan.md')];rows=[]
    for original in review['rows']:
        r=dict(original);g=load(r['generation_path']);assert sha(r['generation_path'])==r['generation_sha256']
        ids=g['generated_token_ids'][:g['reasoning_tokens']];text=r['native_reasoning']
        assert tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)==text
        bounds=boundaries(tokenizer,ids,text);anchors={}
        for a,target in r['chars'].items():
            if target is None:anchors[a]=None;continue
            n,c=min((v for v in bounds if v[1]>=target),key=lambda v:v[0])
            assert not text[target:c].strip(),(r['query_id'],a,target,c)
            assert 0<=n<512
            anchors[a]=dict(native_tokens=n,char_boundary=c,prefix_ids=ids[:n],prefix_text=text[:c],remaining_tokens=512-n)
        r.update(anchors=anchors,split='primary' if r['query_id'] in review['primary_ids'] else 'reserve');rows.append(r)
        inputs += [Path(r['generation_path']),Path(r['result_path']),Path(r['task']['image_path'])]
    save(ROOT/'stage10ar_anchor_annotations.json',dict(at=now(),frozen=True,rows=rows,review_sha256=sha(ROOT/'audit/semantic_review.json'),
        intervention_outcomes_used=False,semantic_reviewer='Main agent manual native-text/source review, intervention-blinded.',protocol_sha256=sha(PROTOCOL)))
    save(ROOT/'stage10ar_primary_cohort.json',dict(at=now(),frozen=True,primary_ids=review['primary_ids'],reserve_ids=review['reserve_ids'],
        successful_reasoning_cohort=True,independent_unit='image',selection_rule='Parity-preferred correct FULL query; balanced hash selection with stage10ar-v1-920260927 seed string.',
        annotations_sha256=sha(ROOT/'stage10ar_anchor_annotations.json')))
    byid={r['query_id']:r for r in rows};optional=[]
    for e in load(ROOT/'audit/optional_a3_annotations.json')['rows']:
        a=byid[e['query_id']]['anchors']['A3'];row=dict(e);texts={c:a['prefix_text'].replace(e['original_span'],e[f'{c}_span']) for c in ('counterfactual','sham')}
        texts['original']=a['prefix_text'];row['conditions']={}
        for c,text in texts.items():
            token_ids=a['prefix_ids'] if c=='original' else tokenizer.encode(text,add_special_tokens=False)
            assert 0<len(token_ids)<512 and 151668 not in token_ids
            row['conditions'][c]=dict(prefix_ids=token_ids,prefix_text=text,prefix_tokens=len(token_ids),remaining_tokens=512-len(token_ids))
        optional.append(row)
    save(ROOT/'audit/optional_a3_tokenized.json',dict(at=now(),frozen=True,rows=optional,annotation_sha256=sha(ROOT/'audit/optional_a3_annotations.json')))
    cfg=dict(at=now(),checkpoint=previous['checkpoint'],files_sha256=previous['files_sha256'],max_total_tokens=512,seed=920260927,
        bootstrap_draws=4000,max_gpus=8,allowed_nodes=['node02','node03','node06','node07'],protocol_sha256=sha(PROTOCOL),
        annotations_sha256=sha(ROOT/'stage10ar_anchor_annotations.json'),cohort_sha256=sha(ROOT/'stage10ar_primary_cohort.json'),
        inputs_sha256={str(p):sha(p) for p in sorted(set(inputs))})
    save(ROOT/'config.json',cfg)
    with (ROOT/'stage10ar_phase_localization_spec.md').open('x') as f:f.write(PROTOCOL.read_text())
    primary=[r for r in rows if r['split']=='primary'];logical=sum(2*sum(a is not None for a in r['anchors'].values()) for r in primary)
    save(ROOT/'audit/resource_estimate_l0.json',dict(at=now(),primary_images=24,logical_continuations=logical,
        A2_available=sum(r['anchors']['A2'] is not None for r in primary),A3_before_A4=sum(r['anchors']['A3']['native_tokens']<r['anchors']['A4']['native_tokens'] for r in primary),
        conservative_seconds_per_token=.06,full_cap_generation_gpu_hours=logical*512*.06/3600,startup_validation_allowance_gpu_hours=.5,
        projected_upper_gpu_hours=logical*512*.06/3600+.5,target_gpu_hours=3,hard_projected_limit=5,reuse_not_yet_counted=True))
    print('L0_FROZEN',len(rows),'logical primary',logical,flush=True)


if __name__=='__main__':main()
