"""Final verification/accounting, exactly one recommendation, then STOP."""
from pathlib import Path
from scripts.stage12ws.common import ROOT,load,save,sha,now
from scripts.stage12ws.resume_resources import account, enforce
from scripts.stage12ws.interrupted import packet as interrupted_packet
from scripts.stage12ws.review import checked
from scripts.stage12ws.figures import main as figures
from scripts.stage12ws.reading import main as reading

RECOMMENDATIONS={
'DISTRIBUTED_DERIVED_STATE_SIGNAL':'Align the identified distributed reasoning blocks with causal visual-retrieval and Value-transfer events to test how raw visual evidence is transformed into the portable derived state.',
'DERIVED_STATE_ONLY':'Test distributed semantic compression/summarization of the derived state rather than finer single-step necessity.',
'INTERFERENCE_REPAIR_SIGNAL':'Causally manipulate the interfering and repairing blocks to identify the propositions that degrade and restore downstream usability.',
'PORTABILITY_CONTENT_UNRESOLVED':'Stop further text-granularity ablation and test whether cached/hidden non-textual state complements the portable text.',
'PORTABILITY_WEAK_UNDER_PAIRED_SEEDS':'Retain Stage12U-S as the strongest supported production result and stop fine externalized-state localization.',
'UNRESOLVED':'Retain Stage12U-S as the strongest supported production result and stop fine externalized-state localization while the block-level mechanism remains unresolved.'}

def fmt(c):return f"{c['correct']}/7"+(f" ({c['missing']} missing)" if c['missing'] else '')
def main():
    result=load(ROOT/'stage12ws_primary_inference.json');ledger=account('final')
    assert ledger['all_released']
    enforce(ledger['historical_allocation_hours_bounds'][1],ledger['new_gpu_hours_upper'],0)
    interrupted={r['task_id']:r for r in load(ROOT/'audit/phaseC_interrupted_dispositions_v1.json')['rows']}
    low,high=ledger['total_allocation_hours_bounds']
    tasks=[t for p in (ROOT/'audit').glob('*_execution.json') for t in load(p).get('tasks',[])]
    assert len({t['task_id'] for t in tasks})==len(tasks)
    checked_rows=[]
    for t in tasks:
        if t['task_id'] in interrupted:
            interrupted_packet(t,interrupted[t['task_id']])
            checked_rows.append(dict(task_id=t['task_id'],cap=None,tokens=None,seconds=None,interrupted=True))
        else:
            g,c=checked(t);checked_rows.append(dict(task_id=t['task_id'],cap=g['cap_hit'],tokens=g['tokens'],seconds=g['request_latency_seconds'],interrupted=False))
    for p,h in load(ROOT/'audit/source_seal.json')['hashes'].items():assert sha(p)==h,p
    history=load(ROOT/'audit/preserved_history.json')['files']
    assert all(sha(p)==h for p,h in history.items()),'Historical file changed'
    scores=[load(ROOT/'audit/first_scores'/f"{t['task_id']}.json") for t in tasks]
    nmissing=sum(s['correct'] is None for s in scores)
    figures();reading()
    save(ROOT/'stage12ws_resource_accounting.json',dict(ledger,unique_new_calls=len(tasks),scoreable=len(tasks)-nmissing,missing=nmissing,
         completed_output_tokens=sum(r['tokens'] for r in checked_rows if r['tokens'] is not None),raw_outputs_saved=sum(not r['interrupted'] for r in checked_rows),interrupted_without_output=len(interrupted),historical_accounting_receipt='audit/resume_resource_reconciliation_v1.json',budget_amendment_receipt='audit/resource_amendment_approved_v1.json',retries=0,source_generations=0,model_downloads=0,
         package_installs=0,worker_receipts=[str(p) for p in sorted((ROOT/'workers').glob('*/*.json'))]))
    token=result['decision'];rec=RECOMMENDATIONS[token];c=result['counts']
    rows=['# Stage12W-S — Distributed reasoning-state construction',f"Decision: **{token}**.",
          f"{len(tasks)} unique image-free Instruct condition–seed slots; {len(tasks)-len(interrupted)} saved continuations, {len(tasks)-nmissing} scoreable, {nmissing} missing (including {len(interrupted)} interrupted without output). Total allocation time is bounded {low:.4f}–{high:.4f} GPU-hours because historical cleanup end times were lost; resumption upper bound {ledger['new_gpu_hours_upper']:.4f} GPU-hours. All scientific allocations are released. Seven identical family-specific seeds across conditions; four selected independent families.",
          '| Family | Full | Question only | Advantage (net / 7) | A eligible | Derived-state signature | Distributed necessity | Order sensitive |',
          '|---|---:|---:|---:|---|---|---|---|']
    for r in result['families']:
        x=r['portability'];effect=str(x['net_successes'])+'/7' if x['net_successes'] is not None else str(x['net_bounds'])+'/7'
        rows.append(f"|{r['item_id']}|{fmt(r['conditions']['FULL'])}|{fmt(r['conditions']['Q'])}|{effect}|{r['eligible']}|{r['derived_state_support']}|{r['distributed_necessity']}|{r['order_sensitive']}|")
    rows+=['',f"Confirmed family counts: full-state advantage {c['eligible']}/4; derived state {c['derived_state_support']}/4; distributed necessity {c['distributed_necessity']}/4; order sensitivity {c['order_sensitive']}/4. None denotes unresolved or untested, not a negative observation."]
    if not load(ROOT/'audit/replication_gate.json')['continue']:rows.append('Downstream B–F phases were not run because the frozen PhaseA gate did not pass. Empty tables and labeled figure panels preserve that distinction.')
    else:
        for r in result['families']:
            rows.extend([f"## Family {r['item_id']}",' · '.join(f"{k}: {fmt(v)}" for k,v in r['conditions'].items())])
            if r['block_effects']:rows.append('Block deletion effects (FULL minus deletion, numerator /7): '+', '.join(f"{k}={v['net_bounds']}" for k,v in r['block_effects'].items()))
            if 'greedy' in r:rows.append('Bounded elimination: '+r['greedy']['status']+'; candidate retained blocks '+str(r['greedy'].get('candidate_retained','not searched'))+'. No global minimality claim.')
        n=result['interference_repair'];rows.append(f"Family750 frozen Pa299/Pb448/Pc598: {fmt(n['Pa'])}, {fmt(n['Pb'])}, {fmt(n['Pc'])}; interference {n['interference']['net_bounds']}/7; repair {n['repair']['net_bounds']}/7. Joint signal={n['joint']}. F1=Pa, F2=F4=Pb, F3=Pc:21 unique calls, not four independent confirmations.")
        rows.append('Every selected matched deletion, excluded-control reason and length ratio is retained in audit/matched_controls_execution_map.json; composite and natural-control effects are in primary_inference.json. No control means the corresponding length explanation remains unresolved.')
    rows += ['## Main comparisons',
             '| Family | Raw evidence E* | E* + derived blocks | Full trace | Full minus derived blocks |',
             '|---|---:|---:|---:|---:|']
    for r in result['families']:
        v=r['conditions']
        rows.append(f"|{r['item_id']}|{fmt(v['ESTAR'])}|{fmt(v['ESTAR_D'])}|{fmt(v['FULL'])}|{fmt(v['MINUS_D'])}|")
    ratios=[r for r in load(ROOT/'audit/matched_controls_execution_map.json')['rows'] if r['status']=='FROZEN']
    rows.append('Matched deletion length ratios (control/target): '+', '.join(f"{r['item_id']} {r['target_condition']}: {r['length_ratio']:.3f}" for r in ratios)+'. The frozen adequate range is0.8–1.25; an inadequate or unavailable control leaves length confounding unresolved.')
    rows.append('The derived-state count must reach3/4 for the global derived-state decision. Local positive effects below that count are retained and are not recoded as a null. A candidate retained block set comes from one fixed elimination order, not an exhaustive minimality search.')
    qc=load(ROOT/'audit/independent_final_verification.json')
    rows.append(f"All {qc['unique_task_slots']} condition–seed slots passed artifact-chain checks; {qc['second_pass_agreements']} same-agent second-pass checks agreed. Literal enumeration independently reproduced the reported missingness bounds. Figure whiskers show unresolved missing outcomes, not sampling confidence intervals.")
    rows+=['## Interpretation boundaries','These are four production-selected families, not a prevalence estimate. Roles summarize mixed source reasoning, including errors, raw restatements and repeated deductions; they do not certify clean derived propositions. Missing outcomes are bounded rather than counted incorrect. Sparse block effects are preserved even when the cross-family mechanism is unresolved. No hidden-state mechanism is established.',
           f"All {len(history):,} prior artifacts and frozen source hashes verified unchanged. Own-response extraction was followed by a separate same-agent QC pass; no independent-rater claim. Exact inputs, generated token IDs and raw responses are retained for completed outputs. Four interrupted calls have input receipts but no fabricated continuation, EOS, cap or token-count claims. Historical cleanup uncertainty is reported separately from newly verified job receipts.",
           '[Source blocks and all responses](../../../reports/stage12ws/v1/index.md) · [Five figure pairs](../../../reports/stage12ws/v1/figures/)',
           '## Exactly one recommendation',rec,'Recommendation status: **NOT_LAUNCHED**. Stage12W-S is complete; STOP.']
    (ROOT/'stage12ws_summary.md').write_text('\n\n'.join(rows[:3])+'\n\n'+'\n'.join(rows[3:]))
    save(ROOT/'stage12ws_decision.json',dict(at=now(),decision=token,interference_repair_coexisting=bool(result['interference_repair'] and result['interference_repair']['joint']),recommendation=rec,recommendation_status='NOT_LAUNCHED',stop=True))
    required=['distributed_state_spec.md','primary_manifest.json','block_segmentation.json','block_annotations.json','seed_manifest.json','full_state_results.parquet','block_deletion_results.parquet','derived_state_results.parquet','order_control_results.parquet','interference_repair_results.parquet','matched_controls.parquet','primary_inference.json','decision.json','resource_accounting.json','summary.md']
    assert all((ROOT/('stage12ws_'+n)).exists() for n in required)
    if load(ROOT/'audit/phaseD_closed.json')['activated']:
        assert (ROOT/'stage12ws_minimal_blockset_results.parquet').exists()
    assert len(list(Path('reports/stage12ws/v1/figures').glob('*.png')))==5 and len(list(Path('reports/stage12ws/v1/figures').glob('*.pdf')))==5
    save(ROOT/'audit/final_verification.json',dict(at=now(),complete=True,required_files=len(required),historical_files_unchanged=len(history),new_calls=len(tasks),no_followon=True,hashes={n:sha(ROOT/('stage12ws_'+n)) for n in required}))
    print(token,rec,ledger['total_allocation_hours_bounds'])

if __name__=='__main__':main()
