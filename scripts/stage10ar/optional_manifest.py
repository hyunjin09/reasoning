"""Materialize only the sealed A3 subset after the primary gate passes."""
from scripts.stage10ar.common import ROOT,load,save,sha,now,verify_config


def main():
    verify_config();inference=load(ROOT/'stage10ar_primary_inference.json')
    assert inference['main_gate_pass'] and inference['optional_a3_edit_gate_pass'] and not inference['reserve_gate_pass']
    ep=ROOT/'audit/optional_a3_tokenized.json';edits=load(ep)
    assert edits['frozen'] and edits['annotation_sha256']==sha(ROOT/'audit/optional_a3_annotations.json')
    primary=load(ROOT/'audit/primary_manifest.json');rows=[]
    for e in edits['rows']:
        q=e['query_id'];original=next(r for r in primary['rows'] if (r['query_id'],r['anchor'],r['condition'])==(q,'A3','text_only'))
        for c in ('original','counterfactual','sham'):
            a=e['conditions'][c];task=f'{q}_{c}_A3'
            r=dict(task_id=task,query_id=q,image_id=e['image_id'],attribute=e['attribute'],anchor='A3',condition=c,
                prefix_ids=a['prefix_ids'],prefix_text=e[f'{c}_prefix'],prefix_tokens=len(a['prefix_ids']),
                original_count=e['original_count'],counterfactual_count=e['counterfactual_count'],execution='reuse' if c=='original' else 'run')
            if c=='original':
                assert r['prefix_ids']==original['prefix_ids']
                r.update(generation_path=original['generation_path'],result_path=original['result_path'],
                    source_generation_sha256=sha(original['generation_path']),source_result_sha256=sha(original['result_path']))
            else:r.update(generation_path=str(ROOT/f'optional/results/{task}/generation.json'),result_path=str(ROOT/f'optional/results/{task}/result.json'))
            rows.append(r)
    assert len(rows)==36 and len({r['image_id'] for r in rows})==12
    sources=['scripts/stage10ar/optional_worker.py','scripts/stage10ar/runtime.py','scripts/stage10a/runtime.py','scripts/stage10ar/analyze_optional.py']
    save(ROOT/'audit/optional_manifest.json',dict(at=now(),frozen=True,rows=rows,query_order=[e['query_id'] for e in edits['rows']],
        annotation_sha256=sha(ep),primary_manifest_sha256=sha(ROOT/'audit/primary_manifest.json'),
        config_sha256=sha(ROOT/'config.json'),source_sha256={p:sha(p) for p in sources},
        logical_continuations=36,new_continuations=24,reused_continuations=12,
        analysis='Secondary signed score: +1 if final count follows counterfactual, -1 if original,0 otherwise including missing. Paired CF-original/CF-sham;4000 image bootstrap seed920260927;ordinary95% intervals. Descriptive, does not change primary gate.',
        limitation='Local edits preserve earlier descriptions/subtotals, which can conflict with the changed inventory clause. No prefix rewriting or sample reselection after outcomes.'))
    save(ROOT/'stage10ar_reserve_extension.json',dict(at=now(),executed=False,gate_pass=False,
        reason='Primary24 main gate passes with all4 adjusted intervals above0; no precision extension needed.',reserve_images=8))
    upper=sum((512-r['prefix_tokens'])*.06 for r in rows if r['execution']=='run')/3600+.15
    save(ROOT/'audit/optional_resource_estimate.json',dict(at=now(),new_continuations=24,reused_continuations=12,projected_gpu_hours=upper,
        total_stage_projected_gpu_hours=upper+.5,optional_target_gpu_hours=1,hard_limit_gpu_hours=5))
    assert upper<1 and upper+.5<5
    print('OPTIONAL36 logical/24new/12reused;GPU-hour upper',upper)


if __name__=='__main__':main()
