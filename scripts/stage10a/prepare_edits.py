"""Seal all text variants before running the bounded text-causality block."""
import os
from transformers import AutoTokenizer
from scripts.stage10a.common import ROOT,load,save,sha,now,verify_config
from scripts.stage10a.edits import variants,replace_fact


def main():
    assert os.environ.get('SLURM_JOB_ID')
    cfg=verify_config(); assert load(ROOT/'audit/gate_a_inference.json')['gate_a_pass']
    tokenizer=AutoTokenizer.from_pretrained(cfg['checkpoint'],local_files_only=True)
    selection=load(ROOT/'stage10a_event_selection.json'); byid={r['query_id']:r for r in selection['rows']}
    originals={r['query_id']:r for r in load(ROOT/'audit/gate_a_manifest.json')['rows']
               if r['condition']=='text_only' and r['anchor']=='emit'}
    rows=[]; edits=[]
    for query in selection['primary_ids']:
        e=byid[query]; a=e['anchors']['emit']; prefix=a['prefix_text']; begin=e['pre_char']; end=e['emit_char']
        assert prefix[begin:end]==e['fact_text']
        cf,sham,note=variants(e['fact_text'],e['emitted_count'])
        for condition,fact in [('original',e['fact_text']),('counterfactual',cf),('delete',''),('sham',sham)]:
            text=replace_fact(prefix,begin,end,fact)
            ids=a['prefix_ids'] if condition=='original' else tokenizer.encode(text,add_special_tokens=False)
            assert tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)==text
            assert 0<len(ids)<512 and 151668 not in ids
            key=f'{query}_{condition}_emit';dest=ROOT/'gate_b/results'/key
            orig=originals[query]; reused=condition=='original'
            row=dict(query_id=query,image_id=e['image_id'],attribute=e['attribute'],anchor='emit',condition=condition,task_id=key,
                generation_path=orig['generation_path'] if reused else str(dest/'generation.json'),
                result_path=orig['result_path'] if reused else str(dest/'result.json'),
                prefix_tokens=len(ids),remaining_tokens=512-len(ids),prefix_ids=ids,prefix_text=text,
                original_count=e['emitted_count'],counterfactual_count=e['emitted_count']%5+1,
                reused=reused,reused_task_id=orig['task_id'] if reused else None)
            if reused:
                row.update(reused_generation_sha256=sha(orig['generation_path']),reused_result_sha256=sha(orig['result_path']))
                g=load(orig['generation_path']);assert g['generated_token_ids'][:len(ids)]==ids
            rows.append(row)
        edits.append(dict(query_id=query,original=e['fact_text'],counterfactual=cf,sham=sham,delete='',note=note,
            start_char=begin,end_char=end,semantic_review='Manual review of the complete frozen variants; task/options and text outside this fact span unchanged.'))
    save(ROOT/'audit/text_edit_annotations.json',dict(at=now(),frozen=True,rows=edits,
        condition_selection='Prospective emit anchor and next-count rule; no text-edit outcomes exist.',
        limitation='Earlier object inventories and arithmetic operands remain intact and may contradict the changed count.'))
    paths=['scripts/stage10a/common.py','scripts/stage10a/runtime.py','scripts/stage10a/edits.py','scripts/stage10a/prepare_edits.py',
           'scripts/stage10a/worker_edits.py','scripts/stage10a/analyze_b.py']
    save(ROOT/'audit/gate_b_manifest.json',dict(at=now(),frozen=True,stage='gate_b',rows=rows,query_order=selection['primary_ids'],
        n_images=24,logical_continuations=96,new_continuations=72,reused_continuations=24,config_sha256=sha(ROOT/'config.json'),
        selection_sha256=sha(ROOT/'stage10a_event_selection.json'),gate_a_sha256=sha(ROOT/'audit/gate_a_inference.json'),
        edit_annotations_sha256=sha(ROOT/'audit/text_edit_annotations.json'),source_sha256={p:sha(p) for p in paths}))
    print('FROZEN_GATE_B',len(rows),'NEW',sum(not r['reused'] for r in rows),flush=True)


if __name__=='__main__':main()
