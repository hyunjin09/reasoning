"""Bounded claim gates; optional assays must be explicitly resolved first."""
import os
from scripts.stage9a5.common import ROOT, load, save, sha, now
from scripts.stage9a5.decisions import relative_gate, reserve_gate


def main():
    assert os.environ.get('SLURM_JOB_ID')
    baseline=load(ROOT/'stage9a5_thinking_full_baseline.json');assert baseline['gates']['pass']
    d=load(ROOT/'audit/absolute_final_decision.json');c=load(ROOT/'stage9a5_absolute_access_comparison.json')
    s=d['surface'];contrast=c['contrasts']['t128'];rel=load(ROOT/'stage9a5_relative_time_analysis.json')
    sink=load(ROOT/'stage9a5_null_sink_control.json')
    if d['action']=='stop_zero':control_ok=False
    else:
        assert sink['status']=='complete'
        ss=sink['surface'];finite=f"t{d['cutoff']}"
        control_ok=(ss['t0']['damage']>.05 and
                    ((ss[finite]['damage']<=.05) == (d['action']=='selected')))
    rg=relative_gate(s,contrast,rel);eg=reserve_gate(s,contrast,control_ok)
    optional={}
    for name,needed,reason in [
        ('relative_time_intervention',rg,'No positive insufficient128 pattern with longer/lower-exposure Thinking traces.'),
        ('reserve_extension',eg,'Frozen positive-and-precision-limited rule with valid controls is not met.')]:
        path=ROOT/f'stage9a5_{name}.json'
        if needed:
            assert path.exists(),f'Approved optional assay required: {name}'
            optional[name]=load(path);assert optional[name]['status']=='complete'
        elif not path.exists():
            optional[name]=dict(at=now(),status='not_run',gate_passed=False,reason=reason)
            save(path,optional[name])
        else:
            optional[name]=load(path);assert optional[name]['status']=='not_run'
    if d['action']=='stop_zero':outcome='D'
    elif s['t128']['damage']<=.05:outcome='A'
    elif d['action']=='selected':outcome='B'
    else:outcome='C'
    relative_support=optional['relative_time_intervention'].get('positive_relative_support',False) if rg else None
    primary=optional['reserve_extension'].get('combined_primary_contrast',contrast)
    gates=dict(full_valid=True,zero_damage=s['t0']['damage']>.05,thinking128_insufficient=s['t128']['damage']>.05,
               paired128_positive_support=primary['ci95'][0]>0,
               later_budget_evaluated='t256' in s,
               relative_assay_support=(bool(relative_support) if rg else None),
               bounded_control_qualitative_support=bool(control_ok))
    prolonged=bool(gates['zero_damage'] and gates['thinking128_insufficient'] and gates['paired128_positive_support'] and
                   gates['later_budget_evaluated'] and control_ok and (not rg or relative_support))
    if prolonged:
        recommendation='Develop the Thinking-specific visual-access-regime claim and test whether the extra necessity is aligned with controlled recurrent visual demand.'
    else:
        recommendation='Retain dynamic visual re-access as the main Thinking mechanism and emphasize the dissociation between native causal use and ablation necessity rather than a Thinking-specific VAB claim.'
    statements={
        'A':'Thinking and prompted CoT share coarse finite direct-access sufficiency at token128 under the frozen point-based5pp criterion. This is not an equivalence test.',
        'B':'Thinking first preserves at token256; CoT preserves at128. Later absolute sufficiency alone does not establish later relative-phase necessity.',
        'C':'Finite direct-access sufficiency is not established for Thinking through256. FULL access is not proven strictly necessary.',
        'D':'ZERO does not establish generated-query direct visual necessity for Thinking; the necessity branch stops.'}
    figure_lines={
        'A':f'Stage9A.5 · matched4B checkpoints\nCoT: first tested preserving cutoff128\nThinking: first tested preserving cutoff{d["cutoff"]}\nNo supported Thinking-specific prolonged claim',
        'B':'Stage9A.5 · matched4B checkpoints\nCoT preserves128; Thinking preserves256\nAbsolute and relative necessity are separate\nSee paired uncertainty and control gates',
        'C':'Stage9A.5 · matched4B checkpoints\nThinking remains damaged through256\nCoT preserves128\nNo proof that FULL access is strictly necessary',
        'D':'Stage9A.5 · matched4B checkpoints\nThinking ZERO damage ≤5pp\nGenerated-query necessity not established\nNo later-cutoff search'}
    out=dict(at=now(),status='complete_stop',outcome=outcome,interpretation=statements[outcome],
             selected_cutoff=d['cutoff'],selected_cutoff_sufficient=d['action']=='selected',
             primary32_contrast=contrast,primary_claim_gates=gates,thinking_specific_prolonged_claim=prolonged,
             relative_gate=rg,reserve_gate=eg,control_qualitative_support=bool(control_ok),
             recommendation=recommendation,next_experiment_launched=False,figure_conclusion=figure_lines[outcome],
             limitations=['32 independent synthetic images; two queries per image.',
                          'Generated-query image keys are masked; native prefill and image-derived cache remain available.',
                          'Checkpoint/training specialization confounded; no causal attribution to thinking, DeepStack or objective.',
                          'Point-based5pp preservation and interval support are reported separately.',
                          'Capped generated horizons are right-censored.'],
             inputs_sha256={str(p):sha(p) for p in [ROOT/'stage9a5_absolute_access_comparison.json',ROOT/'stage9a5_null_sink_control.json',ROOT/'stage9a5_relative_time_analysis.json']})
    out['selected_cutoff_scope']='standard image-key masking'
    if outcome=='A' and not control_ok:
        out['outcome_scope']='OutcomeA for standard masking; selected-cutoff preservation fails the bounded null-sink control.'
        out['interpretation']+=' This preservation result is specific to standard masking: Thinking token128 does not preserve under null-sink. Robust shared sufficiency across the two interventions is not established.'
        out['limitations'].append('Null-sink128 fails Thinking preservation; do not present shared finite sufficiency as robust to redistribution control.')
        out['figure_conclusion']='Stage9A.5 · matched4B checkpoints\nStandard: both first preserve at128\nThinking null-sink128:10.94pp damage\nPreservation does not replicate in this control\nNo supported Thinking-specific prolonged claim'
    diagnostic=ROOT/'audit/control_completion_diagnostic.json'
    if diagnostic.exists():
        out['control_diagnostic_sha256']=sha(diagnostic)
        out['control_failure_cause_status']=load(diagnostic)['cause_status']
    save(ROOT/'stage9a5_cot_vs_thinking_inference.json',out)
    print({k:v for k,v in out.items() if k not in ('inputs_sha256','primary32_contrast')},flush=True)


if __name__=='__main__':main()
