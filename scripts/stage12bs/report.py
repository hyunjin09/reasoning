"""Required fixed figures and a navigable archive of all preserved responses."""
import json
import textwrap
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scripts.stage12bs.common import ROOT, load, save, now
from scripts.stage12bs.review import origin_for

COLORS=['#2563a6','#168a78','#bb6b21','#7b7185']
NAMES=['B1: Evidence recovery','B2: Context access/use','B3: Downstream reasoning','B4: Mixed / unresolved']


def figure_save(fig,name):
    target=ROOT/'figures';target.mkdir(exist_ok=True)
    for ext in ['png','pdf']:fig.savefig(target/f'{name}.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)


def pct(p):
    if p['estimate'] is None:return 'undefined'
    low,high=p['wilson95']
    return f"{p['numerator']}/{p['denominator']} = {p['estimate']:.1%} [{low:.1%}, {high:.1%}]"


def main():
    result=load(ROOT/'stage12bs_primary_inference.json');decision=load(ROOT/'stage12bs_profile_decision.json')
    audit=load(ROOT/'stage12bs_scoring_audit.json');resources=load(ROOT/'stage12bs_resource_accounting.json')
    full=load(ROOT/'stage12bs_full_manifest.json');meta={r['item_id']:r for r in full['rows']}
    f=pd.read_parquet(ROOT/'stage12bs_failure_profiles.parquet');p=pd.read_parquet(ROOT/'stage12bs_pathology_analysis.parquet')
    ir=pd.read_parquet(ROOT/'stage12bs_integrity_results.parquet')
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'font.family':'DejaVu Sans'})

    fig,ax=plt.subplots(figsize=(11,4));ax.axis('off')
    boxes=[(.10,.65,'Original image'),(.46,.85,'E: frozen fact probe\n256-token cap'),(.46,.55,'N: original task\n32,768-token cap'),(.10,.20,'Frozen correct E*\nNo image'),(.46,.20,'O: facts + original task\n32,768-token cap'),(.83,.50,'Seal validity\nSeparate scoring\nFailure profile')]
    for x,y,t in boxes:ax.text(x,y,t,ha='center',va='center',bbox=dict(boxstyle='round,pad=.65',fc='#edf2f7',ec='#728299'))
    for start,end in [((.20,.69),(.32,.83)),((.20,.61),(.32,.56)),((.23,.20),(.32,.20)),((.61,.83),(.72,.60)),((.61,.55),(.72,.52)),((.61,.20),(.72,.40))]:
        ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='->',color='#44556a',lw=1.6))
    ax.set_title('Stage 12B-S: direct evidence probe, native task, equal-evidence oracle',pad=20)
    fig.text(.5,.01,'61 independent families • 157 frozen facts • B1–B4 only among complete-profile native failures',ha='center')
    figure_save(fig,'figure1_assay')

    fig,ax=plt.subplots(figsize=(9,4.8)); counts=list(result['classes'].values());total=sum(counts)
    bars=ax.barh(NAMES,counts,color=COLORS);ax.invert_yaxis();ax.set_xlim(0,max(counts)*1.35)
    for bar,n in zip(bars,counts):ax.text(n+.2,bar.get_y()+bar.get_height()/2,f'{n}/{total} ({n/total:.1%})',va='center')
    ax.set_xlabel('Independent families');ax.set_title('Native-failure composition: 26 complete profiles')
    fig.subplots_adjust(bottom=.28)
    fig.text(.12,.03,'10/61 families lack a complete E/N/O profile; missing arms are never scored as incorrect.\nE− includes unresolved evidence atoms: 4/11 B1 and 4/11 B4 have no explicitly incorrect atom.',fontsize=9)
    figure_save(fig,'figure2_failure_composition')

    fig,ax=plt.subplots(figsize=(7,4))
    for x,key,c in [(0,'True',COLORS[1]),(1,'False',COLORS[0])]:
        v=result['secondary_rescue'][key];point=v['estimate'];lo,hi=v['wilson95']
        ax.bar(x,point,color=c,width=.55);ax.errorbar(x,point,yerr=[[point-lo],[hi-point]],fmt='none',capsize=6,color='black')
        ax.text(x,hi+.04,f"{v['numerator']}/{v['denominator']}",ha='center')
    ax.set_xticks([0,1],['All E* atoms correct (E+)','At least one I/U atom (E−)']);ax.set_ylim(0,1);ax.set_ylabel('Oracle rescue fraction')
    ax.set_title('Oracle rescue among complete-profile native failures\nWilson 95% intervals; descriptive contrast')
    figure_save(fig,'figure3_oracle_rescue')

    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,arm in zip(axes,'NO'):
        matrix=[]
        for b in ['B1','B2','B3','B4']:
            sub=p[p.bottleneck==b];matrix.append([sub[f'{arm}_R{k}'].mean() for k in range(1,5)])
        im=ax.imshow(matrix,cmap='Blues',vmin=0,vmax=1,aspect='auto')
        for y,b in enumerate(['B1','B2','B3','B4']):
            sub=p[p.bottleneck==b]
            for x in range(4):ax.text(x,y,f"{sub[f'{arm}_R{x+1}'].sum()}/{len(sub)}",ha='center',va='center',color='white' if matrix[y][x]>.6 else 'black')
        ax.set_xticks(range(4),['R1\nRepeat','R2\nReopen','R3\nNonconverge','R4\nAdvancing']);ax.tick_params(axis='x',labelsize=9);ax.set_yticks(range(4),['B1','B2','B3','B4']);ax.set_title('Native N' if arm=='N' else 'Oracle O')
    fig.suptitle('Secondary reasoning behaviors by bottleneck (overlapping labels)',y=1.06)
    figure_save(fig,'figure4_pathology')

    examples=[]
    for b in ['B1','B2','B3','B4']:
        ss=f[f.bottleneck==b].sort_values('family_id')
        if len(ss):examples.append(ss.iloc[0].to_dict())
    example_record=dict(rule='Smallest lexicographic family_id in each nonempty frozen category',items=[dict(item_id=r['item_id'],family_id=r['family_id'],bottleneck=r['bottleneck']) for r in examples])
    example_path=ROOT/'audit/representative_examples.json'
    if example_path.exists():
        assert load(example_path)==example_record, 'Frozen representative selection changed'
    else:
        save(example_path,example_record)
    fig,axes=plt.subplots(len(examples),1,figsize=(12,2.9*len(examples)))
    for ax,r in zip(np.atleast_1d(axes),examples):
        m=meta[r['item_id']];e=load(origin_for(f"E_{r['item_id']}_v1")/'generations'/f"E_{r['item_id']}_v1"/'generation.json')['raw_decoded_response']
        question=m['question'].split('\n\nOptions:')[0]
        lines=[f"{r['bottleneck']} | MathVision {r['item_id']} | {r['family_id']}",
               'Question: '+question,'E*: '+'; '.join(x['gold_value'] for x in m['facts']),
               'E response: '+e.replace('\n','; '),
               'E result: '+('E+' if r['e'] else 'E−')+'; atoms: '+', '.join(json.loads(r['e_atom_labels_json'])),
               f"Final outcomes: N={r['N_outcome']}; O={r['O_outcome']}; source answer={m['answer']}",
               'Behaviors: '+ '; '.join(a+': '+(', '.join(f'R{k}' for k in range(1,6) if r[f'{a}_R{k}']) or 'none') for a in 'NO')]
        # Literal text avoids treating model LaTeX as matplotlib instructions.
        text='\n'.join(textwrap.fill(line.replace('$','').replace('\\',''),width=125) for line in lines)
        ax.axis('off');ax.text(0,1,text,va='top',fontsize=10,linespacing=1.4)
    fig.suptitle('Representative examples selected by family ID, not rhetorical strength',y=1.01)
    fig.tight_layout();figure_save(fig,'figure5_examples')

    report=Path('reports/stage12bs/v1');report.mkdir(parents=True,exist_ok=True)
    index=['# Stage 12B-S preserved responses','', '[Scientific summary](../../../outputs/stage12bs/v1/stage12bs_summary.md)','',
           'All 61 families, with original E/N/O responses. Existing generations are linked/copied for reading without modifying their originals.','',
           '| Item | Profile | Native | Oracle | Responses |','|---|---|---|---|---|']
    for r in f.to_dict('records'):
        i=r['item_id'];m=meta[i];path=report/f'{i}.md'
        body=[f'# MathVision {i}',f"Family: {r['family_id']}; profile: {r['bottleneck']}",'', '## Original question',m['question'],'',f"Source answer: `{m['answer']}`",'','## Frozen evidence']
        body.extend(f"- {x['probe_request']} **{x['gold_value']}**" for x in m['facts'])
        for a in 'ENO':
            tid=f'{a}_{i}_v1';rawpath=origin_for(tid)/'generations'/tid/'generation.json';g=load(rawpath)
            body.extend(['',f'## {a} response',f"Tokens: {g['tokens']}; stop: {g['finish_reason']}; technical commitment: `{r[f'{a}_outcome']}`.",
                         f'[Original generation JSON](../../../{rawpath})','', '````text',g['raw_decoded_response'],'````'])
        path.write_text('\n'.join(body)+'\n')
        index.append(f"| {i} | {r['bottleneck']} | {r['n']} | {r['o']} | [Read]({i}.md) |")
    (report/'index.md').write_text('\n'.join(index)+'\n')

    sens=load(ROOT/'stage12bs_sensitivity_results.json')
    summary=['# Stage 12B-S — full scientific failure profiling','',f"**{decision['decision']}**. Completed {now()}. The frozen full-cohort gate passed; labels are sealed and no follow-on experiment was launched.",'',
    '61 independent families (24 multiple choice, 37 open-ended), 157 frozen E* facts, and 183 E/N/O calls. Reused 72 calls on 24 families; generated exactly 111 on the remaining 37 without retries. Model, prompts, evidence, BF16/vLLM recipe, seeds and caps were unchanged. All 407 historical artifacts remain hash-preserved.','',
    '## Validity and denominators','',
    '| Arm | Input-valid | Scoreable | Pre-outcome caps | Cap after outcome |','|---|---:|---:|---:|---:|']
    for a in 'ENO':
        s=ir[ir.arm==a];summary.append(f"| {a} | {s.INPUT_VALID.sum()}/61 | {s.SCOREABLE.sum()}/61 | {s.TRUNCATED_BEFORE_OUTCOME.sum()} | {s.CAP_AFTER_OUTCOME.sum()} |")
    summary.extend(['','Denominators were sealed before gold was opened: N-scoreable=57, complete E/N/O profiles=51, technical unresolved=10. Four native outputs are unscoreable, not wrong. There are 29 native failures overall, of which 26 have complete profiles. O528 ended normally but answered a subsidiary fact rather than the task; E372 retained a placeholder. These remain technical missingness.','',
    '## Frozen primary results','', 'All intervals below are family-level Wilson 95% intervals.','', '| Endpoint | Count, estimate [95% CI] |','|---|---|'] )
    endpoint_names={'P1':'Native failure prevalence','P2':'Oracle-rescuable fraction','P3':'B1: evidence recovery / availability','P4':'B2: task-context access/use','P5':'B3: downstream reasoning','P6':'B4: mixed / unresolved'}
    for key,name in endpoint_names.items():summary.append(f"| {key} — {name} | {pct(result['endpoints'][key])} |")
    summary.extend(['',f"Native accuracy: {pct(result['native_accuracy'])}. Oracle accuracy: {pct(result['oracle_accuracy'])}; these marginal denominators differ, so use the paired contrast for direct comparison. All requested evidence atoms were correct in {pct(result['evidence_all_correct'])}.",'',
    'The profile meets the frozen informative rule because there are 29 scoreable native failures and B1 contains 11 families; both integrity gates pass. B2 has only one family and B3 only three. This does **not** support a substantial Lost-Keys prevalence claim or precise comparisons of the small categories.','',
    '**Evidence-scoring qualification:** E− means at least one INCORRECT or UNRESOLVED atom under the frozen all-atoms-correct rule. Of the 11 B1 families, seven have an explicitly incorrect atom and four have unresolved/underspecified evidence without an explicitly incorrect atom. The same 7+4 split occurs in B4. B1 therefore supports incomplete demonstrated evidence recovery; it must not be described as 11 proven visual misreads. The short E contract can understate recoverability when a response omits a required binding.','',
    '## Oracle contrasts and reasoning behavior','',f"Oracle rescue given E+: {pct(result['secondary_rescue']['True'])}; given E−: {pct(result['secondary_rescue']['False'])}.",''])
    for k,v in result['contrasts'].items():summary.append(f"- {k}: {v['estimate']:+.4f}; family-bootstrap 95% interval {v['percentile95']}; {v['defined_draws']}/4000 defined draws.")
    summary.extend(['','Bootstrap seed 120220260929; one equally weighted independent family per row. Rescue-by-E is descriptive, not a causal effect of probing. Paired oracle-minus-native accuracy is evaluated on the 51 complete profiles.','',
    f"Among the 38 families with N R1/R2/R3 behavior, oracle behavior resolved in 12, shared a pathology type in 21, and was unscoreable in five; none changed to a disjoint pathology type. N scientific failures:26 LOOP_OR_REOPEN,3 WRONG_CONVERGED. O scientific failures:13 LOOP_OR_REOPEN,4 WRONG_CONVERGED. R4 describes advancing computation and is not a pathology exclusion.",'',
    'E+ with pathological O failure occurs in items 2214, 1942, 3011 and 2013. The first three are B3; 2013 lacks a scoreable native answer and remains TECHNICAL_UNRESOLVED. This secondary set is not silently added to the primary profile. Per-label native-pathology rescue IDs are preserved in primary_inference.json.','',
    '## Prespecified sensitivities','', '| Analysis | N failure | Complete-profile failures | B1 / B2 / B3 / B4 | Oracle rescue | Yield rule |','|---|---|---:|---|---|---|'])
    for name,v in sens.items():summary.append(f"| {name} | {v['endpoints']['P1']['numerator']}/{v['native_denominator']} | {v['endpoints']['P2']['denominator']} | {' / '.join(map(str,v['classes'].values()))} | {v['endpoints']['P2']['numerator']}/{v['endpoints']['P2']['denominator']} | {v['decision']} |")
    summary.extend(['','The 37 previously untouched families alone yield only18 scoreable native failures and are PROFILE_SPARSE. This limits standalone fresh-cohort precision; it does not replace the preregistered 61-family main analysis. P1–P6 and intervals for both sensitivities are in the sensitivity artifact.','',
    '## Scoring and resource audit','',
    'All183 first scores were preserved. Second review covered94 mandatory ambiguity cases plus9 calls from3 randomly selected otherwise-unambiguous families (ceil20% of11). E agreement:81/84 atoms,33/34 whole-E outcomes; N41/41 and O28/28 task labels. The three E disagreements and own-arm adjudications remain logged. Random-audit agreement:E8/8 atoms,N3/3,O3/3. This is single-agent, separate-pass quality control, with other-arm outcomes and first labels absent from packets; it is not independent human reliability or a fresh reviewer unaware of prior context.','',
    f"New compute: {resources['allocated_gpu_hours']:.6f} allocated GPU-hours including initialization, below target5/hard7. Slurm127732–127735 all COMPLETED0:0 and released. Prior reused technical-stage costs were0.389167(Stage12B)+0.602778(Stage12B-R)GPUh, reported separately, never double-counted as new compute. No model/dataset download or environment mutation was needed.",'',
    'No mechanistic hidden-state claim follows from these behavioral categories. B2 does not show that the native trajectory internally held correct evidence; B3 does not prove perfect perception. Oracle evidence and prior sufficiency reviews remain frozen. Negative and unscoreable outcomes are preserved.','',
    '## Figures and evidence',''])
    for name,title in [('figure1_assay','Assay schematic'),('figure2_failure_composition','Native-failure composition'),('figure3_oracle_rescue','Oracle rescue by E'),('figure4_pathology','Reasoning behavior by bottleneck'),('figure5_examples','Deterministic examples')]:summary.append(f'- [{title}](figures/{name}.png) · [PDF](figures/{name}.pdf)')
    summary.extend(['','[All 61 families and full E/N/O responses](../../../reports/stage12bs/v1/index.md). Detailed machine-readable tables and all first/second/adjudication records are alongside this report.','',
    '## Exactly one recommendation','',decision['recommendation'],'','**STOP. This recommendation has not been executed.**'])
    (ROOT/'stage12bs_summary.md').write_text('\n'.join(summary)+'\n')


if __name__=='__main__':main()
