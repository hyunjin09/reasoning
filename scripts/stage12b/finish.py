"""Close only a terminal technical stop or the complete reviewed61-family profile."""
import os,re
from pathlib import Path
from scripts.stage12b.common import ROOT,load,save,sha,now
from scripts.stage12b.resources import account

def main():
    gate=load(ROOT/'stage12b_technical_sanity.json');manifest=load(ROOT/'stage12b_frozen_manifest.json')
    integrity=load(ROOT/'stage12b_oracle_integrity_review.json');technical={r['task_id']:r for r in gate['rows']}
    resources=account('closure',final=True)
    assert integrity['pass']
    scientific_path=ROOT/'audit/scientific_review.json'
    science=load(scientific_path) if gate['pass'] else None
    if not gate['pass']:assert not scientific_path.exists()
    scientific={r['task_id']:r for r in science['rows']} if science else {}
    import pandas as pd
    result=[]
    for t in manifest['tasks']:
        p=ROOT/'generations'/t['task_id']/'generation.json'
        r=dict(task_id=t['task_id'],item_id=t['item_id'],family_id=t['family_id'],arm=t['arm'],answer_type=t['answer_type'],
            cap=t['cap'],status='NOT_RUN',raw_decoded_response=None,tokens=None,cap_hit=None,normal_stop=None,
            finish_reason=None,stop_reason=None,committed_final=None,parseable=None,repetition_pathology=None,
            extracted_final=None,correct=None,correctness_status='NOT_SCORED_TECHNICAL_STOP' if not gate['pass'] else 'NOT_RUN',
            atom_labels_json=None,technical_quote=None,technical_reason=None,scientific_review_json=None,
            generation_path=None,generation_sha256=None,request_latency_seconds=None,visual_tokens=None)
        if p.exists():
            g=load(p);receipt=load(p.parent/'result.json');assert sha(p)==receipt['generation_sha256']
            review=technical.get(t['task_id'],scientific.get(t['task_id']))
            assert review and review['generation_sha256']==sha(p)
            r.update(status='COMPLETED_REVIEWED',generation_path=str(p),generation_sha256=sha(p))
            for k in ['raw_decoded_response','tokens','cap_hit','normal_stop','finish_reason','request_latency_seconds','visual_tokens']:r[k]=g[k]
            r['stop_reason']=str(g['stop_reason'])
            for k in ['committed_final','parseable','repetition_pathology','extracted_final']:r[k]=review.get(k)
            r.update(technical_quote=review['quote'],technical_reason=review['reason'])
            if science:
                import json
                s=scientific[t['task_id']];r.update(correct=s['correct'],correctness_status=s['outcome'],
                    atom_labels_json=json.dumps(s.get('atoms')),scientific_review_json=json.dumps(s))
        result.append(r)
    for arm,name in [('E','evidence_probe'),('N','native'),('O','oracle')]:
        p=ROOT/f'stage12b_{name}_results.parquet';assert not p.exists()
        pd.DataFrame([r for r in result if r['arm']==arm]).to_parquet(p,index=False)
    completed=sum(r['status']=='COMPLETED_REVIEWED' for r in result)
    assert completed==(183 if gate['pass'] else 36)
    if science:
        from scripts.stage12b.inference import infer
        by={(r['item_id'],r['arm']):r for r in scientific.values()};profiles=[]
        from scripts.stage12b.protocol import profile
        for source in manifest['rows']:
            e,n,o=[by[(source['item_id'],a)]['correct'] for a in 'ENO']
            profiles.append(dict(item_id=source['item_id'],family_id=source['family_id'],e=e,n=n,o=o,
                bottleneck_class=profile(e,n,o),status='ESTIMATED'))
        inference=infer(profiles);decision=inference['decision']
    else:
        decision='TECHNICAL_STOP'
        profiles=[dict(item_id=r['item_id'],family_id=r['family_id'],e=None,n=None,o=None,bottleneck_class=None,status='NOT_ESTIMATED_TECHNICAL_STOP') for r in manifest['rows']]
        inference=dict(at=now(),status='NOT_ESTIMATED_TECHNICAL_STOP',correctness_opened=False,
            endpoints={f'P{i}':dict(numerator=None,denominator=None,estimate=None,wilson95=None) for i in range(1,7)},
            classes=None,contrasts=None,bootstrap_draws_performed=0,reason='Technical validity gate failed; missing scientific estimates are not zeros.')
    pd.DataFrame(profiles).to_parquet(ROOT/'stage12b_failure_profiles.parquet',index=False)
    save(ROOT/'stage12b_primary_inference.json',inference)
    recommendations=dict(PROFILE_INFORMATIVE='Freeze the Stage12B bottleneck labels and run prompted CoT plus native Thinking on the same families to test selective rescue by failure type.',
        PROFILE_SPARSE='Build a fresh harder E*-annotated cohort before testing CoT/Thinking rescue.',
        TECHNICAL_STOP='Repair the native/oracle assay before any scientific interpretation or additional conditions.')
    save(ROOT/'stage12b_profile_decision.json',dict(at=now(),decision=decision,technical_pass=gate['pass'],oracle_integrity_pass=integrity['pass'],
        source_families=61,source_facts=157,completed_calls=completed,not_run=183-completed,scientific_correctness_opened=bool(science),
        recommendation=recommendations[decision],recommendation_executed=False,additional_conditions_launched=False))
    report=Path('reports/stage12b/v1');report.mkdir(parents=True,exist_ok=True)
    idx=['# Stage12B full responses','','Exact original prompts and raw E/N/O generations. Unexecuted conditions are marked NOT_RUN.','', '| Family / item | Comparison |','|---|---|']
    for source in manifest['rows']:
        rr=[r for r in result if r['item_id']==source['item_id'] and r['status']=='COMPLETED_REVIEWED']
        if not rr:continue
        body=[f'# Case {source["item_id"]}', '',f'[Original image]({source["image"]})','']
        for r in rr:
            t=next(t for t in manifest['tasks'] if t['task_id']==r['task_id']);s=r['raw_decoded_response']
            fence='`'*max(3,1+max([len(m) for m in re.findall(r'`+',s+t['prompt'])] or [0]))
            body += [f'## {r["arm"]}', '',f'{r["tokens"]} tokens; {r["finish_reason"]}; image present={r["arm"]!="O"}. Correctness: {r["correctness_status"]}.','',
                'Exact prompt:','',fence+'text',t['prompt'],fence,'','Full response:','',fence+'text',s,fence,'',f'[Raw receipt]({Path(r["generation_path"]).resolve()})','']
        with (report/f'{source["item_id"]}.md').open('x') as f:f.write('\n'.join(body)+'\n')
        idx.append(f'| {source["item_id"]} | [Full E/N/O]({source["item_id"]}.md) |')
    with (report/'index.md').open('x') as f:f.write('\n'.join(idx)+'\n')
    # Standalone scientific figure artifacts; unavailable quantities explicitly marked.
    os.environ['MPLCONFIGDIR']=str(Path('runs/stage12b/v1/matplotlib').resolve())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figdir=ROOT/'figures';figdir.mkdir(exist_ok=True)
    for number,title in [(1,'Evidence acquisition and text oracle'),(2,'Native failure composition'),(3,'Oracle rescue by recoverability'),(4,'Deterministic example trajectories')]:
        fig,ax=plt.subplots(figsize=(10,4));ax.set_title(title)
        if number==1:
            ax.axis('off');ax.text(.5,.65,'Image  →  E*  →  Task reasoning  →  Answer',ha='center',fontsize=17)
            ax.text(.5,.35,'E: probe requested visual facts     O: replace image with correct frozen E*',ha='center',fontsize=12)
        elif not science:
            ax.axis('off');ax.text(.5,.5,'NOT ESTIMATED — technical validity gate failed',ha='center',fontsize=14)
        elif number==2:
            cc=inference['classes'];ax.bar(list(cc),list(cc.values()));ax.set_ylabel('Independent native-failure families')
            for j,(k,v) in enumerate(cc.items()):ax.text(j,v,f'{v} ({v/sum(cc.values()):.1%})' if sum(cc.values()) else '0',ha='center',va='bottom')
        elif number==3:
            s=inference['secondary_rescue'];vals=[s[str(e)]['estimate'] for e in [True,False]]
            ax.bar(['E+','E−'],[v if v is not None else 0 for v in vals]);ax.set_ylim(0,1);ax.set_ylabel('Oracle rescue fraction among native failures')
            for j,e in enumerate([True,False]):
                q=s[str(e)];ax.text(j,.9,f'{q["numerator"]}/{q["denominator"]}' if q['denominator'] else 'UNDEFINED',ha='center')
        else:
            ax.axis('off');lines=[]
            for b in ['B1','B2','B3','B4']:
                selected=sorted([r for r in profiles if r['bottleneck_class']==b],key=lambda r:r['family_id'])[:2]
                lines.append(b+': '+(', '.join(r['item_id'] for r in selected) or 'No families'))
            ax.text(.1,.5,'Smallest family IDs per class\n'+'\n'.join(lines)+'\nFull prompts/evidence/responses in linked case pages.',va='center',fontsize=13)
        fig.tight_layout()
        for ext in ['png','pdf']:fig.savefig(figdir/f'figure{number}.{ext}',dpi=160)
        plt.close(fig)
    summary=['# Stage12B visual failure bottleneck profile','',f'**{decision}**. '+('Scientific profiling follows the frozen gates.' if science else 'Technical validity failed; no bottleneck proportions or task accuracy are estimated.'),'',
        'All61 independent MathVision families,157 E* facts, questions/images/source answers and earlier Stage12A/12A-R evidence are preserved. '
        'Model: Qwen3-VL-4B-Instruct, revision ebb281ec70b05090aa6165b016eac8ec08e71b17, BF16/vLLM0.11.0. '
        'E cap256; native N and image-free O cap32768; official Instruct .7/.8/top20/repetition1/presence1.5. '
        'N has no appended instruction. O preserves exact facts and original questions; frozen requests provide fact/entity labels.','',
        '## Technical sanity','', '| Arm | Parseable | Committed finals | Caps | Severe repetition | Gate |','|---|---:|---:|---:|---:|---|']
    for a in 'ENO':
        s=gate['summaries'][a];summary.append(f'| {a} | {s["parseable"]}/12 | {s["committed_finals"]}/12 | {s["caps"]}/12 | {s["repetitions"]}/12 | {"PASS" if gate["pass_by_arm"][a] else "FAIL"} |')
    summary += ['', 'E commitment is not a task-solving endpoint; E parseability is the relevant gate. '
        'Native spontaneous reasoning is permitted. Semantic repetition review is separate from token n-gram diagnostics. '
        'No gold correctness entered the technical gate. No prompt/cap adaptation was performed.','',
        '## Oracle integrity','',
        '61 source-only checks and13/61 (21.3%) randomly selected second-pass reviews completed before generation. '
        'The second pass used the same agent, not an independent rater. Actual oracle inputs contain no image and generated input receipts verify zero visual tokens. '
        'Bare values retain their exact original request labels. Original empty question528 is retained, with target implied by its frozen question-mark-cloud fact; '
        'this is an explicit input limitation. Literal image references remain text. Direct-classification item458 requires minimal downstream inference.','',
        '## Scientific profile','']
    if science:
        summary += ['| Endpoint | Count | Proportion | Wilson95% |','|---|---:|---:|---|']
        for p,s in inference['endpoints'].items():summary.append(f'| {p} | {s["numerator"]}/{s["denominator"]} | {s["estimate"]} | {s["wilson95"]} |')
        summary += ['', 'B1–B4 counts: '+str(inference['classes']), '', '4000 independent-family bootstrap draws; selected contrasts and exclusions in primary inference JSON.']
    else:
        summary += ['P1–P6, B1–B4, oracle-rescue contrasts and accuracy: **NOT_ESTIMATED**. '
            'Unrun/null rows are not errors. The gate failed before scientific correctness was opened; no remaining49 families were generated. '
            'This is not evidence for or against perceptual, access/use or downstream dominance. Cause of any noncompletion remains unresolved.']
    summary += ['', 'All labels, if estimable, are bottleneck candidates: E−does not establish absent encoding; E+does not establish native retrieval; '
        'O+changes evidence representation; O−does not prove perfect perception. This cohort is developmental, not population-wide prevalence.','',
        '## Resources and evidence','',f'{completed}/183 calls completed; {183-completed} NOT_RUN. **{resources["allocated_gpu_hours"]:.6f} allocated GPU-hours**, '
        'including startup and teardown; target<6/hard8. All stage GPUs released. No download/install, CoT, Thinking or further experiment.','',
        '[Read complete responses](../../../reports/stage12b/v1/index.md). Exact inputs, text/tokenIDs and receipts are in generations/; '
        'reviews, source hashes and statistical specification are preserved. All15 required root artifacts and four PNG/PDF figures accompany this report.','',
        '## Exactly one recommendation','', recommendations[decision]+' This recommendation was not executed.']
    with (ROOT/'stage12b_summary.md').open('x') as f:f.write('\n'.join(summary)+'\n')
    print('CLOSED',decision,completed,resources['allocated_gpu_hours'])

if __name__=='__main__':main()
