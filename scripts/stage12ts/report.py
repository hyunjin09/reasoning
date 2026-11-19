"""Five prescribed figures and a report separating rescue from causal claims."""
import json,textwrap
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scripts.stage12ts.common import ROOT,load,now
from scripts.stage12ts.review import all_tasks,folder_for

def fmt(p):
    if p['estimate'] is None:return f"undefined (0/{p['denominator']})"
    lo,hi=p['wilson95'];return f"{p['numerator']}/{p['denominator']} ({p['estimate']:.1%}; Wilson95% {lo:.1%}–{hi:.1%})"

def savefig(fig,name):
    (ROOT/'figures').mkdir(exist_ok=True)
    for ext in ['png','pdf']:fig.savefig(ROOT/f'figures/{name}.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)

def responses():
    dest=Path('reports/stage12ts/v1');dest.mkdir(parents=True,exist_ok=True)
    lines=['# Stage12T-S full Thinking responses','','Original Thinking scratchpads and final channels, with exact inputs. Reused outputs are copied for reading only; immutable generation records stay at their original paths.','']
    for t in all_tasks():
        folder=folder_for(t)
        if not (folder/'result.json').exists():continue
        g=load(folder/'generation.json');tid=t['task_id'];p=dest/f'{tid}.md'
        if not p.exists():p.write_text(f"# {tid}\n\n{t['family_id']} · {g['tokens']} tokens · {g['finish_reason']}\n\n## Input\n\n{t['prompt']}\n\n## Full raw response\n\n"+g['raw_decoded_response']+'\n')
        lines.append(f"- [{tid}]({tid}.md) — {g['tokens']} tokens; {g['finish_reason']}")
    (dest/'index.md').write_text('\n'.join(lines)+'\n')

def main():
    r=load(ROOT/'stage12ts_primary_inference.json');d=load(ROOT/'stage12ts_decision.json');tech=load(ROOT/'audit/denominator_seal.json')
    review=load(ROOT/'stage12ts_scoring_review_log.json');sens=load(ROOT/'stage12ts_sensitivity_results.json')
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    bs=['B1','B2','B3','B4'];x=np.arange(4)
    fig,ax=plt.subplots(figsize=(8,4))
    ax.bar(x,[r['by_stratum'][b]['frozen_total'] for b in bs],color='#dce2e8',label='Frozen native failures')
    ax.bar(x-.17,[r['cot_by_stratum'][b]['numerator'] for b in bs],width=.32,color='#8994a1',label='CoT rescue')
    ax.bar(x+.17,[r['by_stratum'][b]['numerator'] for b in bs],width=.32,color='#287eac',label='Thinking rescue')
    for j,b in enumerate(bs):
        p=r['by_stratum'][b];ax.text(j,p['frozen_total']+.25,f"T {p['numerator']}/{p['denominator']} scoreable",ha='center',fontsize=8)
    ax.set_xticks(x,bs);ax.set_ylim(0,14);ax.set_ylabel('Independent families');ax.legend();ax.set_title('Frozen failure map with CoT and Thinking rescue')
    savefig(fig,'T1_failure_map_rescue')
    fig,ax=plt.subplots(figsize=(7,4))
    for j,(b,mode) in enumerate([('B1','C'),('B1','T'),('B4','C'),('B4','T')]):
        p=r['cot_by_stratum' if mode=='C' else 'by_stratum'][b];v=p['estimate']
        if v is not None:
            lo,hi=p['wilson95'];ax.errorbar(j,v,yerr=[[v-lo],[hi-v]],fmt='o',capsize=5,color='#8994a1' if mode=='C' else '#287eac');ax.text(j,hi+.035,f"{p['numerator']}/{p['denominator']}\n{p['missing']} missing",ha='center',fontsize=9)
    ax.set_xticks(range(4),['B1 CoT','B1 Thinking','B4 CoT','B4 Thinking']);ax.set_xlim(-.6,3.6);ax.set_ylim(-.05,1.25);ax.set_ylabel('Rescue fraction');ax.set_title('Scoreable rescue fractions: Wilson95% intervals')
    savefig(fig,'T2_primary_rescue_by_mode')
    fig,ax=plt.subplots(figsize=(8,4));p=r['primary']['T-P4']['B1'];ks=['BOTH_WRONG','FIRST_ONLY','THINKING_ONLY','BOTH_CORRECT','UNSCOREABLE_TECHNICAL'];vals=[p['counts'][k] for k in ks]
    ax.bar(range(5),vals,color=['#a5acb3','#b35e68','#287eac','#238d71','#dce2e8'])
    for j,v in enumerate(vals):ax.text(j,v+.1,str(v),ha='center')
    ax.set_xticks(range(5),['Both fail','CoT only','Thinking only','Both succeed','Missing pair']);ax.set_ylabel('B1 independent families');ax.set_title('B1 paired CoT-to-Thinking outcomes')
    savefig(fig,'T3_B1_paired_transitions')
    states=['TRACE_E_FULL','TRACE_E_PARTIAL','TRACE_E_WRONG_OR_CONFLICTING','TRACE_E_NOT_EXTERNALIZED'];names=['Full','Partial','Wrong/conflicting','Not externalized']
    mat=np.array([[r['B1_evidence_transitions'].get(a+' → '+b,0) for b in states] for a in states])
    fig,ax=plt.subplots(figsize=(7,5));ax.imshow(mat,cmap='Blues',vmin=0,vmax=max(1,mat.max()))
    for i in range(4):
        for j in range(4):ax.text(j,i,str(mat[i,j]),ha='center',va='center',color='white' if mat[i,j]>mat.max()/2 else 'black')
    ax.set_xticks(range(4),names,rotation=20,ha='right');ax.set_yticks(range(4),names);ax.set_xlabel('Thinking visible evidence state');ax.set_ylabel('CoT visible evidence state');ax.set_title('B1 evidence-state transitions (all annotated families)')
    savefig(fig,'T4_B1_evidence_transitions')
    examples=load(ROOT/'audit/T5_deterministic_examples.json');ex=examples['examples']
    fig,ax=plt.subplots(figsize=(10,max(3,len(ex)*3)));ax.axis('off')
    if not ex:body='No qualifying Thinking-only evidence-recovery rescue.\n\nFrozen signature: B1 and C− and T+ and TRACE_E_FULL(T).\nNo alternative cases substituted.'
    else:
        blocks=[]
        for e in ex:
            facts='; '.join(str(f['fact_id'])+': '+str(f['gold_value']) for f in e['facts'])
            blocks.append(f"Item {e['item_id']} · {e['family_id']}\nN− / C− / T+ · C {e['C_state']} → T FULL\nE*: {facts}\nTrace evidence: {e['reason']}")
        body='\n\n'.join('\n'.join(textwrap.fill(line,110) for line in b.splitlines()) for b in blocks)
    ax.text(.02,.98,body,va='top',fontsize=10,transform=ax.transAxes);ax.set_title('Thinking-only evidence-linked rescues: deterministic examples')
    savefig(fig,'T5_evidence_linked_examples')
    responses()
    lines=['# Stage12T-S Thinking scientific rescue and visual evidence recovery','',f"**{' + '.join(d['states'])}**. {now()}",'',
        'Frozen61-family MathVision developmental cohort,157 E* facts;24 validated Thinking81920 responses reused unchanged and37 new calls. Prior E/N/O/C outputs and labels preserved. This is a different-checkpoint/native-recipe comparison, not a causal Thinking-on/off intervention. Visible trace evidence does not establish hidden-state retrieval.','',
        'Qwen3-VL-4B-Thinking1de27d8c51f12e819435303b9e84c4e25ba8401e; original image/question, no suffix; temperature1/top-p.95/top-k20/repetition1/presence0/cap81920. Same BF16/vLLM runtime, preprocessing and family seeds. No retries or decoding search.','',
        f"Technical input-valid{tech['counts']['INPUT_VALID']}/61,scoreable{tech['counts']['SCOREABLE']}/61,pre-outcome caps{tech['counts']['TRUNCATED_BEFORE_OUTCOME']}. R1–R4 are behaviors rather than exclusions. Technical missingness is never an incorrect answer.",'',
        '| Stratum | Thinking rescue | Frozen total | Missing | Missingness bounds |','|---|---|---:|---:|---|']
    for b in bs:
        p=r['by_stratum'][b];lines.append(f"| {b} | {fmt(p)} | {p['frozen_total']} | {p['missing']} | {p['missingness_identification_bounds']} |")
    lines += ['',
        'Interpretation: the frozen decision is a downstream signal, not a demonstrated downstream mechanism. Thinking rescues five B4 families that Native Instruct failed even with correct evidence supplied; all five also fail under prompted CoT. B1 has only three rescues, two Thinking-only successes and one Thinking-only FULL-evidence case, below the visual-recovery thresholds of five/three/three. Thus this stage does not establish improved visible evidence recovery as a substantial source of the variant advantage.', '',
        'The B1 minus B4 estimate is negative, but its bootstrap interval includes zero. The comparison changes checkpoint, decoding recipe and available output budget (CoT 32,768; Thinking 81,920); none of these contributions is isolated. S1 retains three B4 rescues in eight families; S2 retains only two B4 families and rescues neither, so the main signal is not independently validated by a substantial untouched subset.', '']
    lines+=['',f"T-P3 B1−B4 selectivity: {r['primary']['T-P3']['estimate']};4000-family-bootstrap95%{r['primary']['T-P3']['percentile95']},seed{r['bootstrap_seed']}. Equal-weight independent families; B2/B3 and B1 subtypes are descriptive. B1 means incomplete demonstrated recovery of task-critical visual evidence, not uniformly visual misreading.",'',
        f"Central signature: {r['evidence_B1']['thinking_only_evidence_recovery_rescues']} B1 families are CoT-wrong, Thinking-correct and TRACE_E_FULL(T). Total B1 evidence-linked Thinking rescues: {r['evidence_B1']['evidence_linked_rescues']}.",'']
    for title,value in [('Primary paired C/T transitions',r['primary']['T-P4']),('B1 visible evidence and outcome',r['evidence_B1']),('B1 subtypes',r['B1_subtypes']),('B1 evidence-state transitions',r['B1_evidence_transitions']),('Secondary common-denominator accuracy and paired transitions',r['overall']),('Pathology counts',r['pathology_counts']),('B4 pathology transitions',r['pathology_B4'])]:
        lines += [title+':','','```json',json.dumps(value,indent=2),'```','']
    lines+=['Sensitivity analyses use the same definitions and never replace the main decision. S2 includes documented pre-Stage12T-S technical exposures across the lineage, including Stage11C/R and official protocol validation. Scientific generations alone do not count as technical development.','',
        '| Sensitivity | Retained families | B1 T rescue | B4 T rescue | T-only B1 | T-only FULL B1 |','|---|---:|---|---|---:|---:|']
    for name,ss in sens['results'].items():
        rr=ss['inference'];lines.append(f"| {name} | {ss['remaining_families']} | {fmt(rr['primary']['T-P1'])} | {fmt(rr['primary']['T-P2'])} | {rr['primary']['T-P4']['B1']['counts']['THINKING_ONLY']} | {rr['evidence_B1']['thinking_only_evidence_recovery_rescues']} |")
    lines+=['',f"Review:61 T-only first scores;{review['audit']['second_pass_calls']} separate-pass second reviews. All technical and26evidence-trace annotations sealed before correctness. Same-agent packet-blinded review, not independent inter-rater reliability; per-case coverage and literal evidence are preserved.",'',
        'Review coverage limitation: long responses were inspected using deterministic excerpts, answer contexts, complete endings and fact-targeted searches. This was not exhaustive reading of every long trace. Positive pathology/evidence labels have quoted witnesses; negative pathology and not-externalized labels mean not established in the inspected passages. These descriptive annotations are not independent human validation. R1–R4 do not change scoreability.','',
        'The original cap-validation prefix divergences remain unresolved; no pure-budget explanation is claimed. Any B4 rescue may involve downstream/checkpoint differences and is not attributed solely to visual recovery. Small stratum counts limit precision; no benchmark-wide prevalence claim.','',
        'Resource accounting: stage12ts_resource_accounting.json. No automatic follow-on experiment.','']
    for name in ['T1_failure_map_rescue','T2_primary_rescue_by_mode','T3_B1_paired_transitions','T4_B1_evidence_transitions','T5_evidence_linked_examples']:lines.append(f'- [{name}](figures/{name}.png) · [PDF](figures/{name}.pdf)')
    lines+=['','[Full Thinking responses](../../../reports/stage12ts/v1/index.md).','', '**Exactly one recommendation:** '+d['recommendation'],'','STOP. Recommendation not executed.']
    (ROOT/'stage12ts_summary.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':main()
