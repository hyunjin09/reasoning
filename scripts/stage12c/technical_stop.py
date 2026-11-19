"""Close a failed sanity gate without inventing scientific scores or estimates."""
import pandas as pd
from scripts.stage12c.common import ROOT,load,save,sha,now
from scripts.stage12c.resources import account
from scripts.stage12c.seal import preservation
from scripts.stage12c.responses import main as response_archive


def main():
    gate=load(ROOT/'stage12c_technical_sanity.json')
    assert gate['decision']=='TECHNICAL_STOP' and not gate['pass']
    assert not (ROOT/'audit/correctness_opened.json').exists()
    assert len(list((ROOT/'generations').glob('*/result.json')))==24
    preserved=preservation();resource=account('technical_stop',final=True)
    for arm,name in [('C','cot'),('T','thinking')]:
        rr=[dict(r,execution_phase='sanity_only') for r in gate['rows'] if r['arm']==arm]
        path=ROOT/f'stage12c_{name}_results.parquet';assert not path.exists()
        pd.DataFrame(rr).to_parquet(path,index=False)
    empty_tables={
        'cot_scoring_blind':['task_id','family_id','label','correct'],
        'thinking_scoring_blind':['task_id','family_id','label','correct'],
        'rescue_transitions':['family_id','item_id','bottleneck','c','t','CT_transition'],
        'trace_evidence_states':['family_id','item_id','arm','state'],
        'pathology_transitions':['family_id','item_id','arm','N_transition','O_transition']}
    for name,columns in empty_tables.items():
        path=ROOT/f'stage12c_{name}.parquet';assert not path.exists()
        pd.DataFrame({c:pd.Series(dtype='object') for c in columns}).to_parquet(path,index=False)
    not_run=dict(at=now(),status='NOT_RUN_TECHNICAL_STOP',reason='Both-arm sanity gate required before remainder or scientific scoring.',
                 correctness_opened=False,remaining_calls_not_run=98,estimates=None)
    save(ROOT/'stage12c_scoring_review_log.json',dict(not_run,first_pass_calls=0,second_pass_calls=0,reviews=[]))
    save(ROOT/'stage12c_primary_inference.json',dict(not_run,primary={k:None for k in ['P1','P2','P3','P4']},
        empty_tables=list(empty_tables),figures_status='NOT_RUN: no rescue/trace/correctness inference after failed technical gate'))
    decision=dict(at=now(),decision='TECHNICAL_STOP',sanity_gate_sha256=sha(ROOT/'stage12c_technical_sanity.json'),
        gate=gate['summaries'],correctness_opened=False,scientific_rescue_decision='NOT_EVALUATED',
        diagnosis='unknown',
        recommendation='Suspend Stage12C scientific rescue profiling and require a separately approved technical validation of the4B Thinking MathVision completion regime before a rerun.',
        recommendation_executed=False)
    save(ROOT/'stage12c_rescue_decision.json',decision)
    response_archive()
    summary=['# Stage12C — technical sanity stop','',f"**TECHNICAL_STOP**. Closed {now()}.",'',
        'The approved12-family C/T sanity check is complete. The joint frozen gate failed; the98 remaining calls were not launched. No correctness,rescue comparison or visible-evidence inference was opened. This is a technical noncompletion result,not evidence of sparse scientific rescue.','',
        '## Prospective protocol','',
        'The user explicitly approved native4B Thinking sampling with temperature1.0,top-p.95,top-k20,repetition1.0,presence0,max40960. This clarification preceded generation and excluded the task-specific synthetic-counting greedy512 recipe. The pinned checkpoint,identity-only sanity families,prompts,original N seeds and all prior labels remained sealed. C used the unchanged32768-token Instruct recipe and only the approved CoT suffix. Both usedBF16/vLLM in the existing project-local environment.','',
        '## Frozen technical gate','',
        'Each arm requires12/12valid inputs,at least10/12scoreable answers,and at most1/12pre-outcome cap. Repetition has no gate threshold.','',
        '| Arm | Valid inputs | Scoreable | Pre-outcome caps | Total cap hits | Pass |','|---|---:|---:|---:|---:|---|']
    for arm in 'CT':
        s=gate['summaries'][arm];rr=[r for r in gate['rows'] if r['arm']==arm]
        summary.append(f"| {arm} | {s['INPUT_VALID']}/12 | {s['SCOREABLE']}/12 | {s['TRUNCATED_BEFORE_OUTCOME']}/12 | {sum(r['cap_hit'] for r in rr)} | {gate['pass_by_arm'][arm]} |")
    summary.extend(['','Unscoreable cases (never graded as incorrect):',''])
    for r in gate['rows']:
        if not r['SCOREABLE']:summary.append(f"- {r['task_id']}: {r['tokens']:,} tokens,{r['stop_reason']}. {r['reason']}")
    summary.extend(['','All raw responses,token IDs,input/pixel hashes,model/config receipts and semantic technical annotations are preserved. Native Thinking scratchpad guesses are provisional; a cap does not promote them to committed final answers. R1–R5 annotations remain descriptive and do not replace the explicit gate.','',
        '## Preservation and resources','',
        f"Historical hash verification:{preserved['history']} files unchanged; frozen specifications and generation source verified. Exactly24 new calls,no retries. Allocated GPU-hours:{resource['allocated_gpu_hours']:.6f},including initialization; both finite Slurm allocations released. No environment mutation or dataset/model download.",'',
        '## Deliverable status','',
        'The two result parquets contain the12 generated sanity responses per arm. Required scoring,transition and trace tables are schema-bearing empty files explicitly marked NOT_RUN_TECHNICAL_STOP by primary_inference.json. Primary endpoints are null,not zero. Five scientific figures were not generated because their underlying comparisons were not authorized after the gate failed. The original61-family/157-fact inventory remains intact.','',
        '[Full unabridged C/T responses for all12 sanity families](../../../reports/stage12c/v1/index.md).','',
        'The immediate cause of the observed completion behavior is unknown. Input integrity checks do not establish whether the wider model/runtime operating regime is appropriate; no prompt or decoding search was performed.','',
        '## Exactly one recommendation','',decision['recommendation'],'','**STOP. Recommendation not executed.**'])
    path=ROOT/'stage12c_summary.md';assert not path.exists();path.write_text('\n'.join(summary)+'\n')
    print('Stage12C closed at technical sanity gate; correctness remains unopened.')


if __name__=='__main__':main()
